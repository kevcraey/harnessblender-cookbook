---
name: create-changelog
description: Schrijft een heldere, beknopte changelogentry voor eindgebruikers op basis van een ticket, commits of notities. Gebruik wanneer een release note of changelog-entry nodig is voor een feature, verbetering of fix. Output gestructureerd met titel, beschrijving en optionele details.
---

# Changelog voor feature

## Rol

zie `agents-roles/technical-writer`

## Doel

Schrijf een heldere, beknopte en waardevolle changelogentry op basis van technische input (zoals git-commits, Jira-tickets of ruwe notities).

## Input

`INIT.md`

- Een ticketnummer (bijvoorbeeld `PASCAL-123`)
- De documentatie van de toepassing (optioneel)
- De codewijzigingen door de user story (optioneel)
- Alle markdown-bestanden die het ticketnummer bevatten (bijvoorbeeld `PASCAL-123` → `foobar-PASCAL-123-blabla.md`).

## Richtlijnen voor stijl en toon

- Focus op de 'Waarom': Begin niet alleen met wat er is veranderd, maar leg uit welk probleem dit oplost voor de gebruiker.
- Publieksgericht: Schrijf voor de eindgebruiker, niet voor de ontwikkelaar (tenzij ik specifiek om een technische changelog vraag). Vermijd intern jargon (zoals "Refactor backend service X" -> "Verbeterde snelheid bij het laden van data").

## Formaat

Gebruik Markdown voor de opmaak. Volg deze structuur:

Titel: Een korte, krachtige samenvatting (max 6 woorden) [NIEUW], [VERBETERING], of [FIX].

Beschrijving: één of twee zinnen die de waarde uitleggen.

(Optioneel) Details: een opsomming als er specifieke details zijn die belangrijk zijn.

## Voorbeeld

```markdown
Robuuster beheer stalconfiguraties via codes [VERBETERING]

Configureer diersoorten en staltypes nu op basis van stabiele, unieke codes in plaats van veranderlijke omschrijvingen om de robuustheid van het systeem te vergroten.

- Voorkomt dat tekstuele correcties (zoals typefouten) leiden tot onbedoelde configuratiewijzigingen.
- Verbetert de validatie en foutmeldingen bij het opladen van nieuwe configuratiebestanden.
- Maakt het vergelijken van versies (delta's) overzichtelijker door te focussen op technische codes.
```

## Output

- Schrijf uw output in `tmp/{ticketnummer}-changelog.md`.
