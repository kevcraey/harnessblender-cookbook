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
3. **Semantic Wiring** (see subsection 3.2 below):
   - Create inline wikilinks to existing notes
   - Add `related-to` frontmatter for semantic connections
   - Identify emergent topics (≥3 related notes)
4. **Determine domain** based on content and existing MOC structure:
   - Match to existing domain MOC in `0-index/`
   - If no match, flag for potential new domain
5. **Update MOC chain**:
   - Add note link to relevant topic MOC (or create if ≥3 related notes)
   - Ensure topic MOC is linked from domain MOC

### 3.2. Semantic Wiring

> [!NOTE]
> **Internal Subsystem**: This section performs semantic linking operations (formerly sb-semantic-insert).
> See `references/linking-rules.md` for detailed linking decision criteria.

Connect notes through bidirectional links and identify emergent topics.

#### 3.2.1. Concept Linking

**Goal**: Connect the new note to existing knowledge in `1-notes`, `2-events`, `3-people`, `4-tasks`.

**Inline Transform**:

1. **Scan**: Find keywords matching existing note titles or aliases
2. **Transform**: Convert to wikilinks (e.g., `latency` → `[[latency]]`)

**Constraints**:

- **Only** link if target note exists (no red/ghost links)
- **Only** link key concepts (ignore common words)
- **First occurrence**: Link only first mention per section to avoid visual clutter

**Frontmatter Linking**:

For semantic relations not mentioned explicitly:

```yaml
related-to:
  - "[[Existing Concept]]"
```

**Trigger**: Note is semantically related but doesn't mention the term.

#### 3.2.2. Emergent Topic Extraction

**Goal**: Identify when multiple notes form a new cluster.

**Trigger Conditions** - ≥3 notes that:

1. Are strongly connected to each other, OR
2. Reference the same *undefined* concept (e.g., "GDPR" mentioned 3x but no `gdpr.md`)

**Actions**:

1. **Create Topic Note**: `1-notes/{topic}.md`
2. **Synthesize**: Write definition:
   > "This topic sits at the intersection of [[A]], [[B]], and [[C]]."
3. **Refactor**: Update related notes with links to new hub

#### 3.2.3. Confidence Assessment

Evaluate quality of proposed changes:

| Score | Meaning |
|-------|---------|
| 9-10 | High value: creates structure, atomicity, new insights |
| 7-8 | Good value: meaningful connections |
| 5-6 | Moderate: links exist but not transformative |
| 1-4 | Low value: superficial or uncertain |

**Execution Gate**:

- **High Confidence (≥8/10)**: Proceed with changes
- **Low Confidence (<8/10)**: Do NOT proceed, flag for review

**Output Format**:

```json
{
  "confidence": 8,
  "inline_links": ["[[term1]]", "[[term2]]"],
  "frontmatter_links": ["[[Related Note]]"],
  "emergent_topics": [
    {
      "proposed_title": "Topic Name",
      "connected_notes": ["[[A]]", "[[B]]", "[[C]]"],
      "synthesis": "This topic sits at..."
    }
  ],
  "reasoning": "Why these connections were made."
}
```

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
- [ ] DO NOT put checkboxes (`- [ ]`) in the report

## 7. Finalize

- Execute the skill `safety-backup` with context: post-integrate-{YYYY-MM-DD}
