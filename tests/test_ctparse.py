from unittest import TestCase
from datetime import datetime
from ctparse.ctparse import ctparse, _match_rule
from ctparse.types import Time


class TestCTParse(TestCase):

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

    def test_match_rule(self):
        self.assertEqual(list(_match_rule([], ['not empty'])), [])
        self.assertEqual(list(_match_rule(['not empty'], [])), [])
