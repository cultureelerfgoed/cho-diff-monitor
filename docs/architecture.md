# Architectuur DIFF CHO dagelijkse vergelijking

Dit document beschrijft de architectuur en ontwerpkeuzes van de DIFF CHO
producer- en monitor-opzet.

Het doel is uitlegbaarheid, onderhoudbaarheid en overdraagbaarheid.

---

## Overzicht

### Datasets en verantwoordelijkheden

Binnen dit proces worden twee datasets onderscheiden:

- cho  
  Bevat uitsluitend de actuele brondata van CHO-objecten en wordt niet
  aangepast door dit proces.

- diff-cho  
  Bevat alle door dit proces geproduceerde graphs:
  - dagelijkse snapshots (daggraphs);
  - afgeleide vergelijking- en diff-graphs.

Alle vastlegging en historische reconstructie vindt plaats in diff-cho.

### Tijddefinitie en afronding van dagstanden
Binnen dit proces wordt gewerkt met kalenderdagen op basis van Nederlandse tijd (CET/CEST).
Een dagstand wordt als afgerond beschouwd nadat de brondata volledig is verwerkt en beschikbaar is gesteld in de LDV. In de praktijk is dit rond 04:00 uur ’s nachts.
De producer- en monitor-workflows draaien pas na dit moment, zodat uitsluitend volledige en stabiele dagstanden worden vastgelegd en vergeleken.
Cron-tijden in GitHub Actions zijn ingesteld in UTC en zodanig gekozen dat zij in zowel zomer- als wintertijd na afronding van de dagverwerking plaatsvinden.
De scripts bepalen de kalenderdag zelf in `Europe/Amsterdam`, onafhankelijk van de UTC-klok van de runner.
Producer en dagmonitor draaien als twee opeenvolgende jobs in één workflow: de monitor start pas als de producer klaar is.
Het systeem volgt expliciet kalenderdagen en niet dynamische “latest”-logica.

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
- valideert het queryresultaat vóór de upload (geldig, niet leeg, niet afgekapt);
- overschrijft geen bestaande graphs, tenzij een handmatige run expliciet
  *forceren* aanzet.

### Output
Een daggraph (snapshot) met formaat:

https://linkeddata.cultureelerfgoed.nl/rce/diff-cho/graph/YYYY-MM-DD

Deze graph bevat de volledige stand van zaken voor **vandaag**.

---

## Index

### Verantwoordelijkheid
De index-graph fungeert als actueel navigatiepunt binnen de dataset diff-cho.

De index:
- legt vast welke daggraph en welke diff-graph de meest recente zijn;
- bevat uitsluitend metadata (geen inhoudelijke CHO-data);
- wordt dagelijks volledig overschreven.

### Kenmerken
- precies één index-graph is actief;
- de index bevat geen historie;
- historie is volledig afleidbaar uit daggraphs en diff-graphs.

### Graph
https://linkeddata.cultureelerfgoed.nl/rce/diff-cho/graph/index

De index-graph wordt geschreven door de dagmonitor, direct nadat de
resultaat-graph is opgeslagen. Zo verwijst de index nooit naar een
resultaat-graph die (nog) niet bestaat. Bij een vergelijking van een eerdere
datum blijft de index ongewijzigd.

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

### Weekmonitor

Naast de dagelijkse monitor bestaat een weekmonitor.

Kenmerken:
- draait wekelijks (maandag);
- vergelijkt de laatste volledige kalenderweek (maandag t/m zondag), ook als
  hij op een andere dag handmatig wordt gestart;
- valideert expliciet of alle daggraphs aanwezig zijn;
- neemt ook items mee die pas halverwege de week verschijnen of verdwijnen;
- genereert uitsluitend CSV en e-mail.

De weekmonitor schrijft geen graphs naar TriplyDB.

---

## Resultaat-graph als primaire bron

De resultaat-graph is de bron van waarheid voor monitoring en rapportage, niet voor brondata.

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

## Foutafhandeling

Het proces is expliciet ingericht om fouten zichtbaar te maken en
deterministisch te falen. Er zijn geen stille fouten en geen impliciete
herstelacties.

### Ontbrekende daggraphs

Voorafgaand aan elke vergelijking controleert de monitor of de vereiste
daggraphs bestaan.

Als één of meerdere daggraphs ontbreken:

- wordt de vergelijking niet uitgevoerd;
- wordt geen resultaat-graph aangemaakt;
- wordt een foutmelding per e-mail verstuurd.

De foutmelding vermeldt expliciet welke datum(s) ontbreken.

Dit scenario duidt doorgaans op:
- een niet uitgevoerde producer-run;
- een mislukte upload van een daggraph.

### SPARQL-fouten

Als een SPARQL-query faalt (bijvoorbeeld door een endpoint-probleem of
ongeldige respons):

- stopt de verwerking onmiddellijk;
- worden geen afgeleide resultaten gegenereerd;
- wordt een foutmelding per e-mail verstuurd met de technische foutmelding.

Alleen tijdelijke netwerk- en serverfouten (HTTP 429/5xx, verbroken
verbinding) worden maximaal drie keer opnieuw geprobeerd, met oplopende
wachttijd. Dit is geen herstel van data. Inhoudelijke fouten worden nooit
herhaald.

### Uploadfouten

Als het opslaan van een resultaat-graph mislukt:

- stopt het proces;
- wordt geen gedeeltelijk resultaat achtergelaten;
- wordt een foutmelding per e-mail verstuurd.

Hierdoor blijft de dataset vrij van incomplete of inconsistente graphs.

### Rapportage bij fouten

Ook bij fouten wordt altijd een e-mail verstuurd.

De e-mail bevat:
- een duidelijke foutmelding;
- de context (datum of week waarop de fout betrekking heeft);
- geen gedeeltelijke resultaten.

CSV-bestanden worden bij fouten niet gegenereerd of meegestuurd.

### Geen automatische correcties

Het proces voert geen automatische correcties of herstelacties uit.

Fouten worden gesignaleerd en gerapporteerd, maar niet gemaskeerd of
automatisch opgelost. Analyse en eventuele correcties vinden buiten dit
proces plaats.

---

## Ontwerpkeuzes

### Gescheiden producer en monitor
- eenvoudiger onderhoud;
- heldere verantwoordelijkheden;
- fouten zijn beter te isoleren.

Beide zijn aparte jobs met elk hun eigen resultaat, maar in één workflow
gekoppeld. Zo is de volgorde gegarandeerd zonder op een tijdsmarge te
vertrouwen.

### Vergelijking in code, niet in SPARQL
De SPARQL-query (`queries/counts.rq`) haalt alleen tellingen per graph op. De
vergelijking gebeurt in Python (`chodiff/compare.py`). Daardoor tellen items
die in één van de graphs ontbreken altijd mee, en is de logica met unit tests
te controleren.

### Expliciete named graphs
- geen impliciet gedrag;
- geen afhankelijkheid van CLI-interpretatie;
- consistent met bestaande TriplyDB-opzet.

### Geen hergebruik van bronvocabularia
- diff-data is geen domeindata;
- semantische vervuiling wordt voorkomen;
- interpretatie blijft zuiver.

### Geen automatische correcties
Dit proces voert geen correcties of herstelacties uit op de data.
Het systeem signaleert verschillen en afwijkingen, maar past geen gegevens aan. Interpretatie, analyse en eventuele correcties vinden buiten dit proces plaats.

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
