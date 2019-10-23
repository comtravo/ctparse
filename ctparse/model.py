import bz2
import logging
import os
import pickle
from datetime import datetime

from tqdm import tqdm

from .ctparse import _ctparse, _preprocess_string
from .scorer import DummyScorer

logger = logging.getLogger(__name__)


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
            for parse in _ctparse(_preprocess_string(test), ts, relative_match_len=1.0, timeout=0, max_stack_depth=0, scorer=DummyScorer()):
                y = parse.resolution.nb_str() == target

                # Build data set, one sample for each applied rule in
                # the sequence of rules applied in this production
                # *after* the matched regular expressions
                for i in range(1, len(parse.production)+1):
                    Xs.append([str(id) for p in parse.production[:i]])
                    ys.append(1 if y else -1)

                one_prod_passes |= y
                pos_parses += int(y)
                neg_parses += int(not y)
                pos_first_parses += int(y and first_prod)
                first_prod = False
                y_score.append((parse.score, y))
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
    return Xs, ys
