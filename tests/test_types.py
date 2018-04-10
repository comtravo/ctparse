from unittest import TestCase
import regex
from ctparse.types import Artifact, RegexMatch, Time, Interval


class TestArtifact(TestCase):
    def test_init(self):
        a = Artifact()
        self.assertEqual(a.mstart, 0)
        self.assertEqual(a.mend, 0)
        self.assertEqual(len(a), 0)

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
        self.assertEqual(repr(a), 'Artifact[0-0]{}')

    def test_nb_str(self):
        a = Artifact()
        self.assertEqual(a.nb_str(), 'Artifact[]{}')


class TestRegexMatch(TestCase):
    def test_init(self):
        m = next(regex.finditer(r'(?P<R1>match me)', 'xxx match me xxx'))
        r = RegexMatch(1, m)
        self.assertEqual(r.mstart, 4)
        self.assertEqual(r.mend, 12)
        self.assertEqual(len(r), 8)
        self.assertEqual(r._text, 'match me')
        self.assertEqual(repr(r), 'RegexMatch[4-12]{1:match me}')
        self.assertEqual(r.nb_str(), 'RegexMatch[]{1:match me}')


class TestTime(TestCase):
    def test_init(self):
        self.assertIsNotNone(Time())

    def test_isDOY(self):
        self.assertTrue(Time(month=1, day=1).isDOY)
        self.assertFalse(Time(year=1).isDOY)

    def test_isDOM(self):
        self.assertTrue(Time(day=1).isDOM)
        self.assertFalse(Time(month=1).isDOM)

    def test_isDOW(self):
        self.assertTrue(Time(DOW=1).isDOW)
        self.assertFalse(Time().isDOW)

    def test_isMonth(self):
        self.assertTrue(Time(month=1).isMonth)
        self.assertFalse(Time(day=1).isMonth)
        self.assertFalse(Time(year=1).isMonth)

    def test_isPOD(self):
        self.assertTrue(Time(POD='morning').isPOD)
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

    def test_repr(self):
        t = Time(year=1, month=1, day=1, hour=1, minute=1, DOW=1, POD='pod')
        self.assertEqual(repr(t),
                         'Time[0-0]{0001-01-01 01:01 (1/pod)}')


class TestInterval(TestCase):
    def test_init(self):
        self.assertIsNotNone(Interval())

    def test_isTimeInterval(self):
        self.assertTrue(
            Interval(Time(hour=1),
                     Time(hour=2)).isTimeInterval)

    def test_repr(self):
        self.assertEqual(repr(Interval(Time(), Time())),
                         'Interval[0-0]{X-X-X X:X (X/X) - X-X-X X:X (X/X)}')
