---
name: refine-user-story
description: Verfijnt een user story door iteratieve analyse vanuit verschillende expert-rollen (Tech Lead, QA, UX, PO). Gebruikt gespecialiseerde sub-agenten om kritische vragen te stellen en de kwaliteit te verhogen.
---

# Refine User Story

Verfijn een user story via een gelaagd proces waarbij experts (Tech Lead, QA, UX, PO) kritisch naar de ticket kijken.

## Workflow

### 1. Input Verzamelen

Verzamel zelf de relevante context (jira-ticket, gerelateerde bestanden/code) in `tmp/{YYYY-MM-DD}-{ticket}-context.md`.

### 2. Iteratieve Verfijning (Sub-agents)

Dit proces kan meerdere iteraties doorlopen. Start met "Ronde 1".

> [!IMPORTANT]
> **Context Reset**: Start elke iteratie (en sub-agent) met een schone lei (nieuwe sessie). Gebruik **alleen** de informatie uit de opgeslagen bestanden als input. Vertrouw niet op eerdere conversatiegeschiedenis.

#### 2.1 Expert Analyse (Ronde X)

    - Activeer voor elke rol (`references/rol-{rol}.md`) een "sub-agent" sessie.
    - Geef elke sub-agent als input:
        - De verzamelde context.
        - De specifieke rol-definitie: `references/rol-{rol}.md`.
        - (Indien > iteratie 1) Lees het vorige rapport `tmp/{YYYY-MM-DD}-{ticket}-refinement-ronde-{X-1}.md` en de antwoorden van de gebruiker daarop.
    - Opdracht per sub-agent:
        - Geef een score op basis van de parameters in je rol-definitie.
        - Identificeer de top 3 kritische vragen vanuit jouw expertise.
        - Geef feedback op de huidige staat.

#### 2.2. Rapport Genereren

    - Verzamel scores en vragen van alle experts.
    - Schrijf een geconsolideerd rapport naar `tmp/{YYYY-MM-DD}-{ticket}-refinement-ronde-{X}.md`.
    - Structuur van het rapport:
        - **Samenvatting Scores**: Tabel met scores per rol.
        - **Expert Feedback**: Per rol hun feedback en scores.
        - **Vragen aan Gebruiker**: Lijst met alle vragen waarop antwoord nodig is.

#### 2.3. Gebruiker Interactie

    - Toon het rapport aan de gebruiker en geef de gemiddelde score van alle experts.
    - Vraag of de gebruiker wil refinen of finaliseren.
      - Refinen:
        - Verhoog X (Ronde X+1)
        - Vraag om alle vragen te beantwoorden
        - Na de go van de gebruiker ga terug naar stap 2.1
      - Finaliseren:  ga verder naar stap 3

### 3. Finaliseren

- Hernoem het laatste rapport (inclusief antwoorden) naar `tmp/{YYYY-MM-DD}-{ticket}-refinement.md`.
- Schrijf de user story uit via de `write-user-story` skill.
