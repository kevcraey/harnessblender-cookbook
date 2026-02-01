---
name: sb-process-inbox
description: Process braindumps, journal entries, and root files into the staging area.
---

# Process Inbox Workflow

This workflow processes your "Second Brain" inbox by scanning for new content, classifying items, and staging them for integration.

## 1. Safety Backup

- Execute the skill `safety-backup` with context: pre-inbox-{YYYY-MM-DD}

## 2. Parse Previous Report

- Check for existing `{YYYY-MM-DD}-inbox-report.md` or `{YYYY-MM-DD}-curator-report.md` at vault root.
- If user answers exist under "Requires Attention", extract them as high-priority instructions.

## 3. Scan Inbox

- Execute the skill `sb-scan-inbox` to identify:
  - **Root Files**: `*.md` files in vault root → will be MOVED to staging
  - **Journal Entries**: New content in `5-journal/` → will be MARKED & LINKED

## 4. User Handshake

> [!IMPORTANT]
> **Context Reset**: Synchroniseer met de gebruiker voordat je verdergaat. Presenteer alle items en wacht op expliciete goedkeuring.

- Present the Items to Process (including previous report answers).

**STOP**: Do not proceed without explicit user confirmation.

## 5. Classify and Stage

For each item:

1. Execute skill `sb-classify-content` to determine type (Project, Concept, Event, Task, People).
2. **High Confidence (≥8/10)**:
   - Root files: Move to `9-staging/{type-folder}/`
   - Journal items: Mark with ✅, create linked note in staging
3. **Low Confidence (<8/10)**:
   - Flag item with 🚩
   - Add to "Requires Attention" in report

### Collision Rule

If filename exists in Staging: **append** to file, do not overwrite.

## 6. Quality Assurance

Verify all staged items pass these checks:

### Frontmatter Check

```yaml
---
created: "[[{YYYY-MM-DD}]]"
tags:
  - type/{type}
related-to:
---
```

### Task Validation

- [ ] All task notes contain at least one checkbox (`- [ ]`)
- [ ] Due dates parsed to `(due::YYYY-MM-DD)` format
- [ ] Task descriptions are self-contained (not "do that tomorrow")

### People Validation

- [ ] People filenames are capitalized with spaces (`John Doe.md`)

## 7. Generate Report

**Always** generate: `{YYYY-MM-DD}-inbox-report.md` at vault root.

### Report Structure

```markdown
## 📌 Summary
Semantic summary of everything staged.

## 🤖 Autonomous Actions
- [x] Type: [[Link]] (Confidence: X/10)

## ⚠️ Requires Attention
### [?] {{Title}}
> **Confidence**: {{Score}}/10
> **Context**: {{original_text}}
> **Question**: {{AI_question}}
```

**Rule**: No `- [ ]` checkboxes in report (interferes with task management).

## 8. Finalize

- Execute the skill `safety-backup` with context: post-inbox-{YYYY-MM-DD}
