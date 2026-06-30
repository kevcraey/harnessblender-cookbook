# Type: Event

Something that happened at a specific moment in time.

## Indicators

- Contains date reference (explicit or relative)
- Describes occurrence or experience
- Time-bound context

## Examples

- "Meeting with Client X on 2026-01-20"
- "Conference Y attended yesterday"
- "Product launch celebration"

## Target Location

`2-events/` with date prefix `{YYYY-MM-DD}-{title}.md`

## Frontmatter

```yaml
tags:
  - type/event
date: "[[YYYY-MM-DD]]"
```
