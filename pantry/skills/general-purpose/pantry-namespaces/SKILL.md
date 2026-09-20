---
name: pantry-namespaces
description: Namespace-conventies voor deze cookbook's pantry/skills/ — waar hoort een nieuwe skill thuis (welk domein of ecosysteem), nesten of promoveren. Gebruik dit ná de generieke harnessblender-skill (die legt ingredients/recipe/blend/pour uit) — dit is puur de persoonlijke ordening binnen déze cookbook. Gebruik bij "waar hoort deze nieuwe skill thuis", "moet dit een eigen namespace worden".
---

# pantry/skills namespaces

Dit is een aanvulling op de generieke `harnessblender`-skill (die met de tool zelf meekomt, zie
`harnessblender@harnessblender` — installeer die apart, hoeft niet via deze cookbook). Deze skill
gaat enkel over hóé `pantry/skills/` in **deze** cookbook georganiseerd is.

## Namespaces onder `pantry/skills/`

| namespace | soort | inhoud |
|---|---|---|
| `aiec-portfolio` | ecosysteem (hub `aiec-core` + 3 satellites) | AIEC-intake en portfolio-rapportage |
| `general-purpose` | domain | dev-loop meta-tools, domein-onafhankelijk (handoff, pickup, orchestreer, pre-mortem, …) |
| `writing` | domain | outputvorm-skills (proza, decks, briefings) |
| `second-brain` | domain, met geneste ecosystemen `bouwstenen/`, `capture/`, `routine/` | vault-workflow + Open Brain |
| `software-engineering` | domain, met genest ecosysteem `wcag/` | user stories, toegankelijkheid |
| `_archived` | geen domain — dode opslag, uitgesloten van scan (`exclude_dirs`) | historisch, niet actief |

**Ecosysteem nesten of promoveren?** Nest binnen een domain zolang die domain ook ander, los daarvan
staand werk bevat. Promoveer enkel tot eigen top-level namespace als er geen natuurlijke bredere
domain bestaat die er al iets anders in heeft zitten (`aiec-portfolio`).

`description` is het enige dat Claude ziet vóór hij een skill laadt — schrijf hem als een trigger,
concrete werkwoorden en zelfstandige naamwoorden. Schrijf in het Nederlands (technische termen
Engels), deterministisch werk in een script onder `assets/`, houd `SKILL.md` kort.
