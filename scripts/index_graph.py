import yaml
import datetime
import requests

from rdflib import Graph, URIRef, Literal
from rdflib.namespace import DCTERMS, XSD, Namespace


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_graph_uris(config: dict, today: datetime.date, previous: datetime.date):
    snapshot_uri = (
        f"{config['graphs']['snapshot_base']}/"
        f"{config['naming']['snapshot'].format(date=today.isoformat())}"
    )

    previous_snapshot_uri = (
        f"{config['graphs']['snapshot_base']}/"
        f"{config['naming']['snapshot'].format(date=previous.isoformat())}"
    )

    diff_uri = (
        f"{config['graphs']['diff_base']}/"
        f"{config['naming']['diff'].format(date=today.isoformat(), previous_date=previous.isoformat())}"
    )

    return snapshot_uri, previous_snapshot_uri, diff_uri


def build_index_triples(config: dict, snapshot, previous_snapshot, diff, today):
    g = Graph()

    PROV = Namespace("http://www.w3.org/ns/prov#")

    snapshot_ref = URIRef(snapshot)
    previous_ref = URIRef(previous_snapshot)
    diff_ref = URIRef(diff)

    g.add((snapshot_ref, DCTERMS.date, Literal(today.isoformat(), datatype=XSD.date)))
    g.add((snapshot_ref, PROV.wasDerivedFrom, previous_ref))

    g.add((diff_ref, DCTERMS.date, Literal(today.isoformat(), datatype=XSD.date)))
    g.add((diff_ref, PROV.used, snapshot_ref))
    g.add((diff_ref, PROV.used, previous_ref))

    return g


def sparql_insert(endpoint: str, graph_uri: str, rdf_graph: Graph):
    data = rdf_graph.serialize(format="turtle")

    query = f"""
    INSERT DATA {{
      GRAPH <{graph_uri}> {{
        {data}
      }}
    }}
    """

    response = requests.post(
        endpoint,
        data=query.encode("utf-8"),
        headers={"Content-Type": "application/sparql-update"},
        timeout=30,
    )
    response.raise_for_status()


def main():
    config = load_config("index-graph.yml")

    today = datetime.date.today()
    previous = today - datetime.timedelta(days=1)

    snapshot, previous_snapshot, diff = build_graph_uris(
        config, today, previous
    )

    index_graph = build_index_triples(
        config, snapshot, previous_snapshot, diff, today
    )

    sparql_insert(
        config["sparql_endpoint"]["update"],
        config["index_graph"]["uri"],
        index_graph,
    )


if __name__ == "__main__":
    main()
