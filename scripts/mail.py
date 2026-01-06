# scripts/mail.py
#
# Verantwoordelijkheid:
# - opbouwen en versturen van mails voor de CHO diff monitor
# - zowel succes- als foutmeldingen
#
# Dit script bevat GEEN logica over afwijkingen.

import smtplib
from email.message import EmailMessage
from pathlib import Path


MAIL_TO = "thesauri@cultureelerfgoed.nl"
MAIL_FROM = "thesauri@cultureelerfgoed.nl"
SMTP_HOST = "localhost"


def send_mail(
    subject_date,
    datum_gisteren=None,
    datum_eergisteren=None,
    totaal=None,
    afwijkingen=None,
    csv_path=None,
    error_message=None
):
    msg = EmailMessage()
    msg["To"] = MAIL_TO
    msg["From"] = MAIL_FROM
    msg["Subject"] = f"DIV CHO {subject_date}"

    if error_message:
        _build_error_mail(
            msg,
            datum_gisteren,
            datum_eergisteren,
            error_message
        )
    else:
        _build_success_mail(
            msg,
            datum_gisteren,
            datum_eergisteren,
            totaal,
            afwijkingen,
            csv_path
        )

    _send(msg)


def _build_error_mail(msg, datum_gisteren, datum_eergisteren, error_message):
    text = (
        "De dagelijkse CHO-vergelijking kon niet worden uitgevoerd.\n\n"
        f"Datum gisteren: {datum_gisteren}\n"
        f"Datum eergisteren: {datum_eergisteren}\n\n"
        "Foutmelding:\n"
        f"{error_message}\n"
    )

    msg.set_content(text)


def _build_success_mail(
    msg,
    datum_gisteren,
    datum_eergisteren,
    totaal,
    afwijkingen,
    csv_path
):
    html = []
    html.append("<p>Dagelijkse CHO-vergelijking.</p>")
    html.append("<ul>")
    html.append(f"<li>Gisteren: {datum_gisteren}</li>")
    html.append(f"<li>Eergisteren: {datum_eergisteren}</li>")
    html.append(f"<li>Totaal aantal items: {totaal}</li>")
    html.append(f"<li>Aantal afwijkingen: {len(afwijkingen)}</li>")
    html.append("</ul>")

    if afwijkingen:
        html.append("<p>Afwijkingen:</p>")
        html.append("<table border='1' cellpadding='4' cellspacing='0'>")
        html.append(
            "<tr>"
            "<th>Item</th>"
            "<th>Aantal gisteren</th>"
            "<th>Aantal eergisteren</th>"
            "<th>Verschil</th>"
            "</tr>"
        )

        for row in afwijkingen:
            html.append(
                "<tr style='color:red;'>"
                f"<td>{row['item']}</td>"
                f"<td>{row['aantalGisteren']}</td>"
                f"<td>{row['aantalEergisteren']}</td>"
                f"<td>{row['verschil']}</td>"
                "</tr>"
            )

        html.append("</table>")
    else:
        html.append("<p>Er zijn geen afwijkingen gevonden.</p>")

    html.append("<p>Het volledige overzicht is opgenomen in de CSV-bijlage.</p>")

    msg.add_alternative("\n".join(html), subtype="html")

    if csv_path:
        path = Path(csv_path)
        msg.add_attachment(
            path.read_bytes(),
            maintype="text",
            subtype="csv",
            filename=path.name
        )


def _send(msg):
    with smtplib.SMTP(SMTP_HOST) as smtp:
        smtp.send_message(msg)
