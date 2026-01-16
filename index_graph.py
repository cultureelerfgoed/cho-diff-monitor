import yaml
import datetime
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import DCTERMS, XSD


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
        f"{config['naming']['diff'].format(
            date=today.isoformat(),
            previous_date=previous.isoformat()
        )}"
    )

    return snapshot_uri, previous_snapshot_uri, diff_uri


def build_index_graph(config: dict, snapshot, previous_snapshot, diff, today):
    g = Graph()
    PROV = Namespace("http://www.w3.org/ns/prov#")

    index_graph_uri = URIRef(config["index_graph"]["uri"])
    g = Graph(identifier=index_graph_uri)

    snapshot_ref = URIRef(snapshot)
    previous_ref = URIRef(previous_snapshot)
    diff_ref = URIRef(diff)

    # snapshot metadata
    g.add((snapshot_ref, DCTERMS.date, Literal(today.isoformat(), datatype=XSD.date)))
    g.add((snapshot_ref, PROV.wasDerivedFrom, previous_ref))

    # diff metadata
    g.add((diff_ref, DCTERMS.date, Literal(today.isoformat(), datatype=XSD.date)))
    g.add((diff_ref, PROV.used, snapshot_ref))
    g.add((diff_ref, PROV.used, previous_ref))

    return g


def main():
    config = load_config("index-graph.yml")

    today = datetime.date.today()
    previous = today - datetime.timedelta(days=1)

    snapshot, previous_snapshot, diff = build_graph_uris(
        config, today, previous
    )

    index_graph = build_index_graph(
        config, snapshot, previous_snapshot, diff, today
    )

    # schrijf TRIG-bestand
    index_graph.serialize("index.trig", format="trig")


if __name__ == "__main__":
    main()
