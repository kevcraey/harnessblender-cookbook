---
name: pickup
description: Pik het werk op uit een handoff-document (geschreven door /handoff). Zonder argument wordt het meest recente handoff-document in tmp/handoff/ genomen.
argument-hint: "[pad naar handoff-document, optioneel]"
---

Pik het werk op dat een vorige sessie via `/handoff` heeft klaargezet.

1. **Vind het document.**
   - Argument meegegeven → gebruik dat pad.
   - Geen argument → neem het meest recent gewijzigde `.md`-bestand in `tmp/handoff/` (projectroot). Staat daar niets: meld dat en stop.
   - Meerdere recente kandidaten (< 1 dag verschil) → toon de lijst en vraag welke.
2. **Lees het document volledig**, plus de artefacten waarnaar het verwijst (PRD, spec plan, ADR, specs) — die bevatten de details die het handoff-document bewust niet dupliceert.
3. **Verifieer de context** vóór je werkt: klopt de vermelde branch/worktree met de huidige `git status`? Zo niet: eerst rechtzetten of aan de gebruiker melden, niet blind verder werken.
4. **Voer uit** wat het document als doel van deze sessie beschrijft, met de daarin aanbevolen skills. Vat eerst in 2-3 zinnen samen wat je gaat doen, zodat de gebruiker kan bijsturen.
5. **Na afronding:** verplaats het opgepikte document naar `tmp/handoff/done/` zodat een volgende `/pickup` niet hetzelfde werk nogmaals oppakt.
