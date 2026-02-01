---
name: sb-scan-inbox
description: Scan for new content in journal and vault root to process.
---

# Scan Inbox

This skill identifies what needs to be processed. It looks for new content since the last processing run.

> [!NOTE]
> See `references/priority-rules.md` for prioritization logic.

## 1. Find Last Processing Point

Check for the most recent inbox report:

```bash
ls -t *-inbox-report.md 2>/dev/null | head -1
```

Or fall back to git history:

```bash
LAST_PROCESS=$(git log --oneline --grep="^backup: post-inbox" -1 --format="%H")
echo "Last inbox processing: $LAST_PROCESS"
```

## 2. Identify Root Files (Inbox Zero)

Find markdown files in vault root (these will be MOVED):

```bash
find . -maxdepth 1 -name "*.md" -type f ! -name "*-report.md"
```

**Action**: These files represent "Inbox Zero" items → Stage for processing.

## 3. Identify Journal Changes

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

## 4. Check for Pending Reports

Look for reports with unanswered questions:

```bash
find . -maxdepth 1 -name "*-report.md" -exec grep -l "Requires Attention" {} \;
```

## 5. Compile Inbox List

Combine all inputs with priority:

1. **Priority 1**: Unanswered questions from previous reports
2. **Priority 2**: Root `*.md` files (Inbox Zero)
3. **Priority 3**: New/modified journal entries

### Output Format

Return structured list:

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
