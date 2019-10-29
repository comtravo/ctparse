import pytest

from ctparse.corpus import run_corpus
from ctparse.time.corpus import corpus


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
