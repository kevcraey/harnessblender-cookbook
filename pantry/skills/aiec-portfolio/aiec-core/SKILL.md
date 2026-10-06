---
name: aiec-core
user-invocable: false
description: Contract en deterministische CLI voor AIEC-portfolio v2. Wordt gelezen door portfolio en aiec-maintainer.
---
# AIEC — uitvoercontract

`A` hieronder betekent: `uv run <absolute-pad-naar-deze-skill>/scripts/aiec.py`.
Los dat pad op vanuit deze skill; het werkt zowel in de bron als in de gegenereerde plugin. Vereist uv en
Python 3.12 (uv beheert de runtime). Alle globale vlaggen staan vóór het subcommando.

## Bronnen en bestanden

- `schema.yaml`: kenmerken, waarden, pijlers en Confluence-structuur.
- `catalog/process.yaml`: fasebenamingen, gates, procesbeslissingen (`decided`) en eventuele open keuzes.
- `catalog/rules/*.yaml`: controles over gelezen gegevens.
- `catalog/reports/*.yaml`: rapporten, bronnen, vragen en opbouw.
- `catalog/capabilities/*.yaml`: beschikbare handelingen.
- Config: `~/.config/aiec-v2/config.toml`. Los van oude v1-config, standaard **dry-run**.
- Uitvoeringslogs en back-ups: `~/.local/state/aiec-v2/`. Snapshots en voorstellen zijn werkbestanden,
  geen tweede portfoliodatabank. Bewaar ze lokaal; ze kunnen persoonsgegevens bevatten.

Gebruik een unieke werkmap, bijvoorbeeld met `mktemp -d`, en plaats alle werkbestanden daar. De CLI
weigert bestaande outputbestanden te overschrijven. Een concept in de werkmap is nog niet gepubliceerd.

## Lezen en voorbereiden

```sh
A check
A catalog --out catalog.json
A doctor
A config-init
A collect --out snapshot.json
A collect --hours --since 2026-07-01 --until 2026-09-30 --out snapshot-met-uren.json
A review --snapshot snapshot.json --out review.json
A review --snapshot snapshot.json --bewaar --out review.json
A signalen --snapshot snapshot.json --bundle <routine-run>/days --out signalen.json
A report captatie --snapshot snapshot.json --target AI-38 --period 2026-09 --out captatie.json
A report onderhoud --snapshot snapshot.json --target POR-123 --period 2026-11 --inputs onderhoudsantwoorden.json --out onderhoud.json
A report eindrapport --snapshot snapshot.json --target POR-123 --period 2026-11 --inputs eindantwoorden.json --out eindrapport.json
A report retrospectieve --snapshot snapshot.json --target POR-123 --period 2026-11 --inputs antwoorden.json --out retro.json
A report vooruitgang --snapshot snapshot.json --target POR-123 --period 2026-09 --inputs maandantwoorden.json --tracking meetgegevens.json --out maandrapport.json
A propose --request verzoek.json --out voorstel.json
A show --plan voorstel.json
```

`collect` leest live, tenzij `--fixture <sandbox.json>` is meegegeven. Snapshots bevatten een bronmoment en
bekende beperkingen. Geen live data beschikbaar? Meld dat; presenteer fixturedata nooit als echte data.
`report` maakt ook een `.md`-concept. Het vooruitgangsrapport krijgt daarnaast een zelfstandige `.html`-preview met grafieken. Lees voor de invoervorm de gekozen definitie in `catalog/reports/`;
het catalogusoverzicht toont niet alle sectiedetails. Antwoorden zijn een JSON-object per sectie-id:
`input` krijgt tekst, `choice` een waarde uit de keuzelijst, `input_table` een lijst rijobjecten met de
kolom-IDs als sleutels. Geen antwoorden verzinnen om een rapport compleet te laten lijken.

Voor het maandrapport: `vlag`, `wijzigingen` (2–5 niet-lege regels), `milestones` (rijen), `beslissing` en
`volgende`. Iedere milestonerij heeft `nr`, `milestone`, `status`, `actual_md`, `remaining_md`, `gezondheid`
en eventueel `notities`. Baseline (`baseline_md`) is de oorspronkelijke inschatting van de milestone (baselinegewicht of
goedgekeurd scopegewicht) en wijzigt nooit; een ingevulde waarde wordt genegeerd met een melding. Tot 2.4.11
heette dit veld `forecast_md`: oude projectbestanden laten het vallen, oude meetstanden worden bij het lezen hernoemd.
Actual + Remaining heet het verwachte totaal (`expected_md`) en stuurt de scopegrafiek niet. De meetstand
bevat ook `period_actual_md`: de groei van de cumulatieve Actual sinds de vorige stand (eerste rapport of
nieuwe milestone: volledige Actual; onbekend blijft onbekend; een correctie kan negatief zijn).

`status` is een waarde uit de lijst `voortgang`: `backlog`, `in-voorbereiding`, `lopend`, `uitgevoerd`,
`niet-uitgevoerd`. `vlag` en `gezondheid` komen uit `projectgezondheid`: `op-schema`,
`afwijking-geen-actie`, `afwijking-actie`. Wat nog niet gestart is, staat op schema; er is geen vlag voor
onbekend. In Confluence verschijnen ze als Handy Status-macro (globale sets Taakstatus 199 en
ProjectrapporteringIkvProgramma 154). De plugin publiceert de primitieve `handy-status-macro`; Handy zet die
bij het opslaan om naar `status-handy` met een eigen id, en de inhoudshash negeert dat verschil.
Uitgevoerd: Remaining=0. Niet Uitgevoerd: afgesloten zonder oplevering, Remaining=0, telt niet als
opgeleverde scope of lopend werk; het project is klaar als elke milestone Uitgevoerd of Niet Uitgevoerd is.
Backlog: de vaste oorspronkelijke planning als Remaining, tenzij dit nieuwe scope zonder oorspronkelijk
plan is; dan is een expliciete positieve schatting nodig. In Voorbereiding en Lopend vragen Remaining. Nul
resterend zonder afsluitstatus is een vraag, geen automatische afsluiting. Oude projectbestanden met vrije
statustekst en de vijf vroegere vlaggen worden bij het inlezen omgezet (`form_files.LEGACY_*`).

Actual onbekend blijft onbekend; een onvolledige som wordt niet als totale inzet gepresenteerd. Gezondheid
blijft het oordeel van de projectleider, nooit een berekening. Reken uren niet zonder afgesproken daglengte
om naar md en kopieer geen Jira-worklogs naar de invoertabel. Voorbeelden:
`scripts/examples/vooruitgang-antwoorden.json` en `scripts/examples/vooruitgang-meetgegevens.json`.

### Meetbasis, historiek en grafieken

`--tracking` leest een apart JSON-object. Bij `kind: report` staat hetzelfde object onder `tracking` in het
verzoek. De rapportdefinitie bepaalt via `tracking.fields` welke tabelkolommen de rekenmodule gebruikt.

- Eerste rapport: `baseline` met `budget_md`, `source`, `milestones` (`nr`, `milestone`, `planned_md`) en
  `plan` (`period`, `scope_md`, `effort_md`). Vraag de oorspronkelijke afspraken; leid ze niet af uit de
  huidige Baseline. De maandplanning is expliciet, geen automatisch uitgesmeerde lijn.
- Volgende rapporten: hergebruik de meetbasis uit de verzamelde rapporthistoriek. `tracking: {}` volstaat.
  Een opnieuw aangeleverde baseline moet exact dezelfde betekenis hebben. Geen herijking van de noemer.
- Extra scope: `scope_changes` met unieke `id`, `month`, `decision` (`by`, `date`, `source`) en `milestones`
  (`nr`, `milestone`, positief `weight_md`). Het gewicht is vast vanaf de goedkeuringsmaand; het
  oorspronkelijke plan van de toevoeging is nul. Zie `vooruitgang-scopebesluit.json` voor de vorm.
  Geen terugwerkende wijziging over vastgelegde maanden, hergebruik van nummers of scopeverwijdering.
- De vroege aanname volgens plan is automatisch: zolang niets is opgeleverd en er geen volledige
  Actual/Remaining-inschatting is, toont de grafiek de grijze aanname voor die rapportmaand. Nieuwe scope vraagt
  ook dan haar eigen Remaining. Een oud `assume_on_plan` in bestanden wordt genegeerd.
- Oude rapporten zonder meetstand: vraag `legacy_ack: {"pages":["pagina-id"],"reason":"afspraak nieuwe meetstart"}`.
  Dit reconstrueert geen verleden. Een dalende Actual vraagt `corrections: [{"nr":1,"reason":"toelichting"}]`;
  oude waarden blijven staan. Heropening van opgeleverde milestones en gewijzigde historische inhoud vragen review.

Elke gepubliceerde rapportpagina krijgt een gehashte technische meetstand, gekoppeld aan de vorige. Die staat
niet op de pagina maar in de git-repo `[meetstanden].path` (standaard
`2-Work/26-ai-expertisecentrum/aiec-meetstanden`, GitHub `kevcraey/aiec-meetstanden`): één bestand
`<rapport>/<project>/<maand>.json` met `page_id` en `record`. Publiceren voegt na pagina en bijlagen een
gejournaliseerde stap `meetstand.archive` toe (schrijven, commit, push; nooit overschrijven). `collect` leest
het archief in als `meetstanden`; de controlehash vergelijkt het record met de actuele paginatekst. De pagina
toont enkel de ingeklapte **Vooruitgangshistoriek**. Dit is een integriteitscontrole, geen persoonsauthenticatie. Een oud of gewijzigd rapport wordt niet herschreven.
Gebruik een verse `collect`: oude snapshots zonder rapporthistoriek zijn niet geschikt. Een lokaal concept
voegt geen maand toe aan de historiek. Maanden worden chronologisch toegevoegd; een oudere maand achteraf
invoegen of een vastgelegde maand corrigeren vraagt afzonderlijke review, niet een gewone maandupdate.

Grafieken: zwart **Plan**, blauw vol **Opgeleverd**, geel gestippeld **Opgeleverd incl. lopend**. Bij inzet:
blauw vol **Werkelijk besteed**. Elke grafiek heeft een eigen legende; grijs gestippeld is goedgekeurde scope, lichtblauw
±10 procentpunt rond het oorspronkelijke plan. Scope en inzet kunnen boven 100% uitkomen. Ontbrekende
maanden blijven gaten. ‘Klaar’ volgt de afsluitstatus (Uitgevoerd of Niet Uitgevoerd) van alle goedgekeurde milestones, nooit een schatting.
Opbouw van het vooruitgangsrapport: eigenschappenblok (`aiec-vooruitgang`) met de vlag, opgeleverde scope en
besteed budget; wijzigingen; beslissingen; scope en inzet (grafieken, maandplanning enkel als oranje lijnen,
een regel alleen bij backlogfactor ≠ 1); milestones; volgende periode; ingeklapte bijlagen met meetbasis en
scopebesluiten en met de vaste maandstanden. De preview gebruikt dezelfde Flux-stijl als het formulier.
Toon de HTML-preview en open daarin de bijlage met meetbasis en scopebesluiten, vóór het publicatievoorstel
wordt goedgekeurd.
De twee PNG-bijlagen worden afzonderlijk gejournaliseerd en uitsluitend aan de nieuwe rapportpagina toegevoegd.

## Zelfstandig formulier voor projectleiders

De projectleider gebruikt één los HTML-programma en een `.aiec.json`-projectbestand. Geen Claude Code,
Python, account of server nodig aan die kant. Het programma bevat live SVG-grafieken en getypeerde invoer.
Het formulier bewerkt cijfers, gezondheidsvlaggen, milestonenotities en de rapporttekst (`wijzigingen`,
`beslissing`, `volgende`; velden uit `contract().texts`). Lege tekst wordt geen importfout maar een vraag in het
normale rapportgesprek; aanwezige tekst wordt niet uit een ingelezen bestand verwijderd. Een nieuwe maand begint leeg.

```sh
A form build --out aiec-maandrapport.html
A form export --snapshot snapshot.json --target POR-123 --period 2026-10 --out POR-123_2026-10.aiec.json
A form export --snapshot snapshot.json --target POR-123 --period 2026-09 --tracking meetbasis.json --out POR-123_2026-09.aiec.json
A form import --snapshot verse-snapshot.json --file POR-123_2026-10.aiec.json --out rapportverzoek.json
A form import --snapshot verse-snapshot.json --file project.aiec.json --period 2026-09 --out septemberverzoek.json
A form open --snapshot verse-snapshot.json --target POR-123
A form import --snapshot verse-snapshot.json --target POR-123 --out rapportverzoek.json
A propose --request rapportverzoek.json --out voorstel.json
```

`form open` is de snelle weg voor wie zelf invult: het schrijft `<project>_<maand>.html` naar `[form].dir`
(standaard `~/Downloads`) met het project ingebakken en opent het in de browser. Zonder `--period` is de werkmaand
de maand na de laatste meetstand. Staat er in die map een bewaard `<project>_<maand>*.aiec.json` (de download
van **Werk bewaren**, ook met browsersuffix ` (1)`), dan hervat het de nieuwste daarvan; `--fresh` exporteert
opnieuw. `form import --target` zonder `--file` leest datzelfde bewaarde bestand. Het HTML-bestand wordt telkens
opnieuw gemaakt; het werk zit in de download.
Bij de eerste export zonder bestaande meetstand is `--tracking` met de bevestigde baseline nodig.
Bij volgende exports wordt de gepubliceerde historie meegenomen en een nieuwe onbevestigde werkmaand
klaargezet. Geef het gegenereerde HTML-bestand door, niet `form/index.html`: dat is ongebouwde broncode.
De vormgeving volgt Flux (huisstijl Departement Omgeving, zoals `maak-presentatie`): `form build` bakt
Flanders Art Sans uit `form/fonts/` in als data-URI. De grafiekkleuren in `form/style.css`, `form/app.js`
en `report_charts.py` zijn dezelfde Flux-tokens plus het gele accent `#c9a800` voor incl. lopend; pas ze samen aan.

`form import` schrijft alleen een gewoon rapportverzoek. De kern rekent opnieuw; browseruitkomsten of
lokale ‘gepubliceerd’-labels zijn geen autoriteit. Een oudere lokale maand
die nog niet gepubliceerd is moet eerst afzonderlijk worden ingediend. Afwijkende historische cijfers,
vlaggen of aanwezige teksten worden niet stilzwijgend overgenomen. Een stale bestand krijgt geen voorrang
op nieuwere officiële gegevens. Verzamel zo nodig opnieuw en exporteer een actueel projectbestand.

Laat de projectleider **Werk bewaren** gebruiken en de download controleren. Er is geen automatische
cloudopslag of gegarandeerde browserherstelkopie; het oorspronkelijke bestand wordt niet in-place gewijzigd.
De app bewaart ook onvolledige concepten, maar blokkeert een nieuwe maand bij open cijfercontroles.
Het veld `confirmed` blijft in het bestandsformaat voor compatibiliteit, maar wordt niet meer gecontroleerd. Een lokaal afgesloten maand is geen publicatie. Pas daarna volgt het normale akkoordpad.

Het bestandsformaat is versiegebonden. Onbekende velden, dubbele JSON-sleutels en beschadigde structuren
worden geweigerd, niet weggepoetst. Gebruik geen model om schemafouten te ‘repareren’ zonder bespreking.

### Formulier v2: gekoppelde Actual en maandplanning

Bestandsversie 2 bewaart `settings.auto_remaining` en `periods[].planning`. Versie 1 blijft inleesbaar;
upgrade op een kopie, behoud oorspronkelijke baseline en oude invoer, en verzin geen historische
bijgestelde plannen. Opgeslagen v2-bestanden vragen het bijgewerkte formulier.

Auto-calc staat standaard aan: een wijziging in Actual past Remaining tegengesteld aan vanuit de
ankerstand bij het begin van de bewerking. Geen negatieve Remaining, geen nul voor onbekende waarden
en geen automatische oplevering. De schakelaar kan uit en wordt in het projectbestand bewaard.

Bij een nieuw project wordt alleen **inzet per maand** ingevuld. Het programma rekent cumulatief en
leidt de oorspronkelijke scopeplanning af uit diezelfde verdeling. Bestaande baselines worden niet
opnieuw geïnterpreteerd.

De resterende planning is een lijst `[{"period":"2026-10","effort_md":10}]`, met maandbedragen na de
rapportmaand. Ze staat in het projectbestand onder `periods[].planning` en in een rapportverzoek onder
`tracking.planning`. Ze mag tussen rapportmaanden veranderen, maar een opgeslagen historische planning
mag niet achteraf worden aangepast. Bij een nieuwe maand worden alleen nog toekomstige planmaanden
meegenomen. De oranje lijn toont actuele geplande inzet; zwart blijft de oorspronkelijke vergelijking.
Een verschil tussen ingeplande toekomstige inzet en Remaining wordt getoond, niet automatisch over
milestones verdeeld of in een gezondheidsvlag omgezet.

`monthly_planning.cumulative` (en `forwardProjection` in het formulier) geeft per planmaand ook `open_md`
(Remaining min cumulatief geplande inzet, niet onder nul) en `scope_md`: de verwachte scope als geplande inzet
evenredig naar het openstaande werk van alle milestones gaat, dus estimated + (approved − estimated) ×
min(1, gepland/Remaining). Die lijn staat oranje gestippeld in de scopegrafiek: meer inzet haalt de
goedgekeurde scope eerder, te weinig inzet blijft eronder. Zonder volledige Remaining of inschatting geen lijn.
Beide oranje lijnen (inzet en verwachte scope) worden alleen getoond als ze minstens 0,05 procentpunt van de
zwarte planlijn afwijken of voorbij het oorspronkelijke plan lopen. Een maand zonder planning telt als 0 md:
vanaf de rapportmaand loopt de projectie vlak door tot het einde van de as, ook bij een lege planning. De x-as stopt bij de rapportmaand als alles
opgeleverd is, anders bij de eerste planmaand waarin de verwachte scope de goedgekeurde scope haalt; wordt die
niet gehaald, dan blijven oorspronkelijk plan en alle planmaanden zichtbaar.

`effort_ratio` in de meetstand = som verwacht / som Baseline over opgeleverde en lopende milestones (backlog
niet). `tracking.future_factor` kiest de factor voor backlog in de projectie: afwezig = 1, `"ratio"` = gemeten
ratio (onbekend → 1 met melding), of een positief getal. Alleen `projected_remaining`, `open_md`, de verwachte
scopelijn en het asbereik gebruiken de factor; Remaining en het verschil met de maandplanning niet. De keuze
gaat mee naar een nieuwe maand. Met factor ≠ 1 wordt de geprojecteerde Remaining op 0,1 md afgerond.

## Schrijven, uitsluitend na akkoord

```sh
A approve --plan voorstel.json --by Kenzo --evidence "expliciet akkoord in dit gesprek op voorstel-ID" --ack <volledige-sha256> --out akkoord.json
A apply --plan voorstel.json --approval akkoord.json
```

Een voorstel bindt exacte payloads, bronrevisies, code, catalogus, config en omgeving. Het verloopt na
24 uur. Wijzigt een bron tussendoor, verzamel en vraag opnieuw akkoord. `apply` maakt eerst een back-up en
logt elke schrijfactie. Een gestart voorstel wordt niet opnieuw uitgevoerd, ook niet na een timeout.

`dry-run` weigert live writes. `test` laat uitsluitend de testspace toe, nooit Jira. `production` laat
uitsluitend de geconfigureerde AI-space en AI/EAG-projecten toe. Er is geen delete-actie en geen mailverzending.
Wijzig de modus nooit als neveneffect van een opdracht. `--fixture` blijft altijd offline.

## Verzoekvormen

```json
{"kind":"details","key":"AI-38","values":{"afdeling":"Afdeling uit bevestigde bron"}}
```
```json
{"kind":"transition","key":"AI-38","to":"Analyse"}
```
```json
{"kind":"transition","key":"AI-38","to":"Afgesloten","categorie":"stopgezet"}
```
Afsluiten vraagt `categorie` (uitgevoerd, stopgezet of geannuleerd) en zet de bijhorende Jira-resolution
(`uitgevoerd`, `Stopgezet`, `geannuleerd`) op het transitiescherm. Een andere resolution op een afgesloten
initiatief meldt de regel `afsluiting-zonder-categorie`. Bij stopgezet of geannuleerd vraagt afsluiten geen
fasegebonden kenmerken (toepassingstype, batenclaim, rijpheid …), wel de stopreden.
```json
{"kind":"people","key":"AI-38","assignee":"<jira-gebruikersnaam>","verantwoordelijke":"<jira-gebruikersnaam>"}
```
Assignee is de werkverdeling (wie eraan werkt), Verantwoordelijke de inhoudelijk verantwoordelijke;
`trekker` kan ook. Gebruik de Jira-gebruikersnaam, niet de weergavenaam; onbekende of inactieve
gebruikers worden geweigerd.
```json
{"kind":"new-initiative","title":"Titel","description":"Probleem en gewenste uitkomst","soort":"afgebakend"}
```
Soort staat op de Confluence-pagina (bron) én in het Jira-veld Werkorganisatie: afgebakend → `Project`,
doorlopend → `Doorlopende werking`. `soort` bij aanmaak en een `details`-wijziging van soort zetten dat veld;
een `details` met de bestaande soort zet het enkel in Jira recht. De regel `werkorganisatie-afwijkend` meldt
een leeg of afwijkend veld.
```json
{"kind":"ad-hocvraag","vraag":"De vraag in één zin","context":"Wie vroeg het, wanneer, eventuele bron","verwant":["AI-21"]}
```
Een ad-hocvraag wordt een Task onder de epic `adhoc_epic` (standaard AI-95); geen pagina, geen EAG.
`verwant` (optioneel) somt eerdere ad-hocvragen of initiatieven op die over hetzelfde gaan; ze komen in de
beschrijving. Collect leest alle ad-hocvragen (open en afgesloten) in de dataset `adhoc` (met `open`, `age_days`).
```json
{"kind":"initiative-page","key":"AI-123","parent_id":"390605009","summary":"Bevestigde beschrijving","values":{"soort":"afgebakend","pijler":"P3"}}
```
```json
{"kind":"link","key":"AI-123","other":"EAG-456"}
```
```json
{"kind":"label","page_id":"12345","label":"captatierapport"}
```
```json
{"kind":"rapportering","key":"AI-123","frequentie":"jaar","vanaf":"2026"}
```
```json
{"kind":"uitzondering","key":"AI-123","regels":["geen-project","gate:opleveringsverslag"],"reden":"POR aangevraagd","door":"Kenzo"}
```
```json
{"kind":"report","report":"eindrapport","target":"POR-123","period":"2026-11","inputs":{"vlag":"afwijking-geen-actie","context":"…","resultaat":"…","rijpheid":"MVP","waarde":"…","wendingen":"…","productverantwoordelijke":"…","beslissingen":"nee","vervolgstappen":[{"stap":"…","verantwoordelijke":"…","datum":"2027-01-31"}]}}
```
```json
{"kind":"report","report":"onderhoud","target":"POR-123","period":"2026-11","inputs":{"uitval":[{"duur":"15m","impact":"1"},{"duur":"30m","impact":"1"},{"duur":"1u","impact":"2"},{"duur":"4u","impact":"3"},{"duur":"1d","impact":"4"},{"duur":"1w","impact":"5"}],"buiten_kantooruren":"nee","terugval":"…","as_is":[{"md":"0","bron":"green field"}],"runkost":[{"post":"hosting","omschrijving":"…","bedrag":"0"},{"post":"licenties","omschrijving":"Geen.","bedrag":"0"},{"post":"inference","omschrijving":"…","bedrag":"1800"},{"post":"overige","omschrijving":"Geen.","bedrag":"0"}],"modellen":[{"component":"…","model":"…","einde":"2027-11","aanpak":"…","referentiedataset":"ja"}],"kwaliteit":"…","afhankelijkheden":[{"afhankelijkheid":"…","einde":""}],"producten":[{"product":"PROD-12","waarvoor":"…"}],"incidenten":"…","afbouw":"…"}}
```
```json
{"kind":"report","report":"retrospectieve","target":"POR-123","period":"2026-11","inputs":{"goed":"…","anders":"…"}}
```
```json
{"kind":"report","report":"beslissing","target":"AI-38","period":"2026-09","slug":"ingebruikname","inputs":{"overgang":"Uitvoering","besluit":"…","bevoegde":"…","datum":"2026-09-25","bron":"…","gevolg":"…"}}
```
Elk artefact krijgt de titel `JJJJ-MM-DD - type - slug`, zonder `[AI-x]`. De datum is een invoer `datum` als
die bestaat, anders de laatste dag van de periode bij periodieke rapporten, en anders de dag van aanmaak;
pas hem zo nodig achteraf in Confluence aan, behalve bij vooruitgangsrapporten: hun meetstand bewaart de titel.
Projectrapporten (vooruitgang, onderhoudsplan, eindrapport, retrospectieve) dragen ook de projectkey, in hoofdletters:
`JJJJ-MM-DD - type - POR-123 - slug`. De agent stelt de slug voor; de gebruiker keurt hem goed met het voorstel.

Projectrapporten hangen onder een projectpagina `POR-123 - <Jira-summary>`, een map onder de initiatiefpagina.
Ontbreekt die, dan stopt het voorstel; maak ze eerst:
```json
{"kind":"project-page","key":"POR-123"}
```
**Intern project.** Een project zonder POR-taak is de uitzondering: het enige verschil met een standaardproject
is dat er geen POR-taak bestaat. Structuur en vereisten blijven identiek (projectpagina, vooruitgangsrapporten,
eindrapport, onderhoudsplan, gates). Een initiatief kan er meerdere hebben. Het vraagt een formele beslissing, typisch na de
verkenning, als beslissingspagina onder het initiatief; zonder die pagina weigert het voorstel:
```json
{"kind":"project-page","key":"AI-49","intern":true,"summary":"Natuur in je school","status":"InUitvoering","startdatum":"2026-08-01","beslissing":"<page_id beslissing>"}
```
De pagina heet `intern - <naam>`, rapporttitels `JJJJ-MM-DD - vooruitgang - intern - slug`; de slug onderscheidt
projecten. Technisch (archief, formulier, `--target`) heet het project `AI-49-intern-1`, per initiatief genummerd en
enkel bewaard in het verborgen deel van het eigenschappenblok `aiec-project`; het is geen Jira-key en komt in geen
titel. Type, Status, Startdatum en Beslissing (link naar de beslissingspagina) staan zichtbaar in hetzelfde blok. De status is een Portfoliotaak-status (`project_statussen` in het schema) en
wordt niet afgeleid: de projectleider houdt ze bij, net als in Jira. De startdatum (`JJJJ-MM-DD`) is verplicht;
maandelijkse vooruitgangsrapporten zijn verplicht vanaf die maand. Status en/of startdatum wijzigen:
```json
{"kind":"project-eigenschappen","key":"AI-49-intern-1","status":"Uitgevoerd","startdatum":"2026-08-01"}
```
De review meldt `intern-zonder-startdatum` (fout), `intern-zonder-beslissing` en `intern-boven-plafond` (Actual van het laatste vooruitgangsrapport
boven 10 md; het plafond staat in die regel). `uren-op-initiatief` telt enkel POR-projecten, want de uren van een
intern project staan op het initiatief; `--hours` volgt geen interne projecten.

Het eindrapport draagt het label `opleveringsverslag`. De gate naar Uitvoering vraagt een eindrapport per gelinkt
project. Bij precies één project geldt dat eindrapport ook als opleveringsverslag van het initiatief; bij meer
projecten is daarnaast een eigen opleveringsverslag onder de initiatiefpagina nodig.

Het eindrapport moet op zich te lezen zijn, ook door wie het project niet kent. Het komt na het laatste
vooruitgangsrapport en krijgt geen `--tracking`: kopcijfers, grafieken, milestonetabel (Baseline tegenover Actual),
scopebesluiten en Vooruitgangshistoriek komen uit de laatste meetstand; er komt geen nieuwe meetstand bij. Zonder
meetstand vraagt het rapport eerst dat vooruitgangsrapport. De grafieken tonen geen projectie. Stel **Context** voor
uit het captatie- en analyserapport en de Jira-omschrijving, en **Belangrijkste wendingen** uit het bronmateriaal dat
het lokale concept onder die sectie toont (wijzigingen en beslissingen per maandrapport); de projectleider bevestigt.
Waarde volgt de batenregel: alleen een bevestigde claim, geen verzonnen eurobedrag.

Een project sluit af in deze volgorde: laatste vooruitgangsrapport, onderhoudsplan, eindrapport, retrospectieve. Elk
rapport verwijst naar het vorige en vraagt het eerst als het ontbreekt.

Het onderhoudsplan hoort bij het project dat een product (PROD) oplevert of wijzigt; een project zonder product
heeft er geen nodig. De gate naar Uitvoering vraagt het per project (`project_only`), niet op initiatiefniveau.
Het product is het PROD dat aan het initiatief gekoppeld is; bij meer dan één geeft de invoer `product` het aan.
Er is per product één actief plan. Een nieuw plan zoekt het actieve plan van hetzelfde product, over initiatieven
heen, en zet het bij publicatie op `Vervangen` met een link naar het nieuwe (een `page.update` in hetzelfde voorstel).
De code rekent, niemand vult het zelf in:
- **Klasse** uit de uitvalmatrix (impact 1–5 van de VCDV-schaal per duur, niet dalend): `kritisch` bij impact 4
  binnen 1 uur; `belangrijk` bij impact 4 binnen 1 werkdag of 3 binnen 4 uur; anders `standaard`. Geen P-codes:
  die zijn al de pijlers. Ondersteuning buiten de kantooruren bij `standaard` geeft een opmerking.
- **Investering** = as-is + delta. As-is komt uit het vorige actieve plan (Investering, of As-is als dat plan van
  hetzelfde project is); zonder vorig plan vraagt het rapport `as_is` (0 bij green field, leeg = onbekend). Delta is
  de Actual van de laatste meetstand van dit project. Onbekend blijft `onvolledig`, nooit 0.
- **Onderhoud per jaar** = 10 md basiskost + 15% (kritisch), 12,5% (belangrijk) of 10% (standaard) van de
  investering (in de tabel Onderhoudskost apart op as-is en delta) + per model een upgrade van 5 md met
  referentiedataset of 10 md zonder. De rij voor de bestaande investering linkt naar het vorige plan, of toont
  zonder vorig plan de bron. Runkost staat apart in euro, met één rij per post (hosting, licentie, inference,
  overige) en een totaal. AI-specifieke rijen dragen een statuslabel `AI`. Er is geen sectie Compliance.
- **Modellen** (onderdeel, versie, einde ondersteuning, plan van aanpak, referentiedataset) en **Producten**
  (PROD-keys waarop het product steunt) zijn verplicht te beantwoorden; een lege lijst betekent geen. Zonder model
  verschijnt de sectie Modellen niet. Een productkey moet in Jira bestaan (de collector haalt alle PROD-tickets op)
  en is niet het product zelf. Afhankelijkheden noemen geen vanzelfsprekende platformen (hosting, build, dataplatform).

Het verborgen eigenschappenblok `aiec-onderhoud` is de interface voor een latere portfoliosom: vaste labels (Product,
Project, Status, Klasse, Ondersteuning buiten kantooruren, As-is (md), Delta (md), Investering (md), Onderhoud
(md/jaar), Runkost (€/jaar), Team, Onderhoudstaak, Geldig tot, Vervangt, Vervangen door), Status exact `Actief` of
`Vervangen`, getallen met decimale komma of `onvolledig`. Tel alleen `Actief`. Onderhoudsplannen zonder dat blok
(de oude, op initiatiefniveau) vervangt de plugin niet; het rapport noemt ze. Een link op het PROD-issue zet de
plugin niet.

In het eindrapport is **Technisch beheer** een link naar het onderhoudsplan van hetzelfde project.

De retrospectieve verwijst naar het eindrapport van hetzelfde project en vraagt alleen lessons learned (wat werkte,
wat moet anders). Zonder gepubliceerd eindrapport vraagt ze dat eerst.

Elke faseovergang heeft een beslissing; `process.yaml` legt per gate vast waar (`decision_in`):

| Overgang | Artefacten | Beslissing in |
|---|---|---|
| Captatie → Analyse | captatierapport, initiatierapport | sectie Beslissing van het initiatierapport |
| Analyse → Planning | analyserapport, verkenningsrapport | sectie Beslissing van het verkenningsrapport |
| → Implementatie, Uitvoering, Afbouw, Afgesloten | zie gate | aparte beslissing met `overgang`, of het verkenningsrapport met een ingevulde rij Overgang naar |

Initiatie- en verkenningsrapport volgen de twee delen van het EAG-sjabloon (DigiAg 336528064) en horen onder het
AI-initiatief; er wordt niets in DigiAg geschreven. Ze nemen ook de vorm van het sjabloon over (`layout: table`): per
groep (Administratieve info, Overweging, Beslissing) één tabel met de sjabloonvraag (`row`) links en het antwoord rechts,
in plaats van een kop per sectie. De tabel Beslissing is zelf het eigenschappenblok `aiec-beslissing` (Datum, Beslist
door, Wat beslist, plus de overige sjabloonvragen van dat blok), op zijn plaats en niet bovenaan. Het verkenningsrapport kan in dat blok ook Overgang naar, Bron en
Gevolg dragen: leidt de verkenning meteen tot bv. Implementatie (opname in de reguliere werking), dan is geen aparte
beslissing nodig. Captatie- en
analyserapport gebruiken dezelfde tabelvorm: captatie volgt het handsjabloon (Captatie, Aanbeveling), analyse heeft
Analyse, Compliance en Vervolg, waarbij Compliance zelf het eigenschappenblok `aiec-analyse` (DPIA, DPO) is. Elke definitie bewaart een vingerafdruk van de vragen in haar
deel; `collect` leest het sjabloon mee en de review meldt `sjabloon-uit-sync` zodra EAG het aanpast (met de nieuwe
vingerafdruk), of `sjabloon-niet-gelezen` als het sjabloon niet leesbaar was. Een transitie zonder beslissing krijgt een vraag, en de review
meldt elke gepasseerde overgang zonder beslissing (`beslissing-ontbreekt`; na vroegtijdig afsluiten enkel de
afsluitbeslissing). Voor de rapportgates telt de plugin de aanwezigheid van het rapport: een via de plugin gemaakt
rapport heeft een ingevulde beslissing, een handgemaakte pagina wordt niet inhoudelijk gecontroleerd. Een aparte
beslissing staat volledig in één eigenschappenblok (`aiec-beslissing`: Overgang naar, Wat beslist, Beslist door, Datum,
Bron, Gevolg); daaruit lezen de review en het Beslissingen-overzicht op de initiatiefpagina. Dat overzicht toont voor
elke beslissing dezelfde kolommen (Datum, Beslist door, Wat beslist) en neemt naast aparte beslissingen (`decisions`)
ook het initiatie- en verkenningsrapport op. Velden in een
eigenschappenblok worden niet nog eens als sectie herhaald, een beslissing krijgt geen Jira-macro (`jira: false`), en een rapport met een beslissingsdatum krijgt geen
aparte perioderegel. Oudere beslissingen zonder dat blok geven een info-melding.

De sectie Artefacten op initiatief- en projectpagina's is een content-by-label-macro: enkel pagina's met een gekend
artefactlabel (behalve `decisions`, die een eigen overzicht hebben) onder de pagina, ook onder projectpagina's.
Ongelabelde werkdocumenten onder een initiatief vallen buiten de stack en worden niet gemeld. De review
(`artefactlabel`) waarschuwt alleen bij meer dan één artefactlabel, of bij een ongelabelde pagina die op een
artefact lijkt: titel `JJJJ-MM-DD - …` of een artefactlabel in de titel. Rapporteer enkel wat ontbreekt.

Het analyserapport legt in zijn eigenschappen (`aiec-analyse`) het DPIA-oordeel (vereist / niet van toepassing) en
het DPO-oordeel (gecontacteerd / niet van toepassing) vast, met motivering onder Risico en compliance. `geen-dpia`
zwijgt bij "Niet van toepassing"; `geen-dpo-oordeel` meldt persoonsgegevens zonder DPO-oordeel.

Producten: de plugin maakt geen PROD-tickets aan, maar `geen-product` waarschuwt voor een afgebakend initiatief in
Run (Uitvoering) zonder gekoppeld PROD-ticket (via initiatief of POR-taak); soms hoort er geen product bij.
`geen-onderhoudstaak` waarschuwt per gekoppeld product zonder onderhouds-POR-taak: een POR met Bedrijfstoepassing
(customfield_20131) = het product en een billingkey waarvan het Tempo-account categorie `OND` (onderhoud) heeft.
Alleen die categorie beslist; `Investeringstype` en de status van taak of account tellen niet mee.
`product-zonder-applicatiefiche` en `product-zonder-team` waarschuwen per gekoppeld product zonder Applicatiefiche
(customfield_20118) of VerantwoordelijkTeam (customfield_12615).

Rapportering: een rapport over periode N is op tijd tot halverwege periode N+1 (maand: de 15de; kwartaal: de 15de
van de tweede maand; halfjaar: eind van de derde maand; jaar: 30 juni). De review vraagt telkens de laatste periode
waarvan die termijn verstreken is. Het vooruitgangsrapport is maandelijks per project. Het gebruiksrapport
(`gebruik`, periode `JJJJ-Qn`, `JJJJ-Hn` of `JJJJ`) volgt de rapporteringsfrequentie van het initiatief:
`kwartaal` (standaard), `halfjaar`, `jaar` of `niet`, met `vanaf` als eerste periode die telt. Die frequentie is
intern: ze staat niet in Confluence maar in het meetstandenarchief (`rapportering/<AI-key>/<tijdstip>.json`,
commit en push via het `rapportering`-voorstel); een wijziging is een nieuw bestand, het laatste telt. Een
gebruiksrapport telt voor de periode op zijn regel `Periode:`; alleen zonder die regel beslist de titeldatum.

Signalen (beslissing `ochtendsignalen`): `signalen` leest de bundel van de routine (`<dag>/<bron>.md`, enkel
graph, rocketchat, atlassian en vault) en geeft elke regel die een gekende key, een initiatief- of productnaam
(volledig, vóór de `:`, of een acroniem tussen haakjes, hoofdlettergevoelig) of een vraagterm bevat. Een
onbekende AI- of EAG-key staat apart (`onbekend`): mogelijk nieuwe vraag. Code zoekt, het model oordeelt. Het
geeft ook de reviewladder: dagen sinds de laatste bewaarde review, `niveau` info (0–2), vraag (3–4) of
verplicht (≥ 5 of nooit).

Reviewgeschiedenis (beslissing `reviewgeschiedenis`): `review --bewaar` schrijft de run naar
`review/<tijdstip>.json` in het meetstandenarchief (commit en push), zonder voorstel of akkoord: afgeleide
data, geen beslissing. Alleen voor een live snapshot zonder `--today`. `collect` leest de runs mee. Elke
bevinding krijgt een `id` (key|regel|melding; een bevinding onder uitzondering houdt het id van het origineel)
en `sinds`: de eerste run van de ononderbroken reeks bewaarde runs tot nu; verdwijnt ze en komt ze terug, dan
begint `sinds` opnieuw. Het reviewconcept toont bovenaan nieuw en opgelost tegenover de laatste bewaarde run.

Uitzondering (beslissing `uitzonderingen`): een afwijking van een catalogusregel of gatevoorwaarde
(`gate:<artefact>`) op een initiatief, project of product. Intern, zoals de rapporteringsfrequentie:
`uitzondering/<key>/<regel>/<tijdstip>.json` in het meetstandenarchief (commit en push via het
`uitzondering`-voorstel), nooit in Confluence, Jira of een rapport. Elke gebruiker legt ze vast met reden en
`door`; de uitvoering weigert als `door` niet gelijk is aan wie goedkeurt (`approve --by`); ook regels met ernst error. Ingebouwde controles (verplicht veld, waarde, structuur,
koppeling, brondekking, sjabloon) krijgen geen uitzondering. Herzien = hetzelfde voorstel opnieuw; intrekken =
`"ingetrokken": true`. Het laatste record per key en regel telt. Review: tot 30 dagen wordt de bevinding
info "onder uitzondering"; van 30 tot 90 dagen komt `uitzondering-herzien` (info) erbij; na 90 dagen keert de
bevinding terug met `uitzondering-te-herzien` (warning). Een uitzondering zonder bevinding geeft
`uitzondering-overbodig`. Een gate-uitzondering heeft geen eigen bevinding maar volgt hetzelfde ritme. Een gate aanvaardt een `gate:<artefact>` van ten hoogste 90 dagen; bij één project
telt de uitzondering van het project ook voor het initiatief. Stand en kwartaal tonen geen uitzonderingen.

Een beslissing komt onder `[AI-x] Beslissingen`, of onder `parent_id` als die is opgegeven. Ontbreekt de
Beslissingen-pagina, dan stopt het voorstel.

Voorbeelden zijn geen echte opdrachten of bevestigde classificaties. Laat IDs, ouderpagina en inhoud
bevestigen. Confluence Server negeert labels in de create-payload; nieuwe pagina’s krijgen hun label daarom direct na het aanmaken via een aparte label-call, binnen dezelfde actie.

## Grenzen

Geen modelgestuurde berekeningen, verborgen statusafleiding, automatisch parkeren of sluiten. Onbekende
procesregels blijven vragen. Afsluiten vraagt een afsluitcategorie en zet de ene bijhorende resolution;
ook gates die nog niet af zijn worden niet verzonnen. Jira ondersteunt hier geen atomische revisievoorwaarde:
de controle vlak voor schrijven verkleint concurrentierisico maar kan het niet volledig uitsluiten.
