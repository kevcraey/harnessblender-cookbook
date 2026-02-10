---
name: sb-daily-topic-refresh
description: Use when generating a morning report or when the user asks to refresh a previously studied topic. Produces a teaching-style review of an existing vault topic with new information added.
---

# Daily Topic Refresh

Genereer een "herhalingssectie" voor het ochtendrapport door een eerder bestudeerd topic opnieuw uit te leggen en te verdiepen.

## Kernprincipe

**Herleer, niet herlijst.** Geef een uitleg alsof je het topic opnieuw aanleert — niet een opsomming van wat de gebruiker al weet. Dit activeert recall en versterkt begrip.

## Workflow

### 1. Selecteer topic

Scan de vault voor notes met substantiële inhoud (niet enkel frontmatter):

```
1-notes/*.md
9-staging/1-notes/*.md
```

Selectieregels — zie `references/topic-selection.md`

### 2. Lees de bestaande note & Start discovery

Lees de volledige note. Identificeer:
- **Kernconcepten** die de gebruiker al begrijpt
- **Analogieën** die de gebruiker zelf heeft opgeschreven
- **Gaten** — gerelateerde concepten die nog stub-notes zijn of ontbreken
- **Verbindingen** — `related-to` en `[[links]]` in frontmatter en body

**NIEUW: Start discovery engine** (zie `references/discovery-engine.md`):
1. Verzamel kandidaten via primary discovery (distance-1, broken links, semantic gaps)
2. Check count: <3? → trigger fallback discovery (distance-2, domain, reasoning)
3. Score alle kandidaten volgens scoring matrix
4. Select top 3 met diversity filter
5. Genereer learning values voor elke kandidaat
6. Als nog steeds <3: gebruik generieke fallback suggesties

**Timing**: Discovery draait parallel met note analysis (non-blocking).

### 3. Genereer de refresh

Structuur — strikt aanhouden:

```markdown
## Refresh: {Topic naam}

### Herhaling
[Leg het topic uit alsof je het opnieuw aanleert. Gebruik de concepten
en analogieën uit de bestaande note, maar formuleer ze in je eigen
woorden als een coherente uitleg. NIET opsommen als bullets van
"wat je al wist". Schrijf het als een korte les.]

### Verdieping: {specifiek subtopic}
[Eén concreet nieuw inzicht dat voortbouwt op de bestaande kennis.
Moet specifiek zijn — formules, concrete voorbeelden, mechanismen.
Geen vage algemeenheden zoals "het is een adaptief filtersysteem".]

### Connecties
- Sluit aan bij [[bestaande-note]] — {korte uitleg waarom}
- Gat gevonden: [[stub-note]] zou uitgewerkt kunnen worden

### Verken verder
1. [[Kandidaat 1]] - begrijp [learning value 1]
2. [[Kandidaat 2]] - begrijp [learning value 2]
3. [[Kandidaat 3]] - begrijp [learning value 3]

### Verder uitdiepen (optioneel)
- {Suggestie 1}: korte omschrijving
- {Suggestie 2}: korte omschrijving
```

## Anti-patronen

| Fout | Correct |
|------|---------|
| "Wat je al wist: Attention gebruikt Q, K, V..." | Leg uit hoe Q, K, V werken alsof je het aanleert |
| Vage verdieping: "het is een krachtig mechanisme" | Concrete verdieping: de scaling factor $\frac{1}{\sqrt{d_k}}$ voorkomt dat softmax satureerd |
| Geen vault-links | Altijd connecties leggen met `[[bestaande-notes]]` |
| Generieke suggesties | Suggesties gebaseerd op gaten in de vault (stub-notes, ontbrekende links) |
| "Verken verder" sectie ontbreekt | **ALTIJD** tonen, zelfs met generieke fallbacks |
| Suggestie zonder learning value | Elk item: `[[Topic]] - begrijp [specifieke leerwaarde]` |
| Alle 3 suggesties zelfde type | Diversity filter: mix van stubs, broken links, reasoning |

## Taal

Output altijd in het Nederlands, tenzij anders gevraagd. Technische termen mogen in het Engels blijven.
