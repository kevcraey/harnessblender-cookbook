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

Execute skill `sb-identify-patterns` on `1-notes/` to find:

### Lexical Clusters

- Notes that share significant vocabulary overlap
- Recurring terms without dedicated concept notes

### Link Clusters

- Groups of notes heavily linked to each other
- "Hub" notes with high inbound/outbound link counts

### Temporal Clusters

- Topics that appear frequently in recent journal entries
- Seasonal or recurring themes

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
