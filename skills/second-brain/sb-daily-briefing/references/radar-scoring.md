# Radar Bewaking Scoring

Contextuele scoring per content type voor detectie van vergeten items.

## Scoring Formule

```
score = (tijd_weight × tijd_score) + (topic_weight × topic_score) + (freq_weight × freq_score)
```

## Weights Per Type

| Type | Tijd | Topic Relevantie | Edit Frequency |
|------|------|------------------|----------------|
| Task | 50% | 30% | 20% |
| Note | 20% | 60% | 20% |
| Event | 70% | 20% | 10% |

## Thresholds

| Type | Stil Periode | Score Threshold |
|------|-------------|----------------|
| Task | >7 dagen | >6/10 |
| Note | >14 dagen | >7/10 |
| Event | >3 dagen | >8/10 |

## Score Componenten

### Tijd Score (0-10)

```
tijd_score = min(10, dagen_sinds_edit / threshold_dagen × 10)
```

### Topic Relevantie Score (0-10)

- 10: File naam bevat keyword uit top 3 dominant topics
- 7: File pad bevat MOC uit sliding window
- 5: Frontmatter `related-to` links naar actief domein
- 0: Geen relatie

### Edit Frequency Score (0-10)

```
historisch_patroon = edits_laatste_maand / 30
recent_patroon = edits_laatste_week / 7

als historisch_patroon > 2× recent_patroon:
  freq_score = 10
anders:
  freq_score = 0
```

## Voorstellen Genereren

| Score Range | Voorstel |
|-------------|----------|
| 8-10 | "Review urgently, of archiveer als niet meer relevant?" |
| 6-8 | "Review status, of prioriteer deze week?" |
| 4-6 | "Bekijk of dit nog actueel is" |
