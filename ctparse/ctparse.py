import logging
import regex
import pickle
import bz2
import os
from tqdm import tqdm
from time import perf_counter
from datetime import datetime
from math import log
from functools import wraps

from . types import RegexMatch
from . nb import NB
from . rule import rules, _regex


logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    pass


def _timeout(timeout):
    start_time = perf_counter()

    def _tt():
        if timeout == 0:
            return
        if perf_counter() - start_time > timeout:
            raise TimeoutError()
    return _tt


def _timeit(f):
    """timeit wrapper, use as `timeit(f)(args)

    Will return a tuple (f(args), t) where t the time in seconds the function call
    took to run.

    """
    @wraps(f)
    def _wrapper(*args, **kwargs):
        start_time = perf_counter()
        res = f(*args, **kwargs)
        return res, perf_counter() - start_time
    return _wrapper


class StackElement:
    '''A partial parse result with

    * prod: the current partial production
    * rules: the sequence of regular expressions and rules used/applied to produce prod
    * score: the score assigned to this production
    '''
    @classmethod
    def from_regex_matches(cls, regex_matches, txt_len):
        '''Create new initial stack element based on a production that has not
        yet been touched, i.e. it is only a sequence of matching
        regular expressions
        '''
        se = StackElement()
        se.prod = regex_matches
        se.rules = tuple(r.id for r in regex_matches)
        se.txt_len = txt_len
        se.max_covered_chars = se.prod[-1].mend - se.prod[0].mstart
        se.len_score = log(se.max_covered_chars/se.txt_len)
        se.update_score()

        logger.debug('='*80)
        logger.debug('-> checking rule applicability')
        # Reducing rules to only those applicable has no effect for
        # small stacks, but on larger there is a 10-20% speed
        # improvement
        se.applicable_rules, _ts = _timeit(se._filter_rules)(rules)
        logger.debug('of {} total rules {} are applicable in {}'.format(
            len(rules), len(se.applicable_rules), se.prod))
        logger.debug('time in _filter_rules: {:.0f}ms'.format(1000*_ts))
        logger.debug('='*80)

        return se

    def _filter_rules(self, rules):
        """find all rules that can be applied to the current prod sequence"""
        def _hasNext(it):
            try:
                next(it)
                return True
            except StopIteration as e:
                return False

        return {rule_name: r for rule_name, r in rules.items()
                if _hasNext(_seq_match(self.prod, r[1]))}

    @classmethod
    def from_rule_match(cls, se_old, rule_name, match, prod):
        se = StackElement()
        se.prod = se_old.prod[:match[0]] + (prod,) + se_old.prod[match[1]:]
        se.rules = se_old.rules + (rule_name,)
        # Refiltering does not give a speedup - actually rather 10%
        # speed loss se.applicable_rules =
        #
        # se._filter_rules(se_old.applicable_rules)
        se.applicable_rules = se_old.applicable_rules
        se.txt_len = se_old.txt_len
        se.max_covered_chars = se.prod[-1].mend - se.prod[0].mstart
        se.len_score = log(se.max_covered_chars/se.txt_len)
        se.update_score()
        return se

    def update_score(self):
        if _nb.hasModel:
            self.score = _nb.apply(self.rules) + self.len_score
        else:
            self.score = 0.0

    def apply_rule(self, ts, rule, rule_name, match):
        '''Check whether the production in rule can be applied to this stack
        element. If yes, return a copy where this update is
        incorporated in the production, the record of applied rules
        and the score.
        '''
        # prod, prod_name, start, end):
        prod = rule[0](ts, *self.prod[match[0]:match[1]])
        if prod is not None:
            return StackElement.from_rule_match(self, rule_name, match, prod)
        else:
            return

    def __lt__(self, other):
        '''Sort stack elements by (a) the length of text they can
        (potentially) cover and (b) the score assigned to the
        production.

        a < b <=> a.max_covered_chars < b.max_covered_chars or
                  (a.max_covered_chars <= b.max_covered_chars and a.score < b.score)
        '''
        return ((self.max_covered_chars < other.max_covered_chars) or
                (self.max_covered_chars == other.max_covered_chars and
                 self.score < other.score))


class CTParse:
    def __init__(self, resolution, production, score):
        self.resolution = resolution
        self.production = production
        self.score = score

    def __repr__(self):
        return 'CTParse({}, {}, {})'.format(
            self.resolution, self.production, self.score)

    def __str__(self):
        return '{} s={:.3f} p={}'.format(self.resolution,
                                         self.score,
                                         self.production)


def _ctparse(txt, ts=None, timeout=0, relative_match_len=0, max_stack_depth=0):
    def get_score(seq, len_match):
        if _nb.hasModel:
            return _nb.apply(seq) + log(len_match/len(txt))
        else:
            return 0.0

    t_fun = _timeout(timeout)

    try:
        if ts is None:
            ts = datetime.now()
        logger.debug('='*80)
        logger.debug('-> matching regular expressions')
        p, _tp = _timeit(_match_regex)(txt)
        logger.debug('time in _match_regex: {:.0f}ms'.format(1000*_tp))

        logger.debug('='*80)
        logger.debug('-> building initial stack')
        stack, _ts = _timeit(_regex_stack)(txt, p, t_fun)
        logger.debug('time in _regex_stack: {:.0f}ms'.format(1000*_ts))
        # add empty production path + counter of contained regex
        stack = [StackElement.from_regex_matches(s, len(txt)) for s in stack]
        logger.debug('initial stack length: {}'.format(len(stack)))
        # sort stack by length of covered string and - if that is equal - score
        # --> last element is longest coverage and highest scored
        stack.sort()
        # only keep initial stack elements that cover at least
        # relative_match_len characters of what the highest
        # scored/covering stack element does cover
        stack = [s for s in stack
                 if s.max_covered_chars >= stack[-1].max_covered_chars * relative_match_len]
        logger.debug('stack length after relative match length: {}'.format(len(stack)))
        # limit depth of stack
        stack = stack[-max_stack_depth:]
        logger.debug('stack length after max stack depth limit: {}'.format(len(stack)))

        # track what has been added to the stack and do not add again
        # if the score is not better
        stack_prod = {}
        # track what has been emitted and do not emit agin
        parse_prod = {}
        while stack:
            t_fun()
            s = stack.pop()
            logger.debug('-'*80)
            logger.debug('producing on {}, score={:.2f}'.format(s.prod, s.score))
            new_stack = []
            for r_name, r in s.applicable_rules.items():
                for r_match in _match_rule(s.prod, r[1]):
                    # apply production part of rule
                    new_s = s.apply_rule(ts, r, r_name, r_match)
                    if new_s and stack_prod.get(new_s.prod, new_s.score - 1) < new_s.score:
                        # either new_s.prod has never been produced
                        # before or the score of new_s is higher than
                        # a previous identical production
                        new_stack.append(new_s)
                        logger.debug('  {} -> {}, score={:.2f}'.format(
                            r_name, new_s.prod, new_s.score))
                        stack_prod[new_s.prod] = new_s.score
            if not new_stack:
                logger.debug('~'*80)
                logger.debug('no rules applicable: emitting')
                # no new productions were generated from this stack element.
                # emit all (probably partial) production
                for x in s.prod:
                    if not isinstance(x, RegexMatch):
                        # update score to be only relative to the text
                        # match by the actual production, not the
                        # initial sequence of regular expression
                        # matches
                        score_x = get_score(s.rules, len(x))
                        # only emit productions not emitted before or
                        # productions emitted before but scored higher
                        # if True:
                        if parse_prod.get(x, score_x - 1) < score_x:
                            parse_prod[x] = score_x
                            logger.debug(' => {}, score={:.2f}, '.format(
                                x.__repr__(), score_x))
                            yield CTParse(x, s.rules, score_x)
            else:
                # new productions generated, put on stack and sort
                # stack by highst score
                stack.extend(new_stack)
                stack.sort()
                stack = stack[-max_stack_depth:]
                logger.debug('added {} new stack elements, depth after trunc: {}'.format(
                    len(new_stack), len(stack)))
    except TimeoutError as e:
        logger.debug('Timeout on "{}"'.format(txt))
        return


_model_file = os.path.join(os.path.dirname(__file__), 'models', 'model.pbz')
if os.path.exists(_model_file):
    logger.info('Loading model from {}'.format(_model_file))
    _nb = pickle.load(bz2.open(_model_file, 'rb'))
else:
    logger.warning('No model found, initializing empty model')
    _nb = NB()


# replace all comma, semicolon, whitespace, invisible control, opening and closing brackets
_repl1 = regex.compile(r'[,;\pZ\pC\p{Ps}\p{Pe}]+', regex.VERSION1)
_repl2 = regex.compile('(\p{Pd}|[\u2010-\u2015]|\u2043)+', regex.VERSION1)


def _preprocess_string(txt):
    return _repl2.sub('-', _repl1.sub(' ', txt, concurrent=True).strip()).strip()


def ctparse(txt, ts=None, timeout=1.0, debug=False, relative_match_len=1.0, max_stack_depth=10):
    '''Parse a string *txt* into a time expression

    :param ts: reference time
    :type ts: datetime.datetime
    :param timeout: timeout for parsing in seconds; timeout=0
                    indicates no timeout
    :type timeout: int
    :param debug: if True do return iterator over all resolution, else
                  return highest scoring one (default=False)
    :type debug: bool
    :param relative_match_len: relative minimum share of
                               characters an initial regex match sequence must
                               cover compared to the longest such sequence found
                               to be considered for productions (default=1.0)
    :type relative_match_len: float
    :param max_stack_depth: limit the maximal number of highest scored candidate productions
                            considered for future productions (default=10); set to 0 to not
                            limit
    :type max_stack_depth: int

    :returns: Time or Interval
    '''
    parsed = _ctparse(_preprocess_string(txt), ts, timeout=timeout,
                      relative_match_len=relative_match_len, max_stack_depth=max_stack_depth)
    if debug:
        return parsed
    else:
        parsed = [p for p in parsed]
        if not parsed or (len(parsed) == 1 and not parsed[0]):
            logger.warning('Failed to produce result for "{}"'.format(txt))
            return
        parsed.sort(key=lambda p: p.score)
        return parsed[-1]


def _match_rule(seq, rule):
    if not seq:
        return
    if not rule:
        return
    i_r = 0
    i_s = 0
    r_len = len(rule)
    s_len = len(seq)
    while i_s < s_len:
        if rule[0](seq[i_s]):
            i_start = i_s + 1
            i_r = 1
            while i_start < s_len and i_r < r_len and rule[i_r](seq[i_start]):
                i_r += 1
                i_start += 1
            if i_r == r_len:
                yield i_s, i_start
        i_s += 1


def _seq_match(seq, pat, offset=0):
    # :param seq: a list of intermediate productions, either of type
    # RegexMatch or some other Artifact
    #
    # :param pat: a list of rule patterns to be matched, i.e. either a
    # RegexMatch or a callable
    #
    # Determine whether the pattern pat matches the sequence seq and
    # return a list of lists, where each sub-list contains those
    # indices where the RegexMatch objects in pat are located in seq.
    #
    # A pattern pat only matches seq, iff each RegexMatch in pat is in
    # seq in the same order and iff between two RegexMatches aligned
    # to seq there is at least one additional element in seq. Reason:
    #
    # * Rule patterns never have two consequitive RegexMatch objects.
    #
    # * Hence there must be some predicate/dimension between two
    # * RegexMatch objects.
    #
    # * For the whole pat to match there must then be at least one
    #  element in seq that can product this intermediate bit
    #
    # If pat does not start with a RegexMatch then there must be at
    # least one element in seq before the first RegexMatch in pat that
    # is alignes on seq. Likewise, if pat does not end with a
    # RegexMatch, then there must be at least one additional element
    # in seq to match the last non-RegexMatch element in pat.
    #
    # STRONG ASSUMPTIONS ON ARGUMENTS: seq and pat do not contain
    # consequiteve elements which are both of type RegexMatch! Callers
    # obligation to ensure this!

    if not pat:
        # if pat is empty yield the empty match
        yield []
    elif not seq or not pat:
        # if either seq or pat is empty there will be no match
        return
    elif pat[-1].__name__ != '_regex_match':
        # there must be at least one additional element in seq at the
        # end
        yield from _seq_match(seq[:-1], pat[:-1], offset)
    elif len(pat) > len(seq):
        # if pat is longer than seq it cannot match
        return
    else:
        p1 = pat[0]
        # if p1 is not a RegexMatch, then continue on next pat and
        # advance sequence by one
        if p1.__name__ != '_regex_match':
            yield from _seq_match(seq[1:], pat[1:], offset+1)
        else:
            # Get number of RegexMatch in p
            n_regex = sum(1 for p in pat if p.__name__ == '_regex_match')
            # For each occurance of RegexMatch pat[0] in seq
            for iseq, s in enumerate(seq):
                # apply _regex_match check
                if p1(s):
                    # for each match of pat[1:] in seq[iseq+1:], yield a result
                    for subm in _seq_match(seq[iseq+1:], pat[1:], offset+iseq+1):
                        if len(subm) == n_regex - 1:
                            # only yield if all subsequent RegexMatch
                            # have been aligned!
                            yield [iseq+offset] + subm


def _match_regex(txt):
    """Match all known regex in txt and return a list of RegxMatch objects
    sorted by the start of the match. Overlapping matches of the same
    expression are returned as well.

    :param txt: the text to match against
    :return: a list of RegexMatch objects ordered my Regex.mstart

    """
    matches = {RegexMatch(name, m)
               for name, re in _regex.items()
               for m in re.finditer(txt, overlapped=False, concurrent=True)}
    for m in matches:
        logger.debug('regex: {}'.format(m.__repr__()))
    return sorted(matches, key=lambda x: (x.mstart, x.mend))


def _regex_stack(txt, regex_matches, t_fun=lambda: None):
    """assumes that regex_matches are sorted by increasing start index

    Algo: somewhere on paper, but in a nutshell:
    * stack empty

    * add all sequences of one expression to the stack, excluding
      expressions which can be reached from "earlier" expressison
      (i.e. there is no gap between them):

      - say A and B have no gap inbetween and all sequences starting
        at A have already been produced. These be definition (which?
        :-) include as sub-sequences all sequences starting at B. Any
        other sequences starting at B directly will not add valid
        variations, as each of them could be prefixed with a sequence
        starting at A

    * while the stack is not empty:

      * get top sequence s from stack

      * generate all possible continuations for this sequence,
        i.e. sequences where expression can be appended to the last
        element s[-1] in s and put these extended sequences on the stack

      * if no new productions could be generated for s, this is one
        result sequence.
    """
    prods = []
    n_rm = len(regex_matches)
    # Calculate the upper triangle of an n_rm x n_rm matrix M where
    # M[i, j] == 1 (for i<j) iff the expressions i and j are
    # consecutive (i.e. there is no gap and they can be put together
    # in one sequence).

    # import numpy as np
    # M = np.zeros(shape=(n_rm, n_rm), dtype=int)

    # --> avoid use of numpy here; since we need column sums below,
    # --> the representation of M is columns major, i.e. M[i] is the i-th
    # --> column; M[i, j] then basically becomes M[j][i]
    M = [[0 for _ in range(n_rm)] for _ in range(n_rm)]

    _separator_regex = regex.compile(r'\s*', regex.VERSION1)

    def get_m_dist(m1, m2):
        # 1 if there is no relevant gap between m1 and m2, 0 otherwise
        # assumes that m1 and m2 are sorted be their start index
        if m2.mstart < m1.mend:
            return 0  # Overlap
        gap_match = _separator_regex.fullmatch(
            txt[m1.mend:m2.mstart])
        if gap_match:
            return 1  # No Gap
        else:
            return 0  # Gap

    for i in range(n_rm):
        for j in range(i+1, n_rm):
            M[j][i] = get_m_dist(regex_matches[i], regex_matches[j])

    stack = [(i,) for i in reversed(range(n_rm)) if sum(M[i]) == 0]
    while stack:
        t_fun()
        s = stack.pop()
        i = s[-1]
        new_prod = False
        for j in range(i+1, n_rm):
            if M[j][i] == 1:
                stack.append(s + (j,))
                new_prod = True
        if not new_prod:
            prod = tuple(regex_matches[i] for i in s)
            logger.debug('regex stack {}'.format(prod))
            prods.append(prod)
    return prods


def run_corpus(corpus):
    """Load the corpus (currently hard coded), run it through ctparse with
    no timeout and no limit on the stack depth.

    The corpus passes if ctparse generates the desired solution for
    each test at least once. Otherwise it fails.

    While testing this, a labeled data set (X, y) is generated based
    on *all* productions. Given a final production p, based on initial
    regular expression matches r_0, ..., r_n, which are then
    subsequently transformed using production rules p_0, ..., p_m,
    will result in the samples

    [r_0, ..., r_n, p_0, 'step_0']
    [r_0, ..., r_n, p_0, p_1, 'step_1']
    ...
    [r_0, ..., r_n, p_0, ..., p_m, 'step_m']

    All samples from one production are given the same label: 1 iff
    the final production was correct, -1 otherwise.

    """
    model_old = _nb._model
    _nb._model = None
    at_least_one_failed = False
    # pos_parses: number of parses that are correct
    # neg_parses: number of parses that are wrong
    # pos_first_parses: number of first parses generated that are correct
    # pos_best_scored: number of correct parses that have the best score
    pos_parses = neg_parses = pos_first_parses = pos_best_scored = 0
    total_tests = 0
    Xs = []
    ys = []
    for target, ts, tests in tqdm(corpus):
        ts = datetime.strptime(ts, '%Y-%m-%dT%H:%M')
        all_tests_pass = True
        for test in tests:
            one_prod_passes = False
            first_prod = True
            y_score = []
            for prod in _ctparse(_preprocess_string(test), ts, relative_match_len=1.0):
                y = prod.resolution.nb_str() == target
                # Build data set, one sample for each applied rule in
                # the sequence of rules applied in this production
                # *after* the matched regular expressions
                X_prod, y_prod = _nb.map_prod(prod.production, y)
                Xs.extend(X_prod)
                ys.extend(y_prod)
                one_prod_passes |= y
                pos_parses += int(y)
                neg_parses += int(not y)
                pos_first_parses += int(y and first_prod)
                first_prod = False
                y_score.append((prod.score, y))
            if not one_prod_passes:
                logger.warning('failure: target "{}" never produced in "{}"'.format(target, test))
            pos_best_scored += int(max(y_score, key=lambda x: x[0])[1])
            total_tests += len(tests)
            all_tests_pass &= one_prod_passes
        if not all_tests_pass:
            logger.warning('failure: "{}" not always produced'.format(target))
            at_least_one_failed = True
    logger.info('run {} tests on {} targets with a total of '
                '{} positive and {} negative parses (={})'.format(
                    total_tests, len(corpus), pos_parses, neg_parses,
                    pos_parses+neg_parses))
    logger.info('share of correct parses in all parses: {:.2%}'.format(
        pos_parses/(pos_parses + neg_parses)))
    logger.info('share of correct parses being produced first: {:.2%}'.format(
        pos_first_parses/(pos_parses + neg_parses)))
    logger.info('share of correct parses being scored highest: {:.2%}'.format(
        pos_best_scored/total_tests))
    if at_least_one_failed:
        raise Exception('ctparse corpus has errors')
    _nb._model = model_old
    return Xs, ys


#
# Not unittested - would take very long time to run these
#

def build_model(X, y, save=False):  # pragma: no cover
    nb = NB()
    nb.fit(X, y)
    if save:
        pickle.dump(nb, bz2.open(_model_file, 'wb'))
    return nb


def regenerate_model():  # pragma: no cover
    from . time.corpus import corpus as corpus_time
    from . time.auto_corpus import corpus as auto_corpus
    global _nb
    logger.info('Regenerating model')
    _nb = NB()
    X, y = run_corpus(corpus_time + auto_corpus)
    logger.info('Got {} training samples'.format(len(y)))
    build_model(X, y, save=True)
