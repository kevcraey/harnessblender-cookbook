---
name: agenda
description: |
  Zet voor elk overleg van vandaag een header met gelinkte deelnemers en een korte
  voorbereiding in de daily note, en lijst de mail die vandaag dringend aandacht
  verdient plus overdue tasks. Autonoom, geen commit. Onderdeel van de
  ochtendroutine; los aanroepbaar als "agenda van vandaag" of "bereid mijn dag voor".
---

# Agenda

Vault: `~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain`
Kern: lees `../routine-core/SKILL.md`. `S` = `../routine-core/scripts`.

## Invoer

Argument = run-map (`$ROUTINE_RUN_DIR` als het ontbreekt). Lees enkel `days/<vandaag>/graph.md` (secties *Agenda* en *Mail*) en `days/<vandaag>/notes.md`. Zonder run-map: maak er een (`S/state.py run-dir agenda`), token via `S/graph-token.sh save` (anders vraag Kenzo een vers token uit Graph Explorer, tab *Access token*), en `S/collect.py --only graph,notes --since <vandaag>T00:00 --out <run>/days/<vandaag>`.

## Overleg-headers

**Welke events**: alles van vandaag, behalve `[geannuleerd]`, `[afgewezen]`, `[dagvullend]` (die voeden tijdschrijven), `[zonder deelnemers]`, en `[terugkerend]` met ≤30 min (standup, dagstart). Extra uitsluitingen op titel staan in `~/.config/routine/agenda-ignore.txt` (één patroon per regel), als dat bestaat.

**Vorm** — geen tijdstip in de header, maximaal linken:

```
## <Onderwerp>
<one-liner>

aanwezigen: [[Voornaam Naam]], [[Voornaam Naam]]

### voorbereiding
<voorbereiding>
```

- **Onderwerp**: de titel van het event, verder niets. Geen deelnemers, geen tijdstip, geen projectlink in de header.
- **One-liner**: één zin over waar dit overleg over gaat en wat er vandaag op het spel staat. Is er een match op een bestaande note, dan hoort de link daar thuis: zoek op onderwerp-woorden in `01 - Projects/project-moc-*.md` en `02 - Areas/*.md` (bestandsnaam en aliases). Geen match → geen link, geen gok.
- **aanwezigen**: deelnemers **altijd** als `[[Naam]]`, ook zonder People-note (Obsidian toont dan een lege link; Kenzo maakt de note als hij wil). Schrijf de naam zoals de vault ze schrijft als er een note bestaat (`03 - Resources/031 - People/`); anders zoals Graph ze geeft. Bij >10 deelnemers: de organisator en de bekende collega's, dan "e.a.".
- **voorbereiding**: wat Kenzo nodig heeft om binnen te stappen — waar staat het (laatste beslissing, open vraag), wat hij moet meebrengen of beslissen, relevante recente signalen (mail/chat van een deelnemer). Zo lang als het onderwerp vraagt: één regel bij een routineoverleg, een halve alinea of enkele bullets bij een overleg waar iets te beslissen valt. Bronnen: `search_thoughts` (Open Brain) op onderwerp en deelnemers, grep in de vault (`01 - Projects`, `02 - Areas`, recente daily notes), en de mail-sectie van vandaag/gisteren. Niets gevonden → laat de `### voorbereiding`-sectie weg; geen opvulling.

**Samenvoegen met wat Kenzo zelf schreef.** Staat er in de note al een header of bullet die dit overleg raakt (match op onderwerp of deelnemer) — vaak een snelle voorbereiding — dan: nieuwe header maakt, zijn tekst en jouw voorbereiding **samengevoegd** onder `### voorbereiding`, zijn oude header weg. Zijn feiten (namen, cijfers, vragen) blijven allemaal staan; enkel de vorm mag veranderen.

**Plaats**: boven `## 📋 Logs`, na wat er al staat, in agendavolgorde. Note ontbreekt → `S/note.py ensure <vandaag>`, maar enkel als er minstens één header te schrijven is. **Geen commit** — dat doet de orchestrator.

## Dringende mail (enkel rapport, niets mee doen)

Uit de *Mail*-sectie de berichten die **vandaag Kenzo's aandacht verdienen**. Criteria, alle nodig tenzij anders vermeld: `[aan mij]` (niet `[cc]`), van een persoon (geen automaat/nieuwsbrief), bevat een vraag of verzoek, `[onbeantwoord]`, en ≥1 werkdag oud óf expliciete deadline/urgentie in de tekst. **Uitzondering**: onbeantwoorde mail van Tom Van Gulck, Kris Peirlinck of Sigrid Raedschelders altijd tonen. Max 5; de lijst mag leeg zijn — liever leeg dan opgevuld. Vorm: afzender — onderwerp — waarom nu (één zin).

## Overdue tasks

`05 - Tasks/*.md` met `(due::YYYY-MM-DD)` vóór vandaag en nog open checkboxes → lijst `[[taak]] (N dagen)`. Puur lezen.

## Afsluiten

Schrijf `<run>/agenda.done.md` als laatste stap: welke headers geschreven of samengevoegd (met `obsidian://open?vault=1-Second-Brain&file=04%20-%20Journal%2F…`), welke events overgeslagen en waarom (één regel), de dringende-mail-lijst, de overdue-lijst, en wat je aan privé-events liet liggen (categorie).
