from unittest import TestCase

from ctparse.build_corpus import make_partial_rule_corpus
from ctparse.time.corpus import corpus


class TestRunCorpus(TestCase):
    def test_run_corpus(self):
        X, y = make_partial_rule_corpus(corpus)
        self.assertIsInstance(X, list)
        self.assertIsInstance(X[0], list)
        self.assertIsInstance(y[0], int)
        self.assertEqual(len(X), len(y))

    def test_run_corpus_failure(self):
        fail_corpus = [
            ('never produced',
             '2015-12-12T12:30',
             ('today', 'heute'))
        ]
        with self.assertRaises(Exception):
            make_partial_rule_corpus(fail_corpus)
