# AIEC-portfolio — ontwerp

Mix-plugin voor het intakeproces en de portfolio-rapportage van het AI Expertisecentrum (AIEC).
Confluence-space `AI` is de bron voor eigenschappen van initiatieven; Jira levert status, uren en
kost live. Dit document is het contract tussen ontwerp (Fable), implementatie (Opus-panes) en
review. De vastgelegde beslissingen uit de grilling-sessie (handoff 2026-09-15) worden hier niet
heronderhandeld, enkel vertaald naar structuur.

Bronmap: `ai-toolkit-private/skills/project-management/aiec-portfolio/`. Variant:
`custom-plugins/aiec-portfolio/`. Nooit in de variant bewerken (zie `/mix-plugin`).

## 1. Skills

| skill | rol | invocable |
|---|---|---|
| `aiec-core` | contract: `schema.yaml` (het ene model), `scripts/aiec.py` (alle deterministische werk), regels | nee |
| `aiec-initiatief` | één initiatief aanmaken of bijwerken; `retrofit` = dezelfde motor over alle initiatieven | ja |
| `aiec-groom` | manuele regelcheck over space + Jira; kwartaalreview (frigo-beslissingen) | ja |
| `aiec-rapport` | `stand` (wekelijkse/tweewekelijkse mail Kris + Tom) en `kwartaal` (toelichting Tom, Jan, Kris) | ja |

Meegemixt in de variant: agent `ai-track-intake-analyzer` (intakegesprek), skills `write-like-kenzo`
en `humanizer` (proza van `aiec-rapport`).

Lagen, zoals in de routine-plugin:

```
collect (script)  →  judge (LLM)  →  propose (bestand dat Kenzo bewerkt)  →  apply (script, guard)
```

Scripts beslissen niets; de LLM schrijft nooit rechtstreeks naar Confluence of Jira. Eén
uitzondering: `aiec-rapport kwartaal` publiceert de goedgekeurde markdown via de MCP-tool
`confluence_create_page` (markdown→storage niet herbouwen), enkel op "publiceer" én enkel als
`aiec.py config mode` `production` geeft.

## 2. Het model: `aiec-core/schema.yaml`

Eén bestand. Daaruit volgen: het `details`-blok per initiatiefpagina, de sjabloonpagina, de
overzichtspagina, de validatieregels van `aiec-groom`, de groepering in `aiec-rapport` en de
veldenlijst die `aiec-initiatief` voorstelt. SKILL.md-bestanden herhalen géén enums of pijlers;
ze roepen `aiec.py schema` aan.

Ontwerpkeuzes bij het vertalen van de 14 velden naar rijen in het `details`-blok:

- **Titel staat niet in het blok.** De paginatitel is de titel; Page Properties Report toont die
  sowieso als eerste kolom. Groom meldt drift t.o.v. de Jira-summary (info), dwingt niets af.
- **Status staat nooit in het blok** (harde regel datamodel). De overzichtspagina koppelt een
  `detailssummary` aan een Jira-macro voor live status.
- **AI-key** is de join-sleutel naar Jira (foreign key, geen duplicaat).
- **EAG-key** is de gedeclareerde counterpart. De Jira-link `Gerelateerd` wordt daaruit afgeleid;
  groom meldt ontbreken of afwijking, `aiec.py jira link` legt hem.
- **Samengestelde velden zijn gesplitst** waar één helft ooit een filter is: vrager/afdeling,
  batenclaim/aanname, opgeleverd/gebruikers. 14 velden → 16 rijen, plus `stopreden` (enum) bij
  stopzetting omdat die de funnel-analyse voedt. De beslissing zelf blijft een artefact (pagina).
- **Pijler** wordt opgeslagen als `code — naam` (`P3 — Interne Operaties & Productiviteit`). Code is de
  waarheid; de naam mag Kenzo later herformuleren, `conf upsert-details` rendert opnieuw en groom
  meldt verouderde teksten.
- **Multi-waarden** (toepassingstype, AI-techniek) staan als komma-gescheiden tekst in één cel.
  Parser is tolerant (komma's, regeleinden, `<br/>`, hoofdletters).
- **Verplicht-wanneer** is gestructureerd (`required_when`), geen expressietaal.

Vaste identificatoren (allemaal in `schema.yaml`): details-id `aiec-initiatief`, paginalabel
`ai-initiatief`, artefactlabels `captatierapport`, `verkenningsrapport`, `decisions`, `verslag`,
`opleveringsverslag`. `decisions` is bewust het bestaande label waarop de ≥25 `[AI-xx]
Beslissingen`-pagina's al query'en: zodra een beslissingspagina het label krijgt, werken die. Statusmapping Jira → nette naam met fase-index; Jira-hernoeming later is één
kolom aanpassen.

## 3. Confluence-model

- Eén pagina per initiatief, label `ai-initiatief`, met bovenaan het `details`-blok (id
  `aiec-initiatief`) en daaronder de vaste kopjes uit `schema.yaml › page_sections`
  (Waarover gaat het · Stand van zaken (Jira-macro op de key) · Artefacten (children-macro) ·
  Beslissingen (detailssummary op label `decisions`, ancestor = currentContent())).
- Bestaande mini-spaces blijven; de retro-fit voegt het blok en het label toe aan de bestaande
  rootpagina, hernoemt niets.
- Artefacten zijn subpagina's met een artefactlabel. Geen subpagina zonder echt artefact.
- Overzichtspagina "AI-initiatieven — register": één `detailssummary` (cql op label + space,
  kolommen uit `schema.yaml › overzicht`, gesorteerd op Pijler — Page Properties Report kan niet op
  celwaarde filteren, dus geen rapport per pijler), plus één Jira-macro (JQL alle initiatieven) voor
  status en assignee. Jira-macro vereist `serverId`; kopiëren uit een bestaande pagina in de space,
  anders weglaten en melden.
- Sjabloonpagina "Sjabloon AI-initiatief" onder Templates (`411959725`), gegenereerd uit het schema.
- Storage-XML van `details`, `detailssummary`, `jira` en `children` wordt **niet uit het hoofd
  geschreven**. Echte voorbeelden staan klaar (ontwerpsessie, read-only opgehaald): de productfiche
  (`470876655`, zes `details`-blokken zonder id-parameter), `[AI-49] Beslissingen` (`505839625`,
  `detailssummary` schema-version 2 met `firstcolumn`, `headings`, `cql`), de mini-space-template
  (`411959720`, met `jira`-macro incl. `server` en `serverId`). `children` heeft nog geen voorbeeld:
  zoek er een met CQL `macro = "children"` of markeer `# ONGEVERIFIEERD`.
- Geverifieerd: bestaande titels volgen `[AI-n] titel`; mini-spaces hangen onder categoriepagina's
  (Maatwerk & processoptimalisatie, Conversational AI en agents, AI-augmented SDLC) met kinderen
  `[AI-n] Portfoliobeheer dOMG` → `[AI-n] Beoordeling Initiatie`, `[AI-n] Beslissingen`, `[AI-n]
  Logboek`. Labels in gebruik: `aiic-project-overview`, `idee`, `beoordeling-initiatie-verkenning`,
  `meeting-notes` (9). Label `decisions`: 0 pagina's. Space-home `390605009`.

## 4. Jira-model

- Lezen: initiatieven (`issuetype = Initiative`, id 13506) met status, resolution, links,
  changelog (laatste statuswissel, nieuwe links), Hierarchy-kinderen.
- Uren = worklogs op de subtree (Initiative → `Hierarchy` → Epics → `Epic Link`
  (customfield_10510) → Stories → subtasks) plus de gelinkte EAG-tickets zelf (hun kinderen niet).
  Live geverifieerd: het kind draagt de Hierarchy-link als `outwardIssue` ("is part of"), de ouder
  als `inwardIssue` ("includes") — kinderen lees je aan de inward-kant; ze zitten geregeld in een
  ander project (OB-1, ROS-31). Bron:
  `/rest/api/2/issue/{key}/worklog`. Euro's alleen als `report.uurtarief_eur` > 0 in de config, en
  dan gemarkeerd als aanname.
- "Beweging" = max(Jira `updated`, laatste wijziging van de pagina en haar kinderen). Frigo-regel:
  soort = afgebakend, fase in {Captatie, Analyse, Planning}, stil > `report.frigo_dagen` (90).
- Schrijven, enkel via `aiec.py` met guard: initiatief aanmaken (summary, description, Datum
  ontvangst = vandaag, optioneel Verantwoordelijke/Trekker), link `Gerelateerd` naar EAG,
  transitie + resolution na een expliciete beslissing van Kenzo. Geen custom fields; nooit
  automatisch sluiten.

## 5. Guard en configuratie

`~/.config/aiec/config.toml` (`aiec.py config init` schrijft de defaults):

```toml
[atlassian]
confluence_url = "https://confluence.omgeving.vlaanderen.be/confluence"
jira_url = "https://jira.omgeving.vlaanderen.be/jira"
space = "AI"
jira_project = "AI"
eag_project = "EAG"
templates_parent = 411959725
briefings_parent = 398330761

[writes]
mode = "dry-run"          # dry-run | test | production
test_space = "~vancrake"  # enige Confluence-space waarin 'test' mag schrijven

[report]
uurtarief_eur = 0         # 0 = geen euro's
frigo_dagen = 90

[vault]
path = "~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain"
```

Guard, afgedwongen in code: een `http.Client` is alleen-lezen (POST/PUT werpen `GuardRefused`).
De enige weg naar een schrijvende client is `http.writer(cfg, target, scope, apply)`, die
`config.guard` aanroept. Zonder `--apply` krijgt een module een leesclient en rendert enkel de
payload. Acceptatie voor elk mutatiecommando: met `--apply` in mode `dry-run` exit 3.

| mode | zonder `--apply` | met `--apply` |
|---|---|---|
| `dry-run` (default, ook zonder configbestand) | payload + diff naar stdout | geweigerd, exit 3 |
| `test` | idem | Confluence enkel in `test_space`; Jira altijd geweigerd |
| `production` | idem | Confluence in `space`, Jira in `jira_project`/`eag_project` |

Tokens: keychain `confluence-personal-token` en `jira-personal-token` (account `$USER`), override
via `CONFLUENCE_PERSONAL_TOKEN` / `JIRA_PERSONAL_TOKEN`. Nooit printen. Redirects worden niet
gevolgd: een 302 op een REST-call is een auth-fout met duidelijke melding. Tijdens de
implementatie is de mode `dry-run`; `production` zetten is Kenzo's expliciete go.

State `~/.config/aiec/state.json`: `last_stand`, `last_kwartaal`, `last_groom`, `last_retrofit`.
Run-map `~/.config/aiec/runs/<YYYY-MM-DD>-<skill>/` via `aiec.py state run-dir <skill>`; daar staan
voorstellen (`retrofit.md`, `groom.md`), datasets en done-bestanden.

## 6. CLI-contract `aiec.py`

`#!/usr/bin/env -S uv run --script`, PEP 723, `requires-python >= 3.12`, enige dependency `pyyaml`.
Pakket `aiec_lib/` naast het script. Tests: `cd scripts && uv run --with pytest --with pyyaml
python -m pytest tests`. Alle commando's: `--config <pad>`, `--json` (machine-output op stdout;
zonder `--json` markdown voor mensen), `--out <bestand|map>`; deze vlaggen mogen vóór of ná het
subcommando staan. Exitcodes: 0 ok · 1 fout · 2 gebruiksfout · 3 write door guard geweigerd · 4
validatiefout in aangeleverde waarden of ongeldige invoer (`ValueError`).

| commando | doet | output |
|---|---|---|
| `schema [check]` | model tonen; `check` = consistentie (dubbele enums, mapping volledig) | md / json |
| `config init\|show\|mode` | defaults schrijven, tonen, enkel de write-mode printen | |
| `state get\|set\|run-dir` | state lezen/schrijven; run-map aanmaken en pad printen | |
| `jira list [--all]` | initiatieven (default zonder Afgesloten) | `initiatives.json` |
| `jira get <AI-key>` | één initiatief incl. description | json |
| `jira hours [KEY KEY] [--keys KEY...] [--since D] [--until D]` | uren per initiatief (subtree + EAG) | `hours.json` |
| `jira search "<jql>" [--limit N]` | ruwe JQL (key, summary, status, issuetype, updated) — kandidaat-EAG zoeken | json |
| `jira changes --since D [--until D]` | statuswissels, nieuwe initiatieven, nieuwe links | `changes.json` |
| `jira create --title T --description D [--eag EAG-n] [--verantwoordelijke U] [--trekker U] [--apply]` | Initiative + link | key |
| `jira link <AI-key> <EAG-key> [--apply]` | link `Gerelateerd` | |
| `jira transition <AI-key> --to <naam> [--resolution R] [--apply]` | statuswissel (nette naam → Jira-naam) | |
| `conf pages [--discover]` | registerpagina's (label) of, met `--discover`, alle kandidaat-pagina's met `AI-\d+` in de titel | `register.json` |
| `conf get <page-id\|AI-key>` | storage-body + geparsed blok | json |
| `conf search "<cql>"` | ruwe CQL (id, titel, labels, lastModified) | json |
| `conf render --values <json> [--page]` | details-blok; met `--page` de hele initiatiefpagina | storage-xml |
| `conf render-template` · `conf render-overview` | sjabloon- en overzichtspagina uit het schema | storage-xml |
| `conf upsert-details --page <id> --values <json> [--apply]` | blok met id `aiec-initiatief` vervangen of vooraan invoegen; rest van de body ongewijzigd; label toevoegen | diff + payload |
| `conf create-initiative --values <json> --title T [--parent <id>] [--samenvatting S] [--apply]` | nieuwe pagina volgens `page_title` + label + blok | page-id |
| `conf create-child --parent <id> --title T [--label L …] [--from-title T] [--apply]` | kindpagina (artefact), body optioneel gekopieerd van een sjabloonpagina op titel | page-id |
| `conf publish-template [--apply]` · `conf publish-overview [--apply]` | create-or-update op titel | page-id |
| `conf set-labels <page-id> <label>... [--apply]` | labels toevoegen | |
| `validate [--register f] [--jira f] [--hours f] [--discover]` | regels (§7) over live data of aangeleverde bestanden; `--discover` neemt ook ongelabelde pagina's mee (vóór de retro-fit) | `violations.json` + `.md` |
| `report data --since D [--until D]` | dataset register ⨝ Jira ⨝ uren ⨝ wijzigingen ⨝ violations | `data.json` + `data.md` |
| `apply --proposal <f> [--apply]` | voorstel-bestand (§8) uitvoeren | verslag |

Waardenformaat (`--values`, en overal in JSON): sleutels uit `schema.yaml › fields[].key`;
multi-velden als lijst; pijler als code (`P2`); lege string = leeg. `conf render` en
`upsert-details` normaliseren (hoofdletters, spaties, aliassen) en weigeren met exit 4 wat niet in
het schema past; de fouten staan in `problems`.

### JSON-vormen (bevroren)

`register.json`

```json
{"generated": "2026-09-16T10:00:00", "space": "AI", "pages": [{
  "page_id": "431293025", "title": "[AI-25] AI-ondersteuning MIA", "ai_key": "AI-25",
  "version": 7, "last_modified": "2026-09-02T09:12:00", "labels": ["ai-initiatief"],
  "url": "https://…/pages/431293025", "has_details": true,
  "details": {"ai_key": "AI-25", "eag_key": "EAG-927", "soort": "afgebakend", "pijler": "P2",
              "vrager": "…", "afdeling": "…", "herkomst": "management",
              "toepassingstype": ["Documentverwerking"], "ai_techniek": ["Generative AI"],
              "delivery_mode": "eigen bouw", "ai_act_klasse": "beperkt", "persoonsgegevens": "ja",
              "batenclaim": "", "aanname": "", "opgeleverd": "", "gebruikers": "", "stopreden": ""},
  "details_raw": {"AI-key": "AI-25", "Pijler": "P2 — Slimme oplossingen bouwen"},
  "details_problems": ["pijler: tekst wijkt af van schema"],
  "children": [{"page_id": "…", "title": "…", "labels": ["captatierapport"], "last_modified": "…"}],
  "last_activity": "2026-09-02T09:12:00"
}]}
```

`initiatives.json`

```json
{"generated": "…", "issues": [{
  "key": "AI-25", "summary": "…", "status_raw": "In Analyse", "status": "Analyse", "fase": 1,
  "resolution": null, "created": "…", "updated": "…", "last_transition": "2026-07-01T…",
  "eag_keys": ["EAG-927"], "links": [{"type": "Gerelateerd", "key": "EAG-927", "direction": "outward"}],
  "children": ["AI-92"], "billingkey": null, "labels": [], "assignee": null, "trekker": null,
  "verantwoordelijke": null, "confluence_page_ids": ["431293025"], "url": "https://…/browse/AI-25"
}]}
```

`hours.json`: `{"since", "until", "per_initiative": {"AI-25": {"total_h": 12.5, "period_h": 4.0,
"per_month": {"2026-08": 4.0}, "issues": ["AI-25", "AI-92", "EAG-927"]}}}`

`changes.json`: `{"since", "until", "transitions": [{"key", "from", "to", "when"}],
"new_initiatives": [{"key", "summary", "created"}], "new_links": [{"key", "linked", "type", "when"}]}`

`violations.json`: lijst van `{"rule", "severity": "fout|waarschuwing|info", "ai_key", "page_id",
"message", "fix": {"action": "label|jira-link|rerender|transition", "args": {…}} | null}`

`data.json`: de vier bovenstaande samengevoegd plus `per_pijler`, `per_status`, `funnel`
(aantal per fase + verdeling stopreden), `doorlopend` (uren eigen werking), `frigo`, `risico`
(per AI Act-klasse, persoonsgegevens = ja), `heatmap` (afdeling × toepassingstype), `kost`
(uren en, indien tarief, euro als aanname). `data.md` zet dezelfde tabellen in markdown; de LLM
schrijft daar proza van en verzint niets erbuiten.

## 7. Regels (`rules.py`, gevoed door het schema)

| id | ernst | wanneer |
|---|---|---|
| `ontbrekend-veld` | fout | `required` of `required_when` niet voldaan |
| `enum-buiten-bereik` | fout | waarde niet in de enum (na normalisatie) |
| `pijler-tekst-verouderd` | info | code klopt, naam wijkt af van schema → fix `rerender` |
| `geen-eag` | waarschuwing | soort = afgebakend, geen EAG-key en geen Jira-link — Kenzo beslist per stuk |
| `eag-link-ontbreekt` | waarschuwing | EAG-key ingevuld, Jira-link `Gerelateerd` ontbreekt → fix `jira-link` |
| `eag-mismatch` | waarschuwing | EAG-key ≠ gelinkte EAG in Jira |
| `geen-captatierapport` | waarschuwing | afgebakend, fase ≥ Analyse, geen kind met label `captatierapport` |
| `geen-verkenningsrapport` | waarschuwing | afgebakend, fase ≥ Planning, geen kind met label `verkenningsrapport` |
| `frigo` | waarschuwing | zie §4; met de drie opties in de melding |
| `geen-stopreden` | fout | Afgesloten en resolution ≠ uitgevoerd, `stopreden` leeg |
| `geen-pagina` | fout | Jira-initiatief zonder registerpagina |
| `wees-pagina` | fout | registerpagina waarvan de AI-key niet in Jira bestaat |
| `titel-drift` | info | titel bevat de key niet of wijkt af van de Jira-summary |
| `doorlopend-in-funnel` | info | soort = doorlopend met captatierapport of stopreden |
| `artefact-zonder-label` | info | kindpagina zonder artefactlabel → fix `label` (LLM kiest het label) |
| `baten-zonder-aanname` | fout | batenclaim ingevuld, aanname leeg |

`validate` leest live tenzij bestanden meegegeven zijn (tests, offline). Ernst bepaalt de volgorde
in `violations.md`; groepering per initiatief, dan per regel.

## 8. Voorstel-bestand (`proposal.py`)

Markdown dat Kenzo bewerkt vóór `apply`. Zelfde bestand voor retro-fit, één initiatief en groom.

```markdown
# aiec voorstel — retrofit — 2026-09-16
<!-- aiec:proposal v1 -->

## AI-25 — AI-ondersteuning Milieu-Investerings-Aftrek
- pagina: 431293025
- actie: upsert-details

| veld | waarde | bron | zekerheid |
|---|---|---|---|
| soort | afgebakend | jira | hoog |
| pijler | P2 | briefing 2026-09-06 | midden |
| batenclaim |  | — | KENZO |

### Acties
- [x] label ai-initiatief
- [ ] jira link AI-25 EAG-927
```

Parser: secties `## <AI-key> — …`; `actie:` ∈ {`upsert-details`, `create-page`, `skip`}; `pagina:`
verplicht bij upsert; tabelrijen → waarden (`bron`/`zekerheid` zijn voor Kenzo, worden genegeerd;
lege waarde = niet zetten; rij met `~~` = overslaan); aangevinkte actie-bullets worden uitgevoerd
(`label <naam>`, `jira link <A> <B>`, `jira transition <key> <naam> [resolutie]`), niet-aangevinkte
niet. Zonder `--apply` een verslag van wat er zou gebeuren.

## 9. Skills

### `aiec-initiatief` — `<AI-key>` | `nieuw "<titel>"` | `retrofit [AI-key …]`

1. Verzamelen: `jira get`, `conf get` (of `conf pages --discover` bij retro-fit), kindpagina's,
   vault-grep op de key, briefings via MCP-read. Bij `nieuw`: het intakegesprek loopt via de agent
   `ai-track-intake-analyzer` als Kenzo dat vraagt; de drempel (meer dan één gesprek én meer dan
   4 uur) staat in de skill als vraag, niet als automatisme.
2. Voorstellen: per veld waarde + bron + zekerheid; `not_inferable`-velden (batenclaim, aanname)
   blijven leeg met `KENZO`. Schrijven naar `<run>/initiatief.md` of `<run>/retrofit.md`. **Stop.**
3. Na "ok": `aiec.py apply --proposal … --apply`. Bij `nieuw` eerst `jira create` (Initiative +
   EAG-link), dan `conf create-initiative`, dan captatierapport-kind uit de gepubliceerde sjabloon
   als die bestaat (titel in config), anders melden. Doorlopende werking krijgt geen rapport.
4. Retro-fit: Kenzo valideert in batch; Rik is tweede reviewer op zijn dossiers (Kenzo stuurt door,
   niet gemodelleerd). `state set last_retrofit`.

### `aiec-groom` — geen argument | `kwartaal`

1. `validate` → `violations.json/.md` in de run-map.
2. LLM voegt per melding één regel context en een fix-voorstel toe (kandidaat-EAG via Jira-zoek op
   titel, kandidaat-label voor artefacten, herformulering bij enum-fouten).
3. `<run>/groom.md` met drie blokken: uitvoerbaar (aangevinkt = doen), beslissingen voor Kenzo
   (EAG per stuk, frigo: verkennen / parkeren met herbekijkdatum / afsluiten met stopreden), info.
   **Stop.**
4. Na "ok": `apply --proposal groom.md --apply`; `state set last_groom`. Verslag: wat gedaan, wat
   blijft staan. Bij `kwartaal` is het frigo-blok verplicht volledig beantwoord vóór apply.

### `aiec-rapport` — `stand` | `kwartaal` [`--since D`]

1. `report data --since <state.last_* | --since>` → `data.json`, `data.md`.
2. Proza met `write-like-kenzo` en `humanizer`; nuchter, geen superlatieven, geen cijfers buiten
   `data.md`. `stand`: wat bewoog, wat kwam binnen, welke beslissingen eraan komen, één alinea per
   initiatief met beweging. `kwartaal`: per pijler (lopend, opgeleverd, baten met aanname), eigen
   werking (uren), funnel en parkeerlijst, risico's per AI Act-klasse, vooruitblik, kost (uren; euro
   enkel met tarief en als aanname gemarkeerd).
3. Concept naar de vault: `02 - Areas/<datum>-stand-van-zaken-aiec.md` of
   `<datum>-kwartaaltoelichting-aiec.md`. **Stop**; Kenzo bewerkt in Obsidian.
4. `stand` + "verzonden": tekst naar het klembord (`pbcopy`), Kenzo mailt; `state set last_stand`.
   `kwartaal` + "publiceer": MCP `confluence_create_page` (markdown) onder de parent die Kenzo
   noemt (default `briefings_parent`), enkel in mode `production`; `state set last_kwartaal`.

## 10. Implementatie-afspraken (voor de panes)

- Werkmap `ai-toolkit-private`. **Geen commits**: de repo bevat niet-gecommit werk van Kenzo; noem
  in het done-bestand welke paden je aanraakte. Raak niets buiten `skills/project-management/
  aiec-portfolio/` aan.
- **Nooit schrijven naar Confluence of Jira**, ook niet "om te testen". Panes starten met
  `--disallowedTools` voor alle Atlassian-schrijftools; de scripts staan in `dry-run`. Lezen mag.
- Storage-XML komt uit echte pagina's (§3). Is het netwerk weg: bouw tegen een placeholder, markeer
  hem `# ONGEVERIFIEERD` en schrijf in het done-bestand wat nog geverifieerd moet worden.
- Geen imports uit `routine-core`; kopieer wat je nodig hebt (keychain, http zit al in `http.py`).
  De Tempo-feiten uit `tempo.py` (worker key, account-veld `customfield_12012`, epic-veld
  `customfield_10510`) gelden.
- Python ≥ 3.12, stdlib + pyyaml. Elke module heeft tests met fixtures; geen netwerk in tests.
- SKILL.md in het Nederlands, imperatief, kort; details in `references/`. Enums nooit herhalen.
- Done-bestand: `$AIEC_PANE_DONE` (pad in de prompt): wat gebouwd, hoe getest (letterlijke
  pytest-uitvoer), wat ongeverifieerd, wat afwijkt van dit ontwerp en waarom.

Coördinatie tussen panes (parallel op Dropbox, zonder branches):

- **Bevroren bestanden**: `DESIGN.md`, `schema.yaml`, `aiec.py`, `aiec_lib/config.py`,
  `aiec_lib/http.py`, `aiec_lib/schema.py`. Een pane die daar iets aan nodig heeft schrijft het
  verzoek in zijn done-bestand; de ontwerper past het toe.
- Elke pane bezit precies één module in `aiec_lib/` en één `tests/test_<module>.py`; fixtures met
  de namen uit `tests/fixtures/README.md`. Niets anders aanraken.
- Rauwe, ongetrimde pagina's en Jira-output staan buiten de repo (pad in de pane-prompt); trim tot
  wat de test nodig heeft, kopieer niet wholesale.
- Discovery-heuristiek (pane A): de rootpagina van een mini-space is de `[AI-n]`-pagina waarvan de
  parenttitel zelf níet op `[AI-\d+]` matcht.

Werkpakketten:

| pane | levert | tests |
|---|---|---|
| A `conf` | `confluence.py`: client-calls, details-parser en -renderer, page-render, upsert (XML-manipulatie), create, labels, template/overview-renderers, publish; `conf *` in `aiec.py` | parser ⇄ renderer round-trip op fixtures; upsert laat de rest van de body byte-gelijk |
| B `jira` | `jira.py`: list/get/hours/changes/create/link/transition; `report.py` + `report data` | fixtures uit `tests/fixtures/jira-*.json` (geanonimiseerde search-output); subtree- en urenberekening |
| C `prose` | de drie SKILL.md's (`aiec-initiatief`, `aiec-groom`, `aiec-rapport`) + `README.md` van de familie; `aiec-core/SKILL.md` en `mix.yaml` bestaan al | leesbaarheid; elke stap verwijst naar een bestaand commando uit §6 |
| D `rules` | `rules.py` + `validate`, `proposal.py` + `apply` (tegen de JSON-vormen van §6, met fixtures) | elke regel één positieve en één negatieve fixture; proposal-parser op het voorbeeld van §8 |

Integratie (Fable, na A–D): `validate` en `report data` live tegen de echte space (lezen), `conf
upsert-details` zonder `--apply` op één bestaande pagina, `apply --proposal` op een minimale
retro-fit in dry-run. Daarna `./mix-plugin sync aiec-portfolio`.

## 11. Open punten voor Kenzo (blokkeren de implementatie niet)

1. ~~Verwoording van de pijlers~~ — definitief door Kenzo op 2026-09-16: P1 Fundament & Dataveiligheid ·
   P2 Mens & Adoptie · P3 Interne Operaties & Productiviteit · P4 Externe Dienstverlening & Beleid, elk met
   omschrijving en afbakening in `schema.yaml`. OMK Omkadering blijft cross-cutting voor de doorlopende eigen
   werking. Governance (AI-59) valt onder P1, kennisdeling (AI-52) onder P2.
2. Jira-statussen hernoemen of niet; de mapping in het schema werkt in beide gevallen.
3. Resolution-namen: de instance kent 30 namen, niet de drie categorieën van het datamodel. Het
   schema draagt nu een voorgestelde mapping (Gerealiseerd/Afgehandeld/Done → uitgevoerd; Stopgezet/
   Wordt niet verder behandeld → stopgezet; Ingetrokken/Declined/Won't Do → geannuleerd). Kenzo
   bevestigt of verschuift.
4. Uurtarief voor euro's in de kwartaaltoelichting, of uren-only.
5. ~~Titelformaat~~ — geverifieerd: bestaande pagina's heten `[AI-n] titel`; het schema volgt dat.
6. Splitsingen in §2 (afdeling, aanname, gebruikers, stopreden) akkoord?
7. ~~Confluence-token~~ — de 302's waren de WAF die de probe-burst afknepen; keychain-token werkt
   (200). Het token in `mcp-atlassian.sh` verschilt van de keychain en gaf 404 op space AI:
   nakijken welk token de MCP-server hoort te gebruiken.

## 12. Implementatiestatus (2026-09-16)

Gebouwd door vier Opus-panes (A conf, B jira + report, C prose, D rules + proposal), gereviewd
door de ontwerper. 150 tests groen, geen netwerk in tests. Write-mode bleef de hele tijd `dry-run`;
er is **geen enkele write** naar Confluence of Jira uitgevoerd. Niets is gecommit (beide repo's
bevatten ander niet-gecommit werk). De volledige verslagen per pane staan in de Herdr-tab
`aiec-impl`.

### Aanvaarde afwijkingen van dit ontwerp

- Overzichtspagina: één `detailssummary` gesorteerd op Pijler in plaats van één per pijler (§3).
- `ac:macro-id` wordt bij renderen weggelaten en bij vervangen behouden; `url` in `register.json`
  is `…/pages/viewpage.action?pageId=…`.
- `apply --proposal` doet in dry-run géén calls en toont dus geen paginadiff; die haal je met
  `conf upsert-details` zonder `--apply` op één pagina.
- `ontbrekend-veld` meldt een pagina zonder blok één keer (met de lijst verplichte velden) en slaat
  velden met een eigen regel over (`eag_key`, `aanname`, `stopreden`); `enum-buiten-bereik` draagt
  ook pattern-fouten.
- `changes.json › new_links.type` is de changelog-frase (`includes`, `is gerelateerd aan`), niet de
  linktype-naam; gelinkte EAG-tickets tellen mee in de uren, hun kinderen niet; gedeelde epics
  (AI-67 onder AI-4 én AI-59) tellen in beide subtrees — een totaal over de portefeuille moet over
  de unie gaan; `report.bewogen` = transitie ∪ nieuwe link ∪ pagina-activiteit (niet Jira
  `updated`, dat beweegt bij elke worklog).
- Titel-splitsingen en het label `decisions` (§2) zijn in het schema doorgevoerd; `resoluties` is
  een mapping van categorie naar instance-namen (§11.3).
- Toegevoegd aan het contract tijdens de review: `jira search`, `conf create-child`,
  `validate --discover`, `ValueError → exit 4`, globale vlaggen ook ná het subcommando, een pauze
  van 150 ms tussen REST-calls (`AIEC_HTTP_PAUSE`) tegen de WAF.

### Ongeverifieerd (pas met een echte write te zien)

1. Confluence kent zelf een `ac:macro-id` toe aan een blok dat zonder wordt opgeslagen.
2. Invoegen van het blok in een `<ac:layout>`-pagina (vandaag geen enkele mini-space-root).
3. `columnIds` van de Jira-macro voor standaardkolommen (geredeneerd uit 411959720).
4. `POST /issue` (Datum ontvangst als `YYYY-MM-DD`), `POST /issueLink`, `POST /transitions`, en de
   aparte `PUT` voor resolution (het transitiescherm geeft geen velden terug).
5. Mode `test` en het schrijven in `~vancrake`: enkel in unit-tests.
6. De sjabloonpagina van het captatierapport bestaat nog niet; `create-child` maakt dan een leeg
   kind en meldt dat.

### Eerste live-run na Kenzo's go, in volgorde

1. `aiec.py config init`, `mode = "production"` in `~/.config/aiec/config.toml`.
2. `conf publish-template --apply` en `conf publish-overview --apply`.
3. `/aiec-portfolio:aiec-initiatief retrofit` — voorstel over de 11 mini-space-roots en de 14
   initiatieven zonder pagina; Kenzo valideert in batch, Rik op zijn dossiers.
4. `/aiec-portfolio:aiec-groom` — labels op bestaande beslissings- en rapportpagina's, EAG per stuk.
5. `/aiec-portfolio:aiec-rapport stand`; in oktober `kwartaal`.
