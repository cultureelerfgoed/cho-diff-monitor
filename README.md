# DIFF CHO dagelijkse vergelijking

## Doel
Deze repository bevat de workflows voor de dagelijkse productie en vergelijking van CHO-gegevens in TriplyDB.

Het proces bestaat uit twee samenhangende stappen:

1. het dagelijks vastleggen van een daggraph (producer),
2. het dagelijks vergelijken van twee opeenvolgende daggraphs (monitor).

Elke vergelijking resulteert in:
- een resultaat-graph in TriplyDB,
- een CSV-bestand met alle resultaten,
- een e-mailrapportage.

Het doel is vroege signalering van elke wijziging, hoe klein ook.

---

## Dagelijkse flow

### Producer
De producer-workflow draait dagelijks en voert de volgende stappen uit:

1. Ophalen van CHO-data via een vaste TriplyDB-query.
2. Omzetten van het resultaat naar Trig.
3. Opslaan van de data in een named graph voor **vandaag**.

Resultaat:
- één daggraph per datum.

---

### Monitor
De monitor-workflow draait dagelijks en vergelijkt twee bestaande daggraphs.

De stappen zijn:

1. Bepalen van de datums:
   - vandaag,
   - gisteren.
2. Controleren of beide daggraphs bestaan.
3. Uitvoeren van een vergelijking via SPARQL.
4. Berekenen van verschillen per item.
5. Genereren van:
   - een CSV met alle resultaten,
   - een resultaat-graph met diff-informatie.
6. Versturen van een e-mailrapportage.

---

## Graph-conventies

### Input-graphs (daggraphs)
Dagelijkse CHO-graphs hebben het formaat:

https://linkeddata.cultureelerfgoed.nl/rce/diff-cho/graph/YYYY-MM-DD

Elke graph bevat de volledige stand van zaken voor één dag.

---

### Resultaat-graphs (vergelijkingen)
Voor elke vergelijking wordt een aparte graph aangemaakt met het formaat:

https://linkeddata.cultureelerfgoed.nl/rce/diff-cho/graph/YYYY-MM-DD_YYYY-MM-DD

De eerste datum is **vandaag**.  
De tweede datum is **gisteren**.

De graph bevat uitsluitend afgeleide diff-data.

---

## Vocabulaire
Resultaat-graphs gebruiken een eigen vocabulaire, gescheiden van brondata:

https://linkeddata.cultureelerfgoed.nl/def/cho-diff#

Dit vocabulaire bevat uitsluitend eigenschappen voor:
- aantallen per dag,
- verschillen,
- bijbehorende datums.

Bronvocabularia (zoals CEO) worden niet hergebruikt voor diff-data.

---

## Afwijkingsdefinitie
De volgende regels zijn van toepassing:

- Elke verandering is een afwijking.
- Een verschil van +1 of −1 is relevant.
- Een verschil van 0 is **geen** afwijking.

Gevolgen:
- de CSV bevat altijd alle resultaten,
- de mail toont alleen regels met een verschil ongelijk aan nul.

---

## CSV-uitvoer
Bij elke monitor-run wordt een CSV gegenereerd met:

- alle items,
- aantallen voor vandaag en gisteren,
- het berekende verschil.

De CSV:
- bevat geen kleurcodering,
- is bedoeld voor archivering en analyse,
- wordt beschikbaar gesteld als workflow-artifact.

---

## Mailgedrag
Er wordt elke dag een mail verstuurd.

Eigenschappen:
- ook als alle verschillen 0 zijn,
- ook bij fouten,
- onderwerp:
  DIFF CHO YYYY-MM-DD
- ontvanger:
  thesauri@cultureelerfgoed.nl

De mail bevat:
- een korte samenvatting,
- een tabel met alleen afwijkingen,
- een CSV-bijlage met het volledige overzicht.

Kleurgebruik wordt alleen in de mail toegepast.

---

## Foutscenario’s
Als een benodigde daggraph ontbreekt:

- wordt geen vergelijking uitgevoerd,
- wordt geen resultaat-graph aangemaakt,
- wordt een mail verstuurd met een expliciete foutmelding.

De melding vermeldt:
- welke graph ontbreekt,
- om welke datum het gaat.

Er zijn geen stille fouten.

---

## Repository-structuur

- .github/workflows/  
  GitHub Actions voor producer en monitor.
- queries/  
  SPARQL-queries voor productie en vergelijking.
- scripts/  
  Vergelijkingslogica, CSV-generatie en graph-export.
- docs/  
  Nadere documentatie over ontwerpkeuzes en graph-afspraken.

---

## Onderhoud en overdracht
De volledige logica is expliciet vastgelegd in:

- scripts,
- workflows,
- documentatie.

Ontwerpkeuzes zijn bewust gemaakt en beschreven, zodat:
- onderhoud beheersbaar blijft,
- overdracht aan collega’s mogelijk is,
- het proces begrijpelijk blijft zonder voorkennis.
