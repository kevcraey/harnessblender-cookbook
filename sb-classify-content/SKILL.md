---
name: sb-classify-content
description: Classify text as Project, Concept, Event, Task, or People.
---

# Classify Content

Analyze a discrete item (paragraph, list item, or file) and determine its type.

> [!NOTE]
> Detailed type definitions are in `references/type-{type}.md` files.

## Classification Rules

### 1. Project

A collection of tasks/work achieving a specific goal.

- *Example*: "Redesign website homepage", "Plan summer vacation"
- *Target*: `4-tasks/` with project tag

### 2. Concept

Pure knowledge, definitions, mental models.

- *Example*: "RAG architecture explained", "Difference between taxonomy and ontology"
- *Target*: `1-notes/`

### 3. Event

Something that happened at a specific moment.

- *Example*: "Meeting with Client X on 2026-01-20", "Conference Y attended yesterday"
- *Target*: `2-events/` with date prefix

### 4. Task

A specific, actionable item.

- *Example*: "Call Mom", "Update dependencies"
- *Target*: `4-tasks/` with checkbox `- [ ]`

### 5. People

A person or group of people.

- *Example*: "John Doe", "Team X"
- *Target*: `3-people/`

## Entity Extraction

If input contains **People** entities (especially `[[Name Surname]]` patterns):

- **Trigger**: `[[Capitalized Name]]` or clear person context
- **Action**: Output additional classification with `type: "People"`

## Date Extraction Rules

Convert natural language dates to `YYYY-MM-DD`:

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

## Confidence Scoring

Determine confidence (1-10):

- **High (≥8)**: Clear classification, unambiguous
- **Low (<8)**: Ambiguous, lacks context, multiple interpretations

## Output Format

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
