---
name: ochtend
description: |
  Ochtendroutine: token, verzamelen (gemiste dagen + vandaag), dan panes voor
  digest (inhalen), agenda (overleg-headers + dringende mail + overdue tasks),
  tijdschrijven en onthouden; wacht en toont het eindrapport. Dun: geen oordeel in
  deze sessie. Gebruik bij: ochtend, start ochtend, ochtendroutine, goeiemorgen,
  dag starten, start mijn dag.
---

# Ochtend

Vault: `~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain`
Kern: lees `../routine-core/SKILL.md`. `S` = `../routine-core/scripts`.

Deze sessie **oordeelt niet**. Ze draait scripts, opent panes, wacht en rapporteert. Alles wat oordeel vraagt zit in de sub-skills. Werkt op elke dag, ook in het weekend (dan zonder tijdschrijven).

## Stappen

1. **Run-map**: `RUN=$(S/state.py run-dir ochtend)`; `export ROUTINE_RUN_DIR=$RUN GRAPH_TOKEN_FILE=$RUN/.gtok`.
2. **Token**: `S/graph-token.sh save $RUN`. Faalt dat:
   - Chrome-plugin beschikbaar → open `https://developer.microsoft.com/en-us/graph/graph-explorer` in een eigen tab, klik de tab *Access token*, en vraag Kenzo: "klik op Copy". Wacht op zijn bevestiging, `save` opnieuw. De Copy-klik kan niet geautomatiseerd worden (geen user gesture → geen klembord).
   - Geen Chrome-plugin → vraag hem het token te kopiëren (Graph Explorer → tab *Access token* → Copy) en probeer opnieuw.
   - Na twee mislukte pogingen: verder zonder Graph, met de blinde vlek (mail, agenda, Teams) expliciet in het eindrapport. Het token nooit tonen.
3. **Verzamelen** per dag, voor elke dag `D` uit `S/state.py days --today`:
   `S/collect.py --since ${D}T00:00 --until <D+1>T00:00 --out $RUN/days/$D` (voor vandaag zonder `--until`). Uitvoer naar een bestand in de run-map, nooit door `head`/`tail`. Cap-waarschuwing van `state.py` → letterlijk in het rapport.
4. **Panes** (Herdr). `S/pane.sh spawn <naam> <model> "<prompt>"`, in deze volgorde:

   | naam | model | prompt | wanneer |
   |---|---|---|---|
   | `digest` | `opus` | `/routine:digest $RUN` | enkel als `state.py days` minstens één dag vóór vandaag gaf |
   | `agenda` | `sonnet` | `/routine:agenda $RUN` | altijd |
   | `tijdschrijven` | `sonnet` | `/routine:tijdschrijven $RUN` | niet op zaterdag/zondag |
   | `onthouden` | `sonnet` | `/routine:onthouden $RUN` | altijd |

   `pane.sh` geeft exit 3 zonder Herdr → **fallback**: dezelfde skills sequentieel in deze sessie via de Skill-tool, in dezelfde volgorde, met een waarschuwing dat dit de grote-sessie-variant is.
5. **Wachten**: `S/pane.sh wait $RUN digest agenda tijdschrijven onthouden` (enkel de gestarte), **in de achtergrond** (`run_in_background`) — Kenzo kan twintig minuten over een pane doen en een voorgrond-Bash sterft na tien. Je wordt gewekt als het klaar is. Panes gaan pas dicht als Kenzo ze sluit; dat is bewust, hij leest ze na.
6. **Afronden**, in deze volgorde:
   - vault-commit voor wat `agenda` schreef — **enkel de note van vandaag**, niet de map (anders veeg je Kenzo's eigen edits aan andere dagen mee): check `.git/index.lock`; `git -C <vault> add -- "04 - Journal/$(date +%Y/%m/%d)/$(date +%F).md" && git -C <vault> commit -m "routine: ochtend $(date +%F)"` — enkel als er iets gestaged is;
   - `S/state.py set last_ochtend "$(date -Iseconds)"`;
   - `S/graph-token.sh clear $RUN`; `rm -rf $RUN/days`; `S/state.py sweep`.
7. **Eindrapport**: `S/pane.sh report $RUN digest agenda tijdschrijven onthouden` letterlijk tonen, gevolgd door: bronnen die faalden (uit `meta.json` van de dagmappen, vóór je ze wist — lees ze in stap 5), en wat niet afgerond is ("pane X wacht nog" als er geen done-bestand kwam).

## Regels

- Geen oordeel hier: geen bundel lezen, geen mail samenvatten, geen ticket kiezen. Zie je een fout in een pane-rapport, meld ze; los ze niet op in deze sessie.
- `git add -A` nooit in de vault. Token nooit tonen.
- Weekend: alles zoals een werkdag, behalve `tijdschrijven`.
