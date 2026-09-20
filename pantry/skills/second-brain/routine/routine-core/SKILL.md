---
name: routine-core
user-invocable: false
description: |
  Gedeeld contract en scripts van de ochtend-/avondroutine (state, run-map,
  collector, Tempo, mail-marker, Herdr-panes). Geen eigen gedrag; wordt gelezen
  door ochtend, avond, digest, agenda, tijdschrijven en onthouden.
---

# Routine — kern

Vault: `~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain`
Scripts: `scripts/` naast dit bestand. Vanuit een zuster-skill: `<base>/../routine-core/scripts/`.

## Functionele lagen

```
collect (script, per dag)  →  judge (LLM, één pane per onderdeel)  →  propose (bestand)  →  apply (script)
```

- **collect** — `collect.py --since D 00:00 --until D+1 00:00 --out <run>/days/D`: één map per dag met `bundle.md` en één `<bron>.md` per bron (`notes`, `graph` = mail + agenda + Teams, `rocketchat`, `atlassian`, `chrome`, `git`, `vault`, `claude`) plus `meta.json`. Deterministisch, geen oordeel.
- **judge** — elke pane leest enkel de bronbestanden die ze nodig heeft, nooit "alles voor de zekerheid".
- **propose** — het voorstel is een bestand in de run-map (`tijdschrijven.md`, `onthouden.md`), niet enkel terminaltekst. Kenzo kan het bewerken vóór hij "ok" zegt.
- **apply** — boeken (`tempo.py book`), pushen (`capture_thought`), markeren (`mail_sync.py`) is code. De LLM voert het uit, beslist niets meer.

## Run-map

`~/.config/routine/runs/<YYYY-MM-DD>-<ochtend|avond>/` (via `state.py run-dir <soort>`):

```
.gtok                 Graph-token, mode 600 — nooit printen, gewist na de run
.last-pane            laatst aangemaakte Herdr-pane (voor de stapel-layout)
days/<YYYY-MM-DD>/    collector-uitvoer per dag
<skill>.md            voorstel (tijdschrijven, onthouden)
<skill>.done.md       eindrapport van een pane; bestaan = "klaar" voor de orchestrator
```

Env in elke pane: `ROUTINE_RUN_DIR` en `GRAPH_TOKEN_FILE` (= `$ROUTINE_RUN_DIR/.gtok`). Alle scripts lezen het token daar; het klembord is enkel de bron bij `graph-token.sh save`.

## State

`~/.config/routine/state.json` via `state.py`:

- `digest_done_through` — laatste dag waarvan de daily note volledig is. **Enkel `digest` zet dit**, per afgewerkte dag.
- `last_ochtend`, `last_avond` — ISO-tijdstip van de laatste geslaagde run.

`state.py days` = de dagen die nog een digest nodig hebben (t.e.m. gisteren; `--today` t.e.m. vandaag). Cap 14 dagen; daarboven waarschuwing en enkel de 14 recentste — ouder inhalen vraagt een expliciete `--since`.

## Done-bestanden

Een pane is klaar als `<run>/<skill>.done.md` bestaat. Inhoud = het eindrapport dat de orchestrator letterlijk overneemt: wat gedaan, wat geboekt/gepusht, wat overgeslagen en waarom, `obsidian://`-links naar geraakte notes. Schrijf het als **allerlaatste** stap — de orchestrator wacht erop (`pane.sh wait`), en `herdr agent wait` kan "wacht op ok" niet van "klaar" onderscheiden.

## Vault-mutaties

- **Enkel `digest` commit** (per dag, `routine: digest <dag>`). `agenda` schrijft de note maar commit niet; de orchestrator commit dat aan het einde (`routine: ochtend <datum>`). Twee panes die tegelijk committen botsen op `.git/index.lock` (Dropbox).
- Altijd **één bestand** als pathspec: `git add -- "04 - Journal/YYYY/MM/DD/YYYY-MM-DD.md"` — nooit de map, nooit `git add -A` in de vault. Anders veegt de digest van gisteren de half geschreven note van vandaag of Kenzo's eigen edits mee.
- **Overlap.** De avond zet `digest_done_through` op **gisteren**, niet op vandaag: mail en chats van na de avondrun vallen anders nooit meer in een venster. De ochtend herdoet vandaag-van-gisteren met *AL VASTGELEGD* als dedup. Bewuste ruil: één extra Opus-pass tegen geen gaten.
- **Wachten op panes** doet de orchestrator met `pane.sh wait` in de achtergrond (`run_in_background`); een voorgrond-Bash sterft na tien minuten en Kenzo doet soms langer over een pane.
- Check vóór elke commit op `.git/index.lock`; bestaat hij en is hij ouder dan een minuut, meld het en commit niet.
- Nieuwe daily note enkel via `note.py ensure <dag>` en enkel als er inhoud voor is.

## Grenzen (gelden voor elke pane)

- **ICR.** Mail met `ICR2`/`ICR3`/`ICR4` staat als `[ICR-overgeslagen]` in de bundel — negeren, nooit ophalen met `--mail-body`. Rocket.Chat, agenda en Teams dragen die tags niet; wat daar staat gaat integraal naar Claude. Bewuste keuze.
- **Privé blijft buiten vault en brein.** Chrome-geschiedenis, agenda en chats komen ongesorteerd binnen; werk/privé is oordeel. Meld achteraf welke privé-sporen je liet liggen (categorie, niet inhoud).
- **Mutaties buiten de vault:** Tempo-worklogs en Jira-issues (`tijdschrijven`), Open Brain (`onthouden`), Graph enkel de categorie `synced` (`mail_sync.py`). Niets anders — geen mail verplaatsen, verwijderen of beantwoorden.
- **Token nooit tonen**, ook niet gedeeltelijk. `graph-token.sh clear` op het einde van de routine.
- **Retentie.** De orchestrator verwijdert `days/` en `.gtok` na de eindrapportage (werkmail en chats horen niet blijvend op disk); voorstellen en done-bestanden blijven. `state.py sweep` ruimt run-mappen ouder dan 30 dagen.

## Scripts

| script | doet |
|---|---|
| `collect.py` | verzamelen per venster; `--mail-body <id>` voor één volledige mail; `--check-graph` |
| `state.py` | `show`, `get`, `set`, `days [--today]`, `run-dir <soort>`, `sweep` |
| `note.py` | `path`, `ensure`, `body` van een daily note |
| `tempo.py` | `gaps`, `day`, `issue`, `search`, `book <tabel.md> [--dry]`, `issue-create` |
| `mail_sync.py` | `synced` zetten: `<ids.txt>` of `--from-md <mail.md>` |
| `graph-token.sh` | `save <run>` (klembord → `.gtok`, geverifieerd), `clear <run>` |
| `pane.sh` | `spawn <naam> <model> <prompt>`, `wait <run> <naam>…`, `report <run> <naam>…`; exit 3 zonder Herdr |
