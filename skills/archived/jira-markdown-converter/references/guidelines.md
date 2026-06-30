# Jira Formatting Gedetailleerde Richtlijnen

Dit referentiedocument biedt een uitgebreide mapping en voorbeelden voor bidirectionele Markdown ↔ Jira wiki markup conversie.

## Vergelijkingstabel

| Feature | Markdown | Jira Wiki Markup | Opmerkingen |
| :--- | :--- | :--- | :--- |
| **Koptekst 1** | `# Titel` | `h1. Titel` | Moet aan begin van regel staan |
| **Koptekst 2** | `## Subtitel` | `h2. Subtitel` | |
| **Vet** | `**tekst**` | `*tekst*` | Enkele asterisk in Jira |
| **Cursief** | `*tekst*` | `_tekst_` | Underscores in Jira |
| **Lijst** | `- item` | `* item` | |
| **Geneste Lijst** | `- sub` | `** sub` | |
| **Genummerde Lijst** | `1. item` | `# item` | Of `1. item` maar `#` is robuuster |
| **Link** | `[tekst](url)` | `[tekst\|url]` | Pipe als scheidingsteken |
| **Inline Code** | `` `code` `` | `{{code}}` | Dubbele accolades |
| **Code Blok** | ` ``` ` | `{code}...{code}` | |
| **Escaping** | `{braces}` | `\{braces\}` | |

## Uitgebreide Voorbeelden

### Complexe Lijsten

**Markdown:**

```markdown
1. Eerste
   - Genest A
   - Genest B
2. Tweede
```

**Jira:**

```text
# Eerste
** Genest A
** Genest B
# Tweede
```

### Tabel met Code

**Markdown:**

```markdown
| Commando | Gebruik |
| --- | --- |
| `ls` | Bestanden oplijsten |
```

**Jira:**

```text
|| Commando || Gebruik ||
| {{ls}} | Bestanden oplijsten |
```

> [!WARNING]
> **Bekende Rendering Bugs**
>
> **1. Vet/Cursief na Bullets**
> Jira's parser faalt (crasht/verbergt tekst) wanneer een lijstitem direct begint met opmaak.
>
> * ❌ `* *Vet*`
> * ✅ `* Vet`
>
> **2. Code Blokken in Tabellen**
> Jira tabellen ondersteunen GEEN `{code}` blokken (multiline) binnen cellen.
>
> * Gebruik `{{inline code}}` voor kleine fragmenten.
> * Voor grote blokken: Link naar een losse snippet of zet het blok onder de tabel.
