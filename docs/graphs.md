# Graph-afspraken

Dit document beschrijft de afspraken rondom de graphs die worden gebruikt en geproduceerd door de
DIV CHO producer- en monitor-workflows.

---

## Input-graphs (daggraphs)

Dagelijkse CHO-graphs hebben het volgende formaat:

https://linkeddata.cultureelerfgoed.nl/graph/cho-diff/YYYY-MM-DD

Kenmerken:
- één graph per kalenderdag;
- bevat de volledige stand van zaken voor die dag;
- wordt geproduceerd door de producer-workflow;
- dient als input voor de monitor-workflow.

---

## Resultaat-graphs (vergelijkingen)

Voor elke dagelijkse vergelijking wordt een aparte resultaat-graph aangemaakt met het formaat:

https://linkeddata.cultureelerfgoed.nl/graph/cho-diff/YYYY-MM-DD_YYYY-MM-DD

Waarbij:
- de eerste datum de **bron** is (van);
- de tweede datum het **referentiepunt** is (tot).

Kenmerken:
- één graph per vergelijking;
- wordt geproduceerd door de monitor-workflow;
- bevat uitsluitend afgeleide diff-informatie;
- wordt nooit overschreven.

---

## Inhoud van resultaat-graphs

Resultaat-graphs gebruiken een eigen vocabulaire:

https://linkeddata.cultureelerfgoed.nl/def/cho-diff#

Per item worden de volgende eigenschappen vastgelegd:

- diff:aantalGisteren  
  De waarde in de graph van gisteren.

- diff:aantalEergisteren  
  De waarde in de graph van eergisteren.

- diff:verschil  
  Het verschil tussen beide waarden.

- diff:datumGisteren  
  De datum van de bron-graph.

- diff:datumEergisteren  
  De datum van de referentie-graph.

---

## Semantische uitgangspunten

- Resultaat-graphs bevatten **geen brondata**.
- Bronvocabularia (zoals CEO) worden niet hergebruikt.
- Diff-data is expliciet gescheiden van CHO-inhoud.
- Elke graph is zelfstandig interpreteerbaar op basis van zijn URI.

---

## Gebruik

- Input-graphs worden alleen gelezen door de monitor.
- Resultaat-graphs zijn bedoeld voor:
  - kwaliteitsbewaking,
  - trendanalyse,
  - auditing en reconstructie.

De graph is de primaire bron van waarheid; CSV en mail zijn afgeleide rapportages.
