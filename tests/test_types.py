from unittest import TestCase
import regex
from ctparse.types import Artifact, RegexMatch


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
