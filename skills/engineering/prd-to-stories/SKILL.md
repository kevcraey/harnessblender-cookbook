---
name: prd-to-stories
description: Splits een PRD in user stories die elk een verticale slice zijn met observeerbare of testbare wijziging. Gebruik wanneer een PRD klaar is voor implementatieplanning.
---

# PRD to Stories

Splits een PRD in user stories die samen, stap per stap, de PRD opleveren. Elke story = verticale slice met observeerbare of testbare wijziging.

## Principes voor de split

- **Verticale slice, geen laag.** Elke story raakt alle nodige lagen om iets demobaar of testbaar af te leveren. Geen "schema-only" of "service-only" stories.
- **Observeerbaar of testbaar.** Voorbereidend werk (formule vastleggen, losse service zonder gebruik) is geen slice op zich — fuseer met de slice die het gebruikt.
- **Tracer bullet eerst.** Eerste slice = kleinste pad door alle lagen. Aspecten die niet strikt nodig zijn voor dat minimale pad zijn aparte slices erbovenop.
- **Tijdelijke deviatie van de PRD mag**, als de split daarmee beter wordt (tijdelijke identity, stub, no-op). Markeer expliciet welke slice de deviatie wegneemt.
- **Scope-grens per story is glashelder.** Verwijs naar PRD-secties; geen duplicatie van harde requirements.
- **WAT, niet HOE.** Story beschrijft observeerbaar functioneel gedrag. Geen architectuur, datamodellen, library-/framework-keuzes, endpoint- of klassenamen. Technische details uit PRD enkel overnemen als ze functioneel waarneembaar zijn (extern contract, zichtbaar gedrag). Anders weglaten of als open vraag markeren.

## Workflow

### 1. PRD lezen

Lees de PRD volledig.

### 2. Split voorstellen

Tabel per slice: titel, type (HITL/AFK), observeerbaar gedrag, blocked-by, eventuele tijdelijke deviatie.

### 3. HITL validatie

Iterate met user tot akkoord. Vraag minstens: granulariteit, blocked-by relaties, ontbrekende/overbodige slices, HITL/AFK-typering. Niet doorgaan zonder expliciet akkoord.

### 4. Stories schrijven (parallel)

Per slice: dispatch sub-agent `user-story-writer`. Geef mee: nummer, titel, PRD-pad, scope IN, scope OUT (met verwijzing naar slice die het oppakt), eventuele tijdelijke deviatie, blocked-by, observeerbaar/testbaar resultaat, output-pad `tmp/slice-<N>-user-story.md`.

### 5. Validatie (parallel)

Drie reviewer-agents:

- `story-scope-boundary-reviewer`: scope-grens duidelijk, geen overlap
- `story-scope-completeness-reviewer`: alle PRD-aspecten gedekt of expliciet uitgesteld
- `story-prd-alignment-reviewer`: geen scope-drift; tijdelijke deviaties enkel ok als expliciet gemarkeerd

### 6. Fixes toepassen

Targeted edits op basis van de drie reviews. Geen volledige herschrijving.

### 7. Resultaat

Toon de finale lijst stories (paden + summaries). Verdere stappen (publicatie, conversie) vallen buiten deze skill.

## Output

N markdown-bestanden in `tmp/slice-<N>-user-story.md`.
