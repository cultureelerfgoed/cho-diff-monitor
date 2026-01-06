# scripts/mail.py
#
# Verstuurt de dagelijkse DIV CHO mail via Gmail (SMTP + App Password).
#
# - HTML-mail
# - CSV altijd als bijlage
# - item-waarden veilig ge-escaped voor HTML
# - geschikt voor GitHub Actions

import os
import smtplib
import html
from email.message import EmailMessage
from pathlib import Path


SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

FROM_EMAIL = "rce-ldv-monitor@gmail.com"
FROM_NAME = "DIV CHO monitor"
TO_EMAIL = "thesauri@cultureelerfgoed.nl"


def _clean_item(item: str) -> str:
    """
    Verwijdert < > rond IRIs en escapt voor HTML.
    """
    if not item:
        return ""

    item = item.strip()
    if item.startswith("<") and item.endswith(">"):
        item = item[1:-1]

    return html.escape(item)


def _render_html(
    datum_gisteren,
    datum_eergisteren,
    totaal,
    afwijkingen,
    graph_uri,
    error_message=None
):
    if error_message:
        return f"""
        <html>
          <body>
            <h2>DIV CHO – fout</h2>
            <p>Er is een fout opgetreden bij de dagelijkse vergelijking.</p>
            <pre>{html.escape(error_message)}</pre>
            <p>Datum: {datum_gisteren}</p>
          </body>
        </html>
        """

    if afwijkingen:
        rows_html = ""
        for row in afwijkingen:
            item_html = _clean_item(row.get("item", ""))

            rows_html += f"""
            <tr>
              <td><code>{item_html}</code></td>
              <td>{row['aantalGisteren']}</td>
              <td>{row['aantalEergisteren']}</td>
              <td style="color:red;">{row['verschil']}</td>
            </tr>
            """

        tabel_html = f"""
        <table border="1" cellpadding="4" cellspacing="0">
          <thead>
            <tr>
              <th>Item</th>
              <th>Gisteren</th>
              <th>Eergisteren</th>
              <th>Verschil</th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>
        """
    else:
        tabel_html = "<p>Geen afwijkingen.</p>"

    return f"""
    <html>
      <body>
        <h2>DIV CHO dagelijkse vergelijking</h2>
        <p>
          Vergelijking van <b>{datum_gisteren}</b> met <b>{datum_eergisteren}</b>.
        </p>
        <ul>
          <li>Totaal aantal items: {totaal}</li>
          <li>Aantal afwijkingen: {len(afwijkingen)}</li>
        </ul>
        {tabel_html}
        <p>
          Resultaat-graph:<br/>
          <code>{html.escape(graph_uri)}</code>
        </p>
        <p>
          Het volledige overzicht is als CSV-bijlage toegevoegd.
        </p>
      </body>
    </html>
    """


def send_report_mail(
    subject_date,
    datum_gisteren,
    datum_eergisteren,
    rows,
    csv_path,
    graph_uri,
    error_message=None
):
    smtp_user = os.environ.get("GMAIL_USERNAME")
    smtp_pass = os.environ.get("GMAIL_APP_PASSWORD")

    if not smtp_user or not smtp_pass:
        raise RuntimeError(
            "GMAIL_USERNAME of GMAIL_APP_PASSWORD ontbreekt"
        )

    afwijkingen = [r for r in rows if r.get("verschil") != 0]

    html_body = _render_html(
        datum_gisteren=datum_gisteren,
        datum_ee_
