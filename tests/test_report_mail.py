import csv
from datetime import date

import pytest

from chodiff import mail
from chodiff.compare import compare_days, compare_week, deviations, week_deviations
from chodiff.config import load_settings
from chodiff.dates import week_of
from chodiff.report import short, signed, write_day_csv, write_week_csv

CEO = "https://linkeddata.cultureelerfgoed.nl/def/ceo#"
T, P = date(2026, 11, 17), date(2026, 11, 16)


@pytest.fixture
def settings(monkeypatch):
    monkeypatch.delenv("CHODIFF_MAIL_TO", raising=False)
    return load_settings()


def test_short_and_signed():
    assert short(CEO + "Rijksmonument") == "ceo:Rijksmonument"
    assert short("https://onbekend.example/x") == "https://onbekend.example/x"
    assert signed(1234) == "+1.234" and signed(-5) == "−5" and signed(0) == "0"


def test_day_csv_keeps_column_contract(tmp_path):
    path = write_day_csv(compare_days({"https://ex.org/A": 3}, {}), tmp_path / "d.csv")
    rows = list(csv.reader(path.open(encoding="utf-8")))
    assert rows[0] == ["item", "aantalVandaag", "aantalGisteren", "verschil"]
    assert rows[1] == ["https://ex.org/A", "3", "0", "3"]


def test_week_csv_keeps_column_contract(tmp_path):
    path = write_week_csv(
        compare_week([{"https://ex.org/A": i} for i in range(7)]), tmp_path / "w.csv"
    )
    header, row = list(csv.reader(path.open(encoding="utf-8")))
    assert header[1] == "aantalMa" and header[8] == "diffDi" and header[-1] == "totaalVerschil"
    assert len(header) == 15 and row[-1] == "6"


def test_day_report_escapes_and_flags_new_items(settings):
    evil = "https://ex.org/<script>"
    rows = compare_days({CEO + "Rijksmonument": 10, evil: 1}, {CEO + "Rijksmonument": 8})
    m = mail.day_report(settings, T, P, rows, deviations(rows), "https://g", None)
    assert "<script>" not in m.html
    assert "nieuw" in m.html
    assert m.subject == "DIFF CHO 2026-11-17 · 2 afwijkingen, 1 nieuw/verdwenen"
    assert "ceo:Rijksmonument" in m.text


def test_day_report_without_deviations(settings):
    rows = compare_days({CEO + "X": 1}, {CEO + "X": 1})
    m = mail.day_report(settings, T, P, rows, [], None, None)
    assert m.subject.endswith("geen afwijkingen")


def test_week_report_subject(settings):
    week = week_of(date(2026, 11, 9))
    rows = compare_week([{CEO + "X": i + 1} for i in range(7)])
    m = mail.week_report(settings, week, rows, week_deviations(rows), None)
    assert m.subject == "DIFF CHO week 2026-11-09 – 2026-11-15 · 1 item veranderd"
    assert "week 46" in m.html


def test_week_report_flags_new_items(settings):
    week = week_of(date(2026, 11, 9))
    rows = compare_week([{CEO + "X": 1}] * 5 + [{CEO + "X": 1, CEO + "Zaak": 9}] * 2)
    m = mail.week_report(settings, week, rows, week_deviations(rows), None)
    assert m.subject.endswith("1 item veranderd, 1 nieuw/verdwenen")
    assert "nieuw" in m.html


def test_error_report_and_message(settings, tmp_path):
    m = mail.error_report(
        "DIFF CHO 2026-11-17", "Dagmonitor", [("Datum", "2026-11-17")], "RuntimeError: <boom>"
    )
    assert "&lt;boom&gt;" in m.html
    eml = mail.save(settings, m, tmp_path, "fout")
    assert b"FOUT in dagmonitor" in eml.read_bytes()


def test_mail_to_override(monkeypatch):
    monkeypatch.setenv("CHODIFF_MAIL_TO", "a@example.org, b@example.org")
    assert load_settings().mail_to == ("a@example.org", "b@example.org")
