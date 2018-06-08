from unittest import TestCase
from time import sleep
from datetime import datetime
from ctparse.ctparse import _timeout, ctparse
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
        txt = '12.12.'
        res = ctparse(txt, ts=datetime(2020, 12, 1))
        self.assertEqual(res.resolution, Time(year=2020, month=12, day=12))
        res = ctparse(txt, ts=datetime(2020, 12, 1), debug=True)
        self.assertEqual(next(res).resolution, Time(year=2020, month=12, day=12))
