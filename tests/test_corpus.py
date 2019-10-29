from datetime import datetime

import pytest

from ctparse.corpus import (TimeParseEntry, make_partial_rule_dataset,
                            run_corpus)
from ctparse.time.corpus import corpus
from ctparse.types import Time


def test_run_corpus() -> None:
    """The corpus passes if ctparse generates the desired
    solution for each test at least once. Otherwise it fails.
    """
    X, y = run_corpus(corpus)
    assert isinstance(y[0], bool)
    assert isinstance(X[0][0], str)


def test_run_corpus_failure() -> None:
    fail_corpus = [
        ('never produced',
            '2015-12-12T12:30',
            ('today', 'heute'))
    ]
    with pytest.raises(Exception):
        run_corpus(fail_corpus)


def test_make_partial_rule_dataset() -> None:
    ts = datetime(year=2019, month=10, day=1)
    entries = [
        TimeParseEntry("today at 5 pm", ts, Time(year=2019, month=10, day=1, hour=17, minute=0))
    ]

    X, y = zip(*make_partial_rule_dataset(entries))
    assert isinstance(y[0], bool)
    assert isinstance(X[0][0], str)
