# MOC Hierarchy Rules

Maps of Content (MOCs) provide navigable structure for the Second Brain.

## Hierarchy Levels

| Level | Location | Naming | Purpose |
| ----- | -------- | ------ | ------- |
| 0 | `0-index/moc-root.md` | `moc-root` | Single entry point, links to all domains |
| 1 | `0-index/moc-{domain}.md` | `moc-{domain}` | Domain index, links to topics |
| 2 | `1-notes/{topic}.md` | No prefix | Topic index, links to related notes |

## Frontmatter for Topic MOCs (Level 2)

```yaml
---
type: moc
parent: "[[moc-{domain}]]"
---
```

## Emergent Discovery Thresholds

| Trigger | MOC Level | Threshold |
| ------- | --------- | --------- |
| Large cluster with distinct theme | Domain (L1) | ≥10 notes |
| Sub-cluster within domain | Topic (L2) | ≥3 notes |

## MOC Content Structure

### Root MOC Template

```markdown
# 🗺️ Second Brain Index

## Domains
- [[moc-{domain1}]]
- [[moc-{domain2}]]

## Quick Access
- [[4-tasks/|Active Tasks]]
- [[2-events/|Recent Events]]
```

### Domain MOC Template

```markdown
# {Domain Name}

## Topics
- [[topic1]]
- [[topic2]]

## Key Notes
- [[important-note-1]]
- [[important-note-2]]
```

### Topic MOC Template

```markdown
# {Topic Name}

> This topic sits at the intersection of [[A]], [[B]], and [[C]].

## Notes
- [[note1]]
- [[note2]]
```

## Validation Rules

- Every note in `1-notes/` should be reachable from root MOC within 3 hops
- Domain MOCs must have ≥3 topic links to justify existence
- Orphan notes (not linked from any MOC) should be flagged
