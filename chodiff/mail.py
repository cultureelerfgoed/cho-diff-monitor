"""E-mailrapportages: opbouw (HTML + platte tekst) en verzending.

De HTML is opgebouwd met tabellen en inline-stijlen, zodat hij ook in
Outlook en webmail goed wordt weergegeven.
"""

from __future__ import annotations

import logging
import os
import smtplib
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from html import escape
from pathlib import Path

from .compare import DayRow, WeekRow
from .config import Settings
from .dates import WEEKDAYS
from .gha import run_url
from .report import number, short, signed

log = logging.getLogger(__name__)

MAX_ROWS = 100  # meer rijen dan dit staan alleen in de CSV-bijlage

MONTHS = (
    "januari",
    "februari",
    "maart",
    "april",
    "mei",
    "juni",
    "juli",
    "augustus",
    "september",
    "oktober",
    "november",
    "december",
)
DAYNAMES = ("maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag")

# Kleuren: Rijkshuisstijl-lintblauw voor de kop, GitHub-achtige statuskleuren.
BRAND = "#154273"
TEXT = "#1f2328"
MUTED = "#59636e"
BORDER = "#d1d9e0"
STATUS = {
    "ok": ("#1a7f37", "#dafbe1"),
    "info": ("#0969da", "#ddf4ff"),
    "warn": ("#9a6700", "#fff8c5"),
    "error": ("#cf222e", "#ffebe9"),
}
FONT = "-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Consolas,'Liberation Mono',monospace"


@dataclass
class Mail:
    subject: str
    text: str
    html: str
    attachments: list[Path] = field(default_factory=list)


def long_date(d: date, weekday: bool = False) -> str:
    text = f"{d.day} {MONTHS[d.month - 1]} {d.year}"
    return f"{DAYNAMES[d.weekday()]} {text}" if weekday else text


# --------------------------------------------------------------------------
# HTML-bouwstenen
# --------------------------------------------------------------------------


def _diff_cell(n: int, compact: bool = False) -> str:
    color = STATUS["ok"][0] if n > 0 else STATUS["error"][0] if n < 0 else MUTED
    weight = "600" if n else "400"
    if compact:  # smalle dagkolommen in het weekrapport; 0 als rustige punt
        label = escape(signed(n)) if n else "·"
        return (
            f'<td align="right" style="padding:6px 6px;border-top:1px solid {BORDER};'
            f'color:{color};font-size:12px;white-space:nowrap">{label}</td>'
        )
    return (
        f'<td align="right" style="padding:6px 10px;border-top:1px solid {BORDER};'
        f'color:{color};font-weight:{weight};white-space:nowrap">{escape(signed(n))}</td>'
    )


def _num_cell(n: int) -> str:
    return (
        f'<td align="right" style="padding:6px 10px;border-top:1px solid {BORDER};'
        f'color:{TEXT};white-space:nowrap">{escape(number(n))}</td>'
    )


def _item_cell(item: str, badge: str | None = None) -> str:
    badge_html = ""
    if badge:
        fg, bg = STATUS["warn"]
        badge_html = (
            f' <span style="background:{bg};color:{fg};border-radius:10px;padding:1px 7px;'
            f'font:600 11px {FONT}">{escape(badge)}</span>'
        )
    # Korte namen (ceo:Xyz) nooit afbreken; volledige IRI's mogen overal breken.
    wrap = "white-space:nowrap" if short(item) != item else "overflow-wrap:anywhere"
    return (
        f'<td style="padding:6px 10px;border-top:1px solid {BORDER};{wrap}">'
        f'<a href="{escape(item)}" style="color:{TEXT};text-decoration:none;font:13px {MONO}">'
        f"{escape(short(item))}</a>{badge_html}</td>"
    )


def _table(headers: Sequence[tuple[str, str]], body_rows: Sequence[str]) -> str:
    head = "".join(
        f'<th align="{align}" style="padding:8px 10px;background:#f6f8fa;color:{MUTED};'
        f"font:600 12px {FONT};text-transform:uppercase;letter-spacing:.04em;"
        f'white-space:nowrap">{escape(label)}</th>'
        for label, align in headers
    )
    rows = "".join(f"<tr>{r}</tr>" for r in body_rows)
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="border:1px solid {BORDER};border-radius:6px;border-collapse:separate;'
        f'font:14px {FONT}"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>'
    )


def _kpis(items: Sequence[tuple[str, str]]) -> str:
    cells = "".join(
        f'<td style="padding:12px 14px;border:1px solid {BORDER};border-radius:6px;'
        f'background:#ffffff" width="{100 // len(items)}%">'
        f'<div style="font:12px {FONT};color:{MUTED}">{escape(label)}</div>'
        f'<div style="font:600 22px {FONT};color:{TEXT};margin-top:2px">{escape(value)}</div>'
        f"</td>"
        for label, value in items
    )
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="8" '
        f'style="margin:0 -8px 12px -8px"><tr>{cells}</tr></table>'
    )


def _banner(status: str, html_message: str) -> str:
    fg, bg = STATUS[status]
    return (
        f'<div style="background:{bg};border-left:4px solid {fg};border-radius:4px;'
        f'padding:12px 14px;margin:0 0 16px 0;font:15px {FONT};color:{TEXT}">'
        f"{html_message}</div>"
    )


def _paragraph(html_text: str) -> str:
    return f'<p style="font:14px/1.5 {FONT};color:{TEXT};margin:16px 0 0 0">{html_text}</p>'


def _page(kicker: str, title: str, content: str, links: Sequence[tuple[str, str]]) -> str:
    footer_links = " &nbsp;·&nbsp; ".join(
        f'<a href="{escape(url)}" style="color:{BRAND}">{escape(label)}</a>' for label, url in links
    )
    return f"""<!doctype html>
<html lang="nl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title></head>
<body style="margin:0;padding:0;background:#f3f4f6">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6">
<tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
 style="max-width:780px;background:#ffffff;border:1px solid {BORDER};border-radius:8px">
<tr><td style="background:{BRAND};padding:20px 24px;border-radius:8px 8px 0 0">
<div style="font:600 12px {FONT};letter-spacing:.08em;text-transform:uppercase;color:#c9d7e8">
{escape(kicker)}</div>
<div style="font:600 22px {FONT};color:#ffffff;margin-top:4px">{escape(title)}</div>
</td></tr>
<tr><td style="padding:20px 24px 24px 24px">{content}</td></tr>
<tr><td style="padding:14px 24px;border-top:1px solid {BORDER};font:12px {FONT};color:{MUTED}">
{footer_links}{"<br>" if footer_links else ""}
Automatisch verstuurd door de CHO Diff Monitor (Rijksdienst voor het Cultureel Erfgoed).
</td></tr>
</table></td></tr></table></body></html>"""


def _links(*pairs: tuple[str, str | None]) -> list[tuple[str, str]]:
    return [(label, url) for label, url in pairs if url]


def _text_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]

    def fmt(cells: Sequence[str]) -> str:
        first = cells[0].ljust(widths[0])
        rest = (c.rjust(w) for c, w in zip(cells[1:], widths[1:], strict=True))
        return "  ".join([first, *rest]).rstrip()

    return "\n".join([fmt(headers), fmt(["-" * w for w in widths]), *map(fmt, rows)])


# --------------------------------------------------------------------------
# Rapporten
# --------------------------------------------------------------------------


def day_report(
    settings: Settings,
    today: date,
    previous: date,
    rows: Sequence[DayRow],
    devs: Sequence[DayRow],
    graph_uri: str | None,
    csv_path: Path | None,
    notes: Sequence[str] = (),
) -> Mail:
    changed_presence = [r for r in devs if r.is_new or r.is_gone]

    if not devs:
        status, subject_tail = "ok", "geen afwijkingen"
        banner = f"Geen afwijkingen ten opzichte van <b>{escape(long_date(previous))}</b>."
    else:
        status = "warn" if changed_presence else "info"
        subject_tail = f"{len(devs)} afwijking{'en' if len(devs) != 1 else ''}"
        banner = (
            f"<b>{len(devs)}</b> van de {len(rows)} items wijken af ten opzichte van "
            f"<b>{escape(long_date(previous))}</b>."
        )
        if changed_presence:
            subject_tail += f", {len(changed_presence)} nieuw/verdwenen"
            banner += f"<br><b>Let op:</b> {len(changed_presence)} item(s) zijn nieuw of verdwenen."

    content = _banner(status, banner)
    content += _kpis(
        [
            ("Items vergeleken", number(len(rows))),
            ("Afwijkingen", number(len(devs))),
            ("Nieuw / verdwenen", number(len(changed_presence))),
        ]
    )
    if devs:
        body = [
            _item_cell(r.item, "nieuw" if r.is_new else "verdwenen" if r.is_gone else None)
            + _num_cell(r.previous)
            + _num_cell(r.today)
            + _diff_cell(r.diff)
            for r in devs[:MAX_ROWS]
        ]
        content += _table(
            [("Item", "left"), ("Gisteren", "right"), ("Vandaag", "right"), ("Verschil", "right")],
            body,
        )
        if len(devs) > MAX_ROWS:
            content += _paragraph(f"De overige {len(devs) - MAX_ROWS} afwijkingen staan in de CSV.")
    for note in notes:
        content += _paragraph(f"<i>{escape(note)}</i>")
    content += _paragraph("De bijgevoegde CSV bevat alle items, ook die zonder verschil.")

    title = long_date(today, weekday=True)
    links = _links(
        ("Resultaatgraph", settings.graph_web_url(graph_uri) if graph_uri else None),
        ("Workflow-run", run_url()),
    )
    html = _page("DIFF CHO · dagrapport", title, content, links)

    text = [
        f"DIFF CHO – dagrapport {long_date(today, weekday=True)}",
        f"Vergeleken met {long_date(previous)}",
        "",
        f"Items vergeleken:  {len(rows)}",
        f"Afwijkingen:       {len(devs)}",
        f"Nieuw/verdwenen:   {len(changed_presence)}",
        "",
    ]
    if devs:
        text.append(
            _text_table(
                ["Item", "Gisteren", "Vandaag", "Verschil"],
                [
                    [short(r.item), number(r.previous), number(r.today), signed(r.diff)]
                    for r in devs[:MAX_ROWS]
                ],
            )
        )
        text.append("")
    text += list(notes)
    text += [f"{label}: {url}" for label, url in links]
    text.append("De volledige CSV is bijgevoegd.")

    return Mail(
        subject=f"DIFF CHO {today.isoformat()} · {subject_tail}",
        text="\n".join(text),
        html=html,
        attachments=[csv_path] if csv_path else [],
    )


def week_report(
    settings: Settings,
    week: Sequence[date],
    rows: Sequence[WeekRow],
    devs: Sequence[WeekRow],
    csv_path: Path | None,
) -> Mail:
    start, end = week[0], week[-1]
    iso_week = start.isocalendar().week
    period = f"{long_date(start)} t/m {long_date(end)}"

    changed_presence = [r for r in devs if r.is_new or r.is_gone]
    if devs:
        status = "warn" if changed_presence else "info"
        banner = f"<b>{len(devs)}</b> van de {len(rows)} items veranderden in week {iso_week}."
        tail = f"{len(devs)} item{'s' if len(devs) != 1 else ''} veranderd"
        if changed_presence:
            tail += f", {len(changed_presence)} nieuw/verdwenen"
            banner += (
                f"<br><b>Let op:</b> {len(changed_presence)} item(s) zijn deze week "
                "nieuw verschenen of verdwenen."
            )
    else:
        status, banner, tail = "ok", f"Geen veranderingen in week {iso_week}.", "geen afwijkingen"

    content = _banner(status, banner)
    content += _kpis(
        [
            ("Items vergeleken", number(len(rows))),
            ("Veranderd", number(len(devs))),
            ("Nieuw / verdwenen", number(len(changed_presence))),
        ]
    )
    if devs:
        day_headers = [(d, "right") for d in WEEKDAYS[1:]]
        body = [
            _item_cell(r.item, "nieuw" if r.is_new else "verdwenen" if r.is_gone else None)
            + _num_cell(r.counts[-1])
            + _diff_cell(r.total)
            + "".join(_diff_cell(d, compact=True) for d in r.diffs)
            for r in devs[:MAX_ROWS]
        ]
        content += _table(
            [("Item", "left"), ("Stand zo", "right"), ("Netto", "right"), *day_headers],
            body,
        )
        content += _paragraph(
            f'<span style="color:{MUTED};font-size:12px">Di t/m zo: verschil ten opzichte '
            "van de dag ervoor. Netto: zondag min maandag.</span>"
        )
        if len(devs) > MAX_ROWS:
            content += _paragraph(f"De overige {len(devs) - MAX_ROWS} items staan in de CSV.")
    content += _paragraph("De bijgevoegde CSV bevat alle dagtellingen en dagverschillen.")

    links = _links(("Workflow-run", run_url()))
    html = _page(f"DIFF CHO · weekrapport · week {iso_week}", period, content, links)

    text = [
        f"DIFF CHO – weekrapport week {iso_week}",
        period,
        "",
        f"Items vergeleken: {len(rows)}",
        f"Veranderd:        {len(devs)}",
        "",
    ]
    if devs:
        text.append(
            _text_table(
                ["Item", "Ma", "Zo", "Netto", *WEEKDAYS[1:]],
                [
                    [
                        short(r.item),
                        number(r.counts[0]),
                        number(r.counts[-1]),
                        signed(r.total),
                        *(signed(d) for d in r.diffs),
                    ]
                    for r in devs[:MAX_ROWS]
                ],
            )
        )
        text.append("")
    text += [f"{label}: {url}" for label, url in links]
    text.append("De volledige CSV is bijgevoegd.")

    return Mail(
        subject=f"DIFF CHO week {start.isoformat()} – {end.isoformat()} · {tail}",
        text="\n".join(text),
        html=html,
        attachments=[csv_path] if csv_path else [],
    )


def error_report(
    subject_prefix: str, what: str, context: Sequence[tuple[str, str]], error: str
) -> Mail:
    """Foutmelding. `what` is bijvoorbeeld 'Dagmonitor' of 'Producer'."""
    rows = "".join(
        f'<tr><td style="padding:4px 12px 4px 0;color:{MUTED};white-space:nowrap">{escape(k)}</td>'
        f'<td style="padding:4px 0;color:{TEXT}">{escape(v)}</td></tr>'
        for k, v in context
    )
    content = _banner(
        "error",
        f"<b>{escape(what)} is mislukt.</b> Er is niets gedeeltelijk "
        "gerapporteerd; controleer de workflow-run.",
    )
    content += (
        f'<table role="presentation" style="font:14px {FONT};margin-bottom:12px">{rows}</table>'
    )
    content += (
        f'<pre style="background:#f6f8fa;border:1px solid {BORDER};border-radius:6px;'
        f"padding:12px;font:12px/1.45 {MONO};color:{TEXT};white-space:pre-wrap;"
        f'word-break:break-word;margin:0">{escape(error)}</pre>'
    )
    links = _links(("Workflow-run", run_url()))
    html = _page("DIFF CHO · fout", f"{what} mislukt", content, links)
    text = "\n".join(
        [
            f"{what} mislukt",
            "",
            *(f"{k}: {v}" for k, v in context),
            "",
            error,
            "",
            *(f"{label}: {url}" for label, url in links),
        ]
    )
    return Mail(subject=f"{subject_prefix} · FOUT in {what.lower()}", text=text, html=html)


# --------------------------------------------------------------------------
# Verzenden / opslaan
# --------------------------------------------------------------------------


def build_message(settings: Settings, mail: Mail) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = formataddr((settings.mail_from_name, settings.mail_from))
    msg["To"] = ", ".join(settings.mail_to)
    msg["Subject"] = mail.subject
    msg["Message-ID"] = make_msgid(domain=settings.mail_from.split("@")[-1])
    msg.set_content(mail.text)
    msg.add_alternative(mail.html, subtype="html")
    for path in mail.attachments:
        if path.exists():
            msg.add_attachment(
                path.read_bytes(), maintype="text", subtype="csv", filename=path.name
            )
    return msg


def save(settings: Settings, mail: Mail, outdir: Path, stem: str) -> Path:
    """Schrijft de mail als .eml en .html (voor proefdraaien en als artifact)."""
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / f"{stem}.html").write_text(mail.html, encoding="utf-8")
    eml = outdir / f"{stem}.eml"
    eml.write_bytes(bytes(build_message(settings, mail)))
    return eml


def send(settings: Settings, mail: Mail) -> None:
    user = os.environ.get("GMAIL_USERNAME")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not password:
        raise RuntimeError("GMAIL_USERNAME of GMAIL_APP_PASSWORD ontbreekt")

    msg = build_message(settings, mail)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=60) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(msg)
    log.info("Mail verstuurd naar %s: %s", ", ".join(settings.mail_to), mail.subject)
