from datetime import datetime
from ctparse.ctparse import ctparse, ctparse_gen, _match_rule
from ctparse.types import Interval, Time, Artifact


def test_ctparse():
    txt = "12.12.2020"
    res = ctparse(txt)
    assert res
    assert res.resolution == Time(year=2020, month=12, day=12)
    assert str(res)
    assert repr(res)

    # non sense gives no result
    assert ctparse("gargelbabel") is None
    txt = "12.12."
    res = ctparse(txt, ts=datetime(2020, 12, 1))
    assert res
    assert res.resolution == Time(year=2020, month=12, day=12)

    gres = ctparse_gen(txt, ts=datetime(2020, 12, 1))
    first_res = next(gres)
    assert first_res
    assert first_res.resolution == Time(year=2020, month=12, day=12)


def test_ctparse_timeout():
    # timeout in ctparse: should rather mock the logger and see
    # whether the timeout was hit, but cannot get it mocked
    txt = "tomorrow 8 yesterday Sep 9 9 12 2023 1923"
    ctparse(txt, timeout=0.0001)


def test_match_rule():
    def rule(a: Artifact) -> bool:
        return True

    assert list(_match_rule([], [rule])) == []
    assert list(_match_rule([Artifact()], [])) == []


def test_latent_time():
    parse = ctparse("8:00 pm", ts=datetime(2020, 1, 1, 7, 0), latent_time=False)
    assert parse
    assert parse.resolution == Time(None, None, None, 20, 00)

    parse = ctparse("8:00 pm", ts=datetime(2020, 1, 1, 7, 0), latent_time=True)
    assert parse
    assert parse.resolution == Time(2020, 1, 1, 20, 00)


def test_latent_time_interval():
    parse = ctparse(
        "8:00 pm - 9:00 pm", ts=datetime(2020, 1, 1, 7, 0), latent_time=False
    )
    assert parse
    assert parse.resolution == Interval(
        Time(None, None, None, 20, 00), Time(None, None, None, 21, 00)
    )

    parse = ctparse(
        "8:00 pm - 9:00 pm", ts=datetime(2020, 1, 1, 7, 0), latent_time=True
    )
    assert parse
    assert parse.resolution == Interval(
        Time(2020, 1, 1, 20, 00), Time(2020, 1, 1, 21, 00)
    )
