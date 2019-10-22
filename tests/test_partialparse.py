from unittest import TestCase
from ctparse.partial_parse import PartialParse, _seq_match
from ctparse.types import RegexMatch, Time
import datetime
import regex


class TestPartialParse(TestCase):

    def test_partial_parse(self):
        match_a = regex.match("(?<R1>a)", "ab")
        match_b = next(regex.finditer("(?<R2>b)", "ab"))

        pp = PartialParse.from_regex_matches((RegexMatch(1, match_a), RegexMatch(2, match_b)), 2)

        self.assertEqual(len(pp.prod), 2)
        self.assertEqual(len(pp.rules), 2)
        self.assertIsInstance(pp.score, float)

        def mock_rule(ts, a):
            return Time()

        pp2 = pp.apply_rule(datetime.datetime(day=1, month=1, year=2015),
                            (mock_rule, lambda x: True), 'mock_rule', (0, 1))

        self.assertNotEqual(pp, pp2)

        with self.assertRaises(ValueError):
            PartialParse([], [])

    def test_seq_match(self):
        # NOTE: we are testing a private function because the algorithm
        # is quite complex

        def make_rm(i):
            def _regex_match(s):
                return s == i
            return _regex_match

        # empty sequence, empty pattern: matches on a single empty sequence
        self.assertEqual(list(_seq_match([], [])), [[]])
        # non empty sequence, empty pattern matches on an empty sequence
        self.assertEqual(list(_seq_match(['a', 'b'], [])), [[]])
        # non empty sequence, non empty pattern that does not apper: no match
        self.assertEqual(list(_seq_match(['a', 'b'], [make_rm(1)])), [])
        # empty sequence, non empty pattern: no match
        self.assertEqual(list(_seq_match([], [make_rm(1)])), [])
        # sequence shorter than pattern: no match
        self.assertEqual(list(_seq_match(['a'], [make_rm(1), make_rm(2)])), [])
        # seq = pat
        self.assertEqual(list(_seq_match([1], [make_rm(1)])), [[0]])
        self.assertEqual(list(_seq_match([1, 2, 3], [make_rm(1)])), [[0]])
        self.assertEqual(list(_seq_match([1, 2, 3], [make_rm(2)])), [[1]])
        self.assertEqual(list(_seq_match([1, 2, 3], [make_rm(3)])), [[2]])
        self.assertEqual(list(_seq_match([1, 2, 'a'], [make_rm(1), make_rm(2)])), [[0, 1]])
        self.assertEqual(list(_seq_match([1, 'a', 3], [make_rm(1), lambda x: x, make_rm(3)])),
                         [[0, 2]])
        self.assertEqual(list(_seq_match(['a', 2, 3], [make_rm(2), make_rm(3)])),
                         [[1, 2]])
        # starts with non regex
        self.assertEqual(list(_seq_match([1, 2], [lambda x: x, make_rm(1), make_rm(2)])), [])
        self.assertEqual(list(_seq_match(['a', 1, 2], [lambda x: x, make_rm(1), make_rm(2)])),
                         [[1, 2]])
        # ends with non regex
        self.assertEqual(list(_seq_match([1, 2], [make_rm(1), make_rm(2), lambda x: x])), [])
        self.assertEqual(list(_seq_match([1, 2, 'a'], [make_rm(1), make_rm(2), lambda x: x])),
                         [[0, 1]])
        # repeated pattern
        self.assertEqual(list(_seq_match([1, 2, 1, 2, 2], [make_rm(1), make_rm(2)])),
                         [[0, 1], [0, 3], [0, 4], [2, 3], [2, 4]])
        self.assertEqual(list(_seq_match([1, 2, 1, 2, 2], [make_rm(1), lambda x: x, make_rm(2)])),
                         [[0, 3], [0, 4], [2, 4]])
        self.assertEqual(list(_seq_match([1, 2, 1, 2, 2], [lambda x: x, make_rm(1), make_rm(2)])),
                         [[2, 3], [2, 4]])
        self.assertEqual(list(_seq_match([1, 2, 1, 2, 2], [make_rm(1), make_rm(2), lambda x: x])),
                         [[0, 1], [0, 3], [2, 3]])
        self.assertEqual(list(_seq_match(
            [1, 2, 1, 2, 2],
            [lambda x: x, make_rm(1), lambda x: x, make_rm(2), lambda x: x])),
            [])
        self.assertEqual(list(_seq_match(
            [1, 2, 1, 2, 2, 3],
            [lambda x: x, make_rm(1), lambda x: x, make_rm(2), lambda x: x])),
            [[2, 4]])
