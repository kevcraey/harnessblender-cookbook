---
name: avond
description: |
  Avondroutine: token, verzamelen (gemiste dagen + vandaag), dan panes voor digest
  (t.e.m. vandaag), tijdschrijven en onthouden; wacht en toont het eindrapport.
  Dun: geen oordeel in deze sessie. Gebruik bij: avond, avondroutine, dag
  afsluiten, afronden, einde werkdag, dag afwerken.
---

# Avond

Vault: `~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain`
Kern: lees `../routine-core/SKILL.md`. `S` = `../routine-core/scripts`.

Deze sessie **oordeelt niet**. Ze draait scripts, opent panes, wacht en rapporteert. Werkt op elke dag, ook in het weekend (dan zonder tijdschrijven).

## Stappen

1. **Run-map**: `RUN=$(S/state.py run-dir avond)`; `export ROUTINE_RUN_DIR=$RUN GRAPH_TOKEN_FILE=$RUN/.gtok`.
2. **Token**: `S/graph-token.sh save $RUN`. Faalt dat:
   - Chrome-plugin beschikbaar → open `https://developer.microsoft.com/en-us/graph/graph-explorer` in een eigen tab, klik de tab *Access token*, vraag Kenzo: "klik op Copy", wacht op bevestiging, `save` opnieuw.
   - Geen Chrome-plugin → vraag hem het token te kopiëren (Graph Explorer → tab *Access token* → Copy) en probeer opnieuw.
   - Na twee mislukte pogingen: verder zonder Graph, blinde vlek (mail, Teams) expliciet in het rapport. Token nooit tonen.
3. **Verzamelen** per dag, voor elke dag `D` uit `S/state.py days --today`:
   `S/collect.py --since ${D}T00:00 --until <D+1>T00:00 --out $RUN/days/$D` (voor vandaag zonder `--until`). Uitvoer naar bestand, nooit door `head`/`tail`. Cap-waarschuwing → in het rapport.
4. **Panes** (Herdr), `S/pane.sh spawn <naam> <model> "<prompt>"`:

   | naam | model | prompt | wanneer |
   |---|---|---|---|
   | `digest` | `opus` | `/routine:digest $RUN --met-vandaag` | altijd |
   | `tijdschrijven` | `sonnet` | `/routine:tijdschrijven $RUN --met-vandaag` | niet op zaterdag/zondag |
   | `onthouden` | `sonnet` | `/routine:onthouden $RUN` | altijd |

   Exit 3 van `pane.sh` (geen Herdr) → **fallback**: dezelfde skills sequentieel in deze sessie via de Skill-tool, met de waarschuwing dat dit de grote-sessie-variant is.
5. **Wachten**: `S/pane.sh wait $RUN digest tijdschrijven onthouden` (enkel de gestarte), **in de achtergrond** (`run_in_background`) — Kenzo kan twintig minuten over een pane doen en een voorgrond-Bash sterft na tien. Je wordt gewekt als het klaar is. Kenzo sluit de panes zelf.
6. **Afronden**: `S/state.py set last_avond "$(date -Iseconds)"`; `S/graph-token.sh clear $RUN`; `rm -rf $RUN/days`; `S/state.py sweep`. Geen vault-commit hier — `digest` commit zelf per dag.
7. **Eindrapport**: `S/pane.sh report $RUN digest tijdschrijven onthouden` letterlijk, dan de bronnen die faalden (uit `meta.json`, lees ze vóór stap 6) en wat niet afgerond is.

## Regels

- Geen oordeel hier: geen bundel lezen, geen mail samenvatten, geen ticket kiezen. Fout in een pane-rapport → melden, niet oplossen.
- `git add -A` nooit in de vault. Token nooit tonen.
- Dag zonder activiteit: `digest` maakt geen note; state wordt wel bijgewerkt.
