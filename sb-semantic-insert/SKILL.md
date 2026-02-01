---
name: sb-semantic-insert
description: Semantic wiring and emergent topic extraction for Second Brain notes.
---

# Semantic Insert

Connect notes through bidirectional links and identify emergent topics.

> [!NOTE]
> See `references/linking-rules.md` for detailed linking decision criteria.

## 1. Concept Linking (Semantic Wiring)

**Goal**: Connect the new note to existing knowledge in `1-notes`, `2-events`, `3-people`, `4-tasks`.

### Inline Transform

1. **Scan**: Find keywords matching existing note titles or aliases
2. **Transform**: Convert to wikilinks (e.g., `latency` → `[[latency]]`)

**Constraints**:

- **Only** link if target note exists (no red/ghost links)
- **Only** link key concepts (ignore common words)

### Frontmatter Linking

For semantic relations not mentioned explicitly:

```yaml
related-to:
  - "[[Existing Concept]]"
```

**Trigger**: Note is semantically related but doesn't mention the term.

## 2. Emergent Topic Extraction

**Goal**: Identify when multiple notes form a new cluster.

### Trigger Conditions

≥3 notes that:

1. Are strongly connected to each other, OR
2. Reference the same *undefined* concept (e.g., "GDPR" mentioned 3x but no `gdpr.md`)

### Actions

1. **Create Topic Note**: `1-notes/{topic}.md`
2. **Synthesize**: Write definition:
   > "This topic sits at the intersection of [[A]], [[B]], and [[C]]."
3. **Refactor**: Update related notes with links to new hub

## 3. Confidence Assessment

Evaluate quality of proposed changes:

| Score | Meaning |
|-------|---------|
| 9-10 | High value: creates structure, atomicity, new insights |
| 7-8 | Good value: meaningful connections |
| 5-6 | Moderate: links exist but not transformative |
| 1-4 | Low value: superficial or uncertain |

## 4. Execution Gate

- **High Confidence (≥8/10)**: Proceed with changes
- **Low Confidence (<8/10)**: Do NOT proceed, flag for review

## Output Format

```json
{
  "confidence": 8,
  "inline_links": ["[[term1]]", "[[term2]]"],
  "frontmatter_links": ["[[Related Note]]"],
  "emergent_topics": [
    {
      "proposed_title": "Topic Name",
      "connected_notes": ["[[A]]", "[[B]]", "[[C]]"],
      "synthesis": "This topic sits at..."
    }
  ],
  "reasoning": "Why these connections were made."
}
```
