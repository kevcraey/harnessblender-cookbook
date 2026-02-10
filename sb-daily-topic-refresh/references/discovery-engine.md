# Discovery Engine

De discovery engine zoekt systematisch naar gerelateerde topics die nog niet (volledig) in de vault zitten.

## Kernprincipe

**Altijd suggesties.** De sectie "Verken verder" moet altijd verschijnen, zelfs als er geen directe kandidaten zijn. Gebruik fallback strategieën om altijd 3 suggesties te produceren.

## Two-Phase Architecture

### Phase 1: Primary Discovery (snel, direct)

Scan distance-1 connections en immediate gaps:

1. **Graph scan**: Parse `[[wikilinks]]` in note body + `related-to` frontmatter
2. **Broken links**: Detecteer `[[Non-existent]]` links als high-value kandidaten
3. **Stub detection**: Check of linked notes stubs zijn (<100 woorden OR `tag:status/stub` OR `frontmatter.stub: true`)
4. **Semantic gaps**: Extract key terms (capitalized, technical) die NIET als link bestaan

**Threshold**: Als <3 kandidaten → trigger Phase 2

### Phase 2: Fallback Discovery (breder, diverse strategieën)

Mix van strategieën om variatie te garanderen:

1. **Distance-2 exploration**: Volg links van distance-1 notes (circular reference protection)
2. **Domain matching**: Scan vault voor overlappende tags/categories
3. **Reasoning modes** (random select):
   - Prerequisites: "voor [topic] moet je eerst kennen..."
   - Extensions: "na [topic] komt logisch..."

**Ultimate fallback**: Als nog steeds <3, genereer generieke richtingen (gerelateerd domein, praktische toepassing, historische context)

## Scoring Logic

Elke kandidaat krijgt een score om de 3 beste te selecteren:

### Score Components

1. **Link type** (base score):
   - Broken link: 100 punten (hoogste prioriteit - user wil dit expliciet)
   - Stub note: 80 punten (incomplete content, hoge waarde)
   - Distance-1 complete note: 60 punten
   - Distance-2 note: 40 punten
   - Semantic gap: 50 punten
   - Generated suggestion: 20 punten

2. **Connection strength** (+0-20 punten):
   - Multiple references: +5 per extra reference (max +15)
   - In frontmatter `related-to`: +10
   - Domain/tag overlap: +5

3. **Recency penalty** (-0-30 punten):
   - Viewed in last 7 days: -30
   - Viewed in last 30 days: -15
   - Viewed in last 90 days: -5
   - Never viewed: +10

4. **Stub indicators** (+10-20 punten if stub):
   - Explicit `stub: true` frontmatter: +20
   - `status/stub` tag: +15
   - Word count <100: +10

### Diversity Filter

Na scoring, filter voor variatie:

- Maximum 1 broken link in top 3
- Maximum 2 uit dezelfde subcategory/tag
- Bij tie-break: prefer verschillende discovery methods (Phase 1 vs Phase 2)

### Final Selection

1. Sort candidates by total score (descending)
2. Apply diversity filter
3. Select top 3
4. If <3 after diversity filter, fall back to next highest scores

## Learning Value Generation

Voor elke geselecteerde kandidaat, genereer "waarom leren" text:

### Value Templates by Type

**Broken link** (user expliciet geïnteresseerd):
```
Je refereerde al naar [[{topic}]] - tijd om dit uit te werken
```

**Stub note** (incomplete kennis):
```
[[{topic}]] is nog een stub - verdiep je kennis hier
```

**Distance-1 connection** (direct gerelateerd):
```
[[{topic}]] is direct verbonden met {current_topic}
```

**Distance-2 exploration** (breder netwerk):
```
Via [[{intermediate}]] kom je bij [[{topic}]]
```

**Domain match** (thematisch):
```
[[{topic}]] deelt domein/tags met {current_topic}
```

**Prerequisite reasoning**:
```
Voor {current_topic} is kennis van [[{topic}]] nuttig
```

**Extension reasoning**:
```
Na {current_topic} is [[{topic}]] een logische volgende stap
```

**Generic fallback**:
```
Verken [[{topic}]] in relatie tot {domain/category}
```

### Context Integration

Voeg specifieke context toe waar mogelijk:
- Aantal broken links: "3x gerefereerd maar nog geen note"
- Stub details: "5 woorden, tagged status/stub"
- Connection path: "via [[Intermediate]] → [[Target]]"
- Domain: "ook #programming/functional"

## Edge Cases

### 1. Empty Vault / Isolated Note

**Problem**: Note heeft geen links, vault is leeg, of note is geïsoleerd

**Solution**:
- Check domain/category in frontmatter
- Genereer generieke suggesties op basis van domain:
  - Programming: "Design Patterns", "Testing", "Performance"
  - Science: "Research Methods", "Statistical Analysis", "Literature Review"
  - Generic: "Practical Applications", "Historical Context", "Related Fields"

### 2. All Connections Explored

**Problem**: Alle distance-1 en distance-2 notes zijn recent bekeken

**Solution**:
- Negeer recency penalty voor deze selectie
- Prioriteer oudste views (refresh knowledge)
- Of: genereer reasoning-based suggestions (prerequisites/extensions)

### 3. Circular References

**Problem**: Distance-2 scan kan terugverwijzen naar current note

**Solution**:
- Track visited notes in path: `current → intermediate → target`
- Skip if `target == current`
- Skip if `target` already in distance-1 set

### 4. Too Many Candidates

**Problem**: >20 broken links, >50 distance-1 connections

**Solution**:
- Pre-filter broken links: max 10 hoogste reference count
- Pre-filter distance-1: max 20 hoogste connection strength
- Distance-2: sample max 30 (random select from distance-1 links)

### 5. Non-existent Vault Paths

**Problem**: File paths in links bestaan niet (typo's, moved files)

**Solution**:
- Treat as broken links (high value)
- Note in learning value: "broken link - maak nieuwe note of fix reference"

### 6. Duplicate Candidates

**Problem**: Zelfde note via meerdere paths (broken link + distance-2)

**Solution**:
- Deduplicate by note title/path
- Keep highest scoring path
- Combine context info: "broken link + verbonden via [[X]]"

### 7. No Valid Markdown Notes

**Problem**: Links naar non-markdown files, external URLs, etc.

**Solution**:
- Filter out during graph scan: only `.md` files
- Externe links not considered for discovery
- Images/PDFs niet opnemen in kandidaten

### 8. Performance (Large Vaults)

**Problem**: Vault met >10,000 notes, Phase 2 te traag

**Solution**:
- Phase 1: altijd snel (alleen current note scannen)
- Phase 2: lazy execution (alleen als <3)
- Distance-2: sample max 30 intermediate notes
- Domain matching: filter op shared tags eerst (small set)
- Timeout: max 5 seconden totale discovery time
