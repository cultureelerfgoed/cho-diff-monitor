# scripts/compare.py
#
# CHO diff monitor – hoofdscript
#
# Verantwoordelijkheden:
# - uitvoeren van query-monitor.rq
# - genereren van volledige CSV
# - schrijven van resultaat-graph
#
# LET OP:
# - Mail is TIJDELIJK UITGESCHAKELD bij fouten
# - Fouten worden via exceptions zichtbaar in GitHub Actions
#
# De graph is de primaire output.

import sys
import csv
import subprocess
import os
from pathlib import Path

from sparql import run_monitor_query
from mail import send_mail  # blijft staan voor later


CEOPREFIX = "https://linkeddata.cultureelerfgoed.nl/def/ceo#"


def write_result_graph(
    rows,
    datum_gisteren,
    datum_eergisteren,
    graph_uri,
    output_file
):
    lines = []

    lines.append(f"@prefix ceo: <{CEOPREFIX}> .")
    lines.append("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .")
    lines.append("")
    lines.append(f"GRAPH <{graph_uri}> {{")

    for row in rows:
        item = row["item"]

        lines.append(f"  <{item}> ceo:aantalGisteren {row['aantalGisteren']} ;")
        lines.append(f"    ceo:aantalEergisteren {row['aantalEergisteren']} ;")
        lines.append(f"    ceo:verschil {row['verschil']} ;")
        lines.append(f"    ceo:datumGisteren \"{datum_gisteren}\"^^xsd:date ;")
        lines.append(f"    ceo:datumEergisteren \"{datum_eergisteren}\"^^xsd:date .")
        lines.append("")

    lines.append("}")

    Path(output_file).write_text(
        "\n".join(lines),
        encoding="utf-8"
    )


def upload_graph(trig_file):
    token = os.environ.get("TRIPLYDB_TOKEN")
    if not token:
        raise RuntimeError("TRIPLYDB_TOKEN is niet beschikbaar in de environment")

    process = subprocess.run(
        [
            "./triplydb.exe",
            "import-from-file",
            "--account", "rce",
            "--dataset", "cho",
            "--token", token,
            "--url", "https://api.linkeddata.cultureelerfgoed.nl",
            trig_file
        ],
        capture_output=True,
        text=True
    )

    if process.returncode != 0:
        raise RuntimeError(process.stderr)


def main():
    if len(sys.argv) != 5:
        raise RuntimeError(
            "Gebruik: compare.py <datum_gisteren> <datum_eergisteren> "
            "<graph_gisteren> <graph_eergisteren>"
        )

    datum_gisteren = sys.argv[1]
    datum_eergisteren = sys.argv[2]
    graph_gisteren = sys.argv[3]
    graph_eergisteren = sys.argv[4]

    result_graph_uri = (
        "https://linkeddata.cultureelerfgoed.nl/graph/cho-diff/"
        f"{datum_gisteren}_{datum_eergisteren}"
    )

    csv_name = f"div-cho-{datum_gisteren}_{datum_eergisteren}.csv"
    trig_name = f"div-cho-{datum_gisteren}_{datum_eergisteren}.trig"

    # 1. SPARQL-query uitvoeren
    try:
        rows = run_monitor_query(
            "queries/query-monitor.rq",
            graph_gisteren,
            graph_eergisteren
        )
    except Exception as exc:
        raise RuntimeError(f"SPARQL-monitor-query faalde: {exc}")

    # 2. CSV schrijven (altijd volledig)
    with open(csv_name, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "item",
            "aantalGisteren",
            "aantalEergisteren",
            "verschil"
        ])

        for row in rows:
            writer.writerow([
                row["item"],
                row["aantalGisteren"],
                row["aantalEergisteren"],
                row["verschil"]
            ])

    # 3. Resultaat-graph schrijven en uploaden
    try:
        write_result_graph(
            rows,
            datum_gisteren,
            datum_eergisteren,
            result_graph_uri,
            trig_name
        )
        upload_graph(trig_name)
    except Exception as exc:
        raise RuntimeError(f"Resultaat-graph schrijven/uploaden faalde: {exc}")

    # 4. Succespad
    # Mail wordt later weer netjes aangezet
    print(
        f"Monitor succesvol uitgevoerd voor {datum_gisteren} vs {datum_eergisteren}. "
        f"{len(rows)} items verwerkt."
    )


if __name__ == "__main__":
    main()
