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

> [!NOTE]
> **Internal Subsystem**: This section performs inbox scanning (formerly sb-scan-inbox).
> See `references/priority-rules.md` for prioritization logic.

Identify what needs to be processed by looking for new content since the last processing run:

- **Root Files**: `*.md` files in vault root → will be MOVED to staging
- **Journal Entries**: New content in `5-journal/` → will be MARKED & LINKED

### 3.1. Find Last Processing Point

Check for the most recent inbox report:

```bash
ls -t *-inbox-report.md 2>/dev/null | head -1
```

Or fall back to git history:

```bash
LAST_PROCESS=$(git log --oneline --grep="^backup: post-inbox" -1 --format="%H")
echo "Last inbox processing: $LAST_PROCESS"
```

### 3.2. Identify Root Files (Inbox Zero)

Find markdown files in vault root (these will be MOVED):

```bash
find . -maxdepth 1 -name "*.md" -type f ! -name "*-report.md"
```

**Action**: These files represent "Inbox Zero" items → Stage for processing.

### 3.3. Identify Journal Changes

Find new or modified entries in journal:

```bash
# If git reference exists
git diff --name-only $LAST_PROCESS HEAD -- 5-journal/

# Untracked files
git ls-files --others --exclude-standard -- 5-journal/
```

If no git reference, scan `5-journal/{current-year}/` for recent modifications:

```bash
find 5-journal/$(date +%Y) -name "*.md" -mtime -7
```

### 3.4. Check for Pending Reports

Look for reports with unanswered questions:

```bash
find . -maxdepth 1 -name "*-report.md" -exec grep -l "Requires Attention" {} \;
```

### 3.5. Compile Inbox List

Combine all inputs with priority:

1. **Priority 1**: Unanswered questions from previous reports
2. **Priority 2**: Root `*.md` files (Inbox Zero)
3. **Priority 3**: New/modified journal entries

**Output Format** - Return structured list:

```json
{
  "items": [
    {
      "source": "filename.md",
      "path": "/full/path/to/file.md",
      "type": "root_file | journal_entry | report_answer",
      "content_snippet": "First 200 chars...",
      "priority": 1
    }
  ]
}
```

## 4. User Handshake

> [!IMPORTANT]
> **Context Reset**: Synchroniseer met de gebruiker voordat je verdergaat. Presenteer alle items en wacht op expliciete goedkeuring.

- Present the Items to Process (including previous report answers).

**STOP**: Do not proceed without explicit user confirmation.

## 5. Classify and Stage

> [!NOTE]
> **Internal Subsystem**: This section performs content classification (formerly sb-classify-content).
> Detailed type definitions are in `references/type-{type}.md` files.

For each item, analyze and determine its type, then stage accordingly.

### 5.1. Classification Analysis

Analyze a discrete item (paragraph, list item, or file) and determine its type.

**Classification Rules:**

1. **Project** - A collection of tasks/work achieving a specific goal.
   - *Example*: "Redesign website homepage", "Plan summer vacation"
   - *Target*: `4-tasks/` with project tag

2. **Concept** - Pure knowledge, definitions, mental models.
   - *Example*: "RAG architecture explained", "Difference between taxonomy and ontology"
   - *Target*: `1-notes/`

3. **Event** - Something that happened at a specific moment.
   - *Example*: "Meeting with Client X on 2026-01-20", "Conference Y attended yesterday"
   - *Target*: `2-events/` with date prefix

4. **Task** - A specific, actionable item.
   - *Example*: "Call Mom", "Update dependencies"
   - *Target*: `4-tasks/` with checkbox `- [ ]`

5. **People** - A person or group of people.
   - *Example*: "John Doe", "Team X"
   - *Target*: `3-people/`

**Entity Extraction:**

If input contains **People** entities (especially `[[Name Surname]]` patterns):

- **Trigger**: `[[Capitalized Name]]` or clear person context
- **Action**: Output additional classification with `type: "People"`

**Date Extraction Rules** - Convert natural language dates to `YYYY-MM-DD`:

| Input | Calculation |
|-------|-------------|
| `morgen` | reference + 1 day |
| `overmorgen` | reference + 2 days |
| `volgende week` | next Monday |
| `donderdag` | next occurrence of Thursday |
| `eind deze week` | Friday of current week |
| `dit kwartaal` | last day of quarter |
| `deze maand` | last day of month |
| `Q1`, `Q2`... | last day of that quarter |
| `2027/Q2` | last day of Q2 2027 |

**Reference date**: The date of the source note.

**Confidence Scoring:**

Determine confidence (1-10):

- **High (≥8)**: Clear classification, unambiguous
- **Low (<8)**: Ambiguous, lacks context, multiple interpretations

**Output Format:**

```json
{
  "type": "Project | Concept | Event | Task | People | Unknown",
  "confidence": 8,
  "reasoning": "Why you chose this type.",
  "extracted_title": "Suggested title for note/task",
  "extracted_date": "YYYY-MM-DD (if applicable)",
  "extracted_assignee": "[[Name]] (if applicable)"
}
```

For multiple entities (e.g., a Task mentioning a Person), return array:

```json
[
  { "type": "Task", "confidence": 9, "extracted_title": "Call John about project" },
  { "type": "People", "confidence": 8, "extracted_title": "John" }
]
```

### 5.2. Staging Actions

Based on classification results:

1. **High Confidence (≥8/10)**:
   - Root files: Move to `9-staging/{type-folder}/`
   - Journal items: Mark with ✅, create linked note in staging. Mark every journal item with ✅, not the header. I need to see what has been processed and what has not.
2. **Low Confidence (<8/10)**:
   - Flag item with 🚩
   - Add to "Requires Attention" in report

### 5.3. Collision Rule

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

DO NOT put checkboxes (`- [ ]`) in the report

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
