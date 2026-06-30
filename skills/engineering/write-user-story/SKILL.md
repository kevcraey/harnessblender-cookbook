---
name: write-user-story
description: "Genereert of herschrijft user stories. Gebruik deze skill wanneer je een functionele specificatie moet uitschrijven in user story formaat."
---

# Write User Story

Genereer gestandaardiseerde user stories van hoge kwaliteit.

## Workflow

### 1. Input Analyseren

Haal alle beschikbare informatie op. Gebruik hiervoor de **`gather-ticket-context`** skill. Deze zoekt naar het jira-ticket en gerelateerde bestanden.

(Optioneel) Vraag de gebruiker of hij nog extra informatie heeft die je moet meenemen.
(Optioneel) Vraag de gebruiker of hij de user story eerst wil refinen. Gebruik hiervoor de `refine-user-story` skill.

### 2. Structuur Toepassen

Gebruik het sjabloon in `assets/template.md` waarin de richtlijnen als commentaar zijn opgenomen.

### 3. Inhoud Opstellen

Schrijf de secties op basis van beschikbare informatie.

- *Tip*: Als informatie ontbreekt voor een sectie (bv. Testcases), markeer dit expliciet als "Nader te bepalen" of vraag de gebruiker, hallucineer geen details.

### 4. Kwaliteitscontrole

- Controleer of de output exact overeenkomt met `assets/template.md` (kopteksten, bullet stijlen, naamgevingsconventies).
- Controleer of er informatie in de user story staat die niet voort komt uit de verzamelde input-bestanden, JIRA-ticket of input van de gebruiker. Hallucinaties gedetecteerd. Verwijder die informatie en begin opnieuw. Gebruik hiervoor een sub-agent zonder context.

### 5. Output opslaan

- Schrijf de user story altijd uit in een bestand met de naam `tmp/{ticketnummer -user-story.md`. Als er nog geen ticketnummer is, stel voor om eerst een jira-ticket aan te maken. Gebruik daarna het ticketnummer om de user story op te slaan.
- Stel voor om het resultaat weg te schrijven naar het jira-ticket, gebruik daarbij de `jira-formatting` skill om markdown betrouwbaar om te zetten naar Jira-syntax.

## Referenties

- **Sjabloon**: Zie `assets/template.md` voor de structuur en gedetailleerde richtlijnen.
- **Voorbeelden**: Zie `examples/` voor voorbeelden van user stories.
