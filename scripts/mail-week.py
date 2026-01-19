# scripts/mail_week.py
#
# Verstuurt de wekelijkse DIFF CHO mail via Gmail (SMTP + App Password).
#
# - HTML-mail
# - CSV altijd als bijlage
# - toont alleen items met totaalVerschil ≠ 0
# - geschikt voor GitHub Actions

import os
import smtplib
import html
from email.message import EmailMessage
from pathlib import Path


SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

FROM_EMAIL = "rce-ldv-monitor@gmail.com"
FROM_NAME = "DIFF CHO weekmonitor"
TO_EMAIL = "thesauri@cultureelerfgoed.nl"


def _clean_item(item: str) -> str:
    if not item:
        return ""

    item = item.strip()
    if item.startswith("<") and item.endswith(">"):
        item = item[1:-1]

    return html.escape(item)


def send_week_report_mail(
    week_start,
    week_end,
    rows,
    csv_path,
    error_message=None
):
    smtp_user = os.environ.get("GMAIL_USERNAME")
    smtp_pass = os.environ.get("GMAIL_APP_PASSWORD")

    if not smtp_user or not smtp_pass:
        raise RuntimeError(
            "GMAIL_USERNAME of GMAIL_APP_PASSWORD ontbreekt"
        )

    afwijkingen = []

    for row in rows:
        aantallen = [
            row["dag1"],
            row["dag2"],
            row["dag3"],
            row["dag4"],
            row["dag5"],
            row["dag6"],
            row["dag7"],
        ]

        diffs = [
            aantallen[i] - aantallen[i - 1]
            for i in range(1, 7)
        ]

        totaal = sum(diffs)

        if totaal != 0:
            afwijkingen.append({
                "item": row["item"],
                "totaal": totaal
            })

    if error_message:
        html_body = f"""
        <html>
          <body>
            <h2>DIFF CHO weekmonitor – fout</h2>
            <p>Er is een fout opgetreden bij de wekelijkse vergelijking.</p>
            <pre>{html.escape(error_message)}</pre>
            <p>Week: {week_start} t/m {week_end}</p>
          </body>
        </html>
        """
    else:
        rows_html = ""
        for row in afwijkingen:
            rows_html += f"""
            <tr>
              <td><code>{_clean_item(row["item"])}</code></td>
              <td>{row["totaal"]}</td>
            </tr>
            """

        tabel_html = (
            f"""
            <table border="1" cellpadding="4" cellspacing="0">
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Totaal verschil</th>
                </tr>
              </thead>
              <tbody>
                {rows_html}
              </tbody>
            </table>
            """
            if afwijkingen
            else "<p>Geen afwijkingen in deze week.</p>"
        )

        html_body = f"""
        <html>
          <body>
            <h2>DIFF CHO weekoverzicht</h2>
            <p>
              Week: <b>{week_start}</b> t/m <b>{week_end}</b>
            </p>
            <ul>
              <li>Totaal aantal items: {len(rows)}</li>
              <li>Aantal items met afwijking: {len(afwijkingen)}</li>
            </ul>
            {tabel_html}
            <p>
              Het volledige overzicht is als CSV-bijlage toegevoegd.
            </p>
          </body>
        </html>
        """

    msg = EmailMessage()
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = TO_EMAIL
    msg["Subject"] = f"DIFF CHO week {week_start} – {week_end}"

    msg.set_content(
        "Deze mail bevat HTML. Gebruik een HTML-geschikte mailclient."
    )
    msg.add_alternative(html_body, subtype="html")

    if csv_path and Path(csv_path).exists():
        msg.add_attachment(
            Path(csv_path).read_bytes(),
            maintype="text",
            subtype="csv",
            filename=Path(csv_path).name
        )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_pass)
        smtp.send_message(msg)
