---
name: analyze-ticket
description: Voert een multi-rol analyse uit op een ticket (bv. PASCAL-123). Gebruik wanneer een ticket geanalyseerd, verduidelijkt of beoordeeld moet worden vanuit Tech Lead, QA, Technical Writer, UX Engineer, Product Owner en User perspectief. Levert analysedocument met vragen, antwoorden, openstaande punten en kwaliteitsscore.
---

# Ticket begrijpen

## Rol

- [Tech Lead](../agents-roles/tech-lead.md)
- [QA Engineer](../agents-roles/qa.md)
- [Technical Writer](../agents-roles/technical-writer.md)
- [UX Engineer](../agents-roles/ux-engineer.md)
- [Product Owner](../agents-roles/product-owner.md)
- [User](../agents-roles/user.md)

## Doel

Uitvoeren van een analyse op een ticket.

## Input

`INIT.md`

- Een ticketnummer (bijvoorbeeld `PASCAL-123`)
- De documentatie van de toepassing (optioneel)
- Alle markdown-bestanden die het ticketnummer bevatten (bijvoorbeeld `PASCAL-123` → `foobar-PASCAL-123-blabla.md`).

## Plan van aanpak

- Laat het ticket analyseren vanuit alle verschillende rollen.
  - De tech lead die een implementatieplan zal moeten opmaken
  - De QA engineer die een testplan zal moeten opmaken
  - De tech writer die een documentatieplan zal moeten opmaken
  - De UX engineer die een designplan zal moeten opmaken
  - De product owner die het een plaats op de roadmap zal moeten geven
  - De gebruiker die de feature zal gebruiken
- Laat elk van de verschillende rollen mij vragen stellen over het ticket tot het volledig duidelijk is vanuit hun expertise.
  
Volledig duidelijk betekent:

- Er zijn geen vage beschrijvingen meer
- Er zijn geen inconsitenties in het ticket
- Er zijn simpele verduidelijkende voorbeelden
- Gebruikte terminologie is in lijn met de documentatie (begrippenlijst)

- Zet alle rolen samen in een gesimuleerde meeting en laat ze:
  - 3 redenen oplijsten waarom het ticket goed is
  - 3 redenen oplijsten waarom het ticket niet goed is
  - een pre-mortem analyse doen: Geef de 3 meest waarschijnlijke redenen waarom we deze feature over 6 maanden moeten terugdraaien of refactoren.

## Beperkingen

- Je voegt geen nieuwe functionaliteit toe en verzint niets: alles wat je documenteert moet aantoonbaar volgen uit de user story of uit de geïmplementeerde werking.
  
## Output

- Een volledig analysedocument in markdownformaat van het ticket in `tmp/{ticketnummer}-analysis.md`.
- vragen en antwoorden
- resultaten van de analyse
- lijst met openstaande vragen
- Score op 10 van het ticket (1: volledig onduidelijk en nog onimplementeerbaar, 10: zo duidelijk dat het perfect geimplementeerd kan worden zonder enige verdere input)
