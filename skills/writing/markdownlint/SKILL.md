---
name: markdownlint
description: "Enforces Markdown linting standards. Use this skill when creating or updating markdown files.
---

# Format Markdown

Ensure all Markdown files adhere to the project's strict styling rules.

## Core Workflow

1. **Auto-fix**: Run the formatter script. This smart script attempts to use `markdownlint --fix` (if installed) for consistent behavior with your IDE. If not found, it falls back to a built-in Python implementation for common fixes.
   `python3 .agent/skills/format-markdown/scripts/fix_style.py document.md > document_fixed.md`

2. **Manual Review**: Check for semantic issues the linter cannot fix:
   - **MD001**: Heading levels must increment by exactly one (h1 -> h2, not h1 -> h3).
   - **MD025**: Ensure there is exactly one H1 title at the top.
   - **MD040**: Ensure all code blocks have a language identifier.

3. **Reference**: See `references/rules.md` for the complete list of applied rules.

## Common Fixes Applied by Script

- **MD004**: Converts `*` or `+` list markers to `-`.
- **MD009**: Removes trailing spaces.
- **MD010**: Converts tabs to spaces (2 spaces).
- **MD018**: Adds missing space after `#` in headings.
- **MD031**: Adds blank lines around code blocks.

## Integration

- Use this skill **before** using `jira-formatting` to ensure the source is clean.
- Use this skill **after** `write-user-story` to ensure the generated story is perfectly formatted.
