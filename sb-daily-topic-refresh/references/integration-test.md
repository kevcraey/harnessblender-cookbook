# Integration Test - Complete End-to-End Scenario

Complete integration test showing how all discovery engine components work together in a realistic scenario.

## Test Vault Structure

```
vault/
├── notes/
│   ├── attention-mechanism.md (main test note)
│   ├── transformers.md (full note, 2000 words)
│   ├── neural-networks.md (full note, 500 words)
│   ├── positional-encoding.md (stub, 45 words)
│   ├── backpropagation.md (referenced from neural-networks)
│   └── deep-learning.md (tagged similar to attention)
├── staging/
│   └── gradient-descent.md (staged 3 days ago)
└── .discovery-history.json
```

## Test Note: attention-mechanism.md

```markdown
---
title: Attention Mechanism
tags: AI/neural-networks, AI/deep-learning
related-to: [[Transformers]], [[Neural Networks]]
created: 2026-01-15
modified: 2026-02-01
---

# Attention Mechanism

The attention mechanism allows neural networks to focus on relevant parts of the input sequence when producing an output. It revolutionized NLP and computer vision tasks.

## Core Components

The mechanism uses three key components:
- **Query**: What we're looking for
- **Key**: What we're looking at
- **Value**: What we extract

The attention score is computed using Query-Key similarity, then applied to Values.

## Multi-Head Attention

Multi-head attention improves this by running multiple attention operations in parallel, each learning different aspects of the relationships. This is fundamental to the [[Transformers]] architecture.

## Position Information

Since attention has no inherent notion of sequence order, we need [[Positional Encoding]] to inject position information into the input embeddings.

## Related Concepts

The Self-Attention mechanism is a special case where Query, Key, and Value all come from the same sequence. This enables the model to learn relationships between different positions in a single sequence.

Cross-Attention is used when Query comes from one sequence (e.g., decoder) and Key/Value from another (e.g., encoder).
```

## Step-by-Step Discovery Process

### Phase 1: Primary Discovery

#### 1.1 Parse Note Content

```python
note = {
    'path': 'vault/notes/attention-mechanism.md',
    'title': 'Attention Mechanism',
    'tags': ['AI/neural-networks', 'AI/deep-learning'],
    'related_to': ['Transformers', 'Neural Networks'],
    'content': '...' # full markdown body
}
```

#### 1.2 Extract Wikilinks

Regex scan finds: `\[\[([^\]]+)\]\]`

**Found links:**
1. `[[Transformers]]` - line 15
2. `[[Neural Networks]]` - frontmatter
3. `[[Positional Encoding]]` - line 21
4. `[[Self-Attention]]` - line 27
5. `[[Cross-Attention]]` - line 29

#### 1.3 Distance-1 Graph Scan

Check each linked note:

**[[Transformers]]**:
- Exists: Yes
- Path: `vault/notes/transformers.md`
- Word count: 2000
- Is stub: No (>100 words)
- Status: Full note → Skip

**[[Neural Networks]]**:
- Exists: Yes
- Path: `vault/notes/neural-networks.md`
- Word count: 500
- Is stub: No (>100 words)
- Links to: `[[Backpropagation]]`, `[[Gradient Descent]]`
- Status: Full note → Skip

**[[Positional Encoding]]**:
- Exists: Yes
- Path: `vault/notes/positional-encoding.md`
- Word count: 45
- Is stub: Yes (<100 words)
- Frontmatter: `stub: true`
- **→ CANDIDATE** (distance-1 stub)

**[[Self-Attention]]**:
- Exists: No
- **→ BROKEN LINK CANDIDATE**

**[[Cross-Attention]]**:
- Exists: No
- **→ BROKEN LINK CANDIDATE**

#### 1.4 Semantic Gap Analysis

Extract capitalized/special terms not already linked:

Scan for patterns:
- CamelCase: None additional
- Capitalized phrases: "Query", "Key", "Value", "Multi-head attention"
- Domain terms: "Query-Key similarity"

Check if notes exist:
- `[[Query]]` - No
- `[[Key]]` - No (too generic)
- `[[Value]]` - No (too generic)
- `[[Multi-head Attention]]` - No → **CANDIDATE**
- `[[Query Key Value]]` - No → **CANDIDATE**

#### 1.5 Primary Candidates Summary

Total found: 5 candidates (≥3, sufficient to skip Phase 2)

```
1. Positional Encoding (stub)
2. Self-Attention (broken link)
3. Cross-Attention (broken link)
4. Multi-head Attention (semantic gap)
5. Query Key Value (semantic gap)
```

### Phase 2: Candidate Scoring

Calculate scores for each candidate using the scoring matrix:

#### Candidate 1: Positional Encoding
- **Distance weight**: 40 (distance-1 stub)
- **Mention count**: 5 (appears 1 time × 5 = 5)
- **Stub quality**: 15 (has stub note)
- **Recency bias**: 0 (no shared tags with recent staging)
- **Freshness**: 10 (not in .discovery-history.json)
- **Total**: 70

#### Candidate 2: Self-Attention
- **Distance weight**: 35 (broken link)
- **Mention count**: 10 (appears 2 times: "Self-Attention mechanism" + concept × 5 = 10)
- **Stub quality**: 10 (broken link)
- **Recency bias**: 0
- **Freshness**: 10
- **Total**: 65

#### Candidate 3: Cross-Attention
- **Distance weight**: 35 (broken link)
- **Mention count**: 5 (appears 1 time × 5 = 5)
- **Stub quality**: 10 (broken link)
- **Recency bias**: 0
- **Freshness**: 10
- **Total**: 60

#### Candidate 4: Multi-head Attention
- **Distance weight**: 30 (semantic gap)
- **Mention count**: 10 (appears 2 times: explicit mention + "multi-head" discussion × 5 = 10)
- **Stub quality**: 5 (pure inference)
- **Recency bias**: 0
- **Freshness**: 10
- **Total**: 55

#### Candidate 5: Query Key Value
- **Distance weight**: 30 (semantic gap)
- **Mention count**: 15 (Query/Key/Value mentioned 6+ times × 5 = 15, capped at 20)
- **Stub quality**: 5 (pure inference)
- **Recency bias**: 0
- **Freshness**: 10
- **Total**: 60

#### Scoring Table

| Candidate | Distance | Mentions | Stub | Recency | Fresh | Total |
|-----------|----------|----------|------|---------|-------|-------|
| Positional Encoding | 40 | 5 | 15 | 0 | 10 | **70** |
| Self-Attention | 35 | 10 | 10 | 0 | 10 | **65** |
| Cross-Attention | 35 | 5 | 10 | 0 | 10 | **60** |
| Query Key Value | 30 | 15 | 5 | 0 | 10 | **60** |
| Multi-head Attention | 30 | 10 | 5 | 0 | 10 | **55** |

### Phase 3: Top 3 Selection

#### 3.1 Initial Sort (by score desc)

1. Positional Encoding (70) - stub
2. Self-Attention (65) - broken link
3. Cross-Attention (60) - broken link
4. Query Key Value (60) - semantic gap
5. Multi-head Attention (55) - semantic gap

#### 3.2 Diversity Check

Top 3 categories:
1. Stub (1 candidate)
2. Broken link (2 candidates)
3. Semantic gap (0 candidates)

**Diversity issue**: No semantic gap in top 3, but we have two strong semantic candidates.

**Apply diversity filter**: Replace #3 (Cross-Attention, broken link, score 60) with highest semantic gap candidate (Query Key Value, score 60).

**Final top 3**:
1. Positional Encoding (70) - stub
2. Self-Attention (65) - broken link
3. Query Key Value (60) - semantic gap ✓ diversity

### Phase 4: Learning Value Generation

#### Candidate 1: Positional Encoding (stub exists)

**Process**:
1. Read stub file: `vault/notes/positional-encoding.md`
```markdown
---
title: Positional Encoding
tags: AI/transformers
stub: true
---

Positional encoding adds position information to transformer inputs.
```

2. Infer learning value from:
   - Stub title: "Positional Encoding"
   - Context in main note: "inject position information into the input embeddings"
   - Tag: transformers-related

3. **Generate**: "begrijp hoe positional encoding positie-informatie injecteert in transformer embeddings"

#### Candidate 2: Self-Attention (broken link)

**Process**:
1. Extract context around `[[Self-Attention]]`:
```
The Self-Attention mechanism is a special case where Query, Key, and
Value all come from the same sequence. This enables the model to learn
relationships between different positions in a single sequence.
```

2. Key context clues:
   - "special case where Query, Key, and Value all come from the same sequence"
   - "learn relationships between different positions"

3. **Generate**: "begrijp hoe self-attention relaties leert tussen posities binnen dezelfde sequence"

#### Candidate 3: Query Key Value (semantic gap)

**Process**:
1. Extract context around terms:
```
The mechanism uses three key components:
- **Query**: What we're looking for
- **Key**: What we're looking at
- **Value**: What we extract

The attention score is computed using Query-Key similarity, then applied to Values.
```

2. Key context clues:
   - Explicitly defined trio: Query/Key/Value
   - "attention score is computed using Query-Key similarity"
   - Functional descriptions provided

3. **Generate**: "begrijp wat de rollen zijn van Query, Key en Value in attention berekeningen"

### Final Learning Values Summary

```
1. "begrijp hoe positional encoding positie-informatie injecteert in transformer embeddings"
2. "begrijp hoe self-attention relaties leert tussen posities binnen dezelfde sequence"
3. "begrijp wat de rollen zijn van Query, Key en Value in attention berekeningen"
```

## Expected Final Output

### Complete Refresh Structure

```markdown
---
title: Attention Mechanism
tags: AI/neural-networks, AI/deep-learning
related-to: [[Transformers]], [[Neural Networks]]
created: 2026-01-15
modified: 2026-02-01
last-refreshed: 2026-02-10
---

# Attention Mechanism

[... original content unchanged ...]

---

## Verken verder

Gerelateerde topics om je begrip van Attention Mechanism te verdiepen:

1. **[[Positional Encoding]]** - begrijp hoe positional encoding positie-informatie injecteert in transformer embeddings
2. **[[Self-Attention]]** - begrijp hoe self-attention relaties leert tussen posities binnen dezelfde sequence
3. **[[Query Key Value]]** - begrijp wat de rollen zijn van Query, Key en Value in attention berekeningen
```

### Discovery History Update

`.discovery-history.json` should be updated:

```json
{
  "attention-mechanism": {
    "last_refresh": "2026-02-10T14:30:00Z",
    "suggestions": [
      {
        "topic": "Positional Encoding",
        "score": 70,
        "type": "stub",
        "suggested_at": "2026-02-10T14:30:00Z"
      },
      {
        "topic": "Self-Attention",
        "score": 65,
        "type": "broken_link",
        "suggested_at": "2026-02-10T14:30:00Z"
      },
      {
        "topic": "Query Key Value",
        "score": 60,
        "type": "semantic_gap",
        "suggested_at": "2026-02-10T14:30:00Z"
      }
    ]
  }
}
```

## Validation Checklist

Use this checklist to verify the integration test results:

### ✓ Discovery Phase
- [ ] All wikilinks correctly extracted (5 found)
- [ ] Broken links identified (2 found: Self-Attention, Cross-Attention)
- [ ] Stub detection working (1 found: Positional Encoding)
- [ ] Semantic gap analysis found uncaptured concepts (2 found)
- [ ] Phase 2 skipped correctly (≥3 candidates in Phase 1)

### ✓ Scoring Phase
- [ ] All 5 scoring components calculated correctly
- [ ] Distance weights assigned per category (40/35/30)
- [ ] Mention counts accurately reflect term frequency
- [ ] Stub quality scores match candidate types (15/10/5)
- [ ] Freshness bonus applied (all +10)
- [ ] Total scores computed correctly

### ✓ Selection Phase
- [ ] Candidates sorted by total score
- [ ] Top 3 initially selected by score
- [ ] Diversity check performed
- [ ] Diverse categories represented in final top 3
- [ ] Final list contains: 1 stub, 1 broken link, 1 semantic gap

### ✓ Learning Value Generation
- [ ] Stub candidate: read stub file and inferred context
- [ ] Broken link candidate: extracted surrounding context
- [ ] Semantic gap candidate: used explicit definitions
- [ ] All learning values start with "begrijp"
- [ ] All include question word (hoe/wat/waarom/welke)
- [ ] Values are specific and contextual

### ✓ Output Format
- [ ] "Verken verder" section added
- [ ] Three suggestions formatted correctly
- [ ] Each suggestion: `[[Topic]]` - learning value
- [ ] Numbered list (1, 2, 3)
- [ ] Separator line (---) before section
- [ ] `last-refreshed` frontmatter updated

### ✓ Persistence
- [ ] `.discovery-history.json` updated
- [ ] Contains note key (slug of note filename)
- [ ] Timestamp in ISO 8601 format
- [ ] All 3 suggestions logged with metadata
- [ ] Type field correctly categorizes each suggestion

### ✓ Edge Cases Handled
- [ ] No circular references in distance-2 scan (not triggered)
- [ ] Invalid wikilinks filtered out (none in this test)
- [ ] Timeout protection in place (not triggered, <5s)
- [ ] Duplicate candidates deduplicated
- [ ] No infinite loops

## Performance Benchmarks

Expected execution times:

| Phase | Expected Time | This Test |
|-------|---------------|-----------|
| Note parsing | <50ms | 35ms |
| Primary discovery | <200ms | 180ms |
| Fallback discovery | N/A (skipped) | 0ms |
| Scoring | <50ms | 42ms |
| Learning value gen | <100ms | 85ms |
| **Total** | **<500ms** | **342ms** ✓ |

## Test Variations

### Variation A: Fallback Required

Modify test to trigger Phase 2:
- Remove broken links (Self-Attention, Cross-Attention exist as full notes)
- Remove semantic gaps (all concepts already linked)
- Only stub remains (Positional Encoding)

Expected: Distance-2 exploration activates, finds topics via Neural Networks → Backpropagation chain.

### Variation B: Ultimate Fallback

Modify test for minimal candidates:
- All links exist as full notes
- No broken links
- No semantic gaps
- No stubs

Expected: Generic fallbacks generated:
1. "[[Neural Architecture Search]]" (gerelateerd domein)
2. "[[Attention Implementation]]" (praktische toepassing)
3. "[[Attention History]]" (historische context)

### Variation C: Recency Bias Active

Add to staging area:
- `gradient-descent.md` (staged 3 days ago)
- Tags: `AI/optimization`, `AI/deep-learning`

Expected:
- Candidates sharing `AI/deep-learning` tag get +10 recency bias
- Scoring shifts: Positional Encoding (70→80), Self-Attention (65→75), etc.
- Selection order may change based on new scores

## Integration Points

### With Skill System

```bash
# CLI invocation
sb-daily-topic-refresh refresh attention-mechanism.md

# Expected flow:
# 1. Load SKILL.md
# 2. Parse note
# 3. Run discovery engine (this integration test)
# 4. Generate refresh output
# 5. Update note file
# 6. Update .discovery-history.json
# 7. Report results
```

### With Validation System

The validation.md reference file should be used after this integration test to verify:
- Output format compliance
- Learning value quality
- Discovery history accuracy
- Section placement

### With Algorithm Implementation

This integration test validates the pseudocode in `discovery-algorithm.md`:
- All functions have expected outputs
- Data flows correctly between phases
- Error handling works as specified
- Performance meets requirements

## Success Criteria

This integration test passes if:

1. **Correctness**: All expected candidates found with correct scores
2. **Diversity**: Top 3 represents different discovery strategies
3. **Quality**: Learning values are contextual and specific
4. **Performance**: Completes in <500ms
5. **Format**: Output matches expected structure exactly
6. **Persistence**: History file updated correctly

## Troubleshooting

### Issue: Fewer than 3 candidates

**Diagnosis**: Primary discovery too restrictive or note has minimal connections

**Solution**: Check Phase 2 fallback triggered, verify distance-2 exploration works

### Issue: Poor learning values

**Diagnosis**: Context extraction failing or stub files missing context

**Solution**: Improve context window around broken links, enrich stub frontmatter

### Issue: Low diversity scores

**Diagnosis**: All candidates from same category (e.g., all semantic gaps)

**Solution**: Verify diversity filter applies, check if other strategies finding results

### Issue: Performance slow (>1s)

**Diagnosis**: Distance-2 exploration too deep or circular reference loops

**Solution**: Check visited_notes tracking, verify timeout protection, profile bottlenecks
