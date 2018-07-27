from unittest import TestCase
from ctparse.ctparse import run_corpus, _nb
from ctparse.time.corpus import corpus


class TestRunCorpus(TestCase):
    def test_run_corpus(self):
        X, y = run_corpus(corpus)
        _nb.fit(X, y)

    def test_run_corpus_failure(self):
        fail_corpus = [
            ('never produced',
             '2015-12-12T12:30',
             ('today', 'heute'))
        ]
        with self.assertRaises(Exception):
            run_corpus(fail_corpus)
