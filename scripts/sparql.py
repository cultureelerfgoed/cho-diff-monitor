# scripts/sparql.py
#
# Uitvoeren van SPARQL-queries via HTTP endpoint.
# Bevat helpers voor:
# - dagmonitor (vandaag vs gisteren)
# - weekmonitor (maandag t/m zondag)

import requests
from pathlib import Path


SPARQL_ENDPOINT = (
    "https://api.linkeddata.cultureelerfgoed.nl/datasets/rce/cho/sparql"
)

# -------------------------------------------------
# Dagmonitor
# -------------------------------------------------

def run_monitor_query(query_path, graph_vandaag, graph_gisteren):
    """
    Voert de dagvergelijking uit (vandaag vs gisteren).
    """
    query = Path(query_path).read_text(encoding="utf-8")

    query = query.replace("{{GRAPH_VANDAAG}}", graph_vandaag)
    query = query.replace("{{GRAPH_GISTEREN}}", graph_gisteren)

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

    # Eerste regel is header
    for line in lines[1:]:
        if not line.strip():
            continue

        parts = line.split("\t")
        rows.append({
            "item": parts[0],
            "aantalVandaag": int(parts[1]),
            "aantalGisteren": int(parts[2]),
            "verschil": int(parts[3]),
        })

    return rows


# -------------------------------------------------
# Weekmonitor
# -------------------------------------------------

def run_week_monitor_query(query_path, graph_uris):
    """
    Voert de weekvergelijking uit.
    graph_uris: lijst van 7 graph-URI's (maandag t/m zondag)
    """
    if len(graph_uris) != 7:
        raise ValueError("Weekmonitor verwacht exact 7 graph-URI's")

    query = Path(query_path).read_text(encoding="utf-8")

    for i, graph in enumerate(graph_uris, start=1):
        query = query.replace(f"{{{{GRAPH_{i}}}}}", graph)

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

    # Eerste regel is header
    for line in lines[1:]:
        if not line.strip():
            continue

        parts = line.split("\t")
        rows.append({
            "item": parts[0],
            "dag1": int(parts[1]),
            "dag2": int(parts[2]),
            "dag3": int(parts[3]),
            "dag4": int(parts[4]),
            "dag5": int(parts[5]),
            "dag6": int(parts[6]),
            "dag7": int(parts[7]),
        })

    return rows
