"""Vergelijkingslogica (zuiver, zonder netwerk) voor dag- en weekmonitor."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .sparql import Counts


@dataclass(frozen=True)
class DayRow:
    item: str
    today: int
    previous: int

    @property
    def diff(self) -> int:
        return self.today - self.previous

    @property
    def is_new(self) -> bool:
        return self.previous == 0 and self.today != 0

    @property
    def is_gone(self) -> bool:
        return self.today == 0 and self.previous != 0


@dataclass(frozen=True)
class WeekRow:
    item: str
    counts: tuple[int, ...]  # maandag t/m zondag

    @property
    def diffs(self) -> tuple[int, ...]:
        """Verschil t.o.v. de vorige dag, voor dinsdag t/m zondag."""
        return tuple(b - a for a, b in zip(self.counts, self.counts[1:], strict=False))

    @property
    def total(self) -> int:
        """Netto verschil: laatste dag min eerste dag."""
        return self.counts[-1] - self.counts[0]

    @property
    def changed(self) -> bool:
        return any(self.diffs)

    @property
    def is_new(self) -> bool:
        """Op maandag afwezig, op zondag aanwezig."""
        return self.counts[0] == 0 and self.counts[-1] != 0

    @property
    def is_gone(self) -> bool:
        """Op maandag aanwezig, op zondag afwezig."""
        return self.counts[0] != 0 and self.counts[-1] == 0


def compare_days(today: Counts, previous: Counts) -> list[DayRow]:
    """Alle items uit beide dagen; een ontbrekend item telt als 0.

    Gesorteerd op verschil (aflopend), daarna op item, zoals de CSV altijd was.
    """
    items = today.keys() | previous.keys()
    rows = [DayRow(item, today.get(item, 0), previous.get(item, 0)) for item in items]
    return sorted(rows, key=lambda r: (-r.diff, r.item))


def compare_week(per_day: Sequence[Counts]) -> list[WeekRow]:
    items = set().union(*(day.keys() for day in per_day))
    rows = [WeekRow(item, tuple(day.get(item, 0) for day in per_day)) for item in items]
    return sorted(rows, key=lambda r: r.item)


def deviations(rows: Sequence[DayRow]) -> list[DayRow]:
    """Afwijkingen, grootste absolute verschil eerst."""
    return sorted((r for r in rows if r.diff), key=lambda r: (-abs(r.diff), r.item))


def week_deviations(rows: Sequence[WeekRow]) -> list[WeekRow]:
    """Items die ergens in de week veranderden, grootste netto verschil eerst."""
    changed = [r for r in rows if r.changed]
    return sorted(changed, key=lambda r: (-abs(r.total), r.item))
