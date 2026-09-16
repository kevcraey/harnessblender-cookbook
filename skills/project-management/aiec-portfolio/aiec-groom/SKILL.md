---
name: aiec-groom
description: |
  Regelcheck over het AIEC-register: Confluence-space AI en Jira naast elkaar leggen, ontbrekende
  velden, EAG-links, artefacten en stilgevallen initiatieven melden, en de fixes als voorstel
  aanbieden. Met argument `kwartaal` ook de frigo-beslissingen. Gebruik bij: groom, grooming,
  register opschonen, regelcheck AI-initiatieven, validatie Confluence Jira, frigo, kwartaalreview.
argument-hint: '[kwartaal]'
---

# AIEC — groom

Kern: lees `../aiec-core/SKILL.md`; `A` = `../aiec-core/scripts/aiec.py`.

Regels, ernst en fixes komen uit `A validate`; velden en enums uit `A schema`. Herhaal ze niet.
Globale vlaggen staan **vóór** het subcommando: `A --out $RUN validate`.

Deze skill beslist niets. Ze verrijkt meldingen met context en legt Kenzo één bestand voor.

## Stappen

1. **Run-map**: `RUN=$(A state run-dir aiec-groom)`.
2. **Valideren**: `A --out $RUN validate` → `$RUN/violations.json` en `.md` (live gelezen).
   Geen netwerk of stukke bron? Val terug op bestanden:
   `A --json --out $RUN/register.json conf pages --discover`,
   `A --json --out $RUN/initiatives.json jira list --all`,
   `A --json --out $RUN/hours.json jira hours --since <YYYY-MM-DD>`, dan
   `A --out $RUN validate --register $RUN/register.json --jira $RUN/initiatives.json --hours $RUN/hours.json`.
3. **Context toevoegen** (hier zit het oordeel), per melding één regel:
   - kandidaat-EAG: kijk eerst naar `eag_keys` van het initiatief in `$RUN/initiatives.json` (de
     link bestaat dan wel, de veldwaarde niet). Vind je daar niets:
     `A --json jira search 'project = EAG AND summary ~ "<kernwoorden>"'`. Noem de key, waarom je
     denkt dat het klopt, en je zekerheid.
   - kandidaat-label voor een artefact zonder label: kies uit de artefactlabels in `A schema`,
     op basis van de titel en de inhoud van de kindpagina (`A --json conf get <page-id>`).
   - enum-fout: stel de dichtstbijzijnde schemawaarde voor, met de gevonden tekst erbij.
   - frigo: zeg sinds wanneer het stil is en wat er het laatst gebeurde.
4. **Voorstel** `$RUN/groom.md`, drie blokken in deze volgorde (formaat: zie
   `../aiec-initiatief/SKILL.md`, sectie Voorstel-formaat):
   - **Uitvoerbaar** — aangevinkte actie-bullets (`label <naam>`, `jira link <A> <B>`,
     `jira transition <key> <naam> [resolutie]`) en waardetabellen voor `upsert-details`.
     Vink enkel aan wat mechanisch volgt uit een regel; twijfel hoort in blok twee.
   - **Beslissingen voor Kenzo** — niet aangevinkt, één vraag per stuk: EAG per initiatief; frigo
     met exact drie opties (verkennen · parkeren met herbekijkdatum · afsluiten met stopreden uit
     `A schema`).
   - **Info** — wat je enkel meldt (titel-drift, verouderde pijlertekst): geen actie.
   Structuur die `A apply` leest: de drie blokken als `#`-koppen (`# Uitvoerbaar`,
   `# Beslissingen voor Kenzo`, `# Info`), elk initiatief als `## <AI-key> — titel` met `- pagina:`
   en `- actie:`; in het beslissingsblok `- actie: skip` met **niet**-aangevinkte bullets (Kenzo
   vinkt aan en zet de actie om), in het info-blok enkel gewone bullets zonder `##`.
   Toon het pad en de tellingen per ernst. **Stop hier tot Kenzo "ok" zegt.**
5. **Uitvoeren**, na "ok":
   - `A apply --proposal $RUN/groom.md` — droogloop, toon het verslag.
   - `A apply --proposal $RUN/groom.md --apply`. Exit 3 = write-mode `dry-run`; melden en stoppen.
   - `A state set last_groom <YYYY-MM-DD>`.
   - Verslag: wat gedaan, wat geweigerd, wat bewust blijft staan.

## Kwartaal

Met argument `kwartaal`: zelfde stappen, plus

- het frigo-blok is **verplicht volledig beantwoord** vóór stap 5 — is er één initiatief zonder
  keuze, dan apply je niet en zeg je welke openstaan;
- afsluiten gebeurt via een aangevinkte `jira transition`-bullet met resolutie én een
  `stopreden`-rij in de waardetabel; zonder stopreden weigert de validatie het later alsnog;
- meld aan het eind hoeveel initiatieven verkend, geparkeerd en afgesloten werden — invoer voor
  `aiec-rapport kwartaal`.

## Grenzen

- Geen mutatie buiten `A apply`. Nooit rechtstreeks naar Confluence of Jira via MCP.
- Nooit automatisch sluiten, nooit een transitie aanvinken die Kenzo niet gevraagd heeft.
- Regels en drempels (frigo-dagen) niet hier herhalen: ze staan in het schema en de config.
