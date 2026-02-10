# skills

repository for storing skills

## Skills

### Daily Topic Refresh (sb-daily-topic-refresh)

Generates a morning report section that refreshes a previously studied topic.

**Core principle**: "Herleer, niet herlijst" - teach the topic again rather than listing what's known.

**New: Discovery Engine** - Always suggests 3 related topics to explore based on:
- **Graph analysis**: Stub notes and broken links in your vault network
- **Semantic gaps**: Concepts mentioned but not yet documented
- **Smart fallback**: Domain matching and reasoning when direct connections are sparse

Output includes "Verken verder" section with actionable learning suggestions.

See `sb-daily-topic-refresh/references/discovery-engine.md` for details.

## Skill folder template

``` txt
skill-name/
├── SKILL.md         # Hoofdinstructies voor Claude
├── README.md        # Documentatie voor mensen
├── assets/          # Optioneel: templates, scripts, etc.
├── references/      # Optioneel: extra details van en over de skill
└── examples/        # Optioneel: voorbeeldbestanden
```

## Skill template

``` md
name: {skill-name}
description: "short description of the skill"
---
# {skill title}

```
