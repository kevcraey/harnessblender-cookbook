# Scoring Reference

Scoring thresholds used across Second Brain skills.

## Pattern Scoring (sb-identify-patterns)

| Signal | Score Boost |
|--------|-------------|
| Multiple undefined references | +3 |
| Tight link cluster (density >0.5) | +2 |
| Temporal spike (3x baseline) | +2 |
| High hub connectivity | +1 |

**Proposal Threshold**: Patterns scoring ≥5 are worth proposing.

## Confidence Scoring (General)

| Score | Meaning | Action |
|-------|---------|--------|
| 9-10 | Very high confidence | Proceed autonomously |
| 8 | High confidence | Proceed autonomously |
| 7 | Moderate-high | Proceed with logging |
| 5-6 | Moderate | Flag for review |
| 1-4 | Low | Do NOT proceed, require user input |

## Staging Threshold

- **High Confidence (≥8/10)**: Proceed with action
- **Low Confidence (<8/10)**: Flag for user review
