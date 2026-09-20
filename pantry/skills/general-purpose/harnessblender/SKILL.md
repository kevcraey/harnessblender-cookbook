---
name: harnessblender
description: Werken met harnessblender — Kenzo's tool om ingredients (skills, agents, richtlijnen, mcp servers) uit een cookbook te blenden tot installeerbare Claude Code-plugins en te pouren naar projecten. Gebruik bij het aanmaken/aanpassen van een skill, agent, richtlijn of mcp-server, bij het maken/blenden/pouren van een recipe, en bij vragen als "waar hoort dit thuis", "waarom zie ik mijn wijziging niet" of "hoe installeer ik dit in project X".
---

# harnessblender

Terminologie (cocktail-metafoor, bewust):

| term | betekenis |
|---|---|
| **ingredients** | alles wat blendbaar is: skills, agents, richtlijnen, mcp servers |
| **pantry** | jouw eigen ingredients, in de cookbook zelf (`pantry/`) |
| **store** | externe ingredients, gedeclareerd in `store.yaml`, gecloned naar `store/<naam>/` (gitignored) |
| **recipe** | een gekozen selectie ingredients, opgeslagen in `recipes/<naam>/recipe.yaml` |
| **blend** | het resultaat van een recipe bouwen: echte kopieën in `recipes/<naam>/blend/` (self-contained, overdraagbaar) |
| **cookbook** | de map met `pantry/`, `store/`, `recipes/` — herkend aan een `cookbook.yaml`-marker-bestand |
| **drinker** | een projectmap waar een blend in geïnstalleerd wordt |
| **pour** | een blend installeren in een drinker (via de Claude Code CLI) |

harnessblender zelf (de tool, dit `SKILL.md`, de scripts) draagt geen persoonlijke inhoud — alles
specifieks zit in een cookbook. Deze skill leeft zelf als pantry-ingredient in de cookbook die hij
beschrijft.

## Kaart

| Map | Rol | Bewerken? |
|---|---|---|
| `<cookbook>/pantry/{skills,agents,mcp-servers,richtlijnen}` | eigen ingredients, per namespace | ✅ ja, hier schrijf je |
| `<cookbook>/store/<naam>/` | gitignored checkout van een externe bron | ❌ nooit — regenereert via `fetch`, wijzigingen gaan verloren |
| `<cookbook>/store.yaml` | welke externe bronnen bestaan (naam + url) | ✅ ja |
| `<cookbook>/recipes/<naam>/recipe.yaml` | een opgeslagen selectie | ✅ ja (of via de picker) |
| `<cookbook>/recipes/<naam>/blend/` | gegenereerde plugin-kopie | ❌ nooit — `blend` overschrijft zonder waarschuwing |
| `<cookbook>/cookbook.yaml` | marker-bestand + naam/owner/exclude_dirs | ✅ ja |

## Beslisboom

**Nieuwe eigen skill** → map onder `pantry/skills/<namespace>/<skill-naam>/` (namespace = domain of
ecosysteem — zie de namespace-index verderop). Geen verplichte extra wrapper: elke map met een
`SKILL.md` telt, hoe diep ook genest. Zie [Skill-anatomie](#skill-anatomie).

**Agent** → `pantry/skills/<namespace>/agents/<naam>.md` — moet letterlijk onder een map genaamd
`agents` liggen (tool-vereiste). **Richtlijn** → `pantry/richtlijnen/<naam>.md`.

**MCP-server, eigen wrapper** (haalt credentials uit Keychain, roept een upstream `uvx`/`npx`-package
aan) → map onder `pantry/mcp-servers/<naam>/`: wrapper-script + `.claude-plugin/.mcp.json` +
`README.md` over de upstream-origin. Command = absoluut pad, dus niet overdraagbaar naar een andere
machine zonder herconfiguratie.

**Externe skill/repo binnenhalen** → voeg een entry toe aan `store.yaml` (naam + git-url), draai
`harnessblender fetch` (kloont als nog niet aanwezig). Verwijs in een recipe naar het pad binnen die
checkout, bv. `store/caveman/skills/caveman`. Nooit rechtstreeks in `store/` bewerken.

**Nieuwe recipe** → `harnessblender new-recipe <naam>` (picker) of handmatig een map
`recipes/<naam>/` met `recipe.yaml`, dan `harnessblender blend <naam>`.

**Bestaand recipe aanpassen** → `harnessblender edit-recipe <naam>` (picker, huidige selectie
voorgevinkt), of `recipe.yaml` handmatig bewerken + `harnessblender blend <naam>`.

**Installeren in een project (pouren)** → `harnessblender pour <recipe> <drinker-pad...> [--scope local|project|user]`.
Shellt uit naar `claude plugin marketplace add <cookbook>` + `claude plugin install <recipe>@<cookbook-naam> --scope ... -y` —
zelf geverifieerd, werkt non-interactief.

## Namespaces onder `pantry/skills/`

| namespace | soort | inhoud |
|---|---|---|
| `aiec-portfolio` | ecosysteem (hub `aiec-core` + 3 satellites) | AIEC-intake en portfolio-rapportage |
| `general-purpose` | domain | dev-loop meta-tools, domein-onafhankelijk (handoff, pickup, orchestreer, harnessblender, pre-mortem, …) |
| `writing` | domain | outputvorm-skills (proza, decks, briefings) |
| `second-brain` | domain, met geneste ecosystemen `bouwstenen/`, `capture/`, `routine/` | vault-workflow + Open Brain |
| `software-engineering` | domain, met genest ecosysteem `wcag/` | user stories, toegankelijkheid |
| `_archived` | geen domain — dode opslag, uitgesloten van scan (`exclude_dirs`) | historisch, niet actief |

**Ecosysteem nesten of promoveren?** Nest binnen een domain zolang die domain ook ander, los daarvan
staand werk bevat. Promoveer enkel tot eigen top-level namespace als er geen natuurlijke bredere
domain bestaat die er al iets anders in heeft zitten (`aiec-portfolio`).

## Skill-anatomie

```
<skill-naam>/
├── SKILL.md         # verplicht — de instructies voor Claude
├── README.md        # optioneel — uitleg voor mensen
├── assets/          # optioneel — templates, scripts
├── references/      # optioneel — diepere details, lazy-loaded
└── examples/        # optioneel
```

`description` is het enige dat Claude ziet vóór hij de skill laadt — schrijf hem als een trigger,
concrete werkwoorden en zelfstandige naamwoorden. Schrijf in het Nederlands (technische termen
Engels), deterministisch werk in een script onder `assets/`, houd `SKILL.md` kort.

## Commands

```bash
harnessblender new-recipe <naam>              # picker, schrijft recipe.yaml + blend meteen
harnessblender edit-recipe <naam>             # picker, huidige selectie voorgevinkt
harnessblender blend <naam>                   # herbouw blend/ uit recipe.yaml, geen picker
harnessblender list                           # alle recipes + hun status
harnessblender fetch                          # clone-if-missing + ff-only pull van store.yaml
harnessblender pour <naam> <drinker...>       # installeer een blend in project(en)
harnessblender web                            # browser-picker
harnessblender --cookbook <pad> <cmd> ...     # cookbook expliciet, i.p.v. marker-file lookup
```

Zonder `--cookbook` zoekt harnessblender omhoog vanaf de huidige map naar een `cookbook.yaml`.

## Valstrikken

- **"Mijn wijziging is niet zichtbaar"** → `blend` niet gedraaid, of niet opnieuw gepourd + `/plugin reload`.
- **Nooit in `recipes/<naam>/blend/` bewerken** — kopie, `blend` overschrijft zonder waarschuwing.
- **`fetch` slaat dirty/detached/diverged store-checkouts bewust over** — los eerst handmatig op.
- Absolute paden in eigen mcp-server-`.mcp.json`'s zijn niet overdraagbaar naar een andere machine
  (binary/uvx/npx moet lokaal op PATH staan) — `${CLAUDE_PLUGIN_ROOT}`-bundling is een bekende
  beperking, nog niet opgelost.

## Migratie van het oude systeem

`custom-plugins/` (het oude `mix-plugin`, variant-taal) blijft voorlopig bestaan en actief — het is
nog de live marketplace voor `kevcraey-user-level` en andere geïnstalleerde varianten. Niet
aangeraakt tijdens deze migratie. Nieuwe recipes horen in de cookbook via harnessblender; de oude
varianten worden bewust niet overgezet (worden opnieuw opgebouwd).
