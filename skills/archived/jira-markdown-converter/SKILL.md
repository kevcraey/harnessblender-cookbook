---
name: jira-markdown-converter
description: Bidirectionele conversie tussen Markdown en Atlassian Jira wiki. Gebruik deze skill voor jira tickets updaten vanuit markdown bestanden en bestaande jira tickets converteren naar markdown.
---

# Jira Markdown Converter

Converteer efficiënt tussen Markdown en Jira wiki markup.

## Workflow

### 1. Automatische Conversie

Gebruik de bijgeleverde python scripts voor de transformatie.

- **Markdown → Jira**: `python3 ./assets/to_jira.py source.md > output.jira`
- **Jira → Markdown**: `python3 ./assets/from_jira.py source.jira > output.md`

> [!CAUTION]
> **Script Fouten**: Als een script faalt, stop dan NIET. Val terug op een handmatige conversie regel-voor-regel op basis van de `references/guidelines.md` tabel.

### 2. Validatie & Correctie (Agent Actie)

Jira's parser is kwetsbaar. Voer **altijd** deze controles uit op de output:

1. **Scan op Lijst-Crashes**: Zoek naar regels die beginnen met `* *`, `* _`, `# *` of `# _`.
    - *Actie*: Voeg tekst (zoals "Note:") of een extra spatie toe tussen de bullet en de opmaak.
    - *Fout*: `* *Vet*`
    - *Correct*: `* Vet` of `* Note: *Vet*`
2. **Scan op Headers**:
    - *Actie*: Verzeker dat `h1.`, `h2.`, etc. aan het begin van de regel staan.
    - *Actie*: Vervang 'fake headers' (vetgedrukte regels) door echte headers (`h3.`).
3. **Scan op Codeblokken**:
    - *Actie*: Verzeker dat `{code}` blokken correct gesloten zijn.
    - *Actie*: Vervang `{code:gherkin}` door `{code}` of `{code:java}`.

### 3. Referentie Regels

Raadpleeg **altijd** `references/guidelines.md` voor complexe gevallen zoals tabellen en geneste lijsten.

## Referenties

### Snelle Referentie

| Feature | Markdown | Jira |
| :--- | :--- | :--- |
| **Koptekst** | `# Titel` | `h1. Titel` |
| **Vet** | `**tekst**` | `*tekst*` |
| **Cursief** | `*tekst*` | `_tekst_` |
| **Code** | `` `code` `` | `{{code}}` |
| **Link** | `[tekst](url)` | `[tekst|url]` |

> [!WARNING]
> **Kritieke Beperkingen**
>
> - **Lijst Opmaak**: Begin een bullet point nooit direct met vet/cursief teken (`*` / `_`).
> - **Escaping**: Accolades `{}` in platte tekst MOETEN ge-escaped worden: `\{ \}`.
> - **Tabellen**: Gebruik `||` voor headers. Code blocks (`{code}`) werken NIET in cellen; gebruik `{{inline}}`.
