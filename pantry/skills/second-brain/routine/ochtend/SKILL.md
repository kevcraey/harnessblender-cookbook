---
name: ochtend
description: |
  Ochtendroutine: token, verzamelen (gemiste dagen + vandaag), dan digest (inhalen)
  en agenda (overleg-headers + dringende mail + overdue tasks) inline in deze
  sessie, tijdschrijven, onthouden en portfolio (signalen + review) in aparte panes; wacht en toont het
  eindrapport, afgesloten met de overdue tasks en de 3 focuspunten van de dag.
  Dun voor het verzamel-/rapportagewerk; oordeelt enkel voor die afsluitende
  synthese. Gebruik bij: ochtend, start ochtend, ochtendroutine, goeiemorgen,
  dag starten, start mijn dag.
---

# Ochtend

Vault: `~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain`
Kern: lees `../routine-core/SKILL.md`. `S` = `../routine-core/scripts`.

Deze sessie **oordeelt niet**, op één uitzondering na: de focuspunten-synthese die het eindrapport afsluit (stap 8). Voor al de rest geldt: scripts draaien, digest en agenda inline uitvoeren zonder hun inhoud te herwegen, panes openen voor wat bevestiging vraagt, wachten en rapporteren. Werkt op elke dag, ook in het weekend (dan zonder tijdschrijven).

## Stappen

1. **Run-map**: `RUN=$(S/state.py run-dir ochtend)`; `export ROUTINE_RUN_DIR=$RUN GRAPH_TOKEN_FILE=$RUN/.gtok`.
2. **Token**: `S/graph-token.sh save $RUN`. Faalt dat:
   - Chrome-plugin beschikbaar → open `https://developer.microsoft.com/en-us/graph/graph-explorer` in een eigen tab, klik de tab *Access token*, en vraag Kenzo: "klik op Copy". Wacht op zijn bevestiging, `save` opnieuw. De Copy-klik kan niet geautomatiseerd worden (geen user gesture → geen klembord).
   - Geen Chrome-plugin → vraag hem het token te kopiëren (Graph Explorer → tab *Access token* → Copy) en probeer opnieuw.
   - Na twee mislukte pogingen: verder zonder Graph, met de blinde vlek (mail, agenda, Teams) expliciet in het eindrapport. Het token nooit tonen.
3. **Verzamelen** per dag, voor elke dag `D` uit `S/state.py days --today`:
   `S/collect.py --since ${D}T00:00 --until <D+1>T00:00 --out $RUN/days/$D` (voor vandaag zonder `--until`). Uitvoer naar een bestand in de run-map, nooit door `head`/`tail`. Cap-waarschuwing van `state.py` → letterlijk in het rapport.
4. **Digest en agenda — inline**, sequentieel, via de Skill-tool (geen Herdr-pane, geen aparte terminal die Kenzo zelf moet opzoeken):
   - `/routine:digest $RUN` — enkel als `state.py days` minstens één dag vóór vandaag gaf.
   - `/routine:agenda $RUN` — altijd.

   Beide schrijven zelf hun `<run>/<naam>.done.md`; het resultaat verschijnt zo al in deze sessie en is meteen de basis voor het eindrapport (stap 8).
5. **Panes** (Herdr) voor de drie die bevestiging van Kenzo vragen. `S/pane.sh spawn <naam> <model> "<prompt>"`:

   | naam | model | prompt | wanneer |
   |---|---|---|---|
   | `tijdschrijven` | `sonnet` | `/routine:tijdschrijven $RUN` | niet op zaterdag/zondag |
   | `onthouden` | `sonnet` | `/routine:onthouden $RUN` | altijd |
   | `portfolio` | `sonnet` | `/aiec-portfolio:portfolio ochtend $RUN` | altijd; signalen uit de activiteit + reviewladder (verplicht vanaf 5 dagen) |

   `pane.sh` geeft exit 3 zonder Herdr → **fallback**: ook deze drie sequentieel in deze sessie via de Skill-tool, met een waarschuwing dat dit de grote-sessie-variant is (en dat de bulk-bevestiging dan hier moet gebeuren in plaats van in een eigen pane).
6. **Wachten**: `S/pane.sh wait $RUN tijdschrijven onthouden portfolio` (enkel de gestarte), **in de achtergrond** (`run_in_background`) — Kenzo kan twintig minuten over een pane doen en een voorgrond-Bash sterft na tien. Je wordt gewekt als het klaar is. Panes gaan pas dicht als Kenzo ze sluit; dat is bewust, hij leest ze na.
7. **Afronden**, in deze volgorde, ná stap 6:
   - vault-commit voor wat `agenda` schreef — **enkel de note van vandaag**, niet de map (anders veeg je Kenzo's eigen edits aan andere dagen mee): check `.git/index.lock`; `git -C <vault> add -- "04 - Journal/$(date +%Y/%m/%d)/$(date +%F).md" && git -C <vault> commit -m "routine: ochtend $(date +%F)"` — enkel als er iets gestaged is;
   - `S/state.py set last_ochtend "$(date -Iseconds)"`;
   - `S/graph-token.sh clear $RUN`; `rm -rf $RUN/days`; `S/state.py sweep`. Pas hier wissen, niet vroeger: `tijdschrijven` en `onthouden` erven `GRAPH_TOKEN_FILE` en lezen het pad mogelijk nog tijdens hun run.
8. **Eindrapport**:
   - Digest en agenda: hun `.done.md` staat al in deze sessie (stap 4) — toon dat, geen `pane.sh report` nodig.
   - Tijdschrijven, onthouden en portfolio: `S/pane.sh report $RUN tijdschrijven onthouden portfolio`. Is de review verplicht en ontbreekt `portfolio.done.md`, dan meld je dat de routine niet afgerond is.
   - Bronnen die faalden (uit `meta.json` van de dagmappen, vóór je ze wist — lees ze in stap 7) en wat niet afgerond is ("pane X wacht nog" als er geen done-bestand kwam).
   - **Afsluiten, altijd**:
     - de overdue tasks, rechtstreeks uit `agenda.done.md` overgenomen;
     - antwoord op *"Wat zijn mijn 3 focuspunten van de dag, waar moet ik vandaag aan werken en wat moet ik bereiken en waarom?"* — dit is de ene plek waar je zelf mag oordelen. Baseer je op wat digest net over de voorbije dag(en) schreef (wat gebeurde/besliste), agenda (overleg van vandaag, overdue tasks) en, als dat scherper maakt, lopende projecten uit de vault. Drie punten, elk met een korte "waarom nu" — geen volledige takenlijst, geen herhaling van de hele digest.

## Regels

- Geen oordeel buiten stap 8: geen bundel zelf herinterpreteren, geen mail samenvatten los van wat digest/agenda al schreven, geen ticket kiezen. Zie je een fout in een pane-rapport, meld ze; los ze niet op in deze sessie.
- `git add -A` nooit in de vault. Token nooit tonen.
- Weekend: alles zoals een werkdag, behalve `tijdschrijven`.
