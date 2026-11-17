"""Instellingen uit config.toml, met overrides uit de omgeving."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config.toml"


@dataclass(frozen=True)
class Settings:
    api_url: str
    web_url: str
    account: str
    dataset: str
    saved_query: str
    saved_query_version: int
    page_size: int
    query_limit: int
    local_query: Path
    graph_base: str
    index_graph: str
    diff_ns: str
    count_predicate: str
    timezone: str
    smtp_host: str
    smtp_port: int
    mail_from: str
    mail_from_name: str
    mail_to: tuple[str, ...]

    # --- afgeleide URL's -------------------------------------------------

    @property
    def sparql_endpoint(self) -> str:
        return f"{self.api_url}/datasets/{self.account}/{self.dataset}/sparql"

    @property
    def saved_query_url(self) -> str:
        return f"{self.api_url}/queries/{self.account}/{self.saved_query}"

    @property
    def saved_query_run_url(self) -> str:
        return f"{self.saved_query_url}/{self.saved_query_version}/run"

    def snapshot_graph(self, day: date) -> str:
        return f"{self.graph_base}{day.isoformat()}"

    def diff_graph(self, today: date, previous: date) -> str:
        return f"{self.graph_base}{today.isoformat()}_{previous.isoformat()}"

    def graph_web_url(self, graph: str) -> str:
        """Link naar de graph in de TriplyDB-webinterface."""
        return f"{self.web_url}/{self.account}/{self.dataset}/table?graph={quote(graph, safe='')}"


def load_settings(path: Path | None = None) -> Settings:
    data = tomllib.loads((path or DEFAULT_CONFIG).read_text(encoding="utf-8"))
    triply, producer, graphs = data["triplydb"], data["producer"], data["graphs"]
    vocab, mail = data["vocabulary"], data["mail"]

    mail_to = tuple(mail["to"])
    override = os.environ.get("CHODIFF_MAIL_TO", "").strip()
    if override:
        mail_to = tuple(addr.strip() for addr in override.split(",") if addr.strip())

    return Settings(
        api_url=triply["api_url"].rstrip("/"),
        web_url=triply["web_url"].rstrip("/"),
        account=triply["account"],
        dataset=triply["dataset"],
        saved_query=producer["saved_query"],
        saved_query_version=int(producer["saved_query_version"]),
        page_size=int(producer["page_size"]),
        query_limit=int(producer["query_limit"]),
        local_query=ROOT / producer["local_query"],
        graph_base=graphs["base"],
        index_graph=graphs["index"],
        diff_ns=vocab["diff"],
        count_predicate=vocab["count_predicate"],
        timezone=data["time"]["timezone"],
        smtp_host=mail["smtp_host"],
        smtp_port=int(mail["smtp_port"]),
        mail_from=mail["from_address"],
        mail_from_name=mail["from_name"],
        mail_to=mail_to,
    )
