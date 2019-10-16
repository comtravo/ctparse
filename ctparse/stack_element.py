
from typing import Tuple, Union
from .types import Artifact
from .rule import RegexMatch, rules
from .timing import timeit
import logging

logger = logging.getLogger(__name__)
# TODO: rename this as PartialParse? And the scored is assigned separately?


class StackElement:
    '''A partial parse result with

    * prod: the current partial production
    * rules: the sequence of regular expressions and rules used/applied to produce prod
    * score: the score assigned to this production
    '''

    def __init__(self, prod: Tuple[Artifact], rules: Tuple[Union[int, str]]):
        assert isinstance(rules, tuple)
        assert isinstance(prod, tuple)
        self.prod = prod
        self.rules = rules
        self.max_covered_chars = prod[-1].mend - prod[0].mstart
        self.score = 0.0

    @classmethod
    def from_regex_matches(cls, regex_matches, txt_len):
        '''Create new initial stack element based on a production that has not
        yet been touched, i.e. it is only a sequence of matching
        regular expressions
        '''
        se = StackElement(regex_matches, tuple(r.id for r in regex_matches))

        logger.debug('='*80)
        logger.debug('-> checking rule applicability')
        # Reducing rules to only those applicable has no effect for
        # small stacks, but on larger there is a 10-20% speed
        # improvement
        se.applicable_rules, _ts = timeit(se._filter_rules)(rules)
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
            except StopIteration:
                return False

        return {rule_name: r for rule_name, r in rules.items()
                if _hasNext(_seq_match(self.prod, r[1]))}

    # TODO: This could be a regular method, like append_rule_match
    # that generates a new rule, which is actually defined below in apply_rule.
    # This makes the following kinda superfluous?
    @classmethod
    def from_rule_match(cls, se_old: 'StackElement', rule_name: str, match: RegexMatch, prod):
        se = StackElement(se_old.prod[:match[0]] + (prod,) +
                          se_old.prod[match[1]:], se_old.rules + (rule_name,))

        # Refiltering does not give a speedup - actually rather 10%
        # speed loss se.applicable_rules =
        #
        # se._filter_rules(se_old.applicable_rules)
        se.applicable_rules = se_old.applicable_rules
        return se

    def update_score(self, scorer, txt, ts):
        self.score = scorer.score(txt, ts, self)

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
