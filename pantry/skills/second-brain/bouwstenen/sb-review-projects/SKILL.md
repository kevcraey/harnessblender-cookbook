---
name: sb-review-projects
description: |
  On-demand review/grooming van alle project-MOC's: gezondheid toetsen,
  ideeën omzetten naar tasks, stale content signaleren en afgesloten
  projecten netjes afsluiten. Voorstel in bulk, gebruiker bevestigt.
---

# Project-review (grooming)

Vault: `~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain`

## Scope

Alle project-MOC's:

```bash
find ~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain -name "project-moc-*.md" -maxdepth 3 -not -path "*/.obsidian/*" -not -path "*/99 - Archive/*"
```

MOC's buiten `01 - Projects/` zijn zwervers — verhuizen voorstellen (subfolder-patroon: `01 - Projects/<slug>/project-moc-<slug>.md`; MOC zonder werknotes mag rechtstreeks in `01 - Projects/`).

## Checklist per MOC

1. **Gezondheid** — H1 ingevuld (geen `# # `-dubbelhash of template-placeholder), `created` ingevuld, `aliases` aanwezig, canonieke tags.
2. **Gedeeld script** — MOC gebruikt de `dv.view("03 - Resources/030 - Templates/snippets/project-moc-view")`-oneliner, geen gekopieerd dataviewjs-blok en geen statische lege Meetings/Decisions/Recent Activity-secties.
3. **Ideeën → tasks** — losse "ideas/future"-bullets omzetten naar tasks met `#when/someday`; de sectie zelf mag daarna weg.
4. **Stale content** — milestones zonder recente status, lege secties, verlopen due-dates: signaleren en per item vragen (updaten/schrappen/laten).
5. **Afsluiten?** — geen activity, milestones af of project gestopt: afsluiting voorstellen.

## Projectafsluiting

1. Evergreen kennis uit de MOC en de projectsubfolder promoveren naar `02 - Areas` met tag `type/concept` (minimuminformatie-lat geldt). Meetings en decisions staan al in `02 - Areas` (tags `type/meeting`, `type/event`, `type/decision`) — die blijven staan, nooit aanraken.
2. De rest (MOC + subfolder) wordt delete-kandidaat — niet archiveren.
3. Verwijderen loopt via de delete-lijst: goedgekeurde absolute paden naar `~/.sb-triage-delete-list.txt`; de gebruiker draait zelf `sb-triage/scripts/delete-notes.sh`.

## Regels

- **Eerst het volledige voorstel tonen (per MOC gebundeld), pas na akkoord uitvoeren.** Bulk-beslisbaar.
- Terminal-rapporten: vault-relatieve paden, geen `[[wikilinks]]`.
- De skill verwijdert nooit zelf bestanden.
- Git-checkpoints zoals bij triage: `backup: pre-review/post-review YYYY-MM-DD state` (pre overslaan bij schone working tree).
- Alleen canonieke tags; geen rode links; nooit content verzinnen om secties te vullen.
- Roep `sb-screen-decisions` aan over inhoud die tijdens de review verwerkt/verplaatst wordt, en `sb-integrate-note` op nieuwe of gepromoveerde notes.
