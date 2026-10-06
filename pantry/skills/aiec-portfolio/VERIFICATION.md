# Verificatie AIEC-portfolio v2

Laatste controle: 2026-10-01. Deze controles zijn uitgevoerd door de bouwsessie, zonder live mutaties.

## Regelreview — release 2.4.65

Lokaal geïnstalleerd op 2026-10-06. **393 geslaagde tests** (3 nieuw); plugincache identiek aan de blend.
`regelreview` op live snapshot, Q4 lopend (1 bewaarde review): `geen-project` gemarkeerd als
uitzonderingsregel (placeholder-POR's), 15 catalogusregels `dood`. Niet bewaard; eerste echte regelreview
begin januari over Q4.

## Ochtendsignalen — release 2.4.64

Lokaal geïnstalleerd op 2026-10-06, met routine 0.2.4 (pane `portfolio`). **390 geslaagde tests** (2 nieuw);
kernbestanden byte-identiek aan de bron. `signalen` op echte bundels van 2 en 5 oktober (zonder Graph): 15
kandidaten, waaronder AI-44 (onbekende key) en GEZGRO-1 afgesloten (AI-7). Pane in de ochtendroutine nog niet
live gedraaid.

## Reviewgeschiedenis — release 2.4.63

Lokaal geïnstalleerd op 2026-10-05. **388 geslaagde tests** (5 nieuw); kernbestanden byte-identiek aan de bron.
`review --bewaar` bewaart de run in het meetstandenarchief zonder voorstel (beslist door Kenzo); elke bevinding
krijgt `sinds`, het concept toont nieuw en opgelost. Live nulpunt: `review/2026-10-05T121222.json`, 83 bevindingen
(28 error, 46 warning, 9 info), gepusht.

## Uitzonderingen — release 2.4.62

Lokaal geïnstalleerd op 2026-10-04. **383 geslaagde tests** (9 nieuw); kernbestanden byte-identiek aan de bron.
Uitzondering op een catalogusregel of `gate:<artefact>` als interne beheerdata in het meetstandenarchief
(beslist door Kenzo): herzieningsritme 30/90 dagen in de review, niet in Confluence, Jira of rapporten,
`door` = goedkeurder. Live review (alleen lezen) werkt met de nieuwe collector. Live wegschrijven nog niet beproefd.

## Soort vanaf Planning — release 2.4.61

Lokaal geïnstalleerd op 2026-10-01. **374 geslaagde tests**; kernbestanden byte-identiek aan de bron.
Soort is verplicht vanaf Planning (beslist door Kenzo): in Captatie en Analyse is de vorm van de oplossing
nog onbekend. Live review (alleen lezen): "Soort ontbreekt" enkel nog bij AI-8.

## Werkorganisatie — release 2.4.60

Lokaal geïnstalleerd op 2026-10-01. **373 geslaagde tests**; kernbestanden byte-identiek aan de bron.
Soort wordt gespiegeld naar Jira Werkorganisatie (customfield_14113: afgebakend → Project, doorlopend →
Doorlopende werking) bij `new-initiative` met `soort` en bij `details` met soort. Regel
`werkorganisatie-afwijkend` meldt een leeg of afwijkend veld. Live alleen gelezen: veld leeg op alle 15
initiatieven; de regel meldt de 6 met gekende soort (AI-3, 5, 6, 7, 47, 49). Schrijven niet live beproefd.

## Procesbeslissingen — release 2.4.59

Lokaal geïnstalleerd op 2026-10-01. **371 geslaagde tests**. Alle kern- en skillbestanden zijn byte-identiek
aan de bron. `open_decisions` is leeg; parkeren, statusafleiding, deadlines, meting-nota en de gate naar
Implementatie staan in `decided`. Fase "Wacht op analyse" en label `meting` zijn geschrapt. Fixture: de gate
naar Implementatie vraagt enkel een beslissing; het mechanisme voor een onvolledige gate blijft getest.

## Ad-hocvraag te lang open — release 2.4.57 (tekstcorrectie portfolio-skill in 2.4.58)

Lokaal geïnstalleerd op 2026-10-01. **370 geslaagde tests**, waarvan één nieuw. Alle kern- en skillbestanden
zijn byte-identiek aan de bron. `adhoc` staat in `SOURCES`; de regel `adhoc-te-lang-open` is via
`extend propose/approve/apply` toegevoegd (akkoord Kenzo in gesprek). Fixture: 31 dagen open meldt, 30 dagen
niet, afgesloten niet. Live: geen open ad-hocvragen op 2026-10-01, dus geen meldingen te verwachten.

## Terugkerende ad-hocvragen — release 2.4.56

Lokaal geïnstalleerd op 2026-10-01. **369 geslaagde tests**, waarvan één nieuw. Alle kern- en skillbestanden
zijn byte-identiek aan de bron.

Gecontroleerd: de fixture levert een `adhoc`-dataset met `open` en `age_days`; initiatieven blijven zonder
tasks; `verwant` weigert onbekende keys en komt in de beschrijving. Live gelezen: de JQL `"Epic Link" = AI-95`
geeft de 10 ad-hocvragen. Niet getest: een volledige live collect met deze dataset.

## Afsluitvelden — release 2.4.55

Lokaal geïnstalleerd op 2026-10-01. **368 geslaagde tests**, waarvan één nieuw. Alle 122 kern- en
skillbestanden zijn byte-identiek aan de bron.

Gecontroleerd: annuleren vanuit Captatie vraagt enkel de stopreden; daarna geen reviewfouten. Met resolution
`uitgevoerd` blijven fasegebonden kenmerken (zoals batenclaim) verplicht.

## Afsluitcategorieën — release 2.4.54

Lokaal geïnstalleerd op 2026-10-01. **367 geslaagde tests**, waarvan vier nieuw. Alle **122** geïnstalleerde
kern- en skillbestanden (zonder caches) zijn byte-identiek aan de bron.

Gecontroleerd:
- `resoluties` staat als beslist in `process.yaml`: één resolution per categorie (`uitgevoerd`, `Stopgezet`,
  `geannuleerd`).
- Afsluiten zonder `categorie` geeft een vraag; met categorie zet de transitie de juiste resolution; zonder
  resolution-veld op het transitiescherm geen actie.
- De regel `afsluiting-zonder-categorie` meldt `Fixed` en een lege resolution, niet `Stopgezet`/`geannuleerd`.
- Live gelezen: het Closed-scherm van initiatieven laat alle 33 resolutions toe, ook de drie gekozen.

Niet getest: een echte afsluiting via de plugin.

## Instroom en ad-hocvragen — release 2.4.53

Lokaal geïnstalleerd op 2026-10-01. De volledige testsuite telt **363 geslaagde tests**, waarvan twee nieuw
voor `ad-hocvraag`. Alle **126** geïnstalleerde kern- en skillbestanden zijn byte-identiek aan de bron; bron
en installatie hebben dezelfde catalogusfingerprint (`3ab6035c…`).

Gecontroleerd:
- `instroom` staat als beslist in `process.yaml` (2026-10-01, Kenzo), met promotiecriterium.
- `ad-hocvraag` maakt in de fixture een Task met Epic Link `adhoc_epic` (AI-95), status Backlog; een lege
  vraag of een vraag over meerdere regels wordt geweigerd.
- Dezelfde voorstel-, akkoord-, back-up- en journaalweg als `new-initiative`.

Niet getest: een echte Task-aanmaak via de Jira-REST-API van de plugin. De dubbelcontrole vergelijkt enkel met
Initiative-titels, niet met bestaande ad-hoc-tasks. Collect en review lezen ad-hoc-tasks niet; er is geen
signaal na 30 dagen.

## Zelfstandig invulprogramma — release 2.3.0

Lokaal geïnstalleerd op 2026-09-26. De volledige testsuite telt nu **237 geslaagde tests**. Alle **96**
geïnstalleerde kern- en skillbestanden zijn byte-identiek aan de bron; de dossieragent is afzonderlijk
vergeleken. Bron en installatie hebben dezelfde catalogusfingerprint. Het HTML-bestand uit de geïnstalleerde
CLI is byte-identiek aan de gevalideerde standalone app.

Gecontroleerd:
- Eén volledig lokaal HTML-programma: geen CDN, fetch, account of server nodig.
- Echte bestandsselectie, download, herimport en bewaren van ongeldige/onvolledige conceptinvoer.
- Live berekeningen, exacte decimale Baseline voor de geteste invoer en browser/Python-pariteit.
- Vorige waarden als referentie, expliciete rijcontrole, nieuwe maand en alleen-lezen historie.
- Projectwizard, formele scopetoevoeging en behoud van oorspronkelijke meetbasis.
- Onbekende/genest beschadigde velden en dubbele JSON-sleutels geweigerd; bestaande werkmap behouden.
- HTML in notities wordt als tekst behandeld. Geen netwerkrequests of JavaScript-fouten in de browserproef.
- Desktop en 390px mobiel: twee grafieken met eigen legende, geen pagina- of SVG-tekstoverflow.
- De daadwerkelijk gedownloade cijfers zijn geïmporteerd in Python: Actual 72.5 md, geschatte scope 72.5,
  formeel opgeleverd 60, en een compleet rapport. Geen browserberekening als gezaghebbend overgenomen.
- Officiële eerdere cijfers, vlaggen en aanwezige tekst worden vergeleken; lokale afsluiting is geen publicatie.
- Oude lokale maanden moeten eerst chronologisch worden ingediend; een stale bestand verdringt geen
  nieuwere officiële historie.
- Documenten gegenereerd/gecontroleerd, zip met app + fictief voorbeeld + leesmij gemaakt, plugin gevalideerd.

De eerste browserproef liep vast door een fout in de testvolgorde: wachten op de bestandsmelding vóór het
bestand werd aangeboden. De test is hersteld, begrensd met time-outs en volledig opnieuw uitgevoerd.

Bewijs in de vault: `.pi/aiec-verification/formulier/validation-y352d_re/`.
Back-up en releasebewijzen:
`/Users/kenzo/Library/CloudStorage/Dropbox/1-Kenzo/4-Coding/aiec-backups/formulier-20260926T142831/release-txd0ntdk`

Distributie: `99 - Attachments/aiec-maandrapport-startpakket.zip` en `aiec-maandrapport-invullen.html`.
**Geen live wijzigingen uitgevoerd.** Alleen Chrome is end-to-end beproefd; de beheerde browsers van
projectleiders en live publicatie vragen nog een afzonderlijke praktijkproef. De bestaande niet-blokkerende
pluginwaarschuwing over ontbrekende auteurmetadata blijft bestaan.

## Volledig vooruitgangsrapport — release 2.2.0

Lokaal geïnstalleerd op 2026-09-26. **186 tests geslaagd in 14,67 s**, zonder waarschuwingen. De **88**
geïnstalleerde kern- en skillbestanden zijn byte voor byte gelijk aan de bron; de catalogusfingerprints
zijn gelijk (`588ba6e62a80c17b84ea848a204b8bd0bfa909f9938259ff7c006729e39aeb79`).

Gecontroleerd:
- Vijf rapportsecties en dezelfde gezondheidsvlaggen; Remaining, vaste Baseline en Verwacht totaal = Actual + Remaining.
- Onbekend versus nul, tegenstrijdige handmatige waarden, stabiele milestone-identiteit en expliciete correcties.
- Onveranderlijke oorspronkelijke baseline, vaste gewichten voor extra scope en goedkeuringsmaanden.
- Gehashte maandstanden, onderbroken/gewijzigde historiek, oude rapporten zonder meetstand en bronrevisies.
- Geen invulling van ontbrekende maanden; expliciete vroege aannames; 100% en 120% scope; 124% inzet.
- Elke grafiek met eigen legende: zwart Plan, blauw vol Opgeleverd / Werkelijk besteed, blauw gestippeld
  Opgeleverd incl. lopend. Groen ±10 procentpunt. Desktop- en compacte mobiele PNG-weergave.
- Publicatie als één nieuwe pagina en twee afzonderlijk gejournalde bijlagen, uitsluitend naar de nieuwe
  pagina. Veilige bestandsnamen, exacte bijlagehashes, bestaande bijlagen, uploadfalen en gelijktijdige edits.
- Ongewijzigde escapingtest groen na het escapen van HTML-gevoelige tekens in technische JSON.
- CLI levert JSON, Markdown en zelfstandige HTML; bestaande uitvoerbestanden worden niet overschreven.
- Catalogus, documentgeneratie, offline demo, pluginbuild en Claude Code-pluginvalidatie geslaagd.
- Drie volledige fictieve rapporten in zes desktop-/mobiele weergaven gecontroleerd, zonder pagina-overflow
  of JavaScript-fouten. Screenshots bekeken; de laatste maandlabels overlappen niet.

Back-up (oorspronkelijke 338 bestanden met gecontroleerd hashmanifest):
`/Users/kenzo/Library/CloudStorage/Dropbox/1-Kenzo/4-Coding/aiec-backups/vooruitgang-20260926T083817`

Bewijs daarin: `verification-report-zese6ukj/` en `installation-report-yyiuco65/`. Het leesbare fictieve
voorbeeld staat in de vault als `99 - Attachments/aiec-vooruitgangsrapport-voorbeeld.html`.

**Geen live writes uitgevoerd.** De Confluence-upload is met mocks en fixtures getest, nog niet op de
werkelijke instance. Een echte publicatieproef vraagt een afzonderlijk voorstel en akkoord. De bestaande
niet-blokkerende waarschuwing over auteurmetadata van de gegenereerde plugin blijft buiten deze wijziging.

## Maandrapport — release 2.1.0

Geïnstalleerd op 2026-09-25. **139 tests geslaagd** in 2,88 s. Het maandrapport gebruikt vijf secties,
vijf gedeelde gezondheidsvlaggen en een getypeerde milestonetabel. Getest: alle vlaggen op beide niveaus,
onbekend versus nul, decimale mandagen, ongeldige/negatieve waarden, dubbele nummers, ontbrekende inhoud,
2–5 regels wijzigingen, veilige Markdown/XML-rendering en publicatie in de offline fixture na akkoord.
De projectgezondheid wordt niet afgeleid uit Baseline of Actual.

Cataloguscontrole, bestaande demo en gegenereerde documentatie zijn gecontroleerd. Pluginvalidatie slaagt
(met de bestaande niet-blokkerende auteurmetadatawaarschuwing). Geïnstalleerde kern en skills zijn byte voor
byte gelijk aan de bron. De HTML-rondleiding is op desktop en mobiel gecontroleerd; geen overflow.

De oude bron, plugin, recipe en documentatie zijn geback-upt onder:
`/Users/kenzo/Library/CloudStorage/Dropbox/1-Kenzo/4-Coding/aiec-backups/maandrapport-20260925T173858`

Logs en screenshots staan daar onder `verification/`. Het nieuwe invulsjabloon staat in de vault als
`02 - Areas/aiec-maandrapport.md`. Er zijn geen live rapporten aangemaakt of aangepast.

## Eerdere controles

- V1-baseline vóór wijzigingen: **150 tests geslaagd**.
- Eerste volledige v2-regressie: **98 tests geslaagd**.
- Uitgebreide v2-regressie: **107 tests geslaagd** (1,40 s). Onder meer verlopen voorstellen,
  gewijzigde code/config/omgeving, bronwijzigingen, onbekende kenmerken, XML-escaping en reviewperiodes.
- Cataloguscontrole: 11 rapporten, 11 declaratieve regels, 5 capabilities.
- Offline demo: review → voorstel → fixture-akkoord → uitvoering met back-up/log → retrospectieve die eerst het eindrapport vraagt → volledig maandrapport met twee grafieken.
- Gegenereerde documentatie: geen verschillen met actuele definities.
- Claude Code-pluginvalidatie: geslaagd. Enige waarschuwing: auteurmetadata ontbreekt in de door
  harnessblender gegenereerde manifestfile.
- HTML: desktop licht/donker en 390px mobiel; geen horizontale overflow, scenario-tabs functioneren.
  Ook zonder externe CDN-assets blijft de pagina bruikbaar. Screenshots zijn bekeken.
- Vault: de links en sectieverwijzingen van de nieuwe documentatie lossen op; geen dubbele HTML-IDs.
- Back-up: oorspronkelijke SHA-256-manifest volledig gecontroleerd.
- Live lezen: 25 Jira-initiatieven, 12 kandidaatpagina’s en 56 kinddocumenten gelezen.
- Live snapshotreview: 203 meldingen (81 error, 116 warning, 6 info). Geen wijzigingen uitgevoerd.

## Eerdere releasecontrole (2.0.2)

**v2.0.2 is lokaal geïnstalleerd en volledig gecontroleerd.**

- **108 tests geslaagd** in 1,44 s, inclusief de actuele schema-documentgenerator.
- Cataloguscontrole en offline demonstratie geslaagd.
- Gegenereerde documentatie wijkt niet af van de actuele definities.
- Plugin opnieuw gebouwd en door Claude Code gevalideerd.
- Lokale installatie bijgewerkt naar **2.0.2**; een nieuwe Claude Code-sessie is nodig.
- Bestanden van de geïnstalleerde kern zijn byte voor byte gelijk aan de bron.
- Laatste browsercontrole: vijf desktop-/mobiele weergaven zonder horizontale overflow; tabs werken.
- Screenshots en logs zijn bewaard onder `verification-final/`.

## Bewijsbestanden

Back-up en logs:
`/Users/kenzo/Library/CloudStorage/Dropbox/1-Kenzo/4-Coding/aiec-backups/20260925T154054`

- `manifest.json`: oorspronkelijke bestanden en hashes.
- `verification/`: uitgebreide test-, demo-, build-, plugin- en browserlogs.
- `verification-final/`: definitieve releasecontrole, met screenshots zodra afgerond.
- `vault-migration-plan.json`: vervangen documenten en herschreven links.
- `before-vault-links/`: byte-exacte versies vóór de linkmigratie.
- `complete-manifest.json`: aanvullend manifest van de back-upmap na de releasecontrole.

De live snapshot en review staan privé in de vault onder `.pi/aiec-verification/`. Zet die niet in een
publieke repository of gedeelde HTML-pagina.

## Niet geverifieerd of bewust niet geleverd

- Live Confluence- en Jira-writes; deze vragen afzonderlijk goedgekeurde praktijkproeven.
- Volledige POR/PROD-dekking: de huidige expliciete Jira-links leverden geen gekoppelde tickets op.
  Billingkey-only relaties vragen nog implementatie en bevestiging.
- Volledige financiële kwartaalrapportage, mailverzending, cronjobs, gedeelde reviewtakenlijst en Pi-package.
- Open procesbeslissingen zoals parkeren en wachtgates.

Een fixture-akkoord is geen toestemming voor een echte mutatie. Testresultaten bewijzen het geteste
gedrag, niet dat bestaande dossiers inhoudelijk of juridisch in orde zijn.
