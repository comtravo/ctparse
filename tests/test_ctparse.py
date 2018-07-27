from unittest import TestCase
from time import sleep
from datetime import datetime
from ctparse.ctparse import _timeout, ctparse, _seq_match, _match_rule
from ctparse.types import Time


class TestCTParse(TestCase):
    def test_timeout(self):
        t_fun = _timeout(0.5)
        with self.assertRaises(Exception):
            sleep(1)
            t_fun()
        t_fun = _timeout(0)
        t_fun()  # all good

    def test_ctparse(self):
        txt = '12.12.2020'
        res = ctparse(txt)
        self.assertEqual(res.resolution, Time(year=2020, month=12, day=12))
        self.assertIsNotNone(str(res))
        self.assertIsNotNone(repr(res))
        # non sense gives no result
        self.assertIsNone(ctparse('gargelbabel'))
        txt = '12.12.'
        res = ctparse(txt, ts=datetime(2020, 12, 1))
        self.assertEqual(res.resolution, Time(year=2020, month=12, day=12))
        res = ctparse(txt, ts=datetime(2020, 12, 1), debug=True)
        self.assertEqual(next(res).resolution, Time(year=2020, month=12, day=12))

    def test_ctparse_timeout(self):
        # timeout in ctparse: should rather mock the logger and see
        # whether the timeout was hit, but cannot get it mocked
        txt = 'tomorrow 8 yesterday Sep 9 9 12 2023 1923'
        ctparse(txt, timeout=0.0001)

    def test_seq_match(self):
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

    def test_match_rule(self):
        self.assertEqual(list(_match_rule([], ['not empty'])), [])
        self.assertEqual(list(_match_rule(['not empty'], [])), [])
