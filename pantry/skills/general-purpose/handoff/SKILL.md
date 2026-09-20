---
name: handoff
description: Vat de huidige conversatie samen in een handoff-document dat een andere agent kan oppikken met /pickup.
argument-hint: "Waarvoor dient de volgende sessie?"
---

Schrijf een handoff-document dat de huidige conversatie samenvat zodat een verse agent het werk kan verderzetten.

**Locatie (verplicht):** `tmp/handoff/` in de projectroot. Bestandsnaam: `<YYYY-MM-DD>-<korte-slug>.md`. Maak de map aan als die nog niet bestaat. Schrijf nooit naar `$TMPDIR`, `/var/folders/...` of een andere locatie — de `/pickup`-skill zoekt in `tmp/handoff/`.

Inhoud:

- **Doel van de volgende sessie** — als de gebruiker argumenten meegaf, is dat de focus; stem het document daarop af.
- **Stand van zaken** — wat is gedaan, wat is geverifieerd (build/testen groen?), wat is nog open.
- **Branch/worktree-context** — op welke branch staat het werk, wat is uncommitted.
- **Aanbevolen skills** voor de volgende sessie, indien van toepassing (bv. `/tdd`, `/orchestreer`).

Dupliceer geen inhoud die al in andere artefacten zit (PRD's, plannen, ADR's, issues, commits, diffs) — verwijs ernaar met pad of URL.

Meld op het einde het volledige pad en dat de volgende sessie kan starten met `/pickup`.
