"""This file contains regression tests for commonly parsed time expressions"""
import ctparse
from datetime import datetime


def test_military_time():
    result = ctparse.ctparse("3 March 2020", ts=datetime(2020, 2, 25))
    assert result
    assert str(result.resolution) == "2020-03-03 X:X (X/X)"


def test_parse_years_ahead():
    result = ctparse.ctparse("3 March 2023", ts=datetime(2020, 2, 25))
    assert result
    assert str(result.resolution) == "2023-03-03 X:X (X/X)"
