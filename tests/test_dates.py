from datetime import date

import pytest

from chodiff import dates


def test_previous_week_from_monday():
    week = dates.previous_week(date(2026, 11, 16))  # maandag
    assert week[0] == date(2026, 11, 9) and week[-1] == date(2026, 11, 15)


def test_previous_week_from_sunday_is_last_complete_week():
    week = dates.previous_week(date(2026, 11, 15))  # zondag: lopende week nog niet af
    assert week[0] == date(2026, 11, 2) and week[-1] == date(2026, 11, 8)


def test_week_of_returns_monday_to_sunday():
    week = dates.week_of(date(2026, 11, 12))
    assert len(week) == 7
    assert week[0].weekday() == 0 and week[-1].weekday() == 6


def test_parse_date_rejects_garbage():
    with pytest.raises(ValueError, match="JJJJ-MM-DD"):
        dates.parse_date("17-11-2026")


def test_today_uses_timezone():
    assert isinstance(dates.today("Europe/Amsterdam"), date)
