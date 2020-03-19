from unittest import TestCase
from datetime import datetime
from ctparse.ctparse import ctparse, ctparse_gen, _match_rule
from ctparse.types import Time, Artifact


class TestCTParse(TestCase):
    def test_ctparse(self):
        txt = "12.12.2020"
        res = ctparse(txt)
        assert res
        self.assertEqual(res.resolution, Time(year=2020, month=12, day=12))
        self.assertIsNotNone(str(res))
        self.assertIsNotNone(repr(res))
        # non sense gives no result
        self.assertIsNone(ctparse("gargelbabel"))
        txt = "12.12."
        res = ctparse(txt, ts=datetime(2020, 12, 1))
        assert res
        self.assertEqual(res.resolution, Time(year=2020, month=12, day=12))
        gres = ctparse_gen(txt, ts=datetime(2020, 12, 1))
        first_res = next(gres)
        assert first_res
        self.assertEqual(first_res.resolution, Time(year=2020, month=12, day=12))

    def test_ctparse_timeout(self):
        # timeout in ctparse: should rather mock the logger and see
        # whether the timeout was hit, but cannot get it mocked
        txt = "tomorrow 8 yesterday Sep 9 9 12 2023 1923"
        ctparse(txt, timeout=0.0001)

    def test_match_rule(self):
        def rule(a: Artifact) -> bool:
            return True

        self.assertEqual(list(_match_rule([], [rule])), [])
        self.assertEqual(list(_match_rule([Artifact()], [])), [])
