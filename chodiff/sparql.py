"""SPARQL-toegang tot de diff-cho dataset."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import __version__

QUERY_DIR = Path(__file__).resolve().parent.parent / "queries"
USER_AGENT = f"cho-diff-monitor/{__version__}"

# Een IRI die veilig tussen <...> in een query geplaatst kan worden.
_SAFE_IRI = re.compile(r"^[^\s<>\"{}|\\^`]+$")
_INTEGER_TYPES = {
    "http://www.w3.org/2001/XMLSchema#integer",
    "http://www.w3.org/2001/XMLSchema#long",
    "http://www.w3.org/2001/XMLSchema#int",
    "http://www.w3.org/2001/XMLSchema#decimal",
}

Counts = dict[str, int]  # item-IRI -> aantal


class SparqlError(RuntimeError):
    pass


def http_session() -> requests.Session:
    """Sessie met beperkte retries voor tijdelijke netwerk- en serverfouten.

    Dit is geen herstel van data: alleen een mislukte HTTP-aanvraag wordt
    (maximaal drie keer, met oplopende wachttijd) opnieuw geprobeerd.
    """
    retry = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "POST"}),
        raise_on_status=False,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers["User-Agent"] = USER_AGENT
    return session


def iri(value: str) -> str:
    """Geeft `<value>` terug, of faalt als de IRI niet veilig in een query past."""
    if not _SAFE_IRI.match(value):
        raise ValueError(f"Ongeldige IRI: {value!r}")
    return f"<{value}>"


class SparqlClient:
    def __init__(self, endpoint: str, session: requests.Session | None = None, timeout: int = 120):
        self.endpoint = endpoint
        self.session = session or http_session()
        self.timeout = timeout

    def _post(self, query: str) -> dict:
        try:
            response = self.session.post(
                self.endpoint,
                data={"query": query},
                headers={"Accept": "application/sparql-results+json"},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise SparqlError(f"SPARQL-endpoint niet bereikbaar: {exc}") from exc
        if response.status_code != 200:
            raise SparqlError(
                f"SPARQL-query mislukt (HTTP {response.status_code}): {response.text[:1000]}"
            )
        try:
            return response.json()
        except ValueError as exc:
            raise SparqlError("SPARQL-endpoint gaf geen geldige JSON terug") from exc

    def ask(self, query: str) -> bool:
        return bool(self._post(query).get("boolean"))

    def select(self, query: str) -> list[dict[str, str | int]]:
        """SELECT-resultaten als lijst dicts; integer-literals worden int."""
        rows = []
        for binding in self._post(query)["results"]["bindings"]:
            row: dict[str, str | int] = {}
            for name, term in binding.items():
                value = term["value"]
                if term.get("datatype") in _INTEGER_TYPES:
                    value = int(value.split(".")[0])
                row[name] = value
            rows.append(row)
        return rows


def load_query(name: str, **params: str) -> str:
    """Laadt queries/<name> en vult {{PARAM}}-plaatshouders in."""
    query = (QUERY_DIR / name).read_text(encoding="utf-8")
    for key, value in params.items():
        query = query.replace("{{" + key + "}}", value)
    if "{{" in query:
        raise ValueError(f"Niet-ingevulde plaatshouder in {name}")
    return query


def graph_exists(client: SparqlClient, graph: str) -> bool:
    return client.ask(f"ASK {{ GRAPH {iri(graph)} {{ ?s ?p ?o }} }}")


def fetch_counts(client: SparqlClient, graphs: list[str], predicate: str) -> dict[str, Counts]:
    """Tellingen per item, per graph. Ontbrekende of lege graphs ontbreken in het resultaat."""
    query = load_query(
        "counts.rq",
        GRAPHS=" ".join(iri(g) for g in graphs),
        PREDICATE=iri(predicate),
    )
    result: dict[str, Counts] = defaultdict(dict)
    for row in client.select(query):
        result[str(row["graph"])][str(row["item"])] = int(row["total"])
    return dict(result)
