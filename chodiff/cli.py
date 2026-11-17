"""Commandoregel: `python -m chodiff {produce,compare,weekly}`.

Opties kunnen ook via omgevingsvariabelen worden gezet (handig vanuit
GitHub Actions, zonder workflow-invoer in shellcommando's te plakken):

    CHODIFF_DRY_RUN=true    niets uploaden, geen mail versturen
    CHODIFF_FORCE=true      bestaande graphs overschrijven
    CHODIFF_DATE=JJJJ-MM-DD datum voor de dagmonitor
    CHODIFF_WEEK_OF=JJJJ-MM-DD  een dag in de week voor de weekmonitor
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import sys
from collections.abc import Callable, Sequence
from datetime import date, timedelta
from pathlib import Path

from . import dates, gha, mail
from .compare import compare_days, compare_week, deviations, week_deviations
from .config import Settings, load_settings
from .rdfout import diff_dataset, index_dataset, parse_snapshot, snapshot_dataset, write_trig
from .report import day_summary_md, week_summary_md, write_day_csv, write_week_csv
from .sparql import SparqlClient, fetch_counts, graph_exists, http_session
from .triply import upload

log = logging.getLogger("chodiff")


class MissingGraphsError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# Hulpfuncties
# --------------------------------------------------------------------------


def _env_bool(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "ja"}


def _env_date(name: str) -> date | None:
    value = os.environ.get(name, "").strip()
    return dates.parse_date(value) if value else None


def _deliver(settings: Settings, message: mail.Mail, args: argparse.Namespace, stem: str) -> None:
    """Bewaart de mail altijd in de uitvoermap en verstuurt hem tenzij dat is uitgezet."""
    saved = mail.save(settings, message, args.output, stem)
    if args.dry_run or args.no_mail:
        gha.notice(f"Mail niet verstuurd (proefdraai/--no-mail); opgeslagen als {saved}")
        return
    mail.send(settings, message)


def _with_error_mail(
    settings: Settings,
    args: argparse.Namespace,
    what: str,
    subject_prefix: str,
    context: Sequence[tuple[str, str]],
    work: Callable[[], None],
) -> None:
    """Voert `work` uit; bij een fout volgt een foutmail en faalt de run alsnog."""
    try:
        work()
    except Exception as exc:
        detail = f"{type(exc).__name__}: {exc}"
        gha.error(f"{what} mislukt — {detail}")
        try:
            report = mail.error_report(subject_prefix, what, context, detail)
            _deliver(settings, report, args, "mail-fout")
        except Exception as mail_exc:
            gha.error(f"Ook de foutmail kon niet worden verstuurd: {mail_exc}")
        raise


def _missing(day_graphs: Sequence[tuple[date, str]], counts: dict) -> list[str]:
    return [d.isoformat() for d, g in day_graphs if g not in counts]


# --------------------------------------------------------------------------
# produce
# --------------------------------------------------------------------------


def _normalize_query(text: str) -> str:
    text = re.sub(r"#[^\n]*", "", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def _check_query_drift(settings: Settings, session) -> None:
    """Waarschuwt als de opgeslagen TriplyDB-query afwijkt van de lokale kopie."""
    try:
        meta = session.get(
            f"{settings.saved_query_url}/{settings.saved_query_version}", timeout=60
        ).json()
        saved = meta["requestConfig"]["payload"]["query"]
    except Exception as exc:
        gha.warning(f"Kon de opgeslagen query niet controleren: {exc}")
        return
    local = settings.local_query.read_text(encoding="utf-8")
    if _normalize_query(saved) != _normalize_query(local):
        gha.warning(
            f"Opgeslagen query {settings.saved_query} v{settings.saved_query_version} wijkt af "
            f"van {settings.local_query.name}. Breng ze weer in overeenstemming."
        )
    latest = meta.get("numberOfVersions")
    if isinstance(latest, int) and latest > settings.saved_query_version:
        gha.warning(
            f"Er is een nieuwere versie (v{latest}) van {settings.saved_query}; "
            f"de producer gebruikt bewust v{settings.saved_query_version} (zie config.toml)."
        )


def cmd_produce(settings: Settings, args: argparse.Namespace) -> None:
    day = dates.today(settings.timezone)
    graph = settings.snapshot_graph(day)
    log.info("Producer voor %s → %s", day, graph)

    def work() -> None:
        session = http_session()
        _check_query_drift(settings, session)

        response = session.get(
            settings.saved_query_run_url,
            params={"page": 1, "pageSize": settings.page_size},
            headers={"Accept": "text/turtle"},
            timeout=900,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Opgeslagen query gaf HTTP {response.status_code}: {response.text[:1000]}"
            )
        snapshot = parse_snapshot(response.text, settings.count_predicate, settings.query_limit)
        log.info("%d tellingen ontvangen", len(snapshot))

        trig = write_trig(snapshot_dataset(snapshot, graph), args.output / f"daggraph-{day}.trig")

        client = SparqlClient(settings.sparql_endpoint, session)
        exists = graph_exists(client, graph)
        if args.dry_run:
            status = "proefdraai: niet geüpload"
        elif exists and not args.force:
            status = "bestond al: niet opnieuw geüpload (gebruik 'forceren' om te overschrijven)"
            gha.warning(f"Daggraph {day} {status}")
        else:
            upload(settings, trig, overwrite=exists)
            status = "overschreven" if exists else "geüpload"
        gha.notice(f"Daggraph {day}: {len(snapshot)} tellingen, {status}")
        gha.summary(
            f"### Producer {day}\n\n- Graph: `{graph}`\n- Tellingen: **{len(snapshot)}**\n"
            f"- Status: {status}"
        )

    _with_error_mail(
        settings,
        args,
        "Producer",
        f"DIFF CHO {day.isoformat()}",
        [("Datum", day.isoformat()), ("Daggraph", graph)],
        work,
    )


# --------------------------------------------------------------------------
# compare (dagmonitor)
# --------------------------------------------------------------------------


def cmd_compare(settings: Settings, args: argparse.Namespace) -> None:
    current = dates.today(settings.timezone)
    today = args.date or current
    previous = today - timedelta(days=1)
    g_today, g_prev = settings.snapshot_graph(today), settings.snapshot_graph(previous)
    g_diff = settings.diff_graph(today, previous)
    log.info("Dagmonitor %s vs %s", today, previous)

    def work() -> None:
        client = SparqlClient(settings.sparql_endpoint)
        counts = fetch_counts(client, [g_today, g_prev], settings.count_predicate)
        missing = _missing([(today, g_today), (previous, g_prev)], counts)
        if missing:
            raise MissingGraphsError(
                "Ontbrekende of lege daggraph(s): "
                + ", ".join(missing)
                + ". Is de producer voor die dag(en) gedraaid?"
            )

        rows = compare_days(counts[g_today], counts[g_prev])
        devs = deviations(rows)
        stem = f"diff-cho-{today}_{previous}"
        csv_path = write_day_csv(rows, args.output / f"{stem}.csv")
        trig = write_trig(
            diff_dataset(rows, g_diff, today, previous, settings.diff_ns),
            args.output / f"{stem}.trig",
        )

        notes: list[str] = []
        if args.dry_run:
            notes.append("Proefdraai: de resultaatgraph is niet geüpload.")
        else:
            exists = graph_exists(client, g_diff)
            if exists and not args.force:
                notes.append("De resultaatgraph bestond al en is niet overschreven.")
                gha.warning(f"Resultaatgraph {g_diff} bestond al; niet overschreven")
            else:
                upload(settings, trig, overwrite=exists)
            if today == current:
                index = index_dataset(settings.index_graph, g_today, g_prev, g_diff, today)
                upload(settings, write_trig(index, args.output / "index.trig"), overwrite=True)

        report = mail.day_report(settings, today, previous, rows, devs, g_diff, csv_path, notes)
        _deliver(settings, report, args, f"mail-{today}")
        gha.notice(f"Dagmonitor {today}: {len(rows)} items, {len(devs)} afwijkingen")
        gha.summary(day_summary_md(f"Dagmonitor {today} vs {previous}", rows, devs))

    _with_error_mail(
        settings,
        args,
        "Dagmonitor",
        f"DIFF CHO {today.isoformat()}",
        [("Datum", today.isoformat()), ("Vergeleken met", previous.isoformat())],
        work,
    )


# --------------------------------------------------------------------------
# weekly (weekmonitor)
# --------------------------------------------------------------------------


def cmd_weekly(settings: Settings, args: argparse.Namespace) -> None:
    week = (
        dates.week_of(args.week_of)
        if args.week_of
        else dates.previous_week(dates.today(settings.timezone))
    )
    start, end = week[0], week[-1]
    graphs = [settings.snapshot_graph(d) for d in week]
    log.info("Weekmonitor %s t/m %s", start, end)

    def work() -> None:
        client = SparqlClient(settings.sparql_endpoint)
        counts = fetch_counts(client, graphs, settings.count_predicate)
        missing = _missing(list(zip(week, graphs, strict=True)), counts)
        if missing:
            raise MissingGraphsError("Ontbrekende of lege daggraph(s): " + ", ".join(missing))

        rows = compare_week([counts[g] for g in graphs])
        devs = week_deviations(rows)
        csv_path = write_week_csv(rows, args.output / f"diff-cho-week-{start}_{end}.csv")
        report = mail.week_report(settings, week, rows, devs, csv_path)
        _deliver(settings, report, args, f"mail-week-{start}")
        gha.notice(f"Weekmonitor {start} t/m {end}: {len(rows)} items, {len(devs)} veranderd")
        gha.summary(week_summary_md(f"Weekmonitor {start} t/m {end}", rows, devs))

    _with_error_mail(
        settings,
        args,
        "Weekmonitor",
        f"DIFF CHO week {start} – {end}",
        [("Week", f"{start} t/m {end}")],
        work,
    )


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--dry-run",
        action="store_true",
        default=_env_bool("CHODIFF_DRY_RUN"),
        help="niets uploaden en geen mail versturen",
    )
    common.add_argument("--no-mail", action="store_true", help="geen mail versturen")
    common.add_argument(
        "--output",
        type=Path,
        default=Path("output"),
        help="map voor CSV, TriG en mail (standaard: output/)",
    )
    common.add_argument("--config", type=Path, help="alternatief config.toml")
    common.add_argument("-v", "--verbose", action="store_true")

    parser = argparse.ArgumentParser(prog="chodiff", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("produce", parents=[common], help="daggraph maken en uploaden")
    p.add_argument(
        "--force",
        action="store_true",
        default=_env_bool("CHODIFF_FORCE"),
        help="bestaande daggraph overschrijven",
    )
    p.set_defaults(func=cmd_produce)

    p = sub.add_parser("compare", parents=[common], help="dag vergelijken met de dag ervoor")
    p.add_argument(
        "--date",
        type=dates.parse_date,
        default=_env_date("CHODIFF_DATE"),
        help="te vergelijken dag (JJJJ-MM-DD); standaard vandaag",
    )
    p.add_argument(
        "--force",
        action="store_true",
        default=_env_bool("CHODIFF_FORCE"),
        help="bestaande resultaatgraph overschrijven",
    )
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("weekly", parents=[common], help="weekoverzicht (ma t/m zo)")
    p.add_argument(
        "--week-of",
        type=dates.parse_date,
        default=_env_date("CHODIFF_WEEK_OF"),
        help="een dag in de gewenste week; standaard de vorige week",
    )
    p.set_defaults(func=cmd_weekly)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    for stream in (sys.stdout, sys.stderr):  # Windows-console is standaard geen UTF-8
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )
    settings = load_settings(args.config)
    try:
        args.func(settings, args)
    except Exception:
        log.error("Run afgebroken; details hieronder.", exc_info=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
