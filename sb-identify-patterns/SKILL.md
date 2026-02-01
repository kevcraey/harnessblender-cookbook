---
name: sb-identify-patterns
description: Detect lexical overlap and emergent patterns across notes.
---

# Identify Patterns

Analyze the vault to discover emergent topics, clusters, and structural insights.

> [!NOTE]
> See `references/pattern-types.md` for pattern definitions and `references/scoring.md` for thresholds.

## 1. Lexical Analysis

### Term Frequency

Scan notes to find recurring terms:

```bash
# Extract significant terms (excluding stopwords)
grep -roh '\b[A-Za-z]\{4,\}\b' 1-notes/ | sort | uniq -c | sort -rn | head -50
```

### Undefined Concepts

Find terms mentioned multiple times without dedicated notes:

1. Extract `[[wikilinks]]` across vault
2. Identify links pointing to non-existent files
3. Count occurrences
4. Flag terms with ≥3 mentions

## 2. Link Graph Analysis

### Hub Detection

Find notes with high connectivity:

```python
# Pseudocode
for each note:
    inbound = count notes linking TO this note
    outbound = count [[links]] FROM this note
    if inbound + outbound > threshold:
        mark as hub
```

### Cluster Detection

Identify tightly connected groups:

1. Build adjacency matrix of note links
2. Find strongly connected components
3. Report clusters of ≥3 notes

## 3. Temporal Analysis

### Recent Activity

Analyze journal and recent modifications:

```bash
# Notes created/modified in last 30 days
find . -name "*.md" -mtime -30 -exec grep -l "keyword" {} \;
```

### Trending Terms

Track term frequency in recent journal entries vs. historical baseline.

## 4. Pattern Scoring

Rate each discovered pattern:

| Signal | Score Boost |
|--------|-------------|
| Multiple undefined references | +3 |
| Tight link cluster (density >0.5) | +2 |
| Temporal spike (3x baseline) | +2 |
| High hub connectivity | +1 |

**Threshold**: Patterns scoring ≥5 are worth proposing.

## Output Format

```json
{
  "patterns": [
    {
      "type": "undefined_concept | link_cluster | trending_topic | hub",
      "title": "Proposed topic name",
      "score": 7,
      "evidence": {
        "notes": ["[[A]]", "[[B]]", "[[C]]"],
        "terms": ["keyword1", "keyword2"],
        "metrics": {
          "mentions": 12,
          "link_density": 0.8
        }
      },
      "recommendation": "Create MOC for [[Topic]]"
    }
  ],
  "hubs": [
    {
      "note": "[[Popular Note]]",
      "inbound": 15,
      "outbound": 8
    }
  ]
}
```
