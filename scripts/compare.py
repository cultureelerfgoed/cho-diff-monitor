# scripts/compare.py
#
# CHO diff monitor – hoofdscript
#
# Verantwoordelijkheden:
# - uitvoeren van query-monitor.rq
# - genereren van volledige CSV
# - schrijven van resultaat-graph (Trig met expliciete named graph)
# - versturen van e-mail via Gmail (SMTP met App Password)
#
# De graph is de primaire output.
# CSV en mail zijn afgeleide rapportages.

import sys
import csv
import subprocess
import os
import requests
from pathlib import Path

from sparql import run_monitor_query
from mail import send_report_mail


DIFF_NS = "https://linkeddata.cultureelerfgoed.nl/def/cho-diff#"


def normalize_iri(value: str) -> str:
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

    lines.append(f"@prefix diff: <{DIFF_NS}> .")
    lines.append("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .")
    lines.append("")

    # Zelfde constructie als producer
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
        raise RuntimeError("TRIPLYDB_TOKEN ontbreekt")

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

    try:
        # 1. SPARQL-vergelijking
        rows = run_monitor_query(
            "queries/query-monitor.rq",
            graph_gisteren,
            graph_eergisteren
        )

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
        write_result_graph(
            rows,
            datum_gisteren,
            datum_eergisteren,
            result_graph_uri,
            trig_name
        )
        upload_graph(trig_name)

        # 4. Mail (succes)
        send_report_mail(
            subject_date=datum_gisteren,
            datum_gisteren=datum_gisteren,
            datum_eergisteren=datum_eergisteren,
            rows=rows,
            csv_path=csv_name,
            graph_uri=result_graph_uri
        )

        print(
            f"Monitor succesvol uitgevoerd voor {datum_gisteren} vs {datum_eergisteren}. "
            f"{len(rows)} items verwerkt."
        )

    except Exception as exc:
        # Mail bij fout
        send_report_mail(
            subject_date=datum_gisteren,
            datum_gisteren=datum_gisteren,
            datum_eergisteren=datum_eergisteren,
            rows=[],
            csv_path=None,
            graph_uri="",
            error_message=str(exc)
        )
        raise


if __name__ == "__main__":
    main()
