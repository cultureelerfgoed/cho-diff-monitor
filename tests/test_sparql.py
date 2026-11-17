import pytest

from chodiff.sparql import SparqlClient, fetch_counts, iri, load_query


class FakeResponse:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.queries = []

    def post(self, url, data, headers, timeout):
        self.queries.append(data["query"])
        return FakeResponse(self.payload)


def _b(graph, item, total):
    return {
        "graph": {"type": "uri", "value": graph},
        "item": {"type": "uri", "value": item},
        "total": {
            "type": "literal",
            "value": str(total),
            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
        },
    }


def test_fetch_counts_groups_per_graph():
    session = FakeSession({"results": {"bindings": [_b("g:1", "i:a", 5), _b("g:2", "i:a", 7)]}})
    client = SparqlClient("https://endpoint", session=session)
    counts = fetch_counts(client, ["g:1", "g:2", "g:3"], "p:count")
    assert counts == {"g:1": {"i:a": 5}, "g:2": {"i:a": 7}}  # g:3 ontbreekt → niet aanwezig
    assert "VALUES ?graph { <g:1> <g:2> <g:3> }" in session.queries[0]
    assert "<p:count>" in session.queries[0]


@pytest.mark.parametrize("bad", ["a b", "x>y", 'q"', "a{b}"])
def test_iri_rejects_injection(bad):
    with pytest.raises(ValueError):
        iri(bad)


def test_load_query_requires_all_placeholders():
    with pytest.raises(ValueError, match="plaatshouder"):
        load_query("counts.rq", GRAPHS="<g:1>")
