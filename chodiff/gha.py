"""Kleine helpers voor GitHub Actions: annotaties, job-samenvatting en run-link.

Buiten GitHub Actions doen ze niets bijzonders, zodat alles ook lokaal draait.
"""

from __future__ import annotations

import logging
import os

log = logging.getLogger("chodiff")

IN_ACTIONS = os.environ.get("GITHUB_ACTIONS") == "true"


def _escape(message: str) -> str:
    return message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def notice(message: str) -> None:
    log.info(message)
    if IN_ACTIONS:
        print(f"::notice::{_escape(message)}", flush=True)


def warning(message: str) -> None:
    log.warning(message)
    if IN_ACTIONS:
        print(f"::warning::{_escape(message)}", flush=True)


def error(message: str) -> None:
    log.error(message)
    if IN_ACTIONS:
        print(f"::error::{_escape(message)}", flush=True)


def summary(markdown: str) -> None:
    """Voegt Markdown toe aan de samenvatting van de workflow-run."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(markdown.rstrip() + "\n\n")


def run_url() -> str | None:
    server, repo, run_id = (
        os.environ.get("GITHUB_SERVER_URL"),
        os.environ.get("GITHUB_REPOSITORY"),
        os.environ.get("GITHUB_RUN_ID"),
    )
    if server and repo and run_id:
        return f"{server}/{repo}/actions/runs/{run_id}"
    return None
