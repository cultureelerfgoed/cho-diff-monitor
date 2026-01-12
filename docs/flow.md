# Dagelijkse flow

De dagelijkse verwerking bestaat uit twee gescheiden, opeenvolgende processen:
- de producer,
- de monitor.

Samen zorgen zij voor dagelijkse vastlegging en vergelijking van CHO-gegevens.

---

## Producer-flow (daggraphs)

1. Een GitHub Action start automatisch.
2. De datum van **vandaag** wordt bepaald.
3. Een vaste TriplyDB-query wordt uitgevoerd.
4. Het resultaat wordt omgezet naar Trig.
5. De data wordt opgeslagen in een named graph met formaat:

   https://linkeddata.cultureelerfgoed.nl/graph/cho-diff/YYYY-MM-DD

Resultaat:
- één daggraph per datum.

De daggraph bevat de volledige stand van zaken voor **vandaag**.

---

## Monitor-flow (vergelijking)

1. Een GitHub Action start automatisch.
2. De datums **vandaag** en **gisteren** worden bepaald.
3. De bijbehorende daggraphs worden geïdentificeerd.
4. Er wordt gecontroleerd of beide daggraphs bestaan.
5. Een SPARQL-query vergelijkt de twee graphs.
6. Verschillen per item worden berekend.
7. Een CSV met alle resultaten wordt gegenereerd.
8. Een resultaat-graph wordt opgebouwd en opgeslagen met formaat:

   https://linkeddata.cultureelerfgoed.nl/graph/cho-diff/YYYY-MM-DD_YYYY-MM-DD

   De eerste datum is **vandaag**.  
   De tweede datum is **gisteren**.

9. Een e-mailrapportage wordt verstuurd.

---

## Uitvoer en prioriteit

- De **resultaat-graph** is de primaire output.
- De **CSV** is secundaire output.
- De **mail** is een rapportagevorm.

Alle outputs worden dagelijks geproduceerd, ook als er geen afwijkingen zijn.

---

## Foutafhandeling

Als een vereiste daggraph ontbreekt:

- wordt geen vergelijking uitgevoerd,
- wordt geen resultaat-graph aangemaakt,
- wordt een e-mail verstuurd met een expliciete foutmelding.

De melding vermeldt:
- welke graph ontbreekt,
- om welke datum het gaat.

Er zijn geen stille fouten.
