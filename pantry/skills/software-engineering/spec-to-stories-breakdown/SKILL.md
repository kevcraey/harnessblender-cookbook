---
name: spec-to-stories-breakdown
description: maak een breakdown van een spec naar user stories. Gebruik wanneer een spec klaar is voor implementatieplanning.
---

# Spec To Stories Breakdown

Splits een spec in user stories die samen, stap per stap, de spec opleveren. Elke story = verticale slice met observeerbare of testbare wijziging. Stories bevatten geen implementatiedetails, enkel functionele specificaties.

## Principes voor de split

- **Verticale slice, geen laag.** Elke story raakt alle nodige lagen om iets demobaar of testbaar af te leveren. Geen "schema-only" of "service-only" stories.
- **Observeerbaar of testbaar.** Voorbereidend werk (formule vastleggen, losse service zonder gebruik) is geen slice op zich — fuseer met de slice die het gebruikt.
- **Tracer bullet eerst.** Eerste slice = kleinste pad door alle lagen. Aspecten die niet strikt nodig zijn voor dat minimale pad zijn aparte slices erbovenop.
- **Tijdelijke deviatie van de spec mag**, als de split daarmee beter wordt (tijdelijke identity, stub, no-op). Markeer expliciet welke slice de deviatie wegneemt.
- **Scope-grens per story is glashelder.** Verwijs naar spec-secties; geen duplicatie van harde requirements.
- **WAT, niet HOE.** Story beschrijft observeerbaar functioneel gedrag. Geen architectuur, datamodellen, library-/framework-keuzes, endpoint- of klassenamen. Technische details uit spec enkel overnemen als ze functioneel waarneembaar zijn (extern contract, zichtbaar gedrag). Anders weglaten of als open vraag markeren.

## Workflow

### 1. spec lezen

Lees de spec volledig.

### 2. Split voorstellen

Graph met stories met afhankelijkheden tussen stories. Bij elke story: titel, observeerbaar gedrag.

### 3. HITL validatie

Iterate met user tot akkoord. Gebruik de 

### 4. Stories schrijven (parallel)

Per story: dispatch sub-agent `user-story-writer`. Geef mee: nummer, titel, spec-pad, scope IN, scope OUT (met verwijzing naar slice die het oppakt), eventuele tijdelijke deviatie, blocked-by, observeerbaar/testbaar resultaat, output-pad `tmp/slice-<N>-user-story.md`.

### 5. Validatie (parallel)

Drie criteria om een onafhankelijke agent op te laten reviewen:

- Is de scope-grens tussen de stories? Geen overlap, geen ambiguïteit.
  - Kan je zonder de andere stories te lezen afleiden welk gedrag wel/niet in de story valt?
  - Claimen meerdere stories hetzelfde gedrag? Geen subtiele overlap?
- Is de volledige spec, in al zijn aspecten gedekt of expliciet uitgesteld?
- Is er scope toegevoegd aan de stories? Geen scope-creep; enkel ok als expliciet gemarkeerd.

### 6. Fixes toepassen

Targeted edits op basis van de drie reviews. Geen volledige herschrijving.

### 7. Resultaat

Toon de finale lijst stories (paden + summaries). Verdere stappen (publicatie, conversie) vallen buiten deze skill.

## Output

N markdown-bestanden in `tmp/<spec omschrijving>/slice-<N>-user-story.md`.
