# Topic selectie

## Criteria

Een note komt in aanmerking als refresh-topic als:

1. **Substantieel** — meer dan alleen frontmatter en titel (minimaal 3 paragrafen of inhoudelijke bullets)
2. **Type concept** — `type/concept` tag, of inhoudelijk een kennistopic (niet een taak, event, of project)
3. **Niet vandaag aangemaakt** — minimaal 1 dag oud (`created` veld in frontmatter)

## Prioriteit

| Prioriteit | Regel |
|------------|-------|
| 1 | Notes die het langst niet bekeken zijn (oudste `modified` datum) |
| 2 | Notes met veel stub-links (gaten die uitgewerkt kunnen worden) |
| 3 | Notes gerelateerd aan recent gestagede items (thematische aansluiting) |

## Uitsluiting

- Notes die in de afgelopen 3 dagen al als refresh zijn aangeboden
- Pure MOC/index notes (bevatten alleen links, geen uitleg)
- Notes met tag `type/task`, `type/event`, of `type/people`
