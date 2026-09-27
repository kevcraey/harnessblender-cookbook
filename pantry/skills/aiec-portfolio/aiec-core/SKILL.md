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
- `catalog/process.yaml`: fasebenamingen, gates en open proceskeuzes.
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
A report captatie --snapshot snapshot.json --target AI-38 --period 2026-09 --out captatie.json
A report retrospectieve --snapshot snapshot.json --target POR-123 --period 2026-09 --inputs antwoorden.json --out retro.json
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
nieuwe milestone: volledige Actual; onbekend blijft onbekend; een correctie kan negatief zijn). Opgeleverd: Remaining=0. Backlog: de
vaste oorspronkelijke planning als Remaining, tenzij dit nieuwe scope zonder oorspronkelijk plan is;
dan is een expliciete positieve schatting nodig. Andere statussen vragen Remaining. Nul resterend zonder
opleverstatus is een vraag, geen automatische afsluiting.

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

Grafieken: zwart **Plan**, blauw vol **Opgeleverd**, blauw gestippeld **Opgeleverd incl. lopend**. Bij inzet:
blauw vol **Werkelijk besteed**. Elke grafiek heeft een eigen legende; blauwgroen is goedgekeurde scope, groen
±10 procentpunt rond het oorspronkelijke plan. Scope en inzet kunnen boven 100% uitkomen. Ontbrekende
maanden blijven gaten. ‘Klaar’ volgt de opleverstatus van alle goedgekeurde milestones, nooit een schatting.
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
A propose --request rapportverzoek.json --out voorstel.json
```

Bij de eerste export zonder bestaande meetstand is `--tracking` met de bevestigde baseline nodig.
Bij volgende exports wordt de gepubliceerde historie meegenomen en een nieuwe onbevestigde werkmaand
klaargezet. Geef het gegenereerde HTML-bestand door, niet `form/index.html`: dat is ongebouwde broncode.
De vormgeving volgt Flux (huisstijl Departement Omgeving, zoals `maak-presentatie`): `form build` bakt
Flanders Art Sans uit `form/fonts/` in als data-URI. De grafiekkleuren in `form/style.css`, `form/app.js`
en `report_charts.py` zijn dezelfde Flux-tokens; pas ze samen aan.

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
{"kind":"people","key":"AI-38","assignee":"<jira-gebruikersnaam>","verantwoordelijke":"<jira-gebruikersnaam>"}
```
Assignee is de werkverdeling (wie eraan werkt), Verantwoordelijke de inhoudelijk verantwoordelijke;
`trekker` kan ook. Gebruik de Jira-gebruikersnaam, niet de weergavenaam; onbekende of inactieve
gebruikers worden geweigerd.
```json
{"kind":"new-initiative","title":"Titel","description":"Probleem en gewenste uitkomst"}
```
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
{"kind":"report","report":"retrospectieve","target":"POR-123","period":"2026-09","inputs":{"doel":"…","goed":"…","anders":"…","waarde":"…","acties":"…"}}
```
```json
{"kind":"report","report":"beslissing","target":"AI-38","period":"2026-09","slug":"ingebruikname","inputs":{"overgang":"Uitvoering","besluit":"…","bevoegde":"…","datum":"2026-09-25","bron":"…","gevolg":"…"}}
```
Elk artefact krijgt de titel `JJJJ-MM-DD - type - slug`, zonder `[AI-x]`. De datum is een invoer `datum` als
die bestaat, anders de laatste dag van de periode bij maand- en kwartaalrapporten, en anders de dag van aanmaak;
pas hem zo nodig achteraf in Confluence aan, behalve bij vooruitgangsrapporten: hun meetstand bewaart de titel.
Projectrapporten (vooruitgang, eindrapport, retrospectieve) dragen ook de projectkey, in hoofdletters:
`JJJJ-MM-DD - type - POR-123 - slug`. De agent stelt de slug voor; de gebruiker keurt hem goed met het voorstel.

Projectrapporten hangen onder een projectpagina `POR-123 - <Jira-summary>`, een map onder de initiatiefpagina.
Ontbreekt die, dan stopt het voorstel; maak ze eerst:
```json
{"kind":"project-page","key":"POR-123"}
```
Het eindrapport draagt het label `opleveringsverslag`. De gate naar Uitvoering vraagt een eindrapport per gelinkt
project. Bij precies één project geldt dat eindrapport ook als opleveringsverslag van het initiatief; bij meer
projecten is daarnaast een eigen opleveringsverslag onder de initiatiefpagina nodig.

Elke faseovergang heeft een beslissing; `process.yaml` legt per gate vast waar (`decision_in`):

| Overgang | Artefacten | Beslissing in |
|---|---|---|
| Captatie → Analyse | captatierapport, initiatierapport | sectie Beslissing van het initiatierapport |
| Analyse → Planning | analyserapport, verkenningsrapport | sectie Beslissing van het verkenningsrapport |
| → Implementatie, Uitvoering, Afbouw, Afgesloten | zie gate | aparte beslissing met `overgang` |

Initiatie- en verkenningsrapport volgen de twee delen van het EAG-sjabloon (DigiAg 336528064) en horen onder het
AI-initiatief; er wordt niets in DigiAg geschreven. Elke definitie bewaart een vingerafdruk van de vragen in haar
deel; `collect` leest het sjabloon mee en de review meldt `sjabloon-uit-sync` zodra EAG het aanpast (met de nieuwe
vingerafdruk), of `sjabloon-niet-gelezen` als het sjabloon niet leesbaar was. Een transitie zonder beslissing krijgt een vraag, en de review
meldt elke gepasseerde overgang zonder beslissing (`beslissing-ontbreekt`; na vroegtijdig afsluiten enkel de
afsluitbeslissing). Voor de rapportgates telt de plugin de aanwezigheid van het rapport: een via de plugin gemaakt
rapport heeft een ingevulde beslissing, een handgemaakte pagina wordt niet inhoudelijk gecontroleerd. Een aparte
beslissing staat volledig in één eigenschappenblok (`aiec-beslissing`: Overgang naar, Besluit, Beslist door, Datum,
Bron, Gevolg); daaruit lezen de review en het Beslissingen-overzicht op de initiatiefpagina. Velden in een
eigenschappenblok worden niet nog eens als sectie herhaald, een beslissing krijgt geen Jira-macro (`jira: false`), en een rapport met een beslissingsdatum krijgt geen
aparte perioderegel. Oudere beslissingen zonder dat blok geven een info-melding.

De sectie Artefacten op initiatief- en projectpagina's is een content-by-label-macro: enkel pagina's met een gekend
artefactlabel (behalve `decisions`, die een eigen overzicht hebben) onder de pagina, ook onder projectpagina's.

Het analyserapport legt in zijn eigenschappen (`aiec-analyse`) het DPIA-oordeel (vereist / niet van toepassing) en
het DPO-oordeel (gecontacteerd / niet van toepassing) vast, met motivering onder Risico en compliance. `geen-dpia`
zwijgt bij "Niet van toepassing"; `geen-dpo-oordeel` meldt persoonsgegevens zonder DPO-oordeel.

Een beslissing komt onder `[AI-x] Beslissingen`, of onder `parent_id` als die is opgegeven. Ontbreekt de
Beslissingen-pagina, dan stopt het voorstel.

Voorbeelden zijn geen echte opdrachten of bevestigde classificaties. Laat IDs, ouderpagina en inhoud
bevestigen. Confluence Server negeert labels in de create-payload; nieuwe pagina’s krijgen hun label daarom direct na het aanmaken via een aparte label-call, binnen dezelfde actie.

## Grenzen

Geen modelgestuurde berekeningen, verborgen statusafleiding, automatisch parkeren of sluiten. Onbekende
procesregels blijven vragen. De huidige release blokkeert afsluiten zolang de resolution-mapping open is;
ook gates die nog niet af zijn worden niet verzonnen. Jira ondersteunt hier geen atomische revisievoorwaarde:
de controle vlak voor schrijven verkleint concurrentierisico maar kan het niet volledig uitsluiten.
