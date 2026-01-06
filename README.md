# DIV CHO dagelijkse vergelijking

## Doel
Deze repository bevat de workflow voor de dagelijkse vergelijking van CHO-gegevens in TriplyDB.

Elke dag worden twee daggraphs met elkaar vergeleken. De verschillen worden:
- vastgelegd als een nieuwe graph,
- gerapporteerd via e-mail,
- geleverd als CSV-bestand.

Het doel is vroegtijdige signalering van elke wijziging, hoe klein ook.

---

## Dagelijkse flow
De workflow verloopt elke dag volgens dezelfde stappen:

1. Een GitHub Action start automatisch.
2. De datum van vandaag en gisteren wordt bepaald.
3. Er wordt gecontroleerd of de graph van gisteren bestaat.
4. Als de graph ontbreekt:
   - wordt een foutmelding per mail verstuurd,
   - stopt de workflow.
5. Als de graph bestaat:
   - wordt een vergelijking uitgevoerd,
   - worden verschillen berekend,
   - wordt een CSV gegenereerd,
   - wordt een resultaat-graph aangemaakt,
   - wordt een mail verstuurd.

---

## Graph-conventies

### Input-graphs
Dagelijkse CHO-graphs hebben het volgende formaat:
https://linkeddata.cultureelerfgoed.nl/graph/cho-diff/YYYY-MM-DD


Elke graph bevat de stand van zaken voor één dag.

### Resultaat-graphs
Voor elke vergelijking wordt een nieuwe graph aangemaakt met het formaat:

https://linkeddata.cultureelerfgoed.nl/graph/cho-diff/YYYY-MM-DD_YYYY-MM-DD


De eerste datum is de bron (van).  
De tweede datum is het doel (tot).

Deze graph bevat uitsluitend de uitkomst van de vergelijking.

---

## Afwijkingsdefinitie
De volgende regels zijn van toepassing:

- Elke verandering is een afwijking.
- Een verschil van +1 is relevant.
- Een verschil van 0 is relevant.
- Er worden geen drempels gebruikt.

Gevolgen:
- De CSV bevat altijd alle resultaten.
- De mail toont alleen regels waar het verschil niet nul is.

---

## Mailgedrag
Er wordt elke dag een mail verstuurd.

Eigenschappen:
- Ook als alle verschillen 0 zijn.
- Ook bij fouten.
- Onderwerp:  
  `DIV CHO YYYY-MM-DD`
- Ontvanger:  
  `thesauri@cultureelerfgoed.nl`

De mail bevat:
- een korte samenvatting,
- een tabel met alleen afwijkingen,
- een CSV-bijlage met het volledige overzicht.

Kleurgebruik wordt alleen in de mail toegepast, niet in de CSV.

---

## Foutscenario’s
Als een benodigde graph ontbreekt (bijvoorbeeld die van gisteren):

- wordt geen vergelijking uitgevoerd,
- wordt geen resultaat-graph aangemaakt,
- wordt een mail verstuurd met een expliciete melding:
  - welke graph ontbreekt,
  - om welke datum het gaat.

Er zijn geen stille fouten.

---

## Repository-structuur

- `.github/workflows/`  
  GitHub Actions die de dagelijkse workflow uitvoeren.
- `queries/`  
  SPARQL-queries die data ophalen.
- `scripts/`  
  Scriptlaag voor vergelijking, rapportage en mail.
- `docs/`  
  Verdere documentatie over flow en graph-afspraken.
- `tools/`  
  Hulpmiddelen voor interactie met TriplyDB.

---

## Onderhoud en overdracht
De logica van de vergelijking is expliciet vastgelegd in scripts en documentatie.

Ontwerpkeuzes zijn beschreven in deze README en in de documentatie onder `docs/`.

Deze opzet is bedoeld om:
- onderhoud eenvoudig te maken,
- overdracht aan collega’s mogelijk te maken,
- het proces begrijpelijk te houden zonder voorkennis.