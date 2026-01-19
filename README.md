# DIFF CHO dagelijkse vergelijking

## Doel
Deze repository bevat de workflows voor de dagelijkse productie en vergelijking van CHO-gegevens in TriplyDB.

Het proces is ingericht voor volledige uitlegbaarheid, reproduceerbaarheid en overdraagbaarheid.  
Elke wijziging in de data wordt zichtbaar gemaakt, ongeacht omvang.

Het proces bestaat uit drie samenhangende onderdelen:

1. Producer – vastleggen van dagelijkse snapshots (daggraphs)
2. Index – vastleggen van de actuele navigatiestatus (state)
3. Monitor – vergelijken en rapporteren van opeenvolgende daggraphs

Elke dagelijkse vergelijking resulteert in:
- een resultaat-graph in TriplyDB
- een CSV-bestand met alle resultaten
- een e-mailrapportage

Het doel is vroege en volledige signalering van elke wijziging.

---

## Datasets en verantwoordelijkheden

Binnen dit proces worden twee datasets onderscheiden:

- cho  
  Bevat uitsluitend de actuele brondata van CHO-objecten.  
  Deze dataset wordt niet aangepast door dit proces.

- diff-cho  
  Bevat alle door dit proces geproduceerde graphs:
  - dagelijkse snapshots (daggraphs)
  - afgeleide vergelijking- en diff-graphs
  - een index-graph met actuele metadata

Alle vastlegging en historische reconstructie vindt plaats in diff-cho.

---

## Tijddefinitie en afronding van dagstanden

Binnen dit proces wordt gewerkt met kalenderdagen op basis van Nederlandse tijd (CET/CEST).

Een dagstand wordt als afgerond beschouwd nadat de brondata volledig is verwerkt en beschikbaar is gesteld in de LDV. In de praktijk is dit rond 04:00 uur ’s nachts.

De producer- en monitor-workflows draaien pas na dit moment, zodat uitsluitend volledige en stabiele dagstanden worden vastgelegd en vergeleken.

Cron-tijden in GitHub Actions zijn ingesteld in UTC en zodanig gekozen dat zij in zowel zomer- als wintertijd na afronding van de dagverwerking plaatsvinden.

Het systeem volgt expliciet kalenderdagen en geen dynamische “latest”-logica.

---

## Dagelijkse flow

### Producer

De producer-workflow draait dagelijks en is de enige component die bron-graphs schrijft.

Verantwoordelijkheid:
- vastleggen van de volledige CHO-stand per dag
- bouwen van de index-graph

Stappen:
1. Ophalen van CHO-data via een vaste TriplyDB-query
2. Omzetten van het resultaat naar Trig
3. Opslaan van de data in een named graph voor vandaag
4. Opbouwen en overschrijven van de index-graph

Output:
- één daggraph (snapshot) per datum
- één index-graph (state)

---

## Index

### Verantwoordelijkheid
De index-graph fungeert als actueel navigatiepunt binnen de dataset diff-cho.

De index:
- legt vast welke daggraph en welke diff-graph de meest recente zijn
- bevat uitsluitend metadata
- bevat geen historie
- wordt dagelijks volledig overschreven

Graph:
https://linkeddata.cultureelerfgoed.nl/rce/diff-cho/graph/index

De index-graph wordt uitsluitend geschreven door de producer.

### Import-norm (TriplyDB CLI)

De index-graph wordt altijd geïmporteerd met:
triplydb import-from-file --mode overwrite

Snapshots en resultaat-graphs worden nooit overschreven en gebruiken de standaard CLI-modus (rename).

---

## Monitor

### Verantwoordelijkheid
De monitor vergelijkt twee opeenvolgende daggraphs en legt de verschillen vast.

Kenmerken:
- draait dagelijks
- vergelijkt vandaag met gisteren
- rekent alle verschillen expliciet uit
- gebruikt geen drempelwaarden

Stappen:
1. Bepalen van vandaag en gisteren
2. Controleren of beide daggraphs bestaan
3. Uitvoeren van een vergelijking via SPARQL
4. Berekenen van verschillen per item
5. Genereren van:
   - een CSV met alle resultaten
   - een resultaat-graph met diff-informatie
6. Versturen van een e-mailrapportage

De monitor schrijft geen snapshots en geen index.

---

## Resultaat-graph als primaire bron

De resultaat-graph is de bron van waarheid voor monitoring en rapportage.

Eigenschappen:
- bevat uitsluitend afgeleide diff-data
- is volledig reproduceerbaar
- is onafhankelijk van CSV en mail
- blijft permanent beschikbaar in TriplyDB

Graph-formaat:
https://linkeddata.cultureelerfgoed.nl/rce/diff-cho/graph/YYYY-MM-DD_YYYY-MM-DD

De eerste datum is vandaag.  
De tweede datum is gisteren.

---

## Graph-conventies

Input-graphs (daggraphs):
https://linkeddata.cultureelerfgoed.nl/rce/diff-cho/graph/YYYY-MM-DD

Resultaat-graphs (vergelijkingen):
https://linkeddata.cultureelerfgoed.nl/rce/diff-cho/graph/YYYY-MM-DD_YYYY-MM-DD

---

## Vocabulaire

Resultaat-graphs gebruiken een eigen vocabulaire:
https://linkeddata.cultureelerfgoed.nl/def/cho-diff#

Dit vocabulaire bevat uitsluitend eigenschappen voor:
- aantallen per dag
- verschillen
- bijbehorende datums

Bronvocabularia worden niet hergebruikt voor diff-data.

---

## Afwijkingsdefinitie

- elke verandering is een afwijking
- een verschil van +1 of −1 is relevant
- een verschil van 0 is geen afwijking

Gevolgen:
- CSV bevat altijd alle resultaten
- mail toont alleen regels met verschil ongelijk aan nul

---

## CSV-uitvoer

Bij elke monitor-run wordt een CSV gegenereerd met:
- alle items
- aantallen voor vandaag en gisteren
- het berekende verschil

De CSV:
- bevat geen kleurcodering
- is bedoeld voor archivering en analyse
- wordt beschikbaar gesteld als workflow-artifact
- wordt als bijlage meegestuurd per e-mail

CSV’s zijn afgeleide rapportages en geen primaire bron.

---

## Mailgedrag

Er wordt elke dag een mail verstuurd:
- ook als alle verschillen 0 zijn
- ook bij fouten

Onderwerp:
DIFF CHO YYYY-MM-DD

De mail bevat:
- een korte samenvatting
- een tabel met alleen afwijkingen
- een CSV-bijlage met het volledige overzicht

Kleurgebruik wordt uitsluitend in de mail toegepast.

---

## Foutafhandeling

Het proces faalt deterministisch en zichtbaar.

Ontbrekende daggraphs:
- geen vergelijking
- geen resultaat-graph
- foutmelding per e-mail met expliciete datum

SPARQL-fouten:
- directe stop
- geen afgeleide output
- foutmelding per e-mail

Uploadfouten:
- geen gedeeltelijke resultaten
- foutmelding per e-mail

Er zijn geen automatische correcties of herstelacties.

---

## Repository-structuur

- .github/workflows/  
  GitHub Actions voor producer, monitor en weekmonitor
- queries/  
  SPARQL-queries voor productie en vergelijking
- scripts/  
  Vergelijkingslogica, CSV-generatie en graph-export
- docs/  
  Architectuur, CLI-norm en ontwerpkeuzes

---

## Ontwerpprincipes

- Producer is de enige writer van bron-graphs
- Index is state en wordt overschreven
- Monitors zijn read-only consumers
- Alle logica is expliciet
- Geen automatische correcties

---

## Onderhoud en overdracht

Deze architectuur is zelfstandig te begrijpen en overdraagbaar.

Alle afspraken zijn expliciet vastgelegd in:
- workflows
- scripts
- documentatie

Er is geen verborgen logica buiten deze repository.
