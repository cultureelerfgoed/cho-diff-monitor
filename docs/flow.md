# Verwerkingsstappen

De dagelijkse verwerking draait in één workflow (`CHO diff · dagelijks`) met
twee jobs: eerst de producer, daarna de dagmonitor. De dagmonitor start alleen
als de producer is geslaagd, of bewust is overgeslagen bij een handmatige run
met *alleen monitor*.

Alle datums zijn kalenderdagen in Nederlandse tijd (`Europe/Amsterdam`).

---

## Producer (`python -m chodiff produce`)

1. Bepaal de datum van **vandaag**.
2. Controleer of de opgeslagen TriplyDB-query nog gelijk is aan
   `queries/query-producer.rq`. Is dat niet zo, dan volgt een waarschuwing.
3. Voer de opgeslagen query uit (Turtle).
4. Valideer het resultaat: geldige Turtle, niet leeg, alleen
   `ceo:aantalInstanties` met gehele getallen, niet afgekapt door de `LIMIT`.
5. Schrijf de daggraph als TriG met graph-URI
   `https://linkeddata.cultureelerfgoed.nl/rce/diff-cho/graph/JJJJ-MM-DD`.
6. Bestaat die graph al, sla dan de upload over, tenzij *forceren* aan staat.
   Anders volgt de upload naar `rce/diff-cho`.

Bij een fout: foutmail, en de dagmonitor wordt niet gestart.

---

## Dagmonitor (`python -m chodiff compare`)

1. Bepaal **vandaag** (of de opgegeven datum) en **gisteren**.
2. Haal met `queries/counts.rq` de tellingen van beide daggraphs op.
3. Ontbreekt één van beide graphs of is hij leeg: stop met een foutmail die
   de ontbrekende datum(s) noemt.
4. Vergelijk alle items uit beide dagen. Een item dat in één dag ontbreekt,
   telt daar als 0 en wordt gemarkeerd als *nieuw* of *verdwenen*.
5. Schrijf de CSV (alle items) en de resultaatgraph
   `…/graph/JJJJ-MM-DD_JJJJ-MM-DD` (vandaag_gisteren).
6. Upload de resultaatgraph (overslaan als hij al bestaat, tenzij *forceren*).
7. Is de datum vandaag, werk dan de indexgraph bij (overschrijven).
8. Verstuur het dagrapport en zet een samenvatting op de run-pagina.

---

## Weekmonitor (`python -m chodiff weekly`)

1. Bepaal de laatste volledige kalenderweek (maandag t/m zondag), of de week
   van de opgegeven datum.
2. Haal met `queries/counts.rq` de tellingen van de zeven daggraphs op.
3. Ontbreekt een daggraph: stop met een foutmail met de ontbrekende datums.
4. Bereken per item de zes dagverschillen en het netto verschil
   (zondag min maandag).
5. Schrijf de CSV en verstuur het weekrapport met alle items die ergens in de
   week veranderden.

De weekmonitor schrijft geen graphs naar TriplyDB.

---

## Uitvoer en prioriteit

- De **resultaatgraph** is de primaire output.
- De **CSV** is secundair.
- De **mail** en de **run-samenvatting** zijn rapportagevormen.

Alles wordt elke dag gemaakt, ook als er geen afwijkingen zijn. Er zijn geen
stille fouten.
