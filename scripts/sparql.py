# scripts/sparql.py
#
# Verantwoordelijkheid:
# - uitvoeren van query-monitor.rq
# - invullen van graph-placeholders
# - teruggeven van ruwe rijen

import subprocess
from pathlib import Path


def run_monitor_query(query_path, graph_gisteren, graph_eergisteren):
    query = Path(query_path).read_text(encoding="utf-8")

    query = query.replace("{{GRAPH_GISTEREN}}", graph_gisteren)
    query = query.replace("{{GRAPH_EERGISTEREN}}", graph_eergisteren)

    process = subprocess.run(
        ["./triplydb.exe", "query"],
        input=query,
        text=True,
        capture_output=True
    )

    if process.returncode != 0:
        raise RuntimeError(process.stderr)

    rows = []

    for line in process.stdout.splitlines():
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
