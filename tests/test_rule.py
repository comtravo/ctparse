from unittest import TestCase
import regex
from ctparse.types import RegexMatch, Artifact
from ctparse.rule import dimension, predicate, regex_match, rule


class ClassA(Artifact):
    predA = 1


class ClassB(Artifact):
    pass


class TestRule(TestCase):
    def test_empty_regex_match_not_allowed(self):
        with self.assertRaises(ValueError):
            rule(r"")
        with self.assertRaises(ValueError):
            rule(r"[a-z]*")
        self.assertIsNotNone(
            rule(
                r"This long string must not match as this expression "
                "will be part of the system unless ctparse is reloaded"
            )
        )

    def test_consecutive_regex_not_allowed(self):
        with self.assertRaises(ValueError):
            rule(r"one", r"two")

    def test_regex_match(self):
        m = next(regex.finditer("(?P<R1>x)", "x"))
        r = RegexMatch(1, m)
        self.assertTrue(regex_match(1)(r))
        self.assertFalse(regex_match(1)(ClassA()))

    def test_dimension(self):
        self.assertTrue(dimension(ClassA)(ClassA()))
        self.assertFalse(dimension(ClassA)(ClassB()))

    def test_predicate(self):
        self.assertTrue(predicate("predA")(ClassA()))
        self.assertFalse(predicate("predA")(ClassB()))
