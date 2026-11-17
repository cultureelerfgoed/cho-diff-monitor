from datetime import date

import pytest
from rdflib import Dataset, Literal, URIRef
from rdflib.namespace import XSD

from chodiff.compare import compare_days
from chodiff.rdfout import (
    SnapshotError,
    diff_dataset,
    index_dataset,
    parse_snapshot,
    snapshot_dataset,
    write_trig,
)

PRED = "https://linkeddata.cultureelerfgoed.nl/def/ceo#aantalInstanties"
TTL = """@prefix ceo: <https://linkeddata.cultureelerfgoed.nl/def/ceo#>.
ceo:Rijksmonument ceo:aantalInstanties 63000.
<http://www.w3.org/2004/02/skos/core#prefLabel> ceo:aantalInstanties 5945.
"""
G = "https://linkeddata.cultureelerfgoed.nl/rce/diff-cho/graph/"


def test_parse_snapshot_ok():
    assert len(parse_snapshot(TTL, PRED, 500)) == 2


@pytest.mark.parametrize(
    ("ttl", "message"),
    [
        ("", "lege graph"),
        ("dit is geen turtle", "geen geldige Turtle"),
        (
            '<a:x> <https://linkeddata.cultureelerfgoed.nl/def/ceo#aantalInstanties> "veel" .',
            "geen geheel getal",
        ),
        ("<a:x> <a:p> 1 .", "Onverwachte eigenschap"),
    ],
)
def test_parse_snapshot_rejects_bad_input(ttl, message):
    with pytest.raises(SnapshotError, match=message):
        parse_snapshot(ttl, PRED, 500)


def test_parse_snapshot_detects_truncation():
    with pytest.raises(SnapshotError, match="afgekapt"):
        parse_snapshot(TTL, PRED, 2)


def _roundtrip(ds, tmp_path) -> Dataset:
    path = write_trig(ds, tmp_path / "out.trig")
    loaded = Dataset()
    loaded.parse(path, format="trig")
    return loaded


def test_snapshot_trig_has_named_graph(tmp_path):
    ds = snapshot_dataset(parse_snapshot(TTL, PRED, 500), G + "2026-11-17")
    loaded = _roundtrip(ds, tmp_path)
    assert len(loaded.graph(URIRef(G + "2026-11-17"))) == 2


def test_diff_trig_typed_literals(tmp_path):
    rows = compare_days({"https://ex.org/A": 5}, {"https://ex.org/A": 7})
    ns = "https://linkeddata.cultureelerfgoed.nl/def/cho-diff#"
    uri = G + "2026-11-17_2026-11-16"
    ds = diff_dataset(rows, uri, date(2026, 11, 17), date(2026, 11, 16), ns)
    g = _roundtrip(ds, tmp_path).graph(URIRef(uri))
    item = URIRef("https://ex.org/A")
    assert g.value(item, URIRef(ns + "verschil")) == Literal(-2, datatype=XSD.integer)
    assert g.value(item, URIRef(ns + "datumVandaag")) == Literal("2026-11-17", datatype=XSD.date)
    assert len(g) == 5


def test_index_graph(tmp_path):
    ds = index_dataset(
        G + "index",
        G + "2026-11-17",
        G + "2026-11-16",
        G + "2026-11-17_2026-11-16",
        date(2026, 11, 17),
    )
    assert len(_roundtrip(ds, tmp_path).graph(URIRef(G + "index"))) == 5
