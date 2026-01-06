# scripts/compare.py
#
# CHO diff monitor – hoofdscript
#
# Verantwoordelijkheden:
# - uitvoeren van query-monitor.rq
# - genereren van volledige CSV
# - schrijven van resultaat-graph (Trig met named graph)
#
# CSV is bijvangst.
# De named graph is het product.

import sys
import csv
import subprocess
import os
from pathlib import Path

from sparql import run_monitor_query


DIFF_NS = "https://linkeddata.cultureelerfgoed.nl/def/cho-diff#"


def normalize_iri(value: str) -> str:
    """Zorgt dat een IRI exact één keer tussen < > staat."""
    value = value.strip()
    if value.startswith("<") and value.endswith(">"):
        return value[1:-1]
    return value


def write_result_graph(
    rows,
    datum_gisteren,
    datum_eergisteren,
    graph_uri,
    output_file
):
    lines = []

    # Prefixes
    lines.append(f"@prefix diff: <{DIFF_NS}> .")
    lines.append("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .")
    lines.append("")

    # EXACT hetzelfde patroon als de producer
    lines.append(f"<{graph_uri}> {{")

    for row in rows:
        item = normalize_iri(row["item"])

        lines.append(f"  <{item}>")
        lines.append(f"    diff:aantalGisteren {row['aantalGisteren']} ;")
        lines.append(f"    diff:aantalEergisteren {row['aantalEergisteren']} ;")
        lines.append(f"    diff:verschil {row['verschil']} ;")
        lines.append(
            f"    diff:datumGisteren \"{datum_gisteren}\"^^xsd:date ;"
        )
        lines.append(
            f"    diff:datumEergisteren \"{datum_eergisteren}\"^^xsd:date ."
        )
        lines.append("")

    lines.append("}")

    Path(output_file).write_text(
        "\n".join(lines),
        encoding="utf-8"
    )


def upload_graph(trig_file):
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

    # 3. Resultaat-graph (zoals de producer)
    write_result_graph(
        rows,
        datum_gisteren,
        datum_eergisteren,
        result_graph_uri,
        trig_name
    )
    upload_graph(trig_name)

    print(
        f"Monitor succesvol uitgevoerd voor {datum_gisteren} vs {datum_eergisteren}. "
        f"{len(rows)} items verwerkt."
    )


if __name__ == "__main__":
    main()
