# scripts/mail.py
#
# Verstuurt de dagelijkse DIV CHO mail via Gmail (SMTP + App Password).
#
# - HTML-mail
# - CSV altijd als bijlage
# - STARTTLS
# - geschikt voor GitHub Actions

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

FROM_EMAIL = "rce.ldv.monitor@gmail.com"
FROM_NAME = "DIV CHO monitor"
TO_EMAIL = "thesauri@cultureelerfgoed.nl"


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
            <pre>{error_message}</pre>
            <p>Datum: {datum_gisteren}</p>
          </body>
        </html>
        """

    if afwijkingen:
        rows = ""
        for row in afwijkingen:
            rows += f"""
            <tr>
              <td>{row['item']}</td>
              <td>{row['aantalGisteren']}</td>
              <td>{row['aantalEergisteren']}</td>
              <td style="color:red;">{row['verschil']}</td>
            </tr>
            """

        tabel = f"""
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
            {rows}
          </tbody>
        </table>
        """
    else:
        tabel = "<p>Geen afwijkingen.</p>"

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
        {tabel}
        <p>
          Resultaat-graph:<br/>
          <code>{graph_uri}</code>
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

    html = _render_html(
        datum_gisteren=datum_gisteren,
        datum_eergisteren=datum_eergisteren,
        totaal=len(rows),
        afwijkingen=afwijkingen,
        graph_uri=graph_uri,
        error_message=error_message
    )

    msg = EmailMessage()
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = TO_EMAIL
    msg["Subject"] = f"DIV CHO {subject_date}"

    msg.set_content("Deze mail bevat HTML. Gebruik een HTML-geschikte mailclient.")
    msg.add_alternative(html, subtype="html")

    if csv_path and Path(csv_path).exists():
        csv_bytes = Path(csv_path).read_bytes()
        msg.add_attachment(
            csv_bytes,
            maintype="text",
            subtype="csv",
            filename=Path(csv_path).name
        )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_pass)
        smtp.send_message(msg)
