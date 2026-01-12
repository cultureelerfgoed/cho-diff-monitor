# scripts/compare_week.py
#
# CHO diff week monitor – hoofdscript
#
# Verantwoordelijkheden:
# - bepalen van de volledige vorige week (maandag t/m zondag)
# - uitvoeren van week-monitor.rq via SPARQL
# - genereren van volledige week-CSV
# - berekenen van dagverschillen en totaalverschil
# - versturen van e-mail via Gmail (SMTP met App Password)
#
# Er wordt geen resultaat-graph geschreven.
# CSV en mail zijn de primaire outputs.

from datetime import date, timedelta
from pathlib import Path
import csv
import os

from sparql import run_week_monitor_query
from mail_week import send_week_report_mail


QUERY_PATH = "queries/week-monitor.rq"


def bepaal_vorige_week():
    """
    Bepaalt de volledige vorige week (maandag t/m zondag).
    Retourneert een lijst van 7 date-objecten.
    """
    today = date.today()

    # Vorige zondag
    end_date = today - timedelta(days=1)

    # Vorige maandag
    start_date = end_date - timedelta(days=6)

    return [
        start_date + timedelta(days=i)
        for i in range(7)
    ]


def build_graph_uris(dates):
    """
    Bouwt graph-URI's op basis van datums.
    """
    return [
        f"https://linkeddata.cultureelerfgoed.nl/graph/cho-diff/{d.isoformat()}"
        for d in dates
    ]


def bereken_verschillen(aantallen):
    """
    Berekent dagverschillen en totaalverschil.
    """
    diffs = []
    for i in range(1, len(aantallen)):
        diffs.append(aantallen[i] - aantallen[i - 1])

    totaal = sum(diffs)
    return diffs, totaal


def main():
    # 1. Bepaal week
    week_dates = bepaal_vorige_week()
    graph_uris = build_graph_uris(week_dates)

    week_label = (
        f"{week_dates[0].isoformat()}_"
        f"{week_dates[-1].isoformat()}"
    )

    # 2. SPARQL uitvoeren
    rows = run_week_monitor_query(
        QUERY_PATH,
        graph_uris
    )

    csv_name = f"diff-cho-week-{week_label}.csv"

    # 3. CSV schrijven
    with open(csv_name, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "item",
            "aantalMa",
            "aantalDi",
            "aantalWo",
            "aantalDo",
            "aantalVr",
            "aantalZa",
            "aantalZo",
            "diffDi",
            "diffWo",
            "diffDo",
            "diffVr",
            "diffZa",
            "diffZo",
            "totaalVerschil"
        ])

        for row in rows:
            aantallen = [
                row["dag1"],
                row["dag2"],
                row["dag3"],
                row["dag4"],
                row["dag5"],
                row["dag6"],
                row["dag7"],
            ]

            diffs, totaal = bereken_verschillen(aantallen)

            writer.writerow([
                row["item"],
                *aantallen,
                *diffs,
                totaal
            ])

    # 4. Mail versturen
    send_week_report_mail(
        week_start=week_dates[0],
        week_end=week_dates[-1],
        rows=rows,
        csv_path=csv_name
    )

    print(
        f"Weekmonitor uitgevoerd voor {week_label}. "
        f"{len(rows)} items verwerkt."
    )


if __name__ == "__main__":
    main()
