"""Datumlogica. Alles werkt met kalenderdagen in Nederlandse tijd."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

WEEKDAYS = ("ma", "di", "wo", "do", "vr", "za", "zo")


def today(timezone: str) -> date:
    """De huidige kalenderdag in de opgegeven tijdzone (niet de UTC-dag van de runner)."""
    return datetime.now(ZoneInfo(timezone)).date()


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        raise ValueError(f"Ongeldige datum {value!r}; verwacht JJJJ-MM-DD") from None


def week_of(day: date) -> list[date]:
    """Maandag t/m zondag van de week waar `day` in valt."""
    monday = day - timedelta(days=day.weekday())
    return [monday + timedelta(days=i) for i in range(7)]


def previous_week(reference: date) -> list[date]:
    """De laatste volledige kalenderweek vóór `reference` (maandag t/m zondag)."""
    return week_of(reference - timedelta(days=7))
