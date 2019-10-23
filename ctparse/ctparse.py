import logging
from datetime import datetime
from math import log
from typing import Dict, Iterator, List, Optional, Tuple, Union

import regex
from tqdm import tqdm

from .nb import NB, _nb
from .partial_parse import PartialParse
from .rule import _regex, rules
# Avoid collision with variable "timeout"
from .timers import CTParseTimeoutError, timeit
from .timers import timeout as timeout_
from .types import Interval, RegexMatch, Time

logger = logging.getLogger(__name__)


class CTParse:
    def __init__(self,
                 resolution: Union[Time, Interval],
                 production: Tuple[Union[int, str], ...],
                 score: float) -> None:
        """A possible parse returned by ctparse.

        :param resolution: the parsed `Time` or `Interval`
        :param production: the sequence of rules (productions) used to arrive
          at the parse
        :param score: a numerical score used to rank parses. A high score means
          a more likely parse
        """
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


def ctparse(
        txt: str, ts: Optional[datetime] = None, timeout=1.0, debug=False,
        relative_match_len=1.0, max_stack_depth=10) -> Optional[CTParse]:
    '''Parse a string *txt* into a time expression

    :param ts: reference time
    :type ts: datetime.datetime
    :param timeout: timeout for parsing in seconds; timeout=0
                    indicates no timeout
    :type timeout: float
    :param debug: if True do return iterator over all resolution, else
                  return highest scoring one (default=False)
    :param relative_match_len: relative minimum share of
                               characters an initial regex match sequence must
                               cover compared to the longest such sequence found
                               to be considered for productions (default=1.0)
    :type relative_match_len: float
    :param max_stack_depth: limit the maximal number of highest scored candidate productions
                            considered for future productions (default=10); set to 0 to not
                            limit
    :type max_stack_depth: int
    :returns: Optional[CTParse]
    '''
    parsed = ctparse_gen(txt, ts, timeout=timeout,
                         relative_match_len=relative_match_len,
                         max_stack_depth=max_stack_depth)
    # TODO: keep debug for back-compatibility, but remove it later
    if debug:
        return parsed
    else:
        parsed = list(parsed)
        if not parsed or (len(parsed) == 1 and not parsed[0]):
            logger.warning('Failed to produce result for "{}"'.format(txt))
            return
        parsed.sort(key=lambda p: p.score)
        return parsed[-1]


def ctparse_gen(txt: str, ts: Optional[datetime] = None, timeout=1.0, relative_match_len=1.0,
                max_stack_depth=10) -> Iterator[CTParse]:
    """Generate parses for the string *txt*.

    This function is equivalent to ctparse, with the exeption that it returns an iterator
    over the matches as soon as they are produced.
    """
    return _ctparse(_preprocess_string(txt), ts, timeout=timeout,
                    relative_match_len=relative_match_len, max_stack_depth=max_stack_depth)


def _ctparse(txt, ts, timeout, relative_match_len, max_stack_depth):
    def get_score(seq, len_match):
        if _nb.hasModel:
            return _nb.apply(seq) + log(len_match/len(txt))
        else:
            return 0.0

    t_fun = timeout_(timeout)

    try:
        if ts is None:
            ts = datetime.now()
        logger.debug('='*80)
        logger.debug('-> matching regular expressions')
        p, _tp = timeit(_match_regex)(txt, _regex)
        logger.debug('time in _match_regex: {:.0f}ms'.format(1000*_tp))

        logger.debug('='*80)
        logger.debug('-> building initial stack')
        stack, _ts = timeit(_regex_stack)(txt, p, t_fun)
        logger.debug('time in _regex_stack: {:.0f}ms'.format(1000*_ts))
        # add empty production path + counter of contained regex
        stack = [PartialParse.from_regex_matches(s, len(txt)) for s in stack]
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
            new_stack_elements = []
            for r_name, r in s.applicable_rules.items():
                for r_match in _match_rule(s.prod, r[1]):
                    # apply production part of rule
                    new_s = s.apply_rule(ts, r, r_name, r_match)
                    if new_s and stack_prod.get(new_s.prod, new_s.score - 1) < new_s.score:
                        # either new_s.prod has never been produced
                        # before or the score of new_s is higher than
                        # a previous identical production
                        new_stack_elements.append(new_s)
                        logger.debug('  {} -> {}, score={:.2f}'.format(
                            r_name, new_s.prod, new_s.score))
                        stack_prod[new_s.prod] = new_s.score
            if not new_stack_elements:
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
                        if parse_prod.get(x, score_x - 1) < score_x:
                            parse_prod[x] = score_x
                            logger.debug(' => {}, score={:.2f}, '.format(
                                x.__repr__(), score_x))
                            yield CTParse(x, s.rules, score_x)
            else:
                # new productions generated, put on stack and sort
                # stack by highst score
                stack.extend(new_stack_elements)
                stack.sort()
                stack = stack[-max_stack_depth:]
                logger.debug('added {} new stack elements, depth after trunc: {}'.format(
                    len(new_stack_elements), len(stack)))
    except CTParseTimeoutError:
        logger.debug('Timeout on "{}"'.format(txt))
        return


# replace all comma, semicolon, whitespace, invisible control, opening and closing brackets
_repl1 = regex.compile(r'[,;\pZ\pC\p{Ps}\p{Pe}]+', regex.VERSION1)
_repl2 = regex.compile(r'(\p{Pd}|[\u2010-\u2015]|\u2043)+', regex.VERSION1)


def _preprocess_string(txt):
    return _repl2.sub('-', _repl1.sub(' ', txt, concurrent=True).strip()).strip()


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


def _match_regex(txt: str, regexes: Dict[str, regex.Regex]) -> List[RegexMatch]:
    # Match a collection of regexes in *txt*
    #
    # Overlapping matches of the same expression are returned as well. The returened
    # RegexMatch objects are sorted by the start of the match
    # :param txt: the text to match against
    # :param regexes: a collection of regexes name->pattern
    # :return: a list of RegexMatch objects ordered my RegexMatch.mstart
    matches = {RegexMatch(name, m)
               for name, re in regexes.items()
               for m in re.finditer(txt, overlapped=False, concurrent=True)}
    for m in matches:
        logger.debug('regex: {}'.format(m.__repr__()))
    return sorted(matches, key=lambda x: (x.mstart, x.mend))


def _regex_stack(txt, regex_matches: List[RegexMatch], on_do_iter=lambda: None) -> List[Tuple[RegexMatch]]:
    # Group contiguous RegexMatch objects together.
    #
    # Assumes that regex_matches are sorted by increasing start index. on_do_iter
    # is a callback that will be invoked every time the algorithm performs a loop.
    #
    # Example:
    # Say you have the following text, where the regex matches are the
    # words between square brackets.
    #
    # [Tomorrow] I want to go to the movies between [2] [pm] and [5] [pm].
    #
    # This function will return the matches that are contiguous (excluding space characters)
    # [Tomorrow]
    # [2], [pm]
    # [5], [pm]
    #
    # This also works with overlapping matches.
    #
    # Algo:
    # * initialize an empty stack
    #
    # * add all sequences of one expression to the stack, excluding
    #   expressions which can be reached from "earlier" expressison
    #   (i.e. there is no gap between them):
    #
    #   - say A and B have no gap inbetween and all sequences starting
    #     at A have already been produced. These by definition(which?: -) include as sub-sequences all sequences starting at B. Any
    #     other sequences starting at B directly will not add valid
    #     variations, as each of them could be prefixed with a sequence
    #     starting at A
    #
    # * while the stack is not empty:
    #
    #   * get top sequence s from stack
    #
    #   * generate all possible continuations for this sequence,
    #     i.e. sequences where expression can be appended to the last
    #     element s[-1] in s and put these extended sequences on the stack
    #
    #   * if no new continuation could be generated for s, this sequence of RegexMatch is appended
    #     to the list of results.

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

    # NOTE(glanaro): I believe this means that this is a beginning node.
    # why reversed?
    stack = [(i,) for i in reversed(range(n_rm)) if sum(M[i]) == 0]
    while stack:
        on_do_iter()
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
