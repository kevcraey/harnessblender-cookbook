---
name: sb-screen-decisions
user-invocable: false
description: |
  Screen verwerkte input (meeting note, daily-note-sectie, losse note) op registerwaardige
  beslissingen en leg bevestigde kandidaten vast als decision note in 2-events.
  Vaste stap in elke input-verwerking.
---

# Beslissingsscreening

## Criterium: registerwaardig

Een beslissing is registerwaardig als ze **niet obvious** is (verplichte poort) én daarnaast minstens één van beide:

- **grote impact**, of
- **moeilijk omkeerbaar**

Obvious beslissingen vallen altijd af. Bij twijfel over impact/omkeerbaarheid: wél voorstellen — een vals positief kost de gebruiker één bevestigingsklik.

## Input

De verwerkte tekst (meeting note, daily-note-sectie of losse note), plus indien bekend het project (`[[project-moc-...]]`) waar de input bij hoort.

## Workflow

1. **Kandidaten zoeken**: alleen expliciet genomen beslissingen in de tekst. Voornemens, acties, open vragen en opties zijn géén kandidaten.
2. **Toets** elke kandidaat aan het criterium hierboven.
3. **Leg alle kandidaten in bulk voor**: per kandidaat de beslissing als zin + één contextzin. De gebruiker vinkt aan/af in één keer. **Nooit autonoom aanmaken.**
4. Elke bevestigde kandidaat wordt een decision note.

## Decision note

- **Locatie/naam**: `2-events/YYYY-MM-DD-decision-korte-slug.md` — datum = beslisdatum
- **Template**: `6-templates/template-decision.md`
- **Frontmatter**: tag `type/decision`, `timeline: "[[YYYY-MM-DD]]"`, `is-part-of` naar de project-MOC (indien van toepassing)
- **H1** = de beslissing als één zin
- **Eerste paragraaf** = 1–2 zinnen context (waarom, met wie), betrokkenen als `[[wikilinks]]` naar bestaande people-notes
- Niets meer dan dat — geen ADR-secties, nooit context verzinnen die niet in de input zat
- Geen rode links

Er bestaat geen aparte registernote: het beslissingenregister ís de `#type/decision`-query op de project-MOC.
