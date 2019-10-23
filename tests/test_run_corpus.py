import pytest

from ctparse.model import _nb, run_corpus
from ctparse.time.corpus import corpus


def test_run_corpus():
    X, y = run_corpus(corpus)
    _nb.fit(X, y)


def test_run_corpus_failure():
    fail_corpus = [
        ('never produced',
            '2015-12-12T12:30',
            ('today', 'heute'))
    ]
    with pytest.raises(Exception):
        run_corpus(fail_corpus)
