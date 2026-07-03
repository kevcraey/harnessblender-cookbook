---
name: sb-integrate-note
user-invocable: false
description: |
  Integrate a note into the Obsidian vault by adding wikilinks to existing people, projects,
  and concepts. Generic skill — works for meeting notes, concept notes, or any vault content.
---

# Integrate Note into Vault

## Input

A path to a vault note (markdown file) that needs to be enriched with backlinks.

## Workflow

### 1. Load vault indexes

Scan these directories to build a matching index:

```bash
# People (exact filenames without .md)
ls ~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain/3-people/ | sed 's/.md$//'

# Project MOCs (maxdepth 3: MOCs kunnen in een projectsubfolder zitten, bv. 7-projects/<project>/project-moc-<project>.md)
find ~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain/ -name "project-moc-*.md" -maxdepth 3 | sed 's/.*\///' | sed 's/.md$//'

# Concept notes
ls ~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain/1-notes/ | sed 's/.md$//'

# Domain MOCs
ls ~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain/0-index/ | sed 's/.md$//'
```

### 2. Match content against index

For each item in the index, check if it (or a recognizable variant) appears in the note text.

**Matching rules:**
- **People**: match on full name, first name + last name separately, or common abbreviations
- **Projects**: match on project title words (strip `project-moc-` prefix)
- **Concepts**: match on note title (strip hyphens, compare words)

**Confidence threshold:** >= 7/10 for all links

### 3. Add inline wikilinks

For each match with sufficient confidence:
- Replace the **first occurrence** in the body text with a `[[wikilink]]`
- If the match text differs from the note filename, use `[[filename|display text]]`
- Do NOT add links inside frontmatter, headings, or existing wikilinks

### 4. Update frontmatter `related-to`

Add matched items to the `related-to` array in frontmatter:
- People: always add if mentioned
- Projects: add if the meeting is clearly about that project (confidence >= 9/10)
- Concepts: add only at confidence >= 9/10

### 5. Validate — no red links

After all modifications, verify that every `[[wikilink]]` in the note points to an existing file in the vault. Remove any links that would be red (broken).

```bash
# Extract all wikilinks from the note
grep -oP '\[\[([^\]|]+)' note.md | sed 's/\[\[//' | while read link; do
  find ~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain/ -name "${link}.md" -maxdepth 3 | grep -q . || echo "RED LINK: $link"
done
```

## Output

The input note, modified in place with:
- Inline `[[wikilinks]]` on first occurrence of matched terms
- Updated `related-to` frontmatter array
- Zero red links guaranteed

## Scope

This skill handles **literal matching only**. Semantic matching via embeddings/RAG is a future enhancement and out of scope.
