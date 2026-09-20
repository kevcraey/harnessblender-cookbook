---
name: aiec-rapport
description: |
  Rapportage over het AI-portfolio van het AI Expertisecentrum: de periodieke standvanzakenmail
  aan Kris en Tom (`stand`) of de kwartaaltoelichting voor Tom, Jan en Kris (`kwartaal`), met
  cijfers live uit Jira en Confluence. Gebruik bij: stand van zaken AIEC, statusmail portfolio,
  kwartaaltoelichting, kwartaalrapport AI-initiatieven, rapporteren aan de CIO.
argument-hint: 'stand | kwartaal [--since YYYY-MM-DD]'
---

# AIEC — rapport

Kern: lees `../aiec-core/SKILL.md`; `A` = `../aiec-core/scripts/aiec.py`.

Alle cijfers komen uit `A report data`. Reken niets zelf uit en schrijf geen getal dat niet in
`data.md` staat. Pijlers en statussen: `A schema`, nooit uit het hoofd. Globale vlaggen staan
**vóór** het subcommando: `A --out $RUN report data --since 2026-07-01`.

## Stappen

1. **Run-map en periode**: `RUN=$(A state run-dir aiec-rapport)`.
   Ondergrens: het argument `--since`, anders `A state get last_stand` (`stand`) of
   `A state get last_kwartaal` (`kwartaal`). Geeft dat niets of `null`, vraag Kenzo de datum;
   stuur `null` nooit door naar `--since`. Formaat
   `YYYY-MM-DD`, geen tijdstempel. Bovengrens: vandaag, tenzij `--until` meegegeven.
2. **Dataset**: `A --out $RUN report data --since <D> [--until <D>]` → `$RUN/data.json` en
   `$RUN/data.md`. Lees `data.md`; dat is je enige feitenbron voor cijfers.
3. **Proza** schrijven met de skills `write-like-kenzo` en `humanizer`. Nuchter, feitelijk, geen
   superlatieven, geen promotie over eigen oplossingen. Vloeiend proza, geen telegramstijl.
   - `stand`: wat bewoog sinds de ondergrens, wat kwam binnen, welke beslissingen eraan komen.
     Eén alinea per initiatief **met** beweging; initiatieven zonder beweging niet opvullen.
   - `kwartaal`: per pijler (lopend, opgeleverd, baten met de aanname erbij), eigen werking
     (uren), funnel en parkeerlijst, risico's per AI Act-klasse, vooruitblik, kost. Euro's enkel
     als `data.md` ze geeft (tarief in de config) en altijd gemarkeerd als aanname.
   - Een batenclaim citeer je altijd samen met de aanname eronder. Zonder aanname: geen claim.
4. **Concept naar de vault** (vault-pad: `../aiec-core/SKILL.md`), in `02 - Areas/`:
   - `stand` → `<YYYY-MM-DD>-stand-van-zaken-aiec.md`
   - `kwartaal` → `<YYYY-MM-DD>-kwartaaltoelichting-aiec.md`
   Toon het vault-relatieve pad, geen wikilink. **Stop hier; Kenzo bewerkt in Obsidian.**
5. **Afwerken**, elk op zijn eigen trefwoord:
   - `stand` + **"verzonden"**: lees de (ge-edite) note en zet ze op het klembord met `pbcopy`;
     Kenzo mailt zelf. Dan `A state set last_stand <YYYY-MM-DD>`.
   - `kwartaal` + **"publiceer"**: eerst `A config mode`. Enkel als dat letterlijk `production`
     print, publiceer je de goedgekeurde markdown met de MCP-tool `confluence_create_page` onder
     de parent die Kenzo noemt (default: `briefings_parent` uit `A config show`), titel
     `<YYYY-MM-DD>-kwartaaltoelichting`. Print het `dry-run` of `test`, dan publiceer je niet:
     meld de mode en laat Kenzo beslissen. Na publicatie `A state set last_kwartaal <YYYY-MM-DD>`.

## Grenzen

- Dit is de enige plek waar de LLM zelf naar Confluence schrijft, en enkel in stap 5 bij
  `kwartaal` + "publiceer" + mode `production`. Nooit naar Jira. Nooit een bestaande pagina
  overschrijven.
- Niets uit `data.md` weglaten omdat het slecht uitkomt; niets toevoegen dat er niet in staat.
  Ontbreekt er iets (uren zonder worklogs, initiatief zonder pagina), noem dat als hiaat.
- Uren zijn uren. Euro's enkel met tarief, altijd als aanname benoemd.
- De vault-mutatie blijft beperkt tot de conceptnote in `02 - Areas/`; review-first.
