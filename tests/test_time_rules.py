from unittest import TestCase

from ctparse.types import Time
from ctparse.time.rules import ruleDateDate, ruleDOMDate, ruleDateTimeDateTime, \
    ruleDOYDate, ruleQuarterBeforeHH, ruleQuarterAfterHH


class TestRules(TestCase):
    def test_ruleDateDate(self):
        t1 = Time(year=2017)
        t2 = Time(year=2015)
        self.assertIsNone(ruleDateDate(None, t1, None, t2))

        t1 = Time(year=2017, month=12)
        t2 = Time(year=2017, month=11)
        self.assertIsNone(ruleDateDate(None, t1, None, t2))

        t1 = Time(year=2017, month=12, day=31)
        t2 = Time(year=2017, month=12, day=30)
        self.assertIsNone(ruleDateDate(None, t1, None, t2))

        t1 = Time(year=2017, month=12, day=31)
        t2 = Time(year=2017, month=12, day=31)
        self.assertIsNone(ruleDateDate(None, t1, None, t2))

        t1 = Time(year=2017, month=12, day=30)
        t2 = Time(year=2017, month=12, day=31)
        self.assertIsNotNone(ruleDateDate(None, t1, None, t2))

    def test_ruleDOMDate(self):
        t1 = Time(day=30)
        t2 = Time(year=2015, month=1, day=29)
        self.assertIsNone(ruleDOMDate(None, t1, None, t2))

        t1 = Time(day=30)
        t2 = Time(year=2015, month=1, day=30)
        self.assertIsNone(ruleDOMDate(None, t1, None, t2))

        t1 = Time(day=29)
        t2 = Time(year=2015, month=1, day=30)
        self.assertIsNotNone(ruleDOMDate(None, t1, None, t2))

    def test_ruleDateTimeDateTime(self):
        t1 = Time(year=2017, month=4, day=12, hour=12, minute=30)
        t2 = Time(year=2016, month=4, day=12, hour=12, minute=30)
        self.assertIsNone(ruleDateTimeDateTime(None, t1, None, t2))

        t1 = Time(year=2017, month=4, day=12, hour=12, minute=30)
        t2 = Time(year=2017, month=3, day=12, hour=12, minute=30)
        self.assertIsNone(ruleDateTimeDateTime(None, t1, None, t2))

        t1 = Time(year=2017, month=4, day=12, hour=12, minute=30)
        t2 = Time(year=2017, month=4, day=11, hour=12, minute=30)
        self.assertIsNone(ruleDateTimeDateTime(None, t1, None, t2))

        t1 = Time(year=2017, month=4, day=12, hour=12, minute=30)
        t2 = Time(year=2017, month=4, day=12, hour=11, minute=30)
        self.assertIsNone(ruleDateTimeDateTime(None, t1, None, t2))

        t1 = Time(year=2017, month=4, day=12, hour=12, minute=30)
        t2 = Time(year=2017, month=4, day=12, hour=12, minute=29)
        self.assertIsNone(ruleDateTimeDateTime(None, t1, None, t2))

        t1 = Time(year=2017, month=4, day=12, hour=12, minute=30)
        t2 = Time(year=2017, month=4, day=12, hour=12, minute=30)
        self.assertIsNone(ruleDateTimeDateTime(None, t1, None, t2))

        t1 = Time(year=2017, month=4, day=12, hour=12, minute=30)
        t2 = Time(year=2017, month=4, day=12, hour=12, minute=31)
        self.assertIsNotNone(ruleDateTimeDateTime(None, t1, None, t2))

    def test_ruleDOYDate(self):
        t1 = Time(month=4, day=12)
        t2 = Time(year=2017, month=4, day=12)
        self.assertIsNone(ruleDOYDate(None, t1, None, t2))

        t1 = Time(month=4, day=12)
        t2 = Time(year=2017, month=4, day=13)
        self.assertIsNotNone(ruleDOYDate(None, t1, None, t2))

    def test_ruleQuarterBeforeHH(self):
        t1 = Time(hour=12, minute=1)
        self.assertIsNone(ruleQuarterBeforeHH(None, None, t1))

    def test_ruleQuarterAferHH(self):
        t1 = Time(hour=12, minute=1)
        self.assertIsNone(ruleQuarterAfterHH(None, None, t1))
