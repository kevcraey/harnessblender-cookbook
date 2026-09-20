---
name: sb-triage
description: |
  On-demand triage van beide inboxen van het second brain: onverwerkte H2-secties in
  daily notes én rauwe notes in de vault root. Stelt verwerking voor, gebruiker
  bevestigt in bulk, daarna uitvoeren. Geen cron, geen staging.
---

# Triage

Vault: `~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain`

## Bronnen

1. **Daily notes** (`04 - Journal/YYYY/MM/DD/YYYY-MM-DD.md`) — H2-secties zonder verwerkings-marker. Default bereik: vandaag plus de voorbije 7 dagen; expliciete datum of bereik kan als argument meegegeven worden.
2. **Vault root (de inbox)** — alle losse `.md`-bestanden rechtstreeks in de root (`CONTEXT.md` uitgezonderd).

**Verwerkings-marker**: een sectie is al verwerkt als er een `Verslag: [[...]]`- of `→ [[...]]`-regel onder staat. Sla die secties over — herdraaien moet idempotent zijn. Sla ook `## 📋 Logs` en dataview-blokken over.

## Daily-triage — per H2-sectie, eerste match wint

1. H2 linkt naar een project-MOC en de inhoud is louter voortgang/status → **laten staan** (MOC-activity dekt dit al)
2. Inhoud hoort bij een bestaand onderwerp met eigen note → **toevoegen aan die note**; in de daily blijft één samenvattingsregel + `→ [[note]]`
3. Dag-overstijgende kennis zonder bestaande note → **nieuwe note in `02 - Areas`** (tag `type/concept`); in de daily blijft één samenvattingsregel + `→ [[note]]`
4. Al de rest (vluchtige krabbels) → **laten staan**

> [!IMPORTANT]
> De eerste regel onder een H2 moet altijd een zelfstandig leesbare samenvattingszin zijn of blijven — de project-MOC-dataview toont die als recent activity. Nooit een sectie leegtrekken zonder samenvattingsregel achter te laten.

## Root-triage — per note

De lat is de **minimuminformatie**: een canonieke type-tag, een H1 die de inhoud dekt met een klein beetje content eronder, en minstens één wikilink naar een bestaande note.

- **Haalbaar** → aanvullen tot de lat (tag, H1, wikilinks via `sb-integrate-note`) en verplaatsen naar `02 - Areas`. Kennis en tijdsgebonden notes delen die map; het onderscheid zit in de type-tag (`type/concept` versus `type/meeting`, `type/event`, `type/decision`), niet in de locatie.
- **Niet haalbaar** (leeg, test, betekenisloos) → rapporteren als delete-kandidaat; **de skill verwijdert nooit zelf** — zie "Verwijderen via script"
- **Twijfel** → laten staan en melden

## Verwijderen via script

De skill voert nooit zelf een delete uit, ook niet na akkoord. In plaats daarvan:

1. Delete-kandidaten zitten mee in het bulk-voorstel.
2. Bij akkoord schrijft de skill de **absolute paden** van de goedgekeurde kandidaten naar `~/.sb-triage-delete-list.txt` (één pad per regel).
3. De gebruiker voert zelf `scripts/delete-notes.sh` uit (in deze skill-map). Het script toont de lijst, vraagt bevestiging, verwijdert deterministisch en ruimt de lijst op.

## Git-checkpoints

De vault is een git-repository. Twee vaste commit-momenten, in de stijl van de bestaande backup-commits:

- **Vóór de eerste wijziging**: `git add -A && git commit -m "backup: pre-triage YYYY-MM-DD state"`
- **Na afloop**: `git add -A && git commit -m "backup: post-triage YYYY-MM-DD state"`

Sla het pre-commit over als de working tree schoon is; meld het post-commit resultaat in het eindrapport.

## Regels

- Alles is voorstel + bevestiging, in bulk beslisbaar. **Eerst het volledige voorstel tonen, pas na akkoord uitvoeren** — nooit wijzigingen doen die daarna nog gereviewd moeten worden.
- Voorstellen en eindrapporten verschijnen in de terminal: verwijs naar notes met **vault-relatieve paden** (bv. `02 - Areas/blind-review.md`), geen `[[wikilinks]]` — die zijn daar niet klikbaar. Wikilinks horen alleen in vault-content zelf.
- Alleen canonieke tags toekennen: `type/person`, `type/concept`, `type/meeting`, `type/decision`, `type/moc`, `type/project`, `type/event`. Nooit nieuwe tags verzinnen.
- Roep `sb-screen-decisions` aan over alle verwerkte inhoud (vaste stap).
- Roep `sb-integrate-note` aan op elke nieuwe of aangevulde note.
- Geen rode links.
