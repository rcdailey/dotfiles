"""Tests for relative duration parsing."""

import pytest

from gh_review.duration import parse_duration
from datetime import datetime, timezone, timedelta


class TestParseDuration:
    def test_minutes(self):
        result = parse_duration("30m")
        expected = datetime.now(timezone.utc) - timedelta(minutes=30)
        assert abs((result - expected).total_seconds()) < 2

    def test_hours(self):
        result = parse_duration("2h")
        expected = datetime.now(timezone.utc) - timedelta(hours=2)
        assert abs((result - expected).total_seconds()) < 2

    def test_days(self):
        result = parse_duration("7d")
        expected = datetime.now(timezone.utc) - timedelta(days=7)
        assert abs((result - expected).total_seconds()) < 2

    def test_weeks(self):
        result = parse_duration("1w")
        expected = datetime.now(timezone.utc) - timedelta(weeks=1)
        assert abs((result - expected).total_seconds()) < 2

    def test_case_insensitive(self):
        result = parse_duration("1H")
        expected = datetime.now(timezone.utc) - timedelta(hours=1)
        assert abs((result - expected).total_seconds()) < 2

    def test_whitespace_stripped(self):
        result = parse_duration("  2d  ")
        expected = datetime.now(timezone.utc) - timedelta(days=2)
        assert abs((result - expected).total_seconds()) < 2

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="invalid duration"):
            parse_duration("yesterday")

    def test_invalid_unit(self):
        with pytest.raises(ValueError, match="invalid duration"):
            parse_duration("5y")

    def test_no_number(self):
        with pytest.raises(ValueError, match="invalid duration"):
            parse_duration("h")
