"""Tests for relative duration parsing."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from gh_review._duration import parse_duration


def test_minutes():
    result = parse_duration("30m")
    expected = datetime.now(timezone.utc) - timedelta(minutes=30)
    assert abs((result - expected).total_seconds()) < 2


def test_hours():
    result = parse_duration("2h")
    expected = datetime.now(timezone.utc) - timedelta(hours=2)
    assert abs((result - expected).total_seconds()) < 2


def test_days():
    result = parse_duration("7d")
    expected = datetime.now(timezone.utc) - timedelta(days=7)
    assert abs((result - expected).total_seconds()) < 2


def test_weeks():
    result = parse_duration("1w")
    expected = datetime.now(timezone.utc) - timedelta(weeks=1)
    assert abs((result - expected).total_seconds()) < 2


def test_case_insensitive():
    result = parse_duration("1H")
    expected = datetime.now(timezone.utc) - timedelta(hours=1)
    assert abs((result - expected).total_seconds()) < 2


def test_whitespace_stripped():
    result = parse_duration("  2d  ")
    expected = datetime.now(timezone.utc) - timedelta(days=2)
    assert abs((result - expected).total_seconds()) < 2


def test_invalid_format():
    with pytest.raises(ValueError, match="invalid duration"):
        parse_duration("yesterday")


def test_invalid_unit():
    with pytest.raises(ValueError, match="invalid duration"):
        parse_duration("5y")


def test_no_number():
    with pytest.raises(ValueError, match="invalid duration"):
        parse_duration("h")
