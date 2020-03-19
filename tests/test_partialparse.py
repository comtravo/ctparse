import datetime
from typing import Any, Callable

import pytest
import regex

from ctparse.partial_parse import PartialParse, _seq_match
from ctparse.types import RegexMatch, Time


def test_partial_parse() -> None:
    match_a = regex.match("(?<R1>a)", "ab")
    match_b = next(regex.finditer("(?<R2>b)", "ab"))

    pp = PartialParse.from_regex_matches(
        (RegexMatch(1, match_a), RegexMatch(2, match_b))
    )

    assert len(pp.prod) == 2
    assert len(pp.rules) == 2

    assert isinstance(pp.score, float)

    def mock_rule(ts: datetime.datetime, a: Time) -> Time:
        return Time()

    pp2 = pp.apply_rule(
        datetime.datetime(day=1, month=1, year=2015), mock_rule, "mock_rule", (0, 1)
    )

    assert pp != pp2

    with pytest.raises(ValueError):
        PartialParse((), ())


def test_seq_match() -> None:
    # NOTE: we are testing a private function because the algorithm
    # is quite complex

    def make_rm(i: int) -> Callable[[Any], bool]:
        def _regex_match(s: Any) -> bool:
            return bool(s == i)

        return _regex_match

    # empty sequence, empty pattern: matches on a single empty sequence
    assert list(_seq_match([], [])) == [[]]
    # non empty sequence, empty pattern matches on an empty sequence
    assert list(_seq_match(["a", "b"], [])) == [[]]
    # non empty sequence, non empty pattern that does not apper: no match
    assert list(_seq_match(["a", "b"], [make_rm(1)])) == []
    # empty sequence, non empty pattern: no match
    assert list(_seq_match([], [make_rm(1)])) == []
    # sequence shorter than pattern: no match
    assert list(_seq_match(["a"], [make_rm(1), make_rm(2)])) == []
    # seq = pat
    assert list(_seq_match([1], [make_rm(1)])) == [[0]]
    assert list(_seq_match([1, 2, 3], [make_rm(1)])) == [[0]]
    assert list(_seq_match([1, 2, 3], [make_rm(2)])) == [[1]]
    assert list(_seq_match([1, 2, 3], [make_rm(3)])) == [[2]]
    assert list(_seq_match([1, 2, "a"], [make_rm(1), make_rm(2)])) == [[0, 1]]
    assert list(_seq_match([1, "a", 3], [make_rm(1), _identity, make_rm(3)])) == [
        [0, 2]
    ]
    assert list(_seq_match(["a", 2, 3], [make_rm(2), make_rm(3)])) == [[1, 2]]
    # starts with non regex
    assert list(_seq_match([1, 2], [_identity, make_rm(1), make_rm(2)])) == []
    assert list(_seq_match(["a", 1, 2], [_identity, make_rm(1), make_rm(2)])) == [
        [1, 2]
    ]
    # ends with non regex
    assert list(_seq_match([1, 2], [make_rm(1), make_rm(2), _identity])) == []
    assert list(_seq_match([1, 2, "a"], [make_rm(1), make_rm(2), _identity])) == [
        [0, 1]
    ]
    # repeated pattern
    assert list(_seq_match([1, 2, 1, 2, 2], [make_rm(1), make_rm(2)])) == [
        [0, 1],
        [0, 3],
        [0, 4],
        [2, 3],
        [2, 4],
    ]
    assert list(_seq_match([1, 2, 1, 2, 2], [make_rm(1), _identity, make_rm(2)])) == [
        [0, 3],
        [0, 4],
        [2, 4],
    ]
    assert list(_seq_match([1, 2, 1, 2, 2], [_identity, make_rm(1), make_rm(2)])) == [
        [2, 3],
        [2, 4],
    ]
    assert list(_seq_match([1, 2, 1, 2, 2], [make_rm(1), make_rm(2), _identity])) == [
        [0, 1],
        [0, 3],
        [2, 3],
    ]
    assert (
        list(
            _seq_match(
                [1, 2, 1, 2, 2],
                [_identity, make_rm(1), _identity, make_rm(2), _identity],
            )
        )
        == []
    )
    assert list(
        _seq_match(
            [1, 2, 1, 2, 2, 3],
            [_identity, make_rm(1), _identity, make_rm(2), _identity],
        )
    ) == [[2, 4]]


def _identity(x: Any) -> bool:
    return True
