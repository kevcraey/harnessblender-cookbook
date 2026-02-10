# Daily Topic Refresh - Discovery Engine Enhancement

**Date**: 2026-02-10
**Status**: Design Complete
**Skill**: sb-daily-topic-refresh

## Overview

Enhance the daily topic refresh skill met een discovery engine die niet alleen bestaande topics refresht, maar ook systematisch gerelateerde onderwerpen suggereert die nog niet (volledig) in de vault zitten. Dit creëert een laagdrempelige trigger voor kennisnetwerk expansie.

## User Need

"Ik zou de skill willen uitbreiden zodat het ook telkens een onderwerp suggereert dat eraan gerelateerd is, maar waar er momenteel nog niets van de vault zit of enkel een stub-note voor aangemaakt is."

**Use case**: Lichtgewicht "misschien interessant" trigger zonder verplichting - exposure en serendipiteit.

## High-Level Architecture

### Two-Phase Discovery Engine

**Phase 1 - Primary Discovery** (snel, direct):
- Scan distance-1 nodes: `[[wikilinks]]` in note body + `related-to` frontmatter
- Check welke daarvan stubs zijn (bestand bestaat maar <100 woorden content)
- Detecteer broken/red links (expliciet genoemd maar bestaat niet)
- Analyseer note content: identificeer genoemd-maar-niet-gelinkte concepten
- Score kandidaten op relevantie

**Phase 2 - Fallback Discovery** (breder, alleen als <3 kandidaten):
- Distance-2: volg links van directe connecties
- Domain scan: andere notes met overlappende tags/categories
- Reasoning modes: infereer missing prerequisites OF logical extensions
- Mix strategieën random voor variatie

**Output**: Nieuwe sectie "Verken verder" met top 3 kandidaten, elk met format:
```
[[Topic]] - begrijp [wat je zou leren]
```

## Candidate Scoring & Ranking

### Score Components (0-100 totaal)

| Component | Max Points | Details |
|-----------|------------|---------|
| Distance weight | 40 | Distance-1 stub: 40<br>Broken link: 35<br>Semantic gap: 30<br>Distance-2: 20<br>Domain match: 10<br>Pure reasoning: 5 |
| Mention count | 20 | Hoeveel keer concept genoemd/gerefereerd in huidige note |
| Stub quality | 20 | Heeft stub-note (15) vs pure inferentie (5) |
| Recency bias | 10 | Gerelateerd aan recent gestagede items |
| Freshness | 10 | Hoe lang geleden als suggestie getoond (prefer niet-recent) |

### Top 3 Selection

1. Sort alle kandidaten op totale score
2. Select top 3 met **diversity filter**:
   - Als top 3 allemaal uit dezelfde categorie komen (bijv. alle distance-1 stubs)
   - Vervang #3 met hoogst-scorende uit andere categorie
   - Garandeert variatie in suggesties

### Learning Value Generation

Voor elke top-3 kandidaat, genereer "begrijp [x]" tekst:
- **Als stub exists**: lees stub metadata (titel, tags) en infereer leerwaarde
- **Als broken link**: gebruik context waar link staat om waarde te infereren
- **Als inferreed**: gebruik reasoning dat tot kandidaat leidde
- **Format**: altijd beginnen met "begrijp hoe/wat/waarom/welke"

## Search Strategies - Implementation

### Primary Discovery

```
1. Distance-1 Graph Scan:
   - Parse note body voor alle [[wikilinks]]
   - Parse frontmatter "related-to" field
   - Voor elke link:
     * Bestaat niet → broken link kandidaat (score: 35)
     * Bestaat als stub → stub kandidaat (score: 40)
   - Track alle gevonden kandidaten

2. Semantic Gap Analysis:
   - Extract key terms uit huidige note (technical terms, capitalized concepts)
   - Check of deze terms als [[link]] bestaan
   - Zo niet → kandidaat voor "genoemd maar niet uitgewerkt"
   - Score: 30 punten

3. Related-to Chain:
   - Voor notes in related-to die geen stub zijn:
     Check of ze sub-topics hebben die wel stubs/broken zijn
   - Voorbeeld: linkt naar [[Deep Learning]], check [[Backpropagation]]
```

### Fallback Discovery (triggered als <3 kandidaten)

```
4. Distance-2 Exploration:
   - Voor elke distance-1 note, lees hun [[links]] en related-to
   - Filter: alleen notes die NIET al in distance-1 zaten
   - Track visited notes (circular reference protection)
   - Score: 20 punten

5. Domain Matching:
   - Extract tags van huidige note (bijv. "AI/neural-networks")
   - Scan vault voor notes met overlappende tags die stubs zijn
   - Score: 10 punten

6. Reasoning Modes (kies random 1 van 2):
   - Prerequisites mode: "voor [topic], zou je moeten kennen..."
   - Extensions mode: "na [topic], is de volgende stap..."
   - Genereer 2-3 inferreed kandidaten
   - Score: 5 punten (laagste, pure inferentie)
```

## Workflow Integration

### Updated 3-Step Workflow

**Stap 1: Selecteer topic** (unchanged)
- Bestaande topic-selection logica blijft intact
- Criteria: substantieel, type/concept, >1 dag oud
- Prioriteit: oudste modified, veel stub-links, thematisch aansluitend

**Stap 2: Lees & Analyseer** (extended)
- Lees de volledige note (bestaand)
- Identificeer kernconcepten, analogieën, gaten (bestaand)
- **NIEUW: Start discovery engine**
  - Verzamel kandidaten via primary discovery
  - Check count: <3? → trigger fallback discovery
  - Score alle kandidaten
  - Selecteer top 3 met diversity filter
  - Genereer learning values

**Stap 3: Genereer refresh** (extended output)

```markdown
## Refresh: {Topic}

### Herhaling
[bestaande logic - uitleg alsof opnieuw aangeleerd]

### Verdieping: {specifiek subtopic}
[bestaande logic - één concreet nieuw inzicht]

### Connecties
[bestaande logic - directe links en bekende stubs]
- Sluit aan bij [[bestaande-note]] — {waarom}
- Gat gevonden: [[stub-note]] zou uitgewerkt kunnen worden

### Verken verder
1. [[Kandidaat 1]] - begrijp [learning value 1]
2. [[Kandidaat 2]] - begrijp [learning value 2]
3. [[Kandidaat 3]] - begrijp [learning value 3]

### Verder uitdiepen (optioneel)
[bestaande logic - verdiepingssuggesties]
- {Suggestie 1}: korte omschrijving
- {Suggestie 2}: korte omschrijving
```

### Timing

Discovery engine draait parallel met note reading (non-blocking).

## Error Handling & Edge Cases

### Scenario 1: Geen kandidaten gevonden (zelfs na fallback)

Output generieke maar waardevolle fallbacks:

```markdown
### Verken verder
Dit topic lijkt goed uitgewerkt in je vault. Hier zijn drie algemene richtingen:
1. [[Gerelateerd domein]] - verbreed naar aanpalend vakgebied
2. [[Praktische toepassing]] - vertaal theorie naar implementatie
3. [[Historische context]] - begrijp de ontwikkeling van dit concept
```

### Scenario 2: Note heeft geen links/related-to

- Primary discovery faalt direct
- Spring meteen naar fallback
- Domain matching en reasoning modes worden primair

### Scenario 3: Circulaire referenties (A→B→A)

- Track visited notes tijdens distance-2 scan
- Skip notes die al in het pad zitten
- Voorkom infinite loops

### Scenario 4: Stub-note detectie

Definitie stub (OR logic):
- `word_count < 100`, OR
- `tag:status/stub`, OR
- `frontmatter.stub: true`

Als note geen frontmatter heeft: gebruik alleen word count.

### Scenario 5: Discovery timeout

- Max 5 seconden voor hele discovery process
- Als timeout: return wat er tot nu toe gevonden is (kan <3 zijn)
- Log warning maar fail niet
- Graceful degradation

### Scenario 6: Broken/Red links (FEATURE)

- `[[Non-existent Topic]]` die niet resolven zijn **high-value kandidaten**
- Score: 35 punten (tussen stub en distance-2)
- Rationale: expliciet genoemd maar ontbreekt → duidelijke kennishiaat
- Learning value: infereer uit context waar link staat
  - Voorbeeld: "The [[Bellman Equation]] is fundamental for RL"
    → "begrijp hoe de Bellman Equation werkt in reinforcement learning"

### Scenario 7: Mix van stubs en broken links

- Beide zijn valide kandidaten
- Top 3 kan beide types bevatten
- Diversity filter zorgt voor spreiding

### Scenario 8: Invalid/malformed wikilinks

- Skip gracefully met warning
- Tellen niet mee als kandidaat
- Continue met andere links

## Testing & Validation

### Unit Tests

```
Test 1: Primary discovery with distance-1 stubs
  Input: note met [[stub-link]] en related-to met stub
  Expected: beide kandidaten gevonden, score = 40

Test 2: Broken link detection
  Input: note met [[Non-existent Topic]]
  Expected: kandidaat met score = 35, learning value geïnfereerd

Test 3: Fallback trigger
  Input: note met 0 distance-1 kandidaten
  Expected: fallback modes activeren, >0 kandidaten

Test 4: Diversity filter
  Input: 5 kandidaten, allemaal distance-1 stubs
  Expected: top 3 bevat minimaal 1 uit andere categorie

Test 5: Circular reference handling
  Input: A→B→A cycle in distance-2 scan
  Expected: geen dubbele kandidaten, geen infinite loop

Test 6: Timeout handling
  Input: vault met 10,000+ notes
  Expected: discovery stopt na 5s, returnt partial results
```

### Integration Tests

```
Test 7: Complete workflow
  Input: real note uit vault
  Expected: volledige refresh output met "Verken verder" sectie

Test 8: Empty vault edge case
  Input: note zonder enige links
  Expected: fallback reasoning modes produceren 3 generieke suggesties

Test 9: Output format consistency
  Expected: alle 3 kandidaten hebben format "[[Topic]] - begrijp [x]"

Test 10: Broken link in context
  Input: note met "The [[Missing Concept]] is important because..."
  Expected: learning value = "begrijp waarom Missing Concept belangrijk is"
```

### Manual Validation

- Test met 5 verschillende notes uit verschillende domeinen
- Beoordeel: zijn de suggesties zinvol? Zou je ze willen verkennen?
- Check variatie: krijg je diverse suggesties over meerdere runs?

## Implementation Notes

### Dependencies

- Vault access: need to read notes, check file existence, count words
- Frontmatter parser: extract tags, related-to, stub status
- Wikilink parser: extract all [[links]] from markdown
- NLP basic: key term extraction voor semantic gap analysis

### Performance Considerations

- **Caching**: cache vault structure (file paths, sizes) voor snellere stub detection
- **Lazy loading**: lees note content alleen als nodig (niet voor alle distance-2)
- **Parallel scanning**: distance-2 exploration kan parallel per branch
- **Timeout**: hard 5s limit om morning report niet te vertragen

### Future Enhancements (niet nu)

- Machine learning voor betere learning value generation
- User feedback loop: track welke suggesties actie triggeren
- Adaptive scoring: leer van gebruikersgedrag
- Cross-vault discovery: suggesties uit public knowledge bases

## Success Criteria

1. ✅ "Verken verder" sectie verschijnt altijd in refresh output
2. ✅ Minimaal 3 kandidaten (of generieke fallbacks als echt niets te vinden)
3. ✅ Suggesties zijn relevant (manual validation met echte vault notes)
4. ✅ Diversity in suggestietypes (mix van stubs, broken links, reasoning)
5. ✅ Performance: discovery <5s zelfs voor grote vaults
6. ✅ Broken links worden erkend als waardevolle kandidaten

## Approval

Design approved door gebruiker op 2026-02-10.

Ready for implementation.
