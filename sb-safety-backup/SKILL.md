---
name: sb-safety-backup
description: Use when creating safety checkpoints before risky operations (processing inbox, major refactors, bulk operations, or any workflow that modifies multiple files)
---

# Safety Backup

Create git commit checkpoints before and after risky operations to enable quick rollback.

## When to Use

**Use when:**
- Starting a multi-file workflow (inbox processing, curation, integration)
- Before major refactors or bulk operations
- Workflow instructions say "execute safety-backup with context X"

**Don't use for:**
- Normal development commits (use standard git workflow)
- After every single file change

## Quick Reference

```bash
# Standard usage
git add -A && git commit -m "backup: {context} state

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

| Context Example | When Used |
|----------------|-----------|
| `pre-inbox-2026-02-01` | Before processing inbox |
| `post-inbox-2026-02-01` | After processing inbox |
| `pre-integration` | Before integrating staging |
| `post-cleanup` | After maintenance tasks |

## Implementation

**Always commit all changes** - safety backups capture complete state:

```bash
git add -A && git commit -m "backup: {context} state

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Parameters:**
- `{context}`: Descriptive context (e.g., "pre-inbox-2026-02-01", "post-integration")

**Format rules:**
1. Message starts with `backup: `
2. Context describes the operation point
3. Ends with ` state`
4. Blank line before co-author
5. Always include co-authored-by line

## Common Patterns

```bash
# Before risky operation
git add -A && git commit -m "backup: pre-operation-name state

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# After risky operation
git add -A && git commit -m "backup: post-operation-name state

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

## Rollback

To restore from a safety backup:

```bash
# Find the backup commit
git log --oneline --grep="^backup:"

# Reset to that commit (keeping changes as uncommitted)
git reset {commit-hash}

# Or hard reset (discarding all changes)
git reset --hard {commit-hash}
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Selective staging (`git add file.md`) | Use `git add -A` - capture everything |
| Forgot co-author line | Always include attribution |
| Inconsistent format | Follow template exactly |
| Manual commit without skill | Use skill for consistency |
