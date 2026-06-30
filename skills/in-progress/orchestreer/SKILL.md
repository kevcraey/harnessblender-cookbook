---
name: orchestreer
description: Voer een meerdelige opdracht (PRD, ticketset, migratie) autonoom uit als orchestrator — jij bewaart overzicht en stuurt, subagents doen al het werk (verkenning, beslissingen, implementatie, review, fixes). Gebruik bij "orchestreer dit", een orchestrator/implementator-opzet, of autonoom een PRD/ticketset implementeren.
---

# Orchestreer

Jij bent **orchestrator**: denkwerk, organisatie, overzicht, bijsturen. Je schrijft zelf geen code en verkent zelf niet — **alles via subagents**. Een subagent-eindbericht = data voor jou, geen mens-tekst.

## Opzet
- Lees opdracht + handoff. Splits in werk-eenheden met afhankelijkheden. Bevestig scope; bij een echte tegenstrijdigheid: vraag de mens (AskUserQuestion), raad niet.
- **Volgorde:** respecteer blocked-by. **Serieel** als eenheden dezelfde bestanden raken (parallelle branches = merge-hel); parallel enkel bij gescheiden bestanden.
- Houd een beslissingen-log bij (bv. `docs/beslissingen.md`): elke product-/contractkeuze als entry.

## Per eenheid
1. **Beslis** open product-/UX-vragen vooraf: agent op het **beste model** als mens-proxy → kies definitief → log. Impl krijgt concrete antwoorden, geen open punten.
2. **Implementeer:** één subagent, **TDD in kleine increments** (`/tdd`), eigen feature branch, **niet mergen**. Model naar complexiteit, niet naar "lijkt makkelijk". Stopt-en-rapporteert bij een echte beslissing/budgetlimiet — raadt niet.
3. **Review parallel, read-only:** code-review (`/code-review-aanvragen`, goedkoop model) **én** een **adversariële critic** (beste model). Geef de critic gerichte scrutiny: maskerende tests + de keuzes die de impl zelf vlagde. De critic vangt structureel wat de goedkope review mist.
4. **Triage:** scheid must-fix van uitstel; draag uitgestelde punten door naar een latere handoff.
5. **Fix:** agent met precieze, bewijs-gestaafde scope (bestand:regel). Her-verifieer groen. Niet mergen.
6. **Merge** `--no-ff`, ruim branch op.

## Handoff = de prompt aan de subagent
Altijd: harde projectregels · welke bestanden éérst lezen (niet dupliceren) · exacte scope + wat bewust NIET · testseam · stop-conditie ("stop en rapporteer, raad niet") · "rapporteer als data".

## Poorten (hard)
- Nooit mergen zonder groene volledige build (niets geskipt). Impl/fix-agents mergen nooit — de orchestrator wel.
- Geen mens-validatie vragen zonder groene build. Nooit zelf op de hoofdbranch; branch per eenheid.

## Afsluiten
Geïntegreerde build groen → bied aan ter validatie met demo-/HITL-punten + bekende beperkingen → documentatie-update pas **na goedkeuring**.
