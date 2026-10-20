# CHO Diff Monitor

CHO Diff Monitor signaleert veranderingen in tellingen van CHO-gegevens
van de Rijksdienst voor het Cultureel Erfgoed (RCE) in TriplyDB.

De producer bewaart dagelijkse meetstanden. De dagmonitor vergelijkt
vandaag met gisteren en maakt een RDF-resultaatgraph, een CSV-bestand
en een e-mailrapport. De weekmonitor levert een CSV en e-mailrapport
over de zeven voorafgaande dagen.

## Wat meet de monitor?

De monitor vergelijkt aantallen per gemeten item. De lokale
producerquery telt instanties per klasse en het gebruik van
eigenschappen.

Elk verschil ongelijk aan nul geldt als afwijking. Er zijn geen
drempelwaarden: ook een verschil van +1 of -1 telt mee.

Dit is geen volledige vergelijking van afzonderlijke RDF-triples.
Inhoudelijke wijzigingen waarbij de gemeten aantallen gelijk
blijven, blijven buiten beeld. Toevoegingen en verwijderingen
kunnen elkaar in de telling opheffen.

## Onderdelen

| Onderdeel | Functie | Uitvoer |
|---|---|---|
| Producer | Haalt tellingen op en bewaart een dagelijkse meetstand | Daggraph |
| Index | Legt verwijzingen naar beschikbare meetstanden en vergelijkingen vast | Indexgraph |
| Dagmonitor | Vergelijkt vandaag met gisteren | Resultaatgraph, CSV en e-mail |
| Weekmonitor | Vergelijkt de zeven voorafgaande dagen | CSV en e-mail |

## Datasets

| Dataset | Functie |
|---|---|
| `rce/cho` | Actuele CHO-brondata |
| `rce/diff-cho` | Dagelijkse meetstanden, resultaatgraphs en index |

De workflows schrijven hun uitvoer naar `rce/diff-cho`.
Ze wijzigen de brondata in `rce/cho` niet.

Platform: https://api.linkeddata.cultureelerfgoed.nl

## Dagelijkse verwerking

### Producer

De producer:

1. Haalt RDF op via de opgeslagen TriplyDB-query
   `rce/Query-11-4`, versie `2`.
2. Zet de uitvoer om naar TriG met een graph-URI voor de uitvoerdatum.
3. Importeert de daggraph in `rce/diff-cho`.
4. Bouwt en importeert de indexgraph.

Een daggraph bevat de opgehaalde tellingen. Het is geen volledige
kopie van de CHO-brondata.

De workflow voert de opgeslagen TriplyDB-query uit, niet rechtstreeks
het bestand `queries/query-producer.rq`. Controleer bij wijzigingen
of de opgeslagen query en het lokale bestand overeenkomen.

### Index

De indexgraph bevat metadata en verwijzingen naar meetstanden
en vergelijkingen. De producer bouwt deze index.

De index staat in:

`https://linkeddata.cultureelerfgoed.nl/rce/diff-cho/graph/index`

De producer importeert de index met `--mode overwrite`.
De index is daarmee een actuele navigatiehulp, geen historisch logboek.

### Dagmonitor

De dagmonitor:

1. Bepaalt de datums voor vandaag en gisteren.
2. Vraagt de vergelijking van beide daggraphs op via SPARQL.
3. Schrijft een CSV met alle teruggegeven resultaten.
4. Schrijft en uploadt een RDF-resultaatgraph.
5. Verstuurt een e-mailrapport.

De CSV en resultaatgraph bevatten de aantallen voor beide dagen
en het berekende verschil. De e-mail toont de afwijkingen en bevat
de volledige CSV als bijlage.

De dagmonitor wijzigt de daggraphs niet, maar schrijft wel
een afzonderlijke resultaatgraph.

## Weekmonitor

De weekmonitor gebruikt de zeven dagen voorafgaand aan de uitvoerdatum.

Bij de geplande uitvoering op maandag is dat de vorige maandag
tot en met zondag. Bij handmatig starten op een andere dag
verschuift de periode mee.

De weekmonitor:

1. Bepaalt de zeven datums.
2. Controleert of de bijbehorende daggraphs bestaan.
3. Haalt de tellingen op via SPARQL.
4. Berekent verschillen tussen opeenvolgende dagen.
5. Schrijft een CSV en verstuurt een e-mailrapport.

Het totaalverschil is het verschil tussen de laatste en eerste
dag van de periode. Het is geen telling van alle afzonderlijke
wijzigingen gedurende die week.

De weekmonitor schrijft geen RDF-resultaatgraph.

## Planning

De workflows gebruiken de volgende UTC-planning:

| Workflow | Planning UTC | Nederlandse wintertijd | Nederlandse zomertijd |
|---|---|---|---|
| Producer | Dagelijks 07:00 | 08:00 | 09:00 |
| Dagmonitor | Dagelijks 08:00 | 09:00 | 10:00 |
| Weekmonitor | Maandag 09:00 | 10:00 | 11:00 |

De planning gaat ervan uit dat de nachtelijke bronverwerking
vóór de producer is afgerond. Een later starttijdstip bewijst
op zichzelf niet dat de bronverwerking volledig is.

De workflows hebben afzonderlijke tijdschema's. De dagmonitor
wacht niet via een workflow-afhankelijkheid op de producer.

De scripts bepalen datums met de systeemdatum van de runner.
Ze stellen niet expliciet de tijdzone `Europe/Amsterdam` in.
Houd hier rekening mee bij handmatige uitvoeringen rond middernacht.

## Handmatig uitvoeren

1. Open de tab **Actions**.
2. Kies de gewenste workflow:
   - **CHO diff producer**
   - **CHO diff monitor**
   - **CHO diff week monitor**
3. Klik op **Run workflow**.
4. Controleer na afloop de stappen en uitvoer.

Voer de dagmonitor pas uit als de benodigde daggraphs beschikbaar zijn.
Controleer vóór het opnieuw uitvoeren van de producer of de daggraph
voor die datum al bestaat.

## Configuratie

Stel deze repositorysecrets in:

| Secret | Functie |
|---|---|
| `TRIPLYDB_TOKEN` | Authenticatie voor TriplyDB |
| `GMAIL_USERNAME` | Gmail-account voor rapportages |
| `GMAIL_APP_PASSWORD` | App-wachtwoord voor verzending via Gmail |

Je vindt deze instellingen onder:

**Settings > Secrets and variables > Actions > New repository secret**

Controleer de e-mailinstellingen en ontvangers in
`scripts/mail.py` en `scripts/mail_week.py`.

De workflows gebruiken Windows-runners en downloaden de TriplyDB CLI.
De dag- en weekmonitor gebruiken Python 3.11.
De workflows installeren de benodigde Python-pakketten zelf.

## Graph-URI's

| Graph | URI |
|---|---|
| Dagelijkse meetstand | `https://linkeddata.cultureelerfgoed.nl/rce/diff-cho/graph/YYYY-MM-DD` |
| Dagvergelijking | `https://linkeddata.cultureelerfgoed.nl/rce/diff-cho/graph/YYYY-MM-DD_YYYY-MM-DD` |
| Index | `https://linkeddata.cultureelerfgoed.nl/rce/diff-cho/graph/index` |

Bij een dagvergelijking staat de datum van vandaag vooraan
en die van gisteren achteraan.

Daggraphs en resultaatgraphs worden geïmporteerd zonder expliciete
`--mode overwrite`. Controleer het gedrag van de gebruikte CLI-versie
voordat je een bestaande dag opnieuw importeert.

## Resultaatvocabulaire

De dagmonitor gebruikt:

`https://linkeddata.cultureelerfgoed.nl/def/cho-diff#`

Per item legt de resultaatgraph vast:

| Eigenschap | Betekenis |
|---|---|
| `diff:aantalVandaag` | Aantal op de huidige dag |
| `diff:aantalGisteren` | Aantal op de vorige dag |
| `diff:verschil` | Huidig aantal minus vorig aantal |
| `diff:datumVandaag` | Datum van de huidige meetstand |
| `diff:datumGisteren` | Datum van de vorige meetstand |

## Rapportages

### Dagrapport

De dagelijkse CSV bevat:

- `item`
- `aantalVandaag`
- `aantalGisteren`
- `verschil`

Bestandsnaam:

`diff-cho-YYYY-MM-DD_YYYY-MM-DD.csv`

Na een succesvolle uitvoering biedt GitHub Actions de CSV aan
als workflow-artifact. De dagmonitor verstuurt ook een e-mail
wanneer er geen afwijkingen zijn.

### Weekrapport

De wekelijkse CSV bevat de zeven dagtellingen, zes verschillen
tussen opeenvolgende dagen en het totaalverschil.

Bestandsnaam:

`diff-cho-week-YYYY-MM-DD_YYYY-MM-DD.csv`

Na een succesvolle uitvoering biedt GitHub Actions de CSV aan
als workflow-artifact.

## Fouten en controle

Controleer bij een mislukte uitvoering eerst de logs in **Actions**.

Let daarbij op:

- beschikbaarheid van de benodigde daggraphs;
- bereikbaarheid van de TriplyDB-query en het SPARQL-endpoint;
- geldigheid en rechten van het TriplyDB-token;
- fouten bij RDF-import;
- Gmail-instellingen voor de rapportage.

De dagmonitor probeert bij fouten binnen de verwerkingsstappen
een foutmail te versturen en laat daarna de uitvoering mislukken.
Fouten vóór het starten van het script vallen daar niet onder.
Een probleem met de mailverbinding kan ook de foutmail verhinderen.

De weekmonitor stopt als een benodigde daggraph ontbreekt.
Het weekscript bevat geen algemene foutmailafhandeling.

Een mislukte uitvoering kan al bestanden of een resultaatgraph
hebben aangemaakt. Controleer de afgeronde stappen voordat je
opnieuw start. De code bevat geen terugdraaimechanisme.

## Repositorystructuur

| Pad | Inhoud |
|---|---|
| `.github/workflows/` | Producer, dagmonitor, weekmonitor en keep-alive |
| `queries/` | Lokale SPARQL-querybestanden |
| `scripts/` | Vergelijking, indexopbouw, RDF-export en e-mailrapportage |
| `docs/` | Architectuur, graphconventies, vocabulaire en aanvullende bestanden |
| `index-graph.yml` | Configuratie voor de indexgraph |
| `tools/` | Meegeleverde hulpmiddelen |

## Verdere documentatie

- [Architectuur](docs/architecture.md)
- [Verwerkingsstappen](docs/flow.md)
- [Graphconventies](docs/graphs.md)
- [Vocabulaire](docs/vocabulary.md)

## Onderhoud

Houd bij wijzigingen de workflows, scripts, opgeslagen TriplyDB-query
en documentatie met elkaar in overeenstemming.

Leg wijzigingen aan tellingen en queryversies vast. Een gewijzigde
telmethode kan verschillen veroorzaken die niet voortkomen uit
wijzigingen in de brondata.
