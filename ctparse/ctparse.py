import logging
import regex
import pickle
import bz2
import os
from tqdm import tqdm
from time import perf_counter
from datetime import datetime
from math import log

from . types import RegexMatch
from . nb import NB
from . rule import rules, _regex


logger = logging.getLogger(__name__)


# any character matched by a production regex will spoil this (as
# e.g. with '-'), since the expression sequence will not be "E1 - E2",
# and hence E1+E2 are only separated by these chars, but rather "E1 ED
# E3", where ED is the '-'-matching expression. Hence, to capture this
# case a corresponding rule is needed (at least for the time being)
# [Adding a "eat dash"-rule made things very slow and let to unmatched
# "trivial" cases]
_separator_regex = regex.compile(r'(^|$|\s|\n|,)+', regex.VERSION1)


# used in many places in rules
_regex_to_join = (r'(\-|to( the)?|(un)?til|bis( zum)?|auf( den)?|und|'
                  'no later than|spätestens?|at latest( at)?)')


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


def timeit(f):
    """timeit wrapper, use as `timeit(f)(args)

    Will return a tuple (f(args), t) where t the time in seconds the function call
    took to run.

    """
    def _wrapper(*args, **kwargs):
        start_time = perf_counter()
        res = f(*args, **kwargs)
        return res, perf_counter() - start_time
    return _wrapper


def _ctparse(txt, ts=None, timeout=0, nb=None):
    t_fun = _timeout(timeout)

    try:
        if not ts:
            ts = datetime.now()
        p, _tp = timeit(_match_regex)(txt)
        logger.debug('time in _match_regex: {:.0f}ms'.format(1000*_tp))
        stash, _ts = timeit(_regex_stack)(txt, p, t_fun)
        logger.debug('time in _regex_stack: {:.0f}ms'.format(1000*_ts))
        # add empty production path + counter of contained regex
        stash = [(s, tuple(r.id for r in s), nb.apply([r.id for r in s])) for s in stash]
        # track what has been added to the stash and do not add again
        stash_prod = set(s for s in stash)
        # track what has been emitted and do not emit agin
        parse_prod = set()
        while stash:
            t_fun()
            s, rule_seq, score = stash.pop()
            new_stash = []
            for r_name, r in rules.items():
                for r_match in match_rule(s, r[1]):
                    ns = r[0](ts, *s[r_match[0]:r_match[1]])
                    if ns is not None:
                        new_el = s[:r_match[0]] + (ns,) + s[r_match[1]:]
                        if new_el not in stash_prod:
                            new_seq = rule_seq + (r_name,)
                            new_score = nb.apply(new_seq)
                            new_stash.append((new_el, new_seq, new_score))
                            stash_prod.add(new_el)
            if not new_stash:
                for x in s:
                    if type(x) is not RegexMatch:
                        if x not in parse_prod:
                            parse_prod.add(x)
                            score_rule = nb.apply(rule_seq)
                            len_score = log(float(len(x))/len(txt))
                            logger.debug('New parse (len stash {} {:6.2f} {:6.2f})'
                                         ': {} -> {}'.format(
                                             len(stash), score_rule, len_score, txt, x.__repr__()))
                            yield x, rule_seq, score_rule + len_score

            else:
                stash.extend(new_stash)
                stash.sort(key=lambda s: s[2])
    except TimeoutError as e:
        logger.warning('Timeout on "{}"'.format(txt))
        yield None
        return


_model_file = os.path.join(os.path.dirname(__file__), 'models', 'model.pbz')
if os.path.exists(_model_file):
    logger.info('Loading model from {}'.format(_model_file))
    _nb = pickle.load(bz2.open(_model_file, 'rb'))
else:
    logger.warning('No model found, initializing empty model')
    _nb = NB()


def ctparse(txt, ts=None, timeout=0, debug=False):
    parsed = _ctparse(txt, ts, timeout=timeout, nb=_nb)
    if debug:
        return parsed
    else:
        parsed = [p for p in parsed if p]
        if not parsed or (len(parsed) == 1 and not parsed[0]):
            logger.warning('Failed to produce result for "{}"'.format(txt))
            return None
        parsed.sort(key=lambda tup: float(tup[2]))
        return parsed[-1]


def match_rule(seq, rule):
    if len(seq) == 0:
        return
    if len(rule) == 0:
        return
    i_r = 0
    i_s = 0
    r_len = len(rule)
    s_len = len(seq)
    while i_s < s_len:
        while i_s < s_len and i_r < r_len and rule[i_r](seq[i_s]):
            i_r += 1
            i_s += 1
        if i_r == r_len:
            yield i_s - r_len, i_s
        else:
            i_s += 1
        i_r = 0


def _match_regex(txt):
    """Match all known regex in txt and return a list of RegxMatch objects
    sorted by the start of the match. Overlapping matches of the same
    expression are not returned.

    :param txt: the text to match against
    :return: a list of RegexMatch objects ordered my Regex.mstart

    """
    matches = {RegexMatch(name, m)
               for name, re in _regex.items()
               for m in re.finditer(txt, overlapped=False, concurrent=True)}
    for m in matches:
        logger.debug('regex: {} -> {}'.format(txt, m.__repr__()))
    return sorted(matches, key=lambda x: (x.mstart, x.mend))


def _regex_stack(txt, regex_matches, t_fun=lambda: None):
    """assumes that regex_matches are sorted by increasing start index

    Algo: somewhere on paper, but in a nutshell:
    * stack empty

    * add all sequences of one expression to the stack, excludiong
      expressions which can be reached from "earlier" expressison
      (i.e. there is no gap between them):

      - say A and B have no gap inbetween and all sequences starting
        at A have already been produced. These be definition (which
        :-) include as sub-sequences all sequences starting at B. Any
        other sequences starting at B directly will not add valid
        variations, as each of them could be prefixed with a sequence
        starting at A

    * while the stack is not empty:

      * get top sequence s from stack

      * generate all possible continuation for this sequence,
        i.e. sequences where expression can be appended to the last
        element s[-1] in s and put these extended sequences on the stack

      * if no new productions could be generated for s, this is one
        result sequence.
    """

    n_rm = len(regex_matches)
    # Calculate the upper triangle of an n_rm x n_rm matrix M where
    # M[i, j] == 1 (for i<j) iff the expressions i and j are
    # consecutive (i.e. there is no gap and they can be put together
    # in one sequence).

    # import numpy as np
    # M = np.zeros(shape=(n_rm, n_rm), dtype=int)

    # --> avoid use of numpy here; since we need column sums below,
    # --> the representation of M is columns major, i.e. M[i] is the i-th
    # --> column; M[i, j] then basically becomes M[j][i]
    M = [[0 for _ in range(n_rm)] for _ in range(n_rm)]

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
            logger.debug(' -> sub sequence {}'.format(prod))
            yield prod


def run_corpus(corpus):
    """Load the corpus (currently hard coded), run it through ctparse with no timeout.

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
    at_least_one_failed = False
    pos_parses = neg_parses = 0
    Xs = []
    ys = []
    for target, ts, tests in tqdm(corpus):
        ts = datetime.strptime(ts, '%Y-%m-%dT%H:%M')
        all_tests_pass = True
        for test in tests:
            one_prod_passes = False
            for prod in _ctparse(test, ts, timeout=0, nb=_nb):
                if prod is None:
                    continue
                y = prod[0].nb_str() == target
                # Build data set, one sample for each applied rule in
                # the sequence of rules applied in this production
                # *after* the matched regular expressions
                X_prod, y_prod = _nb.map_prod(prod[1], y)
                Xs.extend(X_prod)
                ys.extend(y_prod)
                one_prod_passes |= y
                pos_parses += int(y)
                neg_parses += int(not y)
            if not one_prod_passes:
                logger.warning('failure: target "{}" never produced in "{}"'.format(target, test))
            all_tests_pass &= one_prod_passes
        if not all_tests_pass:
            logger.warning('failure: "{}" not always produced'.format(target))
            at_least_one_failed = True
    logger.info('share of correct parses in all parses: {:.2%}'.format(
        pos_parses/(pos_parses + neg_parses)))
    if at_least_one_failed:
        raise Exception('ctparse corpus has errors')
    return Xs, ys


def build_model(X, y, save=False):
    nb = NB()
    nb.fit(X, y)
    if save:
        pickle.dump(nb, bz2.open(_model_file, 'wb'))
    return nb
