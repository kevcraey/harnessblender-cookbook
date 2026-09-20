---
name: sb-system-maintenance
description: Periodic maintenance for vault hygiene, dead links, and archival.
---

# System Maintenance Workflow

Maintain the health of the "Second Brain" by fixing entropy and rot.

> [!NOTE]
> See `references/moc-hierarchy.md` for MOC structure validation rules.

## 1. Safety Backup

- Execute the skill `safety-backup` with context: pre-maintenance-{YYYY-MM-DD}

## 2. Dead Link Detection

- Scan all notes for `[[wikilinks]]` pointing to non-existent files
- **Action**: Log each broken link in report

## 3. Tag Hygiene

- Identify tags used < 2 times (potential typos or orphans)
- **Action**: Propose merges/deletions in report

## 4. Staging Cleanup

- Alert if files remain in `9-staging/` for > 7 days
- **Action**: List stale items with age in report

## 5. Completed Task Archival

- Scan `4-tasks/` for notes with:
  - At least one checked task (`- [x]`)
  - Zero unchecked tasks (`- [ ]`)
- **Action**: Move to `99-archive/` and log in report

## 6. MOC Structure Validation

Scrutinize the indexing hierarchy:

### Orphan Detection

- Find notes in `1-notes/` not reachable from `moc-root.md` within 3 hops
- **Action**: List orphan notes, suggest domain assignment

### Domain MOC Health

- Domain MOCs with <3 topic links → suggest merge or deletion
- Domain MOCs not linked from `moc-root.md` → flag

### Topic MOC Health

- Topic MOCs with `type: moc` but missing `parent` frontmatter → flag
- Topic MOCs not linked from any domain MOC → suggest parent

### Hierarchy Integrity

- Verify `0-index/moc-root.md` exists
- Verify all domain MOCs in `0-index/` are linked from root

## 7. User Handshake

> [!CAUTION]
> **Destructive Operations**: The following actions modify or delete content. Review carefully before proceeding.

- Present proposed tag merges/deletions.
- Present tasks to be archived.
- Present stale staging items for cleanup.
- Present MOC structure issues and proposed fixes.

**STOP**: Do not execute destructive actions without explicit user confirmation.

## 8. Generate Report

**Always** generate: `{YYYY-MM-DD}-maintenance-report.md` at vault root.

### Report Structure

```markdown
## 📌 Summary
Overview of maintenance actions.

## 🔗 Dead Links
- [[Broken Link]] in [[Source Note]]

## 🏷️ Tag Issues
- `#orphan-tag` (used: 1x) → Suggest merge with `#similar-tag`

## ⏰ Stale Staging Items
- [[note]] (age: 12 days)

## 📦 Archived Tasks
- [x] [[Completed Task]] → Moved to 99-archive

## 🗺️ MOC Issues
- **Orphans**: [[note1]], [[note2]] (not reachable from root)
- **Weak Domains**: [[moc-domain]] (<3 topics)
- **Missing Parents**: [[topic-moc]] (no parent frontmatter)
```

## 9. Finalize

- Execute the skill `safety-backup` with context: post-maintenance-{YYYY-MM-DD}
