# scripts/compare.py
#
# CHO diff monitor – hoofdscript
#
# Verantwoordelijkheden:
# - uitvoeren van query-monitor.rq
# - genereren van volledige CSV
# - schrijven van resultaat-graph (N-Quads)
#
# Mail is tijdelijk uitgeschakeld bij fouten.
# De graph is de primaire output.

import sys
import csv
import subprocess
import os
from pathlib import Path

from sparql import run_monitor_query


DIFF_NS = "https://linkeddata.cultureelerfgoed.nl/def/cho-diff#"
XSD_DATE = "<http://www.w3.org/2001/XMLSchema#date>"


def write_result_graph(
    rows,
    datum_gisteren,
    datum_eergisteren,
    graph_uri,
    output_file
):
    lines = []

    for row in rows:
        item = row["item"]

        lines.append(
            f"<{item}> <{DIFF_NS}aantalGisteren> {row['aantalGisteren']} <{graph_uri}> ."
        )
        lines.append(
            f"<{item}> <{DIFF_NS}aantalEergisteren> {row['aantalEergisteren']} <{graph_uri}> ."
        )
        lines.append(
            f"<{item}> <{DIFF_NS}verschil> {row['verschil']} <{graph_uri}> ."
        )
        lines.append(
            f"<{item}> <{DIFF_NS}datumGisteren> "
            f"\"{datum_gisteren}\"^^{XSD_DATE} <{graph_uri}> ."
        )
        lines.append(
            f"<{item}> <{DIFF_NS}datumEergisteren> "
            f"\"{datum_eergisteren}\"^^{XSD_DATE} <{graph_uri}> ."
        )

    Path(output_file).write_text(
        "\n".join(lines),
        encoding="utf-8"
    )


def upload_graph(nq_file):
    token = os.environ.get("TRIPLYDB_TOKEN")
    if not token:
        raise RuntimeError("TRIPLYDB_TOKEN is niet beschikbaar")

    process = subprocess.run(
        [
            "./triplydb.exe",
            "import-from-file",
            "--account", "rce",
            "--dataset", "cho",
            "--token", token,
            "--url", "https://api.linkeddata.cultureelerfgoed.nl",
            nq_file
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
    nq_name = f"div-cho-{datum_gisteren}_{datum_eergisteren}.nq"

    # 1. SPARQL
    rows = run_monitor_query(
        "queries/query-monitor.rq",
        graph_gisteren,
        graph_eergisteren
    )

    # 2. CSV
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

    # 3. Resultaat-graph
    write_result_graph(
        rows,
        datum_gisteren,
        datum_eergisteren,
        result_graph_uri,
        nq_name
    )
    upload_graph(nq_name)

    print(
        f"Monitor succesvol uitgevoerd voor {datum_gisteren} vs {datum_eergisteren}. "
        f"{len(rows)} items verwerkt."
    )


if __name__ == "__main__":
    main()
