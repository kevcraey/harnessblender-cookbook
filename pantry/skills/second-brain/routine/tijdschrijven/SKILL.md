---
name: tijdschrijven
description: |
  Tijdschrijven in Tempo/Jira: onvolledige werkdagen opsporen (norm 7,6h), een
  voorstel per dag opstellen uit daily notes, agenda en Jira-activiteit, en na "ok"
  boeken via script. Gebruik bij: tijdschrijven, timesheet invullen, tijd boeken,
  uren boeken, Tempo, worklog, timesheets bijwerken. Onderdeel van de ochtend-/
  avondroutine; los aanroepbaar met optioneel een datum (YYYY-MM-DD).
---

# Tijdschrijven

Vault: `~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain`
Kern: lees `../routine-core/SKILL.md`. `S` = `../routine-core/scripts`.

Billable boekingen: een fout ticket is duurder dan een gat. Daarom **altijd eerst voorstellen**, nooit zelf boeken; en bij twijfel over een ticket de regel openlaten en vragen.

## Invoer

- Argument: optioneel een run-map, een datum `YYYY-MM-DD` en/of `--met-vandaag`. Run-map ontbreekt → `$ROUTINE_RUN_DIR`, anders `S/state.py run-dir tijdschrijven`.
- Zonder datum: alle onvolledige werkdagen van de laatste 30 dagen **tot en met gisteren** (`S/tempo.py gaps --days 30`). Vandaag telt enkel mee met `--met-vandaag` (→ `tempo.py gaps --today`); dat geeft de avondroutine mee, de ochtend niet — 's ochtends is vandaag nog geen gat. Met datum: enkel die dag (`S/tempo.py day <datum>` voor wat er al staat).

## Regels

- **Nooit weekend.** Zaterdag en zondag worden niet geschreven, ook al werd er gewerkt. `tempo.py book` weigert ze.
- Norm **7,6h** per werkdag; ook >8h melden. Het voorstel vult aan tot exact 7,6h.
- Dagvullend agenda-event `verlof`, `ziek`, `assessment`, `feestdag`, `recup` → **TM-4** voor de hele dag. Feestdagen kent het script niet; Kenzo meldt ze ad hoc.
- Vaste buckets: **AI-48** (Algemene Omkadering AI-Expertisecentrum, alles wat geen eigen initiatief heeft), **ZEND-3248** (Decibel-teamwerk zonder eigen ticket: sprintdemo, planning, standup, Jira-grooming), **TM-4** (inactief). Standup → altijd ZEND-3248.
- Initiatieven met eigen ticket krijgen dat ticket: zoek in de Jira-activiteit van die dag (`atlassian.md`, of `S/tempo.py search "<jql>"`) en in eerdere worklogs (`S/tempo.py day`) hoe vergelijkbaar werk eerder geboekt werd. Gewoonte weegt zwaarder dan de titel van een epic.
- Geen passend ticket → regel **openlaten** met `?` als ticket en de vraag erbij. Nieuw ticket aanmaken enkel als Kenzo dat vraagt: `S/tempo.py issue-create --project … --summary … --epic … --account <id> [--close]`; lees daarna terug dat de billingkey staat vóór je erop boekt.
- Commentaar = billingrecord: neutraal, feitelijk, één regel; niets persoonlijks (geen "assessment bij X", geen medische of privéredenen).

## Stappen

1. **Gaten**: `S/tempo.py gaps --days 30` (of `day <datum>`).
2. **Bewijs per dag**, in deze volgorde en niet meer dan nodig: de daily note (`S/note.py body <dag>` — de digest heeft ze net geschreven of Kenzo zelf), de dagmap in de run-map als die bestaat (`days/<dag>/graph.md` voor dagvullende events en overleggen, `atlassian.md` voor tickets, `claude.md` voor Claude-sessies die dag), anders niets ophalen dat er niet is. Voor vandaag zonder daily note: `bundle.md` van vandaag.
3. **Voorstel** naar `<run>/tijdschrijven.md` in het tabelformaat van `tempo.py book` (kolommen op naam; `titel` is voor Kenzo, wordt niet geboekt):

   ```
   | datum      | ticket    | titel                                   | uren | commentaar |
   |------------|-----------|-----------------------------------------|------|------------|
   | 2026-09-04 | AI-48     | Algemene Omkadering AI-Expertisecentrum | 7.6  | Assessment |
   | 2026-09-07 | ZEND-3248 | Gebouwenregister (Decibel-algemeen)     | 2.6  | Sprintdemo en -planning Decibel |
   | 2026-09-07 | ?         |                                         | 1.0  | Depositieruimte-cijfers Sofie — welk ticket? |
   ```

   **Altijd key én titel**, overal waar een ticket voorkomt — in de tabel, in de context-regels, in het rapport, ook bij wat al geboekt staat. Kenzo kent de nummers niet van buiten; een kale `AI-64` is voor hem geen informatie. Titel via `S/tempo.py issue <KEY>` of uit de `gaps`-uitvoer. Per dag som = 7,6h. Toon de tabel in de terminal met per dag één regel context (waarop het voorstel steunt). Open vragen apart eronder.
4. **Wacht op akkoord.** Kenzo antwoordt in bulk ("ok", "ok behalve regel 3 → AI-49", of bewerkt het bestand zelf). Pas het bestand aan; regels met `?` of `skip` in de laatste kolom worden niet geboekt.
5. **Boek**: `S/tempo.py book <run>/tijdschrijven.md` (eerst `--dry` als er iets gewijzigd is aan de tabel). Het script print OK/FAIL per regel en de dagtotalen erna; die totalen moeten 7,6 zijn — anders melden, niet maskeren.
6. **Rapport** als laatste stap naar `<run>/tijdschrijven.done.md`: geboekte regels, dagtotalen, wat open bleef en waarom.

Los aangeroepen (geen routine): zelfde stappen, rapport ook in de terminal.
