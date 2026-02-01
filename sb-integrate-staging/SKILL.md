---
name: sb-integrate-staging
description: Integrate staged notes into the permanent vault via semantic linking.
---

# Integrate Staging Workflow

Integrate "Staged Notes" into the permanent "Second Brain" by synthesizing connections.

> [!NOTE]
> See `references/moc-hierarchy.md` for MOC structure and domain assignment rules.

## 1. Safety Backup

- Execute the skill `safety-backup` with context: pre-integrate-{YYYY-MM-DD}

## 2. Input Analysis

### Sources

- All notes in `9-staging/`
- Previous reports outside `5-journal/`

### Context

- Existing vault: `1-notes`, `2-events`, `3-people`, `4-tasks`

## 3. Process Each Staged Note

For each note in `9-staging/`:

1. Read the content
2. Search existing vault for related concepts
3. Execute skill `sb-semantic-insert` to:
   - Create inline wikilinks to existing notes
   - Add `related-to` frontmatter for semantic connections
   - Identify emergent topics (≥3 related notes)
4. **Determine domain** based on content and existing MOC structure:
   - Match to existing domain MOC in `0-index/`
   - If no match, flag for potential new domain
5. **Update MOC chain**:
   - Add note link to relevant topic MOC (or create if ≥3 related notes)
   - Ensure topic MOC is linked from domain MOC

### Confidence Gating

- **High Confidence (≥8/10)**: Promote to permanent vault location
- **Low Confidence (<8/10)**: Keep in staging, add to report

## 4. User Handshake

> [!IMPORTANT]
> **Approval Required**: Present proposed promotions before executing. Do not promote without explicit user confirmation.

- Present items with their proposed connections and confidence scores.
- Wait for user approval before proceeding.

**STOP**: Do not proceed without explicit user confirmation.

## 5. Generate Report

**Always** generate: `{YYYY-MM-DD}-integrate-report.md` at vault root.

### Report Structure

```markdown
## 📌 Summary
Semantic summary of integration actions.

## 🕸️ Weaved (Promoted)
- [x] [[Note]] → Linked to [[A]], [[B]] (Confidence: X/10)

## ⏳ Staged (Pending)
### [?] [[note-title]]
> **Confidence**: {{Score}}/10
> **Reason**: Why was it not promoted?
```

## 6. Quality Assurance

- [ ] All promoted notes removed from `9-staging/`
- [ ] Staging structure intact: `9-staging/{1-notes,2-events,3-people,4-tasks}`
- [ ] Report files properly located at vault root

## 7. Finalize

- Execute the skill `safety-backup` with context: post-integrate-{YYYY-MM-DD}
