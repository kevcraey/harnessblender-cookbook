---
name: zet-schoolmenu-in-agenda
description: Lees in MyRo Resto (online.myro.be) op welke dagen Robin en Zoé warm eten op school en zet die dagen als dag-event met het menu in de gedeelde Google-agenda "Celien & Kenzo". Gebruik bij "schoolmenu in agenda", "warm eten in agenda", "MyRo", "Resto-reservaties naar agenda".
disable-model-invocation: true
---

# Schoolmenu in agenda

Zet de dagen waarop Robin en/of Zoé warm eten op school als dag-event in de agenda "Celien & Kenzo", met het menu in de beschrijving.

## Bron: MyRo Resto

- URL: `https://online.myro.be/Resto/index.php` (Kenzo is ingelogd in Chrome; niet zelf inloggen — vraag Kenzo als de loginpagina verschijnt).
- Lees via Claude in Chrome in een nieuwe tab. `innerHTML` wordt door de extensie geblokkeerd; gebruik `get_page_text`.
- Bovenaan links staan de knoppen **Zoé** en **Robin**; de kop toont "Reservatie voor Van Craeynest <naam>". Klik de andere knop, controleer de kop, lees opnieuw.
- **Gereserveerd = de dag toont een menu** (regel "basismenu vanaf L3" gevolgd door de gerechten). Dagen zonder menu, of met enkel "herfstvakantie", "Sportweek …" e.d., zijn geen warme dag.
- Legende "In winkelkar" vs "Betaald" is niet uit de tekst af te leiden; beide tellen als warm eten. Vermeld in het rapport dat nog niet betaalde dagen er ook tussen kunnen zitten.

## Doel: Google Calendar

- Kalender "Celien & Kenzo": `pdam3rp5mulpm0niinp5inb4bc@group.calendar.google.com`.
- Eerst bestaande events ophalen (`list_events`, `fullText: "warm"`, over de periode met menu's) en enkel ontbrekende dagen toevoegen. Bestaat een dag al maar met andere kinderen (bv. alleen Zoé, nu beiden), pas het bestaande event aan in plaats van een tweede te maken.
- Titels (volg de bestaande conventie):
  - beiden: `Robin & Zoé eten warm op school`
  - één kind: `Robin eet warm op school` / `Zoé eet warm op school`
- Beschrijving: de gerechten, één per regel, zonder de regel "basismenu vanaf L3".
- Dag-event, `availability: AVAILABILITY_FREE`, standaard-reminders.

### Valkuil: datum schuift een dag

Met de claude.ai Google Calendar-connector (`create_event` met `allDay: true`) wordt de datum uit de UTC-omzetting gehaald. `2026-11-10T00:00:00+01:00` wordt dan 9 november. Geef daarom altijd UTC-middernacht mee:

```
startTime: 2026-11-10T00:00:00Z
endTime:   2026-11-11T00:00:00Z
```

Controleer in het resultaat dat `start.date` de bedoelde dag is.

Werkt de lokale google-calendar-plugin niet (verlopen token), gebruik dan de claude.ai-connector.

## Afsluiten

Sluit de Chrome-tab. Rapporteer een tabel: datum, wie, menu (kort), en wat al bestond en overgeslagen werd.
