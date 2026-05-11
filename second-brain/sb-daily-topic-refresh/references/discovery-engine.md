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

## Candidate Scoring

Elke kandidaat krijgt score 0-100 op basis van:

| Component | Max | Berekening |
|-----------|-----|------------|
| Distance weight | 40 | Distance-1 stub: 40<br>Broken link: 35<br>Semantic gap: 30<br>Distance-2: 20<br>Domain match: 10<br>Reasoning: 5 |
| Mention count | 20 | Count hoeveel keer concept in note voorkomt |
| Stub quality | 20 | Heeft stub-note: 15<br>Pure inferentie: 5 |
| Recency bias | 10 | Gerelateerd aan recent gestagede items: +10 |
| Freshness | 10 | Niet recent als suggestie getoond: +10 |

### Top 3 Selection

1. Sort kandidaten op totale score (desc)
2. Select top 3
3. **Diversity filter**: Als top 3 alle uit dezelfde categorie (bijv. alle distance-1), vervang #3 met hoogste uit andere categorie

## Learning Value Generation

Voor elke top-3 kandidaat, genereer "begrijp [x]" tekst:

### Als stub note bestaat
- Lees stub frontmatter (titel, tags)
- Infereer leerwaarde uit metadata
- Format: "begrijp hoe/wat/waarom/welke [inferred value]"

### Als broken link
- Extract context waar link staat (surrounding sentence)
- Gebruik context om leerwaarde te infereren
- Voorbeeld: "The [[Bellman Equation]] is fundamental for RL"
  → "begrijp hoe de Bellman Equation werkt in reinforcement learning"

### Als inferreed (reasoning mode)
- Gebruik het reasoning dat tot kandidaat leidde
- Prerequisites: "begrijp wat [prerequisite] is als basis voor [current topic]"
- Extensions: "begrijp hoe [extension] voortbouwt op [current topic]"

**Regel**: Altijd beginnen met "begrijp" + vraagwoord (hoe/wat/waarom/welke)

## Edge Cases & Error Handling

### Circulaire referenties (A→B→A)
- Track `visited_notes` set tijdens distance-2 scan
- Skip notes die al in pad zitten
- Voorkomt infinite loops

### Invalid wikilinks
- Regex: `\[\[([^\]]+)\]\]` om links te extracten
- Skip links met: pipe syntax errors, nested brackets, empty content
- Log warning maar continue met andere links

### Timeout protection
- Max 5 seconden voor hele discovery process
- Als timeout: return wat er tot nu toe is (kan <3 zijn)
- Log: "Discovery timeout na 5s, gevonden: [N] kandidaten"

### Geen kandidaten (zelfs na fallback)
- Genereer 3 generieke suggesties:
  1. "[[Gerelateerd domein]] - verbreed naar aanpalend vakgebied"
  2. "[[Praktische toepassing]] - vertaal theorie naar implementatie"
  3. "[[Historische context]] - begrijp de ontwikkeling van dit concept"
- Infereer concrete names uit current topic (bijv. "AI" → "Cognitieve Wetenschap", "Python implementatie", "AI geschiedenis")
