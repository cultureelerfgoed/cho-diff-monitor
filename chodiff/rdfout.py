"""Opbouw en serialisatie van de graphs die naar TriplyDB gaan."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from pathlib import Path

from rdflib import Dataset, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, PROV, XSD

from .compare import DayRow

CEO = Namespace("https://linkeddata.cultureelerfgoed.nl/def/ceo#")


class SnapshotError(ValueError):
    pass


def parse_snapshot(turtle: str, count_predicate: str, query_limit: int) -> Graph:
    """Parseert en valideert de Turtle-uitvoer van de producerquery."""
    graph = Graph()
    try:
        graph.parse(data=turtle, format="turtle")
    except Exception as exc:
        raise SnapshotError(f"Producer leverde geen geldige Turtle: {exc}") from exc

    if len(graph) == 0:
        raise SnapshotError("Producer leverde een lege graph op")

    predicate = URIRef(count_predicate)
    for s, p, o in graph:
        if p != predicate:
            raise SnapshotError(f"Onverwachte eigenschap in producer-uitvoer: {p}")
        if not isinstance(o, Literal) or not isinstance(o.toPython(), int):
            raise SnapshotError(f"Telling voor {s} is geen geheel getal: {o!r}")

    if len(graph) >= query_limit:
        raise SnapshotError(
            f"Producer leverde {len(graph)} tellingen op, gelijk aan de LIMIT van "
            f"{query_limit} in de opgeslagen query. Het resultaat is vermoedelijk "
            "afgekapt; verhoog de LIMIT (en query_limit in config.toml)."
        )
    return graph


def _dataset(graph_uri: str, prefixes: dict[str, Namespace]) -> tuple[Dataset, Graph]:
    ds = Dataset()
    for prefix, ns in prefixes.items():
        ds.bind(prefix, ns)
    return ds, ds.graph(URIRef(graph_uri))


def snapshot_dataset(snapshot: Graph, graph_uri: str) -> Dataset:
    ds, g = _dataset(graph_uri, {"ceo": CEO})
    for triple in snapshot:
        g.add(triple)
    return ds


def diff_dataset(
    rows: Sequence[DayRow], graph_uri: str, today: date, previous: date, diff_ns: str
) -> Dataset:
    diff = Namespace(diff_ns)
    ds, g = _dataset(graph_uri, {"diff": diff, "xsd": Namespace(str(XSD))})
    today_lit = Literal(today.isoformat(), datatype=XSD.date)
    previous_lit = Literal(previous.isoformat(), datatype=XSD.date)
    for row in rows:
        item = URIRef(row.item)
        g.add((item, diff.aantalVandaag, Literal(row.today, datatype=XSD.integer)))
        g.add((item, diff.aantalGisteren, Literal(row.previous, datatype=XSD.integer)))
        g.add((item, diff.verschil, Literal(row.diff, datatype=XSD.integer)))
        g.add((item, diff.datumVandaag, today_lit))
        g.add((item, diff.datumGisteren, previous_lit))
    return ds


def index_dataset(
    index_graph: str, snapshot: str, previous_snapshot: str, diff: str, today: date
) -> Dataset:
    """Navigatiegraph met verwijzingen naar de meest recente dag- en resultaatgraph."""
    ds, g = _dataset(index_graph, {"dct": Namespace(str(DCTERMS)), "prov": Namespace(str(PROV))})
    day = Literal(today.isoformat(), datatype=XSD.date)
    snap, prev, dif = URIRef(snapshot), URIRef(previous_snapshot), URIRef(diff)
    g.add((snap, DCTERMS.date, day))
    g.add((snap, PROV.wasDerivedFrom, prev))
    g.add((dif, DCTERMS.date, day))
    g.add((dif, PROV.used, snap))
    g.add((dif, PROV.used, prev))
    return ds


def write_trig(ds: Dataset, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    ds.serialize(destination=str(path), format="trig", encoding="utf-8")
    return path
