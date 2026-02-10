# Daily Briefing Skill

Morning briefing generator voor Second Brain vault.

## Features

- 📊 **Macro Trend**: Incrementele historiek van laatste 20 actieve dagen
- 📝 **Recent Detail**: Narrative analyse van 48u sliding window
- 🎯 **Vandaag Focus**: Overdue tasks + hot topics + overige taken
- 🔍 **Radar Bewaking**: Intelligente detectie van vergeten items

## Gebruik

```bash
# Genereer briefing voor vandaag
/daily-briefing

# Specifieke datum
/daily-briefing 2026-02-15
```

## Output Locatie

Briefing wordt geïnjecteerd in:
```
5-journal/{YYYY}/{MM}/{DD}/{YYYY-MM-DD}.md
```

Onder sectie: `## 🤖 Briefing`

## Architectuur

- **Git log parsing**: Sliding window voor activiteit detectie
- **Incrementele macro trend**: Bouwt voort op vorige briefing
- **Contextuele scoring**: Per-type scoring voor radar bewaking
- **Template-based**: Consistent markdown formatting

## Dependencies

- Git (voor history parsing)
- Bash (date utils, scripting)
- Claude tools: Grep, Glob, Read, Edit/Write

## Zie Ook

- Design doc: `docs/plans/2026-02-10-daily-briefing-design.md`
- Implementation: `docs/plans/2026-02-10-daily-briefing-implementation.md`
- Test plan: `tests/sb-daily-briefing/test-plan.md`
