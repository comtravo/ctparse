"""This test runs the implicit tests coded for in the corpora"""
import pytest
from ctparse.ctparse import run_corpus, _nb
from ctparse.time.corpus import corpus


@pytest.mark.slow
def test_run_corpus():
    X, y = run_corpus(corpus)
    _nb.fit(X, y)
