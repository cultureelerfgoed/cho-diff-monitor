"""CSV-rapporten en weergavehulpjes die mail en job-samenvatting delen."""

from __future__ import annotations

import csv
from collections.abc import Sequence
from pathlib import Path

from .compare import DayRow, WeekRow
from .dates import WEEKDAYS

PREFIXES = {
    "ceo": "https://linkeddata.cultureelerfgoed.nl/def/ceo#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "geo": "http://www.opengis.net/ont/geosparql#",
    "dct": "http://purl.org/dc/terms/",
    "prov": "http://www.w3.org/ns/prov#",
    "sdo": "https://schema.org/",
    "zo": "https://linkeddata.cultureelerfgoed.nl/def/zo/",
}


def short(iri: str) -> str:
    """Compacte weergave van een IRI, bv. ceo:Rijksmonument."""
    for prefix, ns in PREFIXES.items():
        if iri.startswith(ns) and len(iri) > len(ns):
            return f"{prefix}:{iri[len(ns) :]}"
    return iri


def signed(n: int) -> str:
    """Getal met teken en duizendtalscheiding: +1.234 / −56 / 0."""
    text = f"{abs(n):,}".replace(",", ".")
    if n > 0:
        return f"+{text}"
    if n < 0:
        return f"−{text}"
    return "0"


def number(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def write_day_csv(rows: Sequence[DayRow], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["item", "aantalVandaag", "aantalGisteren", "verschil"])
        for r in rows:
            writer.writerow([r.item, r.today, r.previous, r.diff])
    return path


def write_week_csv(rows: Sequence[WeekRow], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    days = [d.capitalize() for d in WEEKDAYS]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "item",
                *(f"aantal{d}" for d in days),
                *(f"diff{d}" for d in days[1:]),
                "totaalVerschil",
            ]
        )
        for r in rows:
            writer.writerow([r.item, *r.counts, *r.diffs, r.total])
    return path


def day_summary_md(title: str, rows: Sequence[DayRow], devs: Sequence[DayRow], limit=25) -> str:
    lines = [f"### {title}", "", f"**{len(rows)}** items vergeleken, **{len(devs)}** afwijkingen."]
    if devs:
        lines += ["", "| Item | Gisteren | Vandaag | Verschil |", "|---|--:|--:|--:|"]
        for r in devs[:limit]:
            lines.append(
                f"| `{short(r.item)}` | {number(r.previous)} | {number(r.today)} "
                f"| {signed(r.diff)} |"
            )
        if len(devs) > limit:
            lines.append(f"\n… en nog {len(devs) - limit} (zie CSV-artifact).")
    return "\n".join(lines)


def week_summary_md(title: str, rows: Sequence[WeekRow], devs: Sequence[WeekRow], limit=25) -> str:
    lines = [f"### {title}", "", f"**{len(rows)}** items vergeleken, **{len(devs)}** veranderd."]
    if devs:
        lines += ["", "| Item | Ma | Zo | Netto |", "|---|--:|--:|--:|"]
        for r in devs[:limit]:
            lines.append(
                f"| `{short(r.item)}` | {number(r.counts[0])} | {number(r.counts[-1])} "
                f"| {signed(r.total)} |"
            )
        if len(devs) > limit:
            lines.append(f"\n… en nog {len(devs) - limit} (zie CSV-artifact).")
    return "\n".join(lines)
