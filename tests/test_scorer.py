import datetime
import random

from ctparse.nb_scorer import NaiveBayesScorer, train_naive_bayes
from ctparse.partial_parse import PartialParse
from ctparse.scorer import DummyScorer, RandomScorer
from ctparse.types import Interval, Time


def test_dummy():
    scorer = DummyScorer()
    pp = PartialParse((Time(), Interval()), ("rule1", "rule2"))

    assert scorer.score("a", datetime.datetime(2019, 1, 1), pp) == 0.0
    assert scorer.score_final("a", datetime.datetime(2019, 1, 1), pp, pp.prod[0]) == 0.0


def test_random():
    rng = random.Random(42)
    scorer = RandomScorer(rng)

    pp = PartialParse((Time(), Interval()), ("rule1", "rule2"))

    assert 0.0 <= scorer.score("a", datetime.datetime(2019, 1, 1), pp) <= 1.0
    assert 0.0 <= scorer.score_final("a", datetime.datetime(2019, 1, 1), pp, pp.prod[1]) <= 1.0


def test_nbscorer():
    # We only test that it runs just fine
    X = [("a", "b"), ("a",), ("b"), ("a", "b", "a", "b")]
    y = [False, True, True, False]

    model = train_naive_bayes(X, y)
    scorer = NaiveBayesScorer(model)

    pp = PartialParse((Time(), Interval()), ("rule1", "rule2"))

    pp.prod[0].mstart = 0
    pp.prod[1].mend = 1

    pp.prod[0].mend = 1
    pp.prod[1].mend = 2

    assert 0.0 <= scorer.score("ab", datetime.datetime(2019, 1, 1), pp) <= 1.0
    assert 0.0 <= scorer.score_final("ab", datetime.datetime(2019, 1, 1), pp, pp.prod[1]) <= 1.0
