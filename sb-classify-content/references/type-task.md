# Type: Task

A specific, actionable item.

## Indicators

- Single action, not a project
- Can be completed in one session
- Contains verb or action language

## Examples

- "Call Mom"
- "Update dependencies"
- "Review PR #42"

## Target Location

`4-tasks/` with checkbox `- [ ]`

## Frontmatter

```yaml
tags:
  - type/task
```

## Task Format

All tasks must contain at least one checkbox:

```markdown
- [ ] Action to complete
```

## Date Parsing

Convert natural language dates to `(due::YYYY-MM-DD)`:

| Input | Calculation |
|-------|-------------|
| `morgen` | reference + 1 day |
| `overmorgen` | reference + 2 days |
| `volgende week` | next Monday |
| `donderdag` | next occurrence of Thursday |
| `eind deze week` | Friday of current week |
| `dit kwartaal` | last day of quarter |
| `deze maand` | last day of month |
