"""Upload naar TriplyDB via de officiële TriplyDB CLI."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path

from .config import Settings

log = logging.getLogger(__name__)


class UploadError(RuntimeError):
    pass


def _cli() -> str:
    cli = os.environ.get("TRIPLYDB_CLI") or shutil.which("triplydb") or shutil.which("triplydb.exe")
    if not cli:
        raise UploadError(
            "TriplyDB CLI niet gevonden. Zet TRIPLYDB_CLI op het pad naar de CLI "
            "of zet 'triplydb' op het PATH."
        )
    return cli


def upload(settings: Settings, trig: Path, *, overwrite: bool) -> None:
    """Importeert een TriG-bestand in de diff-cho dataset.

    Het token gaat via de omgevingsvariabele TRIPLYDB_TOKEN (die de CLI zelf
    leest) en dus niet via de commandoregel. Zonder `overwrite` gebruikt de CLI
    `--mode rename`; daarom controleert de aanroeper vooraf of de graph al bestaat.
    """
    if not os.environ.get("TRIPLYDB_TOKEN"):
        raise UploadError("TRIPLYDB_TOKEN ontbreekt")

    cmd = [
        _cli(),
        "import-from-file",
        "--url",
        settings.api_url,
        "--account",
        settings.account,
        "--dataset",
        settings.dataset,
    ]
    if overwrite:
        cmd += ["--mode", "overwrite"]
    cmd.append(str(trig))

    log.info(
        "Upload %s naar %s/%s%s",
        trig.name,
        settings.account,
        settings.dataset,
        " (overschrijven)" if overwrite else "",
    )
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800, check=False)
    except subprocess.TimeoutExpired as exc:
        raise UploadError(f"Upload van {trig.name} duurde langer dan 30 minuten") from exc

    if proc.returncode != 0:
        output = "\n".join(part for part in (proc.stdout, proc.stderr) if part).strip()
        raise UploadError(f"Upload van {trig.name} mislukt (exitcode {proc.returncode}):\n{output}")
