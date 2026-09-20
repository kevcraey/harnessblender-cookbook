---
name: sb-new-project
description: |
  Maak een nieuw project aan in het second brain: subfolder in `01 - Projects` plus
  project-MOC uit de template. Deterministische stappen via script, daarna
  minimale invulling (alias, related-to, Overview, People).
---

# Nieuw project

Vault: `~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain`

## Workflow

1. **Slug en titel bepalen** uit de projectomschrijving van de gebruiker:
   - slug: kebab-case, kort (bv. `ai-poc-sbi`) — wordt `01 - Projects/<slug>/project-moc-<slug>.md`
   - titel: de H1, een leesbare projectnaam
   - Bij twijfel over de naam: voorstel doen, niet gokken.
2. **Script draaien** (deterministisch deel — folder + MOC uit template + datum + H1):
   ```bash
   scripts/new-project.sh <slug> "<Titel>"
   ```
3. **Invullen** (judgment-deel), alleen met info die de gebruiker gaf:
   - `aliases`: de leesbare projectnaam (en projectnummer indien gekend, bv. `AI-9`)
   - `related-to`: relevante bestaande notes/MOC's — alleen bij hoge zekerheid
   - `## Overview`: 1–3 zinnen wat/waarom
   - `## People`: gekende betrokkenen als `[[wikilinks]]` naar bestaande people-notes
   - Verzin niets; lege secties zijn oké.
4. Roep `sb-integrate-note` aan op de nieuwe MOC.
5. Rapporteer het vault-relatieve pad (geen wikilinks in terminal-output).

## Regels

- MOC's leven altijd in `01 - Projects/<slug>/` — nooit in `02 - Areas` of `05 - Tasks`.
- Alleen canonieke tags (staan al in de template: `type/moc`, `type/project`).
- Geen rode links.
- Template en gedeeld dataview-script (`03 - Resources/030 - Templates/snippets/project-moc-view.js`) nooit vanuit deze skill wijzigen.
