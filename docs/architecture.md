# Architectuur DIFF CHO dagelijkse vergelijking

Dit document beschrijft de architectuur en ontwerpkeuzes van de DIFF CHO
producer- en monitor-opzet.

Het doel is uitlegbaarheid, onderhoudbaarheid en overdraagbaarheid.

---

## Overzicht

## Datasets en verantwoordelijkheden

Binnen dit proces worden twee datasets onderscheiden:

- cho  
  Bevat uitsluitend de actuele brondata van CHO-objecten en wordt niet
  aangepast door dit proces.

- diff-cho  
  Bevat alle door dit proces geproduceerde graphs:
  - dagelijkse snapshots (daggraphs);
  - afgeleide vergelijking- en diff-graphs.

Alle vastlegging en historische reconstructie vindt plaats in diff-cho.


De oplossing bestaat uit twee gescheiden maar samenhangende processen:

1. Producer  
2. Monitor  

De scheiding is bewust aangebracht en structureel.

---

## Producer

### Verantwoordelijkheid
De producer is verantwoordelijk voor het dagelijks vastleggen van de
volledige stand van zaken van CHO-gegevens.

### Kenmerken
- draait dagelijks;
- gebruikt een vaste TriplyDB-query;
- produceert exact één graph per dag;
- overschrijft geen bestaande graphs.

### Output
Een daggraph met formaat:

https://linkeddata.cultureelerfgoed.nl/rce/diff-cho/graph/YYYY-MM-DD

Deze graph bevat de volledige stand van zaken voor **vandaag**.

---

## Monitor

### Verantwoordelijkheid
De monitor vergelijkt twee opeenvolgende daggraphs en legt de verschillen vast.

### Kenmerken
- draait dagelijks;
- vergelijkt **vandaag** met **gisteren**;
- rekent alle verschillen expliciet uit;
- gebruikt geen drempels.

### Output
De monitor produceert drie vormen van output:

1. Resultaat-graph (primair)
2. CSV-bestand (secundair)
3. E-mailrapportage (afgeleid)

---

## Resultaat-graph als primaire bron

De resultaat-graph is de **bron van waarheid**.

Eigenschappen:
- bevat uitsluitend afgeleide diff-data;
- is volledig reproduceerbaar;
- is onafhankelijk van CSV en mail;
- blijft permanent beschikbaar in TriplyDB.

Graph-formaat:

https://linkeddata.cultureelerfgoed.nl/rce/diff-cho/graph/YYYY-MM-DD_YYYY-MM-DD

De eerste datum is **vandaag**.  
De tweede datum is **gisteren**.

---

## CSV en mail

### CSV
- bevat altijd alle items;
- bevat ook nul-verschillen;
- wordt gebruikt voor analyse en archivering;
- wordt beschikbaar gesteld als workflow-artifact;
- wordt als bijlage gemaild.

CSV’s zijn afgeleide rapportages en geen primaire bron.

### Mail
- wordt elke dag verstuurd;
- ook bij fouten;
- ook als alle verschillen nul zijn;
- bevat een samenvatting en een tabel met afwijkingen.

De mail is een **rapportagekanaal**, geen gegevensbron.

---

## Ontwerpkeuzes

### Gescheiden producer en monitor
- eenvoudiger onderhoud;
- heldere verantwoordelijkheden;
- fouten zijn beter te isoleren.

### Expliciete named graphs
- geen impliciet gedrag;
- geen afhankelijkheid van CLI-interpretatie;
- consistent met bestaande TriplyDB-opzet.

### Geen hergebruik van bronvocabularia
- diff-data is geen domeindata;
- semantische vervuiling wordt voorkomen;
- interpretatie blijft zuiver.

---

## Wat bewust niet is gedaan

- geen drempelwaarden;
- geen aggregatie over meerdere dagen;
- geen dashboards;
- geen automatische correcties.

Het systeem signaleert, maar corrigeert niet.

---

## Overdracht

Deze architectuur is bedoeld om:
- zelfstandig begrepen te worden;
- eenvoudig aangepast te kunnen worden;
- robuust te blijven bij personele wisselingen.

Alle logica is expliciet vastgelegd in:
- workflows;
- scripts;
- documentatie.
