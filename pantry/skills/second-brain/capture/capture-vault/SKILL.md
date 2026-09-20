---
name: capture-vault
description: |
  Scan de vault-wijzigingen sinds de vorige run en push relevante nieuwe kennis
  naar Open Brain. Een deterministisch script doet al het voorwerk (git-diff,
  ruis wegfilteren); de LLM oordeelt enkel over de overgebleven proza. Voorstel +
  bevestiging in bulk, dan pas capturen. On-demand; geen cron. Zusje van
  capture-session (bron = sessie i.p.v. vault-diff).
---

# Capture Vault

Vault: `~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain`

Doel: nieuwe kennis uit de vault periodiek naar Open Brain brengen, met **de LLM
enkel ingeschakeld wanneer er echt iets te oordelen valt**. Alles wat zonder
oordeel kan (diff, filteren, committen, marker) doet het script.

## Werkverdeling

- **Script (`scripts/scan-changes.sh`)** — deterministisch: bootstrap-marker,
  snapshot-commit, `git diff` sinds de marker met pathspec-excludes, per file
  enkel de toegevoegde prozaregels, ruis (frontmatter, kale links/tags, headers,
  callouts, tabellen, whitespace) weg, files onder de woorddrempel weg.
- **LLM (deze skill)** — oordeel: relevantie, atomaire extractie, dedup tegen het
  bestaande brein, en het uiteindelijke voorstel.

## Stappen

1. **Scannen.** Draai `scripts/scan-changes.sh`.
   - Uitvoer `EMPTY` → niks zinvols gewijzigd. Draai `scripts/advance-marker.sh`
     (tenzij het een BOOTSTRAP-melding was — dan staat de marker al goed) en
     rapporteer "geen nieuwe kennis". **Stop hier; niet verder oordelen.**
   - Anders: de uitvoer bevat blokken `===FILE=== <pad>` gevolgd door de
     overgebleven toegevoegde regels. Werk enkel met die bundel — lees de
     originele files niet opnieuw tenzij een blok zonder context onbegrijpelijk is.

2. **Oordelen & extraheren.** Per blok: haal de zelfstandige, bewaarwaardige
   feiten eruit als atomaire thoughts (beslissing, inzicht, referentie, persoon,
   observatie). Laat vluchtige status/voortgang, puur persoonlijke journal-ruis
   en dingen die de repo/git al vastlegt vallen.

3. **Dedup tegen het brein.** Roep vóór het voorstellen voor elke kandidaat
   `search_thoughts` aan (Open Brain MCP). Al gekend / semantisch dubbel → weg
   uit het voorstel. Dit is de correctheidsstap: zonder dedup stel je bij elke
   run dezelfde feiten opnieuw voor.

4. **Voorstellen.** Toon één genummerde lijst, gegroepeerd per type, met per
   kandidaat het **vault-relatieve bronpad** (geen `[[wikilinks]]` — niet
   klikbaar in de terminal). Wacht op akkoord. Kenzo beslist in bulk
   ("alles", of "alles behalve 3, 7").

5. **Pushen.** Push de goedgekeurde kandidaten via `capture_thought` (Open Brain
   MCP). Eén thought = één zelfstandige, herbruikbare uitspraak.

6. **Marker verzetten.** Draai `scripts/advance-marker.sh` (zet `brain-sync-last`
   op HEAD). Doe dit als laatste, ná de push — zo verdwijnen geskipte kandidaten
   permanent, maar verliest een afgebroken run niks.

## Argumenten

- Geen argument → normale run (sinds de marker).
- `backfill <git-ref>` → geef dit door als `BRAIN_SINCE=<ref>` aan het script om
  eenmalig verder terug te scannen dan de marker (bv. `BRAIN_SINCE=HEAD~20`).

## Regels

- **Voorstel eerst, push pas na akkoord** — nooit capturen wat daarna nog
  gereviewd moet worden.
- Terminal-output verwijst naar notes met **vault-relatieve paden**, nooit
  wikilinks.
- De LLM raakt geen vault-bestanden aan; deze skill schrijft enkel naar Open
  Brain. Vault-mutaties zijn beperkt tot de git-commit + tag van de scripts.
- Op een lege run mag er **geen** oordeelwerk gebeuren — script + marker, klaar.
- Excludes en de woorddrempel staan boven in `scan-changes.sh` (`BRAIN_MIN_WORDS`);
  pas ze daar aan, niet hier.
