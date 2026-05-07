---
name: sb-write-meeting-note
description: Generate a structured meeting note for the Obsidian vault from a parsed transcript, attendee list, and meeting context.
---

# Write Meeting Note

## Input

This skill expects the following context to be available in the conversation:

1. **Parsed transcript** (output from `sb-parse-whisper`)
2. **Aanwezigenlijst** with correct names as `[[wikilinks]]`
3. **Meeting context**: titel, datum (YYYY-MM-DD), doel/aanleiding
4. **Meeting note filename**: `YYYY-MM-DD-beschrijving.md` (determined by the agent)

## Vault Location

Write the meeting note to:
```
~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain/2-events/{filename}
```

## Template

Use the vault template `6-templates/template-01-meeting-minutes.md` as basis. The output must follow this structure:

### Frontmatter

```yaml
---
is-part-of:
  - "[[project-moc-naam]]"   # if meeting relates to a project
related-to:
  - "[[vorig-overleg]]"       # if this is a recurring meeting
  - "[[Person 1]]"
  - "[[Person 2]]"
tags:
  - meeting-minutes
  - type/event
  - type/meeting
timeline: "[[YYYY-MM-DD]]"
created: "[[YYYY-MM-DD]]"
source: "[[YYYY-MM-DD]]"
aliases:
last-review:
---
```

### Body

```markdown
# {Korte Titel}

## Aanwezigen
- [[Persoon 1]]
- [[Persoon 2]]
- [[Persoon 3]]

## Aanleiding overleg
{Waarom vindt dit overleg plaats? Wat is het doel?}

## Agenda
### {Topic 1 - afgeleid uit de transcript-inhoud}

{Topic-gebaseerd verslag. Beschrijf wat besproken werd, welke standpunten er waren, en wat de conclusie is. Interne bedenkingen en observaties van Kenzo mogen erbij.}

### {Topic 2}

{Idem}

## Acties
- {Actie 1 - wie, wat, wanneer indien bekend}
- {Actie 2}
```

## Stijlregels

- **Topic-gebaseerd**, niet speaker-gebaseerd (speaker diarization is onbetrouwbaar)
- **Voor eigen consumptie** (Kenzo): schrijf alsof je notities maakt voor jezelf
- **Interne bedenkingen** welkom: observaties, twijfels, strategische overwegingen mogen erin
- **Nederlands** (Vlaams register)
- **Geen AI-stijl**: vermijd opsommingstekens waar een korte paragraaf volstaat, geen overmatig gebruik van vetgedrukte tekst, geen "samenvattend" of "concluderend" taalgebruik
- Attributie van uitspraken aan specifieke personen **alleen** als dit duidelijk uit de inhoud blijkt (niet op basis van speaker labels)
- Beslissingen en concrete actiepunten in aparte secties
