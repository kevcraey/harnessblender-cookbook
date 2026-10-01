# AIEC-portfolio v2

Code-first portfoliobeheer voor Claude Code: één ingang, uitbreidbare definities en altijd een
concreet voorstel vóór een wijziging. Praktische documentatie begint bij de vault-note `aiec-portfolio`.
De HTML-rondleiding staat in `99 - Attachments/aiec-portfolio-uitleg.html` in de vault.

## Indeling

```text
portfolio/                 aanspreekpunt en werkwijze
agents/aiec-dossier.md      optionele read-only dossierlezer
aiec-maintainer/           gecontroleerd uitbreiden
aiec-core/
  schema.yaml              kenmerken, enums en pijlers
  catalog/process.yaml     gates, procesbeslissingen en eventuele open keuzes
  catalog/rules/           declaratieve controles
  catalog/reports/         bronnen, vragen en rapportopbouw
  catalog/capabilities/    beschikbare handelingen
  scripts/aiec.py          enige operationele CLI
  scripts/aiec_v2/         nieuwe kern
  scripts/aiec_lib/        behouden en geteste transport/XML-hulpfuncties
  scripts/tests/          adapterregressie en offline end-to-end tests
  scripts/examples/       synthetische sandbox en verzoeken
```

De v1-CLI, oude gedrags-skills en oude regel/rapport/voorstelmotor zijn vervangen. De oorspronkelijke
bestanden zijn veiliggesteld buiten de actieve bron. Enkele lage-niveaubibliotheken zijn hergebruikt;
roep hun schrijffuncties niet rechtstreeks aan. De plugin loopt uitsluitend via de v2-CLI.

## Proberen zonder netwerk

Vereist `uv`; Python 3.12, PyYAML en Pillow worden via de scriptmetadata opgelost. Pillow tekent de PNG-grafieken met een ingebouwd lettertype; er is geen browser of externe fontdienst nodig.

```sh
uv run aiec-core/scripts/aiec.py check
cp aiec-core/scripts/examples/sandbox.json /tmp/aiec-sandbox.json
uv run aiec-core/scripts/aiec.py --fixture /tmp/aiec-sandbox.json collect --out /tmp/aiec-snapshot.json
uv run aiec-core/scripts/aiec.py review --snapshot /tmp/aiec-snapshot.json --out /tmp/aiec-review.json
uv run aiec-core/scripts/aiec.py --fixture /tmp/aiec-sandbox.json propose --request aiec-core/scripts/examples/update.json --out /tmp/aiec-plan.json
uv run aiec-core/scripts/aiec.py show --plan /tmp/aiec-plan.json
```

Outputbestanden mogen nog niet bestaan. Gebruik een nieuwe werkmap bij herhaling. Alleen de kopie van de
synthetische sandbox wordt eventueel gewijzigd. De fixture heeft geen netwerk- of credentialtoegang.

Na het daadwerkelijk beoordelen van het voorstel:

```sh
uv run aiec-core/scripts/aiec.py --fixture /tmp/aiec-sandbox.json approve --plan /tmp/aiec-plan.json --by Kenzo --evidence "akkoord op deze fixtureproef" --ack <sha256-uit-voorstel> --out /tmp/aiec-akkoord.json
uv run aiec-core/scripts/aiec.py --fixture /tmp/aiec-sandbox.json apply --plan /tmp/aiec-plan.json --approval /tmp/aiec-akkoord.json
```

## Volledig vooruitgangsrapport

Het maandrapport houdt zijn vijf onderdelen. Bij de milestones komen Remaining en twee grafieken met
een eigen legende: zwart Plan, blauw vol Opgeleverd, blauw gestippeld Opgeleverd incl. lopend. Bij inzet
betekent de volle blauwe lijn Werkelijk besteed. De groene band is ±10 procentpunt, niet ±10% relatief.

```sh
uv run aiec-core/scripts/aiec.py report vooruitgang --snapshot /tmp/aiec-snapshot.json --target POR-1 --period 2026-09 --inputs aiec-core/scripts/examples/vooruitgang-antwoorden.json --tracking aiec-core/scripts/examples/vooruitgang-meetgegevens.json --out /tmp/aiec-maandrapport.json
```

Dit levert JSON, Markdown en een zelfstandige HTML-preview. De invoerbestanden zijn volledig fictief.
Een publicatieverzoek gebruikt dezelfde objecten onder `inputs` en `tracking`; ook daarvoor blijven
`propose → approve → apply` verplicht.

- Baseline is de oorspronkelijke inschatting per milestone en wijzigt nooit; Actual + Remaining is het verwachte totaal.
- Originele scopegewichten, budget en maandplanning worden één keer goedgekeurd en blijven vast.
- Extra scope krijgt een formele goedkeuringsmaand en een vast gewicht. Nieuwe scope met oorspronkelijk
  plan nul vraagt een expliciete Remaining. Scope en inzet kunnen boven 100% uitkomen.
- Opgeleverd en inclusief lopend werk zijn verschillende lijnen. Klaar betekent dat alle goedgekeurde
  milestones daadwerkelijk zijn opgeleverd. Een vlag wordt nooit uit inspanning afgeleid.
- Ontbrekende rapportmaanden blijven gaten; onbekende inzet is geen nul. Een vroege planaanname moet
  expliciet worden gekozen en blijft grijs en als aanname benoemd.
- Gepubliceerde rapporten dragen hun eigen gehashte meetstand en verwijzing naar de vorige. De collector
  leest die historiek terug. Nieuwe concepten veranderen niets aan bestaande maanden.
- De nieuwe pagina en beide PNG-bijlagen zijn afzonderlijk gejournalde acties. Bij een gedeeltelijke
  publicatie stopt de uitvoering; geen automatische herhaling of overschrijven van oude bijlagen.

Details en de JSON-contracten staan in `aiec-core/SKILL.md`. Oude rapporten zonder meetstand vragen een
expliciete meetstart; gewijzigde historische inhoud vraagt review. De actuele implementatie ondersteunt
scope-toevoegingen, niet het verwijderen of heropenen van goedgekeurde scope via een gewone maandstand.

## Zelfstandig invulprogramma

Projectleiders kunnen de cijfers invullen zonder Claude Code of Python. Eén gegenereerd HTML-bestand
bevat de invoer, berekeningen en SVG-grafieken; een versiegebonden `.aiec.json`-bestand bevat het project.
Geen CDN, server, account of automatische netwerkcalls. Een nieuwe maand kopieert de vorige cijfers als
onbevestigd voorstel; eerdere maanden blijven alleen-lezen. Bewaren kan ook met onvolledige concepten.

```sh
uv run aiec-core/scripts/aiec.py form build --out /tmp/aiec-maandrapport.html
uv run aiec-core/scripts/aiec.py form export --snapshot /tmp/aiec-snapshot.json --target POR-1 --period 2026-09 --tracking aiec-core/scripts/examples/vooruitgang-meetgegevens.json --out /tmp/POR-1_2026-09.aiec.json
uv run aiec-core/scripts/aiec.py form import --snapshot /tmp/aiec-snapshot.json --file /tmp/POR-1_2026-09.aiec.json --out /tmp/rapportverzoek.json
```

De voorbeelden zijn fictief. De bronbestanden in `aiec-core/form/` zijn geen distributie: gebruik `form build`.
Import maakt alleen een verzoek, geen publicatie. De Python-kern rekent opnieuw, vergelijkt met de officiële
historie en weigert conflicterende oudere cijfers of tekst. Niet-gepubliceerde eerdere lokale maanden
moeten eerst worden verwerkt (`form import --period`). Daarna blijft `propose → approve → apply` gelden.

V1 bewerkt cijfers, vlaggen en milestonenotities; de overige rapporttekst wordt nog met de assistent
verzorgd. De HTML-app verstuurt niets automatisch. Een download is de primaire bewaring, geen browsercache.
De projectleider moet controleren dat het bestand daadwerkelijk is opgeslagen.

## Claude Code-plugin bouwen

De bestaande cookbook-marketplace verwijst naar `recipes/aiec-portfolio/blend`.
Vanuit de cookbook-map:

```sh
../harnessblender/harnessblender blend aiec-portfolio
claude plugin validate recipes/aiec-portfolio/blend
```

Maak vóór rebuild een back-up van een bestaande blend. De recipe selecteert `portfolio`, `aiec-core`,
`aiec-maintainer` en de dossieragent. Bronwijzigingen horen in `pantry`, nooit in de blend of plugincache.
Daarna de geïnstalleerde plugin bijwerken en Claude Code herstarten. Start met
`/aiec-portfolio:portfolio bereid een review voor`.

## Live gebruiken

`config-init` maakt `~/.config/aiec-v2/config.toml`, standaard `dry-run`. Bestaande v1-config wordt niet
stilzwijgend hergebruikt. Tokens via `CONFLUENCE_PERSONAL_TOKEN` / `JIRA_PERSONAL_TOKEN` of bestaande
macOS-keychain-items. Tokens worden niet weergegeven. Geen automatische retries van schrijfacties.

`collect` leest de AI-space en expliciet gekoppelde Jira-tickets. `--hours --since D --until D` leest
gepagineerde worklogs. Een netwerkmislukking is geen lege dataset. Onvolledige brondekking wordt vermeld.
Live writes zijn nog niet op de echte instance getest; begin met een afzonderlijk goedgekeurde proef
in de testspace. Jira-writes zijn in testmodus uitgeschakeld.

## Uitbreiden

Regels, rapporten en bestaande capability-combinaties kunnen via `scaffold` en `extend propose/approve/apply`
worden toegevoegd. Catalogusvalidatie gebeurt vóór activering; wijzigingen worden geback-upt. Nieuwe
adapters of uitvoerhandelingen vragen gewone codewijzigingen, tests en expliciete review.

## Veiligheidsmodel

- Exacte payloads en bronrevisies worden opgenomen in het voorstel; code, catalogus, config en omgeving
  zijn aan de hash gebonden. Geldigheid: 24 uur.
- Goedkeuring is een apart bestand met voorstelhash en verwijzing naar menselijk akkoord. Dit is geen
  cryptografische persoonsauthenticatie: een lokale gebruiker met schrijftoegang kan bestanden vervalsen.
- Uitvoering doet preflight, back-up, exclusieve lokale lock en een append-only journaal per actie.
- Een gestart voorstel wordt nooit blind herhaald, ook niet na een timeout. Er is geen gedistribueerde
  transactie; herstel vraagt inspectie en een nieuw voorstel.
- Confluence-updates gebruiken een versie. Jira heeft geen atomische if-match voor deze transities;
  een re-read vlak vóór schrijven verkleint maar elimineert de race niet.
- Onbekende kenmerken, menselijke proza en niet-gewijzigde cellen worden behouden. Dubbele blokken of
  dubbele bekende rijen worden geweigerd in plaats van weggepoetst.
- Geen delete, mailverzending of automatische prioriteitsbump.

## Testen

Voor browsermodel-pariteit is ook Node.js nodig. Dat is een testafhankelijkheid, geen vereiste voor de
projectleider of de Python-CLI. De echte browserbediening is aanvullend met headless Chrome getest.

```sh
uv run --python 3.12 --with pytest --with pyyaml --with 'pillow>=11,<13' python -m pytest aiec-core/scripts/tests -q -p no:cacheprovider
```

V1-baseline vóór wijzigingen: 150 tests geslaagd. V2 heeft eigen regressies; zie `VERIFICATION.md` voor de
laatste run. Fixturetests zijn geen bewijs van live-integratie.
