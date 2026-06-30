---
name: sb-discover-insights
description: Discover emergent patterns and suggest new Maps of Content (MOCs).
---

# Discover Insights Workflow

Identify emergent patterns and propose structural improvements to cultivate the knowledge garden.

> [!NOTE]
> See `references/moc-hierarchy.md` for MOC structure and thresholds.

## 1. Safety Backup

- Execute the skill `safety-backup` with context: pre-insights-{YYYY-MM-DD}

## 2. Cluster Analysis

> [!NOTE]
> **Internal Subsystem**: This section performs pattern identification (formerly sb-identify-patterns).
> See `references/pattern-types.md` for pattern definitions and `references/scoring.md` for thresholds.

Analyze the vault (`1-notes/`) to discover emergent topics, clusters, and structural insights.

### 2.1. Lexical Analysis

**Term Frequency** - Scan notes to find recurring terms:

```bash
# Extract significant terms (excluding stopwords)
grep -roh '\b[A-Za-z]\{4,\}\b' 1-notes/ | sort | uniq -c | sort -rn | head -50
```

**Undefined Concepts** - Find terms mentioned multiple times without dedicated notes:

1. Extract `[[wikilinks]]` across vault
2. Identify links pointing to non-existent files
3. Count occurrences
4. Flag terms with ≥3 mentions

### 2.2. Link Graph Analysis

**Hub Detection** - Find notes with high connectivity:

```python
# Pseudocode
for each note:
    inbound = count notes linking TO this note
    outbound = count [[links]] FROM this note
    if inbound + outbound > threshold:
        mark as hub
```

**Cluster Detection** - Identify tightly connected groups:

1. Build adjacency matrix of note links
2. Find strongly connected components
3. Report clusters of ≥3 notes

### 2.3. Temporal Analysis

**Recent Activity** - Analyze journal and recent modifications:

```bash
# Notes created/modified in last 30 days
find . -name "*.md" -mtime -30 -exec grep -l "keyword" {} \;
```

**Trending Terms** - Track term frequency in recent journal entries vs. historical baseline.

### 2.4. Pattern Scoring

Rate each discovered pattern:

| Signal | Score Boost |
|--------|-------------|
| Multiple undefined references | +3 |
| Tight link cluster (density >0.5) | +2 |
| Temporal spike (3x baseline) | +2 |
| High hub connectivity | +1 |

**Threshold**: Patterns scoring ≥5 are worth proposing.

### 2.5. Pattern Results

Output discovered patterns:

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

## 3. MOC Proposals

For each identified cluster, propose appropriate MOC level:

### Domain MOC (Level 1)

- **Threshold**: ≥10 notes forming a distinct domain
- **Location**: `0-index/moc-{domain}.md`
- **Action**: Propose new domain, update `moc-root.md`

### Topic MOC (Level 2)

- **Threshold**: ≥3 strongly connected notes within a domain
- **Location**: `1-notes/{topic}.md` with `type: moc` frontmatter
- **Draft**: Create synthesis summary:
   > "This topic sits at the intersection of [[A]], [[B]], and [[C]]."

## 4. Generate Report

**Always** generate: `{YYYY-MM-DD}-insights-report.md` at vault root.

### Report Structure

DO NOT put checkboxes (`- [ ]`) in the report

```markdown
## 📌 Summary
Overview of patterns discovered.

## 🌱 Emergent Topics
### Proposed: [[Topic Name]]
> **Cluster**: [[Note A]], [[Note B]], [[Note C]]
> **Signal**: Shared terms: "keyword1", "keyword2"
> **Action**: Create MOC? (Y/N)

## 🔗 Hub Analysis
- [[Popular Note]] (inbound: 15, outbound: 8)

## 📈 Trending Topics
- "keyword" mentioned 12x in last 30 days
```

## 5. User Decision

- Present proposals for user approval
- **STOP**: Do not create MOCs without explicit confirmation

## 6. (Optional) Execute Approved Actions

If user approves:

1. **Domain MOCs**: Create in `0-index/moc-{domain}.md`, add to `moc-root.md`
2. **Topic MOCs**: Create in `1-notes/` with frontmatter `type: moc`, `parent: [[moc-{domain}]]`
3. Update related notes with links to new MOC

## 7. Finalize

- Execute the skill `safety-backup` with context: post-insights-{YYYY-MM-DD}
