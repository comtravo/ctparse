from unittest import TestCase
import regex
from datetime import datetime
from ctparse.types import Artifact, RegexMatch, Time, Interval


class TestArtifact(TestCase):
    def test_init(self):
        a = Artifact()
        self.assertEqual(a.mstart, 0)
        self.assertEqual(a.mend, 0)
        self.assertEqual(len(a), 0)
        self.assertTrue(a)

    def test_eq(self):
        a = Artifact()
        b = Artifact()
        self.assertEqual(a, b)

        a = Time(2017, 12, 12, 12, 12, 4, "morning")
        b = Time(2017, 12, 12, 12, 12, 4, "morning")
        self.assertEqual(a, b)

        a = Time(2017, 12, 12, 12, 12, 4, "morning")
        b = Time(2017, 12, 12, 12, 12, 3, "morning")
        self.assertNotEqual(a, b)

        a = Time()
        b = Interval()
        self.assertNotEqual(a, b)

    def test_update_span(self):
        a1 = Artifact()
        a2 = Artifact()
        a3 = Artifact()
        a2.mstart = 10
        a3.mend = 100
        a1.update_span(a2, a3)
        self.assertEqual(a1.mstart, 10)
        self.assertEqual(a1.mend, 100)
        self.assertEqual(len(a1), 90)

    def test_repr(self):
        a = Artifact()
        self.assertEqual(repr(a), "Artifact[0-0]{}")

    def test_nb_str(self):
        a = Artifact()
        self.assertEqual(a.nb_str(), "Artifact[]{}")


class TestRegexMatch(TestCase):
    def test_init(self):
        m = next(regex.finditer(r"(?P<R1>match me)", "xxx match me xxx"))
        r = RegexMatch(1, m)
        self.assertEqual(r.mstart, 4)
        self.assertEqual(r.mend, 12)
        self.assertEqual(len(r), 8)
        self.assertEqual(r._text, "match me")
        self.assertEqual(repr(r), "RegexMatch[4-12]{1:match me}")
        self.assertEqual(r.nb_str(), "RegexMatch[]{1:match me}")


class TestTime(TestCase):
    def test_init(self):
        self.assertIsNotNone(Time())

    def test_isDOY(self):
        self.assertTrue(Time(month=1, day=1).isDOY)
        self.assertFalse(Time(year=1).isDOY)

    def test_isDOM(self):
        self.assertTrue(Time(day=1).isDOM)
        self.assertFalse(Time(month=1).isDOM)

    def test_isHour(self):
        self.assertTrue(Time(hour=1).isHour)
        self.assertFalse(Time(hour=1, minute=1).isHour)
        self.assertFalse(Time(hour=1, month=1).isHour)

    def test_isDOW(self):
        self.assertTrue(Time(DOW=1).isDOW)
        self.assertFalse(Time().isDOW)

    def test_isMonth(self):
        self.assertTrue(Time(month=1).isMonth)
        self.assertFalse(Time(day=1).isMonth)
        self.assertFalse(Time(year=1).isMonth)

    def test_isPOD(self):
        self.assertTrue(Time(POD="morning").isPOD)
        self.assertFalse(Time(day=1).isPOD)
        self.assertFalse(Time(year=1).isPOD)

    def test_isTOD(self):
        self.assertTrue(Time(hour=1, minute=1).isTOD)
        self.assertTrue(Time(hour=1).isTOD)
        self.assertFalse(Time(minute=1).isTOD)
        self.assertFalse(Time().isTOD)

    def test_isDate(self):
        self.assertTrue(Time(year=1, month=1, day=1).isDate)
        self.assertFalse(Time(year=1, month=1).isDate)
        self.assertFalse(Time(year=1, day=1).isDate)
        self.assertFalse(Time(day=1, month=1).isDate)
        self.assertFalse(Time(year=1, month=1, day=1, hour=1).isDate)

    def test_isDateTime(self):
        self.assertTrue(Time(year=1, month=1, day=1, hour=1).isDateTime)
        self.assertFalse(Time(year=1, month=1, day=1).isDateTime)

    def test_isYear(self):
        self.assertTrue(Time(year=1).isYear)
        self.assertFalse(Time(year=1, month=1).isYear)

    def test_hasDate(self):
        self.assertTrue(Time(year=1, month=1, day=1).hasDate)
        self.assertFalse(Time(year=1, month=1).isDate)
        self.assertFalse(Time(year=1, day=1).isDate)
        self.assertFalse(Time(day=1, month=1).isDate)
        self.assertTrue(Time(year=1, month=1, day=1, hour=1).hasDate)

    def test_hasTime(self):
        self.assertTrue(Time(hour=1, minute=1, day=1, month=1, year=1).hasTime)
        self.assertTrue(Time(hour=1, day=1, month=1, year=1).hasTime)
        self.assertFalse(Time(day=1, month=1, year=1).hasTime)

    def test_hasPOD(self):
        self.assertTrue(Time(POD="pod").hasPOD)
        self.assertFalse(Time(day=1, month=1, year=1).hasPOD)

    def test_repr(self):
        t = Time(year=1, month=1, day=1, hour=1, minute=1, DOW=1, POD="pod")
        self.assertEqual(repr(t), "Time[0-0]{0001-01-01 01:01 (1/pod)}")

    def test_from_str(self):
        # Complete time
        t = Time(year=1, month=1, day=1, hour=1, minute=1, DOW=1, POD="pod")
        t_str = str(t)
        t_back = Time.from_str(t_str)
        self.assertEqual(t, t_back)

        # Incomplete time
        t = Time(year=None, month=1, day=1, hour=None, minute=None, DOW=None, POD="pod")
        t_str = str(t)
        t_back = Time.from_str(t_str)
        self.assertEqual(t, t_back)

        # Zeroed time
        t = Time()
        t_str = str(t)
        t_back = Time.from_str(t_str)
        self.assertEqual(t, t_back)

        # Mistake
        with self.assertRaises(ValueError):
            Time.from_str("0001-01-01 01-01 (1/pod)")

    def test_start(self):
        t = Time()
        self.assertEqual(t.start, Time(hour=0, minute=0))
        t = Time(year=2012, month=1, day=1)
        self.assertEqual(t.start, Time(2012, 1, 1, 0, 0))
        t = Time(year=2012, month=1, day=1, hour=12)
        self.assertEqual(t.start, Time(2012, 1, 1, 12, 0))
        t = Time(year=2012, month=1, day=1, hour=12, minute=20)
        self.assertEqual(t.start, Time(2012, 1, 1, 12, 20))
        t = Time(year=2012, month=1, day=1, POD="last")
        self.assertEqual(t.start, Time(2012, 1, 1, 23, 00))

    def test_end(self):
        t = Time()
        self.assertEqual(t.end, Time(hour=23, minute=59))
        t = Time(year=2012, month=1, day=1)
        self.assertEqual(t.end, Time(2012, 1, 1, 23, 59))
        t = Time(year=2012, month=1, day=1, hour=12)
        self.assertEqual(t.end, Time(2012, 1, 1, 12, 59))
        t = Time(year=2012, month=1, day=1, hour=12, minute=20)
        self.assertEqual(t.end, Time(2012, 1, 1, 12, 20))
        t = Time(year=2012, month=1, day=1, POD="last")
        self.assertEqual(t.end, Time(2012, 1, 1, 23, 59))

    def test_dt(self):
        t = Time(2015, 12, 12, 12, 12)
        self.assertEqual(t.dt, datetime(2015, 12, 12, 12, 12))
        t = Time(2015, 12, 12, 12)
        self.assertEqual(t.dt, datetime(2015, 12, 12, 12))
        t = Time(2015, 12, 12)
        self.assertEqual(t.dt, datetime(2015, 12, 12))

        with self.assertRaises(ValueError):
            t = Time(year=2012, month=12, hour=12, minute=12)
            t.dt


class TestInterval(TestCase):
    def test_init(self):
        self.assertIsNotNone(Interval())

    def test_isTimeInterval(self):
        self.assertTrue(Interval(Time(hour=1), Time(hour=2)).isTimeInterval)

    def test_repr(self):
        self.assertEqual(
            repr(Interval(Time(), Time())),
            "Interval[0-0]{X-X-X X:X (X/X) - X-X-X X:X (X/X)}",
        )

    def test_from_str(self):
        # Complete interval
        t1 = Time(year=1, month=1, day=1, hour=1, minute=1, DOW=1, POD="pod")
        t2 = Time(year=2, month=1, day=1, hour=1, minute=1, DOW=1, POD="pod")
        interval = Interval(t1, t2)
        i_back = Interval.from_str(str(interval))
        self.assertEqual(interval, i_back)

        # Incomplete interval
        interval = Interval(None, t2)
        i_back = Interval.from_str(str(interval))
        self.assertEqual(interval, i_back)

        # Zeroed interval
        interval = Interval()
        i_back = Interval.from_str(str(interval))
        self.assertEqual(interval, i_back)

        # Mistake
        with self.assertRaises(ValueError):
            Interval.from_str("X-X-X X: X(X/X) -X-X-X X: X(X/X)")

    def test_start(self):
        i = Interval(Time(2013, 1, 1), Time(2013, 1, 2))
        self.assertEqual(i.start, Time(2013, 1, 1, 0, 0))

        i = Interval(Time(2013, 1, 1), None)
        self.assertEqual(i.start, Time(2013, 1, 1, 0, 0))

        i = Interval(None, Time(2013, 1, 2))
        self.assertIsNone(i.start)

    def test_end(self):
        i = Interval(Time(2013, 1, 1), Time(2013, 1, 2))
        self.assertEqual(i.end, Time(2013, 1, 2, 23, 59))

        i = Interval(None, Time(2013, 1, 2))
        self.assertEqual(i.end, Time(2013, 1, 2, 23, 59))

        i = Interval(Time(2013, 1, 1), None)
        self.assertIsNone(i.end)
