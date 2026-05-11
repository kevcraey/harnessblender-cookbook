---
name: sb-summarize-for-daily
description: Write an ultra-short meeting summary for the daily note. Output is a markdown block that replaces existing content under the meeting header.
---

# Summarize Meeting for Daily Note

## Input

This skill expects:

1. **Parsed transcript** or **completed meeting note** (from `sb-write-meeting-note`)
2. **Meeting note filename** (for the link)
3. **Meeting header** in the daily note (the `##` heading to place content under)

## Output Format

The output is a markdown block to be placed directly under the meeting `##` header in the daily note. Structure:

```markdown
Aanwezigen: [[Persoon 1]], [[Persoon 2]], [[Persoon 3]]

{Een scherpe zin die het doel of de kern van de meeting samenvat. Deze eerste paragraaf wordt opgepikt door project-MOC dataview-queries als "recent activity" — maak hem zelfstandig leesbaar.}

- {Key takeaway 1}
- {Key takeaway 2}
- {Key takeaway 3 — maximaal 5 bullets}

Verslag: [[YYYY-MM-DD-beschrijving]]
```

## Regels

- **Ultra-kort**: doel + maximaal 5 bullets. Dit is een geheugensteuntje, geen verslag.
- **Geen acties**: die staan in de meeting note
- **Geen details**: enkel wat nodig is om bij herlezen te weten "ah ja, dat was die meeting"
- **Eerste paragraaf is kritiek**: dit wordt de one-liner in project-MOC "Recent Activity" via dataview. Moet zelfstandig leesbaar zijn zonder de bullets.
- **Aanwezigen**: als `[[wikilinks]]`, komma-gescheiden op een lijn
- **Link naar verslag**: altijd als laatste regel

## Plaatsing in Daily Note

De daily note staat op:
```
~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain/5-journal/YYYY/MM/DD/YYYY-MM-DD.md
```

Zoek de `##` header die bij deze meeting hoort. Vervang alle inhoud tussen deze header en de volgende `##` header (of het einde van de handmatige inhoud, voor de `## Logs` sectie) door het output-blok.

> [!IMPORTANT]
> De bestaande inhoud gaat niet verloren — die zit in het volledige verslag in `2-events/`. De daily note is puur een geheugensteuntje met een link.
