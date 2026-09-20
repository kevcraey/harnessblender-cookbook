---
name: digest
description: |
  Schrijf per dag de daily note uit de verzamelde bundel (mail, agenda, Teams,
  Rocket.Chat, Jira, Confluence, Chrome, git, Claude-sessies, vault): wat is er
  gebeurd en beslist, geconsolideerd met wat Kenzo zelf al noteerde, zonder
  informatieverlies. Autonoom, één commit per dag. Onderdeel van de ochtend-/
  avondroutine; los aanroepbaar met een run-map of "digest van gisteren".
---

# Digest

Vault: `~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain`
Kern: lees `../routine-core/SKILL.md` (contract, grenzen, scripts). `S` = `../routine-core/scripts`.

Doel van de daily note: **je geheugen opporren**, en bij een weekoverzicht zien wat er ligt te verwateren. Geen archiefdocument. Dat bepaalt de lat: een leesbaar, geconsolideerd verhaal per onderwerp, geen log.

## Invoer

- Argument = pad van de run-map (`$ROUTINE_RUN_DIR` als het ontbreekt). Daarin `days/<YYYY-MM-DD>/`.
- Verwerk elke dagmap **behalve die van vandaag**, tenzij het argument `--met-vandaag` bevat (de avondroutine geeft dat mee).
- Zonder run-map (los aangeroepen): maak er zelf een (`S/state.py run-dir digest`), haal een token (`S/graph-token.sh save`; faalt dat, vraag Kenzo een vers token te kopiëren uit Graph Explorer, tab *Access token*) en draai `S/collect.py` voor elke dag uit `S/state.py days` (of de gevraagde dag).

## Per dag

1. **Lees** `bundle.md`. Sectie *AL VASTGELEGD* is de dedup-input: alles daar staat al in de vault.
2. **Mail uitdiepen waar het telt.** Previews zijn 300 tekens; de beslissende inhoud staat vaak voorbij. Kies de handvol mails die er echt toe doen en haal ze op met `S/collect.py --mail-body <id>` (token via `GRAPH_TOKEN_FILE`). Niet standaard voor alles.
3. **Oordeel.** Wat is er *gebeurd*, wat is er *beslist*? Groepeer per onderwerp, niet per bron — een beslissing die in Rocket.Chat begint, in Jira landt en per mail bevestigd wordt, is één punt. Bewaar: beslissingen mét argument, afspraken met naam en datum, cijfers die later nog gelden, open discussies met wie welk standpunt inneemt. Laat vallen: statusgepingpong, "ok"/"bedankt", agenda-accepts, herhaling van wat al staat.
4. **Consolideer** met wat er al staat. Je mag Kenzo's eigen tekst herschrijven, samenvoegen en verplaatsen tot één samenhangend verhaal per onderwerp. Eén harde grens: **geen informatieverlies** — een detail dat je niet kwijt kan, blijft staan zoals het is. Headers van `agenda` (overleg-headers met voorbereiding) blijven staan; zet het verslag van dat overleg eronder.
5. **Schrijf** in `04 - Journal/YYYY/MM/DD/YYYY-MM-DD.md`, tussen de blockquote en `## 📋 Logs`. Note ontbreekt → `S/note.py ensure <dag>`, maar **enkel als er werkinhoud is**; geen lege notes voor stille dagen.
6. **Commit** die ene note — **enkel dat bestand**, niet de map (`agenda` kan tegelijk aan de note van vandaag schrijven): check `.git/index.lock`, dan `git add -- "04 - Journal/YYYY/MM/DD/YYYY-MM-DD.md" && git commit -m "routine: digest <dag>"`. Eén commit per dag, zodat `git revert` per dag kan.
7. **State**: `S/state.py set digest_done_through <dag>` — pas ná de commit. **Uitzondering vandaag** (`--met-vandaag`): zet de marker op **gisteren**, niet op vandaag. Mail en chats van na de avondrun zouden anders nooit meer in een venster vallen; de volgende ochtend doet vandaag dan nog eens, met *AL VASTGELEGD* als dedup — meestal een no-op.

## Regels

- **Privé blijft buiten de note.** Chrome-geschiedenis komt ongesorteerd binnen; jij beslist. Persoonlijke afwezigheden van collega's, HR, sport, nieuws, privé-tooling: niet in de note.
- **ICR** en **token**: zie kern. `[ICR-overgeslagen]` nooit ophalen.
- **Tijdstippen**: Chrome-tijden lopen soms uren achter op de andere bronnen; citeer ze niet als kloktijd.
- **Bronnen die faalden** (onderaan elke bundel, `meta.json`): altijd in het rapport, behalve de structurele gaten (Teams-kanaalberichten, meeting-transcripts, GitLab-discussies) — die kent Kenzo.
- Namen als `[[Wikilink]]` enkel voor personen die een People-note hebben of collega's die hij zelf zo schrijft; externen zonder context als platte naam.

## Afsluiten

Schrijf `<run>/digest.done.md` als **laatste** stap: per dag wat toegevoegd of herschreven is (2-4 regels), met `obsidian://open?vault=1-Second-Brain&file=04%20-%20Journal%2FYYYY%2FMM%2FDD%2FYYYY-MM-DD`, de bronnen die faalden, en welke privé-sporen je liet liggen (categorie). Daarna niets meer.
