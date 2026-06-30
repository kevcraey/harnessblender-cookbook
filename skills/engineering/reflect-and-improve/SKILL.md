---
name: reflect-and-improve
description: Use when AI agent interaction feels suboptimal and user wants the lesson persisted. Optional arg names the friction; without arg, scan current transcript.
---

# reflect-and-improve

Turn friction into a config change on the right surface.

## Steps

1. **Diagnose** — list concrete friction points. Symptom + root cause. Skip one-shot mistakes; only persist recurring patterns. Examine BOTH sides: AI behavior AND the human's prompting/workflow. Root cause may be unclear instructions, missing context up front, premature scope, skipped clarification, or wrong tool choice by the user — name it directly, don't only fault the AI.

 **Pick surface per fix** (smallest that solves it):

   | Fix type                                            | Surface                                   |
   |-----------------------------------------------------|-------------------------------------------|
   | Automated trigger ("each time X", "before/after Y") | `settings.json` hooks via `update-config` |
   | Cross-project preference / tool policy              | global `~/.claude/CLAUDE.md`              |
   | Repo-specific convention                            | project `CLAUDE.md`                       |
   | Reusable on-demand procedure                        | new/edited skill                          |
   | User prompting / workflow habit                     | feedback to user, no config change        |

   Memory cannot execute behavior — automated triggers MUST be hooks.

4. **Propose** — table of fixes + exact diff/content. Wait for OK. User may accept subset.

5. **Apply** approved fixes via the matching sub-skill.

6. **Verify** path written. Give one trigger phrase to test next session.

## Rules

- Edit existing rules before adding new ones.
- Flag conflicts with existing CLAUDE.md, don't silently override.
