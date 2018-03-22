"""This test runs the implicit tests coded for in the corpora"""
import pytest
from ctparse.ctparse import run_corpus, _nb


@pytest.mark.slow
def test_run_corpus():
    X, y = run_corpus()
    _nb.fit(X, y)
