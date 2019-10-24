import pytest

from ctparse.model import run_corpus
from ctparse.time.corpus import corpus


def test_run_corpus() -> None:
    run_corpus(corpus)


def test_run_corpus_failure() -> None:
    fail_corpus = [
        ('never produced',
            '2015-12-12T12:30',
            ('today', 'heute'))
    ]
    with pytest.raises(Exception):
        run_corpus(fail_corpus)
