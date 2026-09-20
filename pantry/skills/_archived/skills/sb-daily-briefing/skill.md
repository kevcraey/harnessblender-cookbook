---
name: sb-daily-briefing
description: Genereer intelligente morning briefing in daily journal
---

# Daily Briefing Workflow

Deze skill genereert een morning briefing in je daily journal met:
- Macro trend (laatste 20 dagen)
- Recente activiteit (48u sliding window)
- Taken focus (overdue + hot topics)
- Radar bewaking (vergeten items)

## Gebruik

```bash
/daily-briefing
# of met specifieke datum
/daily-briefing 2026-02-15
```

## Workflow Stappen

### 1. Bepaal Target Datum

**Argument parsing:**
- Als geen argument: gebruik vandaag (`date +%Y-%m-%d`)
- Als argument gegeven: valideer format YYYY-MM-DD

**Output:** `TARGET_DATE` variabele (bijv. `2026-02-10`)

### 2. Bepaal Journal Pad

**Logica:**
- Extract jaar/maand/dag uit `TARGET_DATE`
- Pad: `04 - Journal/{YYYY}/{MM}/{DD}/{YYYY-MM-DD}.md`
- Voorbeeld: `04 - Journal/2026/02/10/2026-02-10.md`

**Als journal niet bestaat:**
- Creëer parent directories
- Schrijf basic journal template (format zal beschikbaar zijn in references/)

### 3. Laad Vorige Briefing

**Doel:** Haal macro trend op voor incrementele update

**Logica:**
- Bepaal gisteren's datum (of laatste actieve dag met journal)
- Pad: `04 - Journal/{YYYY}/{MM}/{DD}/{YYYY-MM-DD}.md`
- Parse sectie `## 📊 Trend (laatste 20 dagen)`

**Als vorige briefing niet bestaat:**
- Start fresh (macro trend wordt nieuw aangemaakt)

### 4. Analyseer Git Activity (Sliding Window)

**Doel:** Vind 24u netto activiteit, max 7 dagen lookback

**Command:**
```bash
git log --since="7 days ago" --pretty=format:"%H|%at|%s" --name-status
```

**Parsing logica:**
- Loop door commits van nieuw naar oud
- Track totale "netto activiteit tijd" (tijd tussen eerste en laatste commit in batch)
- Stop als 24u activiteit bereikt OF 7 dagen lookback
- Extraheer per commit:
  - Timestamp
  - Commit message
  - Gewijzigde files (A/M/D status)
  - File paths (classificeer per folder: "00 - Maps of Content", "01 - Projects", "02 - Areas", "03 - Resources/031 - People", "05 - Tasks")

**Output data:**
- `commits[]`: Array van commits met metadata
- `file_changes{}`: Map van folders → aantal changes
- `dominant_topics[]`: Top 3 keywords/MOCs

### 5. Scan Vault State

**Taken scan:**
- Glob: `05 - Tasks/*.md`
- Per task file:
  - Parse `(due::YYYY-MM-DD)` → overdue lijst
  - Parse checkboxes `- [ ]` → open taken lijst
  - Extract file naam zonder .md → taak naam

**Events scan:**
- Glob: `02 - Areas/*.md`
- Enkel notes met tag `type/meeting`, `type/event` of `type/decision` (kennis en events delen die map)
- Filter op datum in naam ≤ TARGET_DATE + 7 dagen (upcoming)

### 6. Genereer Macro Trend

**Als vorige briefing bestaat:**
- Parse trend regels (max 20)
- Drop oudste regel als al 20 regels
- Voeg nieuwe regel toe voor gisteren/laatste activiteit

**Format nieuwe regel:**
```
- **{dag} {maand}** → {topic1}, {topic2}, {aantal} taken voltooid
```

**Als geen vorige briefing:**
- Start met 1 regel voor sliding window periode

### 7. Genereer Recent Detail

**Narrative structuur (1-3 paragrafen):**

Paragraaf 1: Dominant thema + kwantitatieve metrics
- "Gisteren lag de focus op..."
- Aantal notes/people/events/tasks

Paragraaf 2: Specifieke domeinen + activiteiten
- "Het domein X blijft actief met Y edits..."

Paragraaf 3: Call-to-action
- Staging reminder
- Pending reviews

### 8. Genereer Vandaag Focus

**Structuur:**

```markdown
### ⚠️ Overdue
{overdue_tasks}

### 🔥 Hot Topics (recent actief)
{hot_topic_groups}

### 📋 Overige Taken
{other_tasks}
```

**Hot topics matching:**
- Match task file names tegen dominant_topics uit sliding window
- Group by topic

### 9. Genereer Radar Bewaking

**Voor elke task/note:**
- Bereken score (scoring criteria zal beschikbaar zijn in references/)
- Filter op threshold (task >6/10, note >7/10)
- Genereer voorstellen (Review? Archiveer? Prioriteer?)

**Format:**
```markdown
- [[item-naam]] — {reden}. **Voorstel**: {actie}
```

### 10. Inject Briefing

**Logica:**
- Read journal file
- Check of `## 🤖 Briefing` bestaat
  - Ja: Replace volledige sectie tot volgende `#` header
  - Nee: Append aan einde van file

**Format:**
```markdown
## 🤖 Briefing

### 📊 Trend (laatste 20 dagen)
{macro_trend}

### 📝 Recente Activiteit (48u)
{recent_detail}

### 🎯 Vandaag
{focus_tasks}

### 🔍 Van Radar Geraakt?
{radar_items}
```

### 11. Write Journal File

- Gebruik Edit tool als file bestaat
- Gebruik Write tool als nieuwe file

### 12. Optioneel: Git Commit

**Command:**
```bash
git add "04 - Journal/{YYYY}/{MM}/{DD}/{YYYY-MM-DD}.md"
git commit -m "briefing: {YYYY-MM-DD}

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

## Implementatie Details

### Datum Parsing

**Vandaag bepalen:**
```bash
TARGET_DATE=$(date +%Y-%m-%d)
```

**Argument parsing:**
```bash
if [ -n "$1" ]; then
  # Valideer format YYYY-MM-DD
  if [[ "$1" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    TARGET_DATE="$1"
  else
    echo "Error: Invalid date format. Use YYYY-MM-DD"
    exit 1
  fi
fi
```

**Extract components:**
```bash
YEAR=$(echo $TARGET_DATE | cut -d'-' -f1)
MONTH=$(echo $TARGET_DATE | cut -d'-' -f2)
DAY=$(echo $TARGET_DATE | cut -d'-' -f3)
```

**Journal pad:**
```bash
JOURNAL_PATH="04 - Journal/$YEAR/$MONTH/$DAY/$TARGET_DATE.md"
```

**Gisteren bepalen (voor vorige briefing):**
```bash
YESTERDAY=$(date -d "$TARGET_DATE -1 day" +%Y-%m-%d 2>/dev/null || date -v-1d -j -f "%Y-%m-%d" "$TARGET_DATE" +%Y-%m-%d)
PREV_YEAR=$(echo $YESTERDAY | cut -d'-' -f1)
PREV_MONTH=$(echo $YESTERDAY | cut -d'-' -f2)
PREV_DAY=$(echo $YESTERDAY | cut -d'-' -f3)
PREV_JOURNAL="04 - Journal/$PREV_YEAR/$PREV_MONTH/$PREV_DAY/$YESTERDAY.md"
```

### Git Log Sliding Window

**Query commits (7 dagen lookback):**
```bash
git log --since="7 days ago" --pretty=format:"%H|%at|%s" --name-status --no-merges > /tmp/git-activity.txt
```

**Parse commits met Grep/Read tools:**
- Read `/tmp/git-activity.txt`
- Per commit: extract hash, timestamp, message
- Per file change: extract status (A/M/D) en path

**Categoriseer files:**
```
00 - Maps of Content/          → MOC changes (domain)
01 - Projects/                 → Project-MOC changes
02 - Areas/                    → Concept- en event-changes (onderscheid via type-tag)
03 - Resources/031 - People/   → People changes
05 - Tasks/                    → Task changes
```

**Extract keywords:**
- Van commit messages: split op spaties, filter stopwoorden (de, het, een, van, voor)
- Van file paths: extract MOC namen (moc-{domain})
- Van file names: extract basenaam zonder .md

**Dominant topics (top 3):**
- Count keyword frequency
- Return top 3 met hoogste count

### Task Scanning

**Scan alle tasks:**
```bash
# Via Glob tool: 05 - Tasks/*.md
```

**Parse per task:**
- Read task file
- Extract `(due::YYYY-MM-DD)` met regex
- Count open checkboxes `- [ ]` (exclude `- [x]`)
- Extract filename zonder .md voor wikilink

**Overdue detectie:**
```bash
# Als due date < TARGET_DATE
# Bereken dagen overdue: TARGET_DATE - due_date
```

**Hot topics matching:**
- Match task filename keywords tegen dominant_topics[]
- Group tasks per topic
- Count edits per topic uit git log

**Output structuur:**
```
overdue_tasks[] = [
  {name: "taak-1", days_overdue: 3},
  {name: "taak-2", days_overdue: 7}
]

hot_topics[] = [
  {
    topic: "AI Agents",
    edits: 4,
    tasks: ["strategie-coding-agents", "bekijken-video-ai"]
  }
]

other_tasks[] = ["taak-x", "taak-y"]
```

### Radar Bewaking

**Scan vault voor kandidaten:**
```bash
# Tasks:  Glob 05 - Tasks/*.md (filter op geen recente edits)
# Notes:  Glob 02 - Areas/*.md, tag type/concept (filter op geen recente edits)
# Events: Glob 02 - Areas/*.md, tag type/meeting|type/event (upcoming zonder prep)
```

**Per item, bereken score:**

```python
# Pseudo-code voor scoring
def calculate_radar_score(item, item_type, dominant_topics):
    # Tijd component
    days_since_edit = (TODAY - item.last_modified).days
    if item_type == "task":
        time_score = min(10, days_since_edit / 7 * 10)
        time_weight = 0.5
        threshold_days = 7
        score_threshold = 6
    elif item_type == "note":
        time_score = min(10, days_since_edit / 14 * 10)
        time_weight = 0.2
        threshold_days = 14
        score_threshold = 7

    # Topic relevantie component
    topic_score = 0
    if any(topic in item.filename for topic in dominant_topics):
        topic_score = 10
    elif any(moc in item.path for moc in active_mocs):
        topic_score = 7

    if item_type == "task":
        topic_weight = 0.3
    else:
        topic_weight = 0.6

    # Edit frequency component
    edits_last_month = count_edits(item, days=30)
    edits_last_week = count_edits(item, days=7)
    freq_score = 10 if edits_last_month / 30 > 2 * edits_last_week / 7 else 0
    freq_weight = 0.2

    # Total score
    score = (time_weight * time_score +
             topic_weight * topic_score +
             freq_weight * freq_score)

    return score, (days_since_edit > threshold_days and score > score_threshold)
```

**Genereer voorstellen:**
```
score 8-10: "Review urgently, of archiveer als niet meer relevant?"
score 6-8: "Review status, of prioriteer deze week?"
```

**Output format:**
```markdown
- [[item-naam]] — Laatst bewerkt {X} dagen geleden, gerelateerd aan actief domein "{topic}". **Voorstel**: {suggestie}
```

### Briefing Generatie

**Macro Trend (incrementeel):**

Als vorige briefing bestaat:
1. Parse `## 📊 Trend (laatste 20 dagen)` sectie
2. Extract regels (format: `- **{dag} {maand}** → ...`)
3. Als ≥20 regels: drop eerste (oudste)
4. Genereer nieuwe regel voor sliding window periode
5. Append aan lijst

Als geen vorige briefing:
1. Start met 1 regel voor huidige analyse

**Nieuwe regel format:**
```
- **{dag} {maand kort}** → {topic1}, {topic2}, {N} taken voltooid
```

Maand mapping:
```
01: jan, 02: feb, 03: mrt, 04: apr, 05: mei, 06: jun,
07: jul, 08: aug, 09: sep, 10: okt, 11: nov, 12: dec
```

**Recent Detail (narrative):**

Template:
```
{paragraaf_1_dominant_thema}

{paragraaf_2_specifieke_domeinen}

{paragraaf_3_call_to_action}
```

Paragraaf 1:
```
Gisteren lag de focus op {dominant_topic}. Er werden {N} notes toegevoegd
aan {M} domeinen, {P} taken voltooid, en {Q} meetings gepland.
```

Paragraaf 2:
```
Het domein "{top_domain}" blijft het meest actief met {X} edits verspreid over
{subtopics}. Daarnaast {other_activity}.
```

Paragraaf 3:
```
Er ligt nog werk in staging ({N} items) dat geïntegreerd moet worden.
```

**Vandaag Focus:**

Format:
```markdown
### ⚠️ Overdue
{for each overdue_task}
- [[{task.name}]] ({task.days_overdue} dagen)

### 🔥 Hot Topics (recent actief)
{for each hot_topic}
**{topic.name}** ({topic.edits} edits afgelopen 48u)
{for each task in topic.tasks}
- [[{task}]]

### 📋 Overige Taken
{for each other_task}
- [[{task}]]
```

**Radar Bewaking:**

Format:
```markdown
{for each radar_item}
- [[{item.name}]] — Laatst bewerkt {item.days} dagen geleden, gerelateerd aan actief domein "{item.topic}". **Voorstel**: {item.suggestion}
```

### Journal Injection

**Lees bestaand journal (of creëer nieuw):**

Als `JOURNAL_PATH` niet bestaat:
1. Creëer parent directories: `mkdir -p "04 - Journal/$YEAR/$MONTH/$DAY"`
2. Write journal template (zie references/journal-template.md)
3. Replace variabelen: `{YYYY-MM}`, `{YYYY-MM-DD}`

**Injection logic:**

1. Read journal content
2. Check of `## 🤖 Briefing` sectie bestaat
   - Search voor regex: `^## 🤖 Briefing`

Als sectie bestaat:
- Find start index (lijn met `## 🤖 Briefing`)
- Find end index (volgende lijn met `^#` of EOF)
- Replace content tussen start en end

Als sectie niet bestaat:
- Append aan einde van file

**Briefing content template:**
```markdown
## 🤖 Briefing

### 📊 Trend (laatste 20 dagen)
{macro_trend_lines}

### 📝 Recente Activiteit (48u)
{narrative_paragraphs}

### 🎯 Vandaag
{focus_sections}

### 🔍 Van Radar Geraakt?
{radar_items}
```

**Write met Edit/Write tools:**
- Als file bestaat: gebruik Edit tool (old_string = oude briefing sectie, new_string = nieuwe)
- Als nieuwe file: gebruik Write tool

## Kritieke Regels

- **Geen checkboxes**: Output mag NOOIT `- [ ]` bevatten
- **Alleen wikilinks**: Verwijs naar taken als `[[taak-naam]]`
- **Nederlands**: Alle gegenereerde tekst in Nederlands
- **Incrementeel**: Macro trend bouwt voort, niet volledig heranalyseren
