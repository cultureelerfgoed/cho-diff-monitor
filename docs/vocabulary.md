# Vocabulaire cho-diff

Dit document beschrijft het vocabulaire dat wordt gebruikt in
resultaat-graphs van de DIFF CHO monitor.

Dit vocabulaire is uitsluitend bedoeld voor **afgeleide diff-data**.

---

## Namespace

https://linkeddata.cultureelerfgoed.nl/def/cho-diff#

Prefix (conventie):
diff:

---

## Gebruik

Het vocabulaire wordt uitsluitend gebruikt in resultaat-graphs met formaat:

https://linkeddata.cultureelerfgoed.nl/rce/diff-cho/graph/YYYY-MM-DD_YYYY-MM-DD

Het vocabulaire wordt niet gebruikt in:
- daggraphs;
- brondata;
- CHO-inhoud.

---

## Klassen

Er worden geen expliciete klassen gedefinieerd.

Resultaat-graphs beschrijven verschillen **per bestaand item**.
Het item-IRI fungeert als subject.

---

## Eigenschappen

### diff:aantalVandaag
- betekenis: waarde in de graph van vandaag
- domein: bestaand CHO-item
- bereik: xsd:integer

---

### diff:aantalGisteren
- betekenis: waarde in de graph van gisteren
- domein: bestaand CHO-item
- bereik: xsd:integer

---

### diff:verschil
- betekenis: verschil tussen vandaag en gisteren
- domein: bestaand CHO-item
- bereik: xsd:integer

Positieve en negatieve waarden zijn toegestaan.

---

### diff:datumVandaag
- betekenis: datum van de graph van vandaag
- domein: bestaand CHO-item
- bereik: xsd:date

---

### diff:datumGisteren
- betekenis: datum van de graph van gisteren
- domein: bestaand CHO-item
- bereik: xsd:date

---

## Semantische uitgangspunten

- Diff-data is afgeleid en nooit brondata.
- Waarden worden niet geïnterpreteerd of genormaliseerd.
- Elke resultaat-graph is zelfstandig interpreteerbaar.
- Het vocabulaire is bewust klein gehouden.

---

## Relatie tot andere vocabularia

- CEO en andere domeinvocabularia worden niet hergebruikt.
- Er is geen formele koppeling tussen diff-termen en bron-termen.
- Interpretatie gebeurt op procesniveau, niet op vocabulaire-niveau.

---

## Stabiliteit

Dit vocabulaire is:
- stabiel;
- uitbreidbaar;
- bedoeld voor langdurig gebruik.

Nieuwe eigenschappen mogen alleen worden toegevoegd als:
- ze afgeleide informatie beschrijven;
- ze geen brondata dupliceren.
