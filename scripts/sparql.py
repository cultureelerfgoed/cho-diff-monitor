# scripts/sparql.py
#
# Uitvoeren van query-monitor.rq via HTTP SPARQL endpoint
# Geen TriplyDB CLI nodig voor queries

import requests
from pathlib import Path


SPARQL_ENDPOINT = "https://api.linkeddata.cultureelerfgoed.nl/datasets/rce/cho/sparql"


def run_monitor_query(query_path, graph_gisteren, graph_eergisteren):
    query = Path(query_path).read_text(encoding="utf-8")

    query = query.replace("{{GRAPH_GISTEREN}}", graph_gisteren)
    query = query.replace("{{GRAPH_EERGISTEREN}}", graph_eergisteren)

    headers = {
        "Accept": "text/tab-separated-values"
    }

    response = requests.post(
        SPARQL_ENDPOINT,
        data={"query": query},
        headers=headers,
        timeout=60
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"SPARQL query failed ({response.status_code}):\n{response.text}"
        )

    rows = []
    lines = response.text.splitlines()

    # eerste regel = header
    for line in lines[1:]:
        if not line.strip():
            continue

        parts = line.split("\t")
        rows.append({
            "item": parts[0],
            "aantalGisteren": int(parts[1]),
            "aantalEergisteren": int(parts[2]),
            "verschil": int(parts[3])
        })

    return rows
