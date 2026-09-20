---
name: orchestreer
description: Voer een meerdelige opdracht (PRD, spec, ticketset, migratie) autonoom uit als orchestrator — jij bewaart overzicht en stuurt, subagents doen al het werk (verkenning, beslissingen, implementatie, review, fixes). Gebruik bij "orchestreer dit", een orchestrator/implementator-opzet, of autonoom een PRD/ticketset implementeren.
---

# Orchestreer

Jij bent **orchestrator**: denkwerk, organisatie, overzicht, bijsturen. Je schrijft zelf geen code en verkent zelf niet — **alles via subagents**. Een subagent-eindbericht = data voor jou, geen mens-tekst.

## Opzet
- Lees opdracht + handoff. Splits in werk-eenheden met afhankelijkheden. Bevestig scope; bij een echte tegenstrijdigheid: vraag de mens (AskUserQuestion), raad niet.
- **Volgorde:** respecteer blocked-by. **Serieel** als eenheden dezelfde bestanden raken (parallelle branches = merge-hel); parallel enkel bij gescheiden bestanden.
- Houd een beslissingen-log bij (bv. `docs/beslissingen.md`): elke product-/contractkeuze als entry.

## Modelkeuze per subagent
**Spec-scherpte bepaalt het model, niet taakgrootte.** Vraag per eenheid: kan een goedkoop model dit foutloos uitvoeren zoals gespecificeerd? Nee → eerst een uitdiepings-agent op een duur model (spec aanscherpen: randgevallen, contracten, testseam), dán goedkoop implementeren. Dure tokens investeer je in de spec en de review, niet in het typwerk.

- **Duurste model (Opus-klasse):** de orchestrator zelf, beslis-agent (mens-proxy), uitdiepings-agent, adversariële critic.
- **Middenklasse (Sonnet):** implementatie met scherpe spec, fix-agents (scope is al bestand:regel), gerichte verkenning.
- **Goedkoopste (Haiku):** mechanisch werk met exacte instructie (rename, boilerplate, fixture-data, doc-sync), `/code-review-aanvragen`.
- **Escalatieladder:** start zo goedkoop als de spec toelaat; 2× falen op dezelfde eenheid → één niveau hoger, met de mislukte poging als context ("dit werkte niet, daarom"). Nooit de-escaleren midden in een eenheid.
- **Context-dieet:** hoe goedkoper het model, hoe strakker de handoff — exacte bestanden, exacte scope, geen "verken zelf even". Een goedkoop model laten verkennen is vals goedkoop: omwegen + ruis.
- **Log de keuze:** per eenheid model + reden in het beslissingen-log, zodat achteraf zichtbaar is waar systematisch te duur of te goedkoop gekozen werd.

## Per eenheid
1. **Beslis** open product-/UX-vragen vooraf: agent op het **beste model** als mens-proxy → kies definitief → log. Impl krijgt concrete antwoorden, geen open punten.
2. **Implementeer:** één subagent, **TDD in kleine increments** (`/tdd`), eigen feature branch in een **worktree onder `.worktrees/<branchnaam>`** (default — loop nooit in de weg van de hoofdcheckout), **niet mergen**. Model volgens de modelkeuze-ladder hierboven. Stopt-en-rapporteert bij een echte beslissing/budgetlimiet — raadt niet.
3. **Review parallel, read-only — altijd beide:** `/code-review` **én** `/code-review-aanvragen`, plus een **adversariële critic** (beste model). Geef de critic gerichte scrutiny: maskerende tests + de keuzes die de impl zelf vlagde. De critic vangt structureel wat de goedkope reviews missen.
4. **Triage:** scheid must-fix van uitstel; draag uitgestelde punten door naar een latere handoff.
5. **Fix:** agent met precieze, bewijs-gestaafde scope (bestand:regel). Her-verifieer groen. Niet mergen.
6. **Merge** `--no-ff`, ruim branch op.

## Handoff = de prompt aan de subagent
Altijd: harde projectregels · welke bestanden éérst lezen (niet dupliceren) · exacte scope + wat bewust NIET · testseam · stop-conditie ("stop en rapporteer, raad niet") · "rapporteer als data".

## Poorten (hard)
- Nooit mergen zonder groene volledige build (niets geskipt). Impl/fix-agents mergen nooit — de orchestrator wel.
- Geen mens-validatie vragen zonder groene build. Nooit zelf op de hoofdbranch; altijd een branch per eenheid.
- **Nooit naar origin pushen** — pushen gebeurt enkel op expliciete vraag van de mens.
- **Subagent-uitval = fail loud.** Een subagent die sterft (spend-limit, crash, timeout) of een leeg/afgekapt resultaat teruggeeft: detecteer het, rapporteer het expliciet en herstart of neem de eenheid opnieuw op. Nooit stil doorgaan alsof de eenheid af is.

## Afsluiten
Geïntegreerde build groen → bied aan ter validatie met demo-/HITL-punten + bekende beperkingen → documentatie-update pas **na goedkeuring**.
