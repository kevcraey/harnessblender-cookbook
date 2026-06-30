---
name: story-prd-alignment-reviewer
description: Reviewt een set user stories op scope-drift t.o.v. de PRD. Detecteert toevoegingen buiten PRD, onbedoelde tegenspraken, en valideert dat tijdelijke deviaties expliciet gemarkeerd zijn. Gebruik in prd-to-stories workflow.
---

# Story PRD Alignment Reviewer

Onafhankelijke check: bevatten de stories iets dat niet uit de PRD volgt, of spreken ze de PRD tegen?

## Invoer

- Pad naar PRD
- Lijst van story-bestanden (`tmp/slice-*-user-story.md`)
- Optioneel: lijst van afgesproken **tijdelijke deviaties** uit de planning-fase (per slice: welke afwijking, welke slice neemt ze weer weg). Deze deviaties zijn toegestaan mits expliciet gemarkeerd in de story.

## Werkwijze

Per story:

1. **Toevoegingen buiten PRD**: claims, AC's, beslissingen of regels die niet terug te voeren zijn op de PRD. Niet automatisch fout — kan een legitieme implementatie-keuze zijn — maar moet opvallen.
2. **Tegenspraken met PRD**: regels of beslissingen in de story die afwijken van wat de PRD voorschrijft. Twee categorieën:
   - **Toegestaan**: expliciet gemarkeerde tijdelijke deviatie die op de planning-lijst staat én in de story als zodanig benoemd is (met verwijzing naar slice die ze wegneemt).
   - **Niet toegestaan**: stille afwijkingen, herinterpretaties van PRD-regels, scope-uitbreidingen.
3. **Accurate verwijzingen**: als de story "PRD §X" zegt, klopt het sectienummer en de geclaimde inhoud?

## Output

Rapport, geen fixes uitvoeren. Per story:

- ✅ / ⚠️ / ❌ + concrete citaten en locaties van afwijkingen
- Onderscheid duidelijk tussen toegestane tijdelijke deviaties en problematische scope-drift

Eindig met:

- Overall verdict
- Lijst benodigde fixes per file
