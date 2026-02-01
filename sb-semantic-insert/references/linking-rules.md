# Linking Rules

Rules for semantic linking in Second Brain notes.

## Inline Links

Transform keywords to wikilinks when:

1. **Target exists**: Only link if target note exists (no red/ghost links)
2. **Key concepts only**: Ignore common words, pronouns, articles
3. **First occurrence**: Link only first mention per section to avoid visual clutter

### Example

```markdown
# Before
The latency of the API was impacting user experience.

# After
The [[latency]] of the [[API]] was impacting user experience.
```

## Frontmatter Links

Use `related-to` frontmatter for semantic relations NOT explicitly mentioned in text:

```yaml
related-to:
  - "[[Parent Concept]]"
  - "[[Sibling Concept]]"
```

### When to Use

- Note is semantically related but doesn't mention the term directly
- Concept is a "parent" or category of the current note
- Notes share context but link would be awkward inline

## Confidence Thresholds

| Score | Linking Decision |
|-------|------------------|
| 9-10 | Create inline links and frontmatter |
| 7-8 | Create inline links only |
| 5-6 | Add to frontmatter only, flag for review |
| <5 | Do NOT link, flag for user decision |
