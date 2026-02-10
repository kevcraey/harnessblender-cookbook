# Date Utilities Reference

Deze reference bevat date utilities voor de daily briefing workflow.

## Basis Date Operations

### Huidige Datum
```bash
date +%Y-%m-%d  # Output: 2026-02-10
```

### Datum Validatie
```bash
# Valideer YYYY-MM-DD format
if [[ "$DATE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo "Valid format"
fi
```

### Datum Componenten Extracten
```bash
TARGET_DATE="2026-02-10"
YEAR=$(echo "$TARGET_DATE" | cut -d'-' -f1)   # 2026
MONTH=$(echo "$TARGET_DATE" | cut -d'-' -f2)  # 02
DAY=$(echo "$TARGET_DATE" | cut -d'-' -f3)    # 10
```

## Datum Berekeningen

### Gisteren
```bash
# macOS/BSD
date -v-1d +%Y-%m-%d

# Linux/GNU
date -d "yesterday" +%Y-%m-%d
date -d "1 day ago" +%Y-%m-%d
```

### N Dagen Geleden
```bash
# macOS/BSD
date -v-7d +%Y-%m-%d  # 7 dagen geleden

# Linux/GNU
date -d "7 days ago" +%Y-%m-%d
```

### Datum Naar Unix Timestamp
```bash
# macOS/BSD
date -j -f "%Y-%m-%d" "2026-02-10" +%s

# Linux/GNU
date -d "2026-02-10" +%s
```

## Git Datum Filtering

### Since/Until
```bash
# Laatste 7 dagen
git log --since="7 days ago"

# Specifieke datum range
git log --since="2026-02-03" --until="2026-02-10"

# Unix timestamp format
git log --since="@$(date -d '7 days ago' +%s)"
```

### Parse Git Timestamp
```bash
# Git log output: %at (unix timestamp)
git log --pretty=format:"%at" -1  # Output: 1739187086

# Convert terug naar leesbaar
date -r 1739187086 +%Y-%m-%d  # macOS
date -d @1739187086 +%Y-%m-%d # Linux
```

## Datum Vergelijkingen

### Datum Verschil Berekenen
```bash
# Unix timestamps vergelijken
START_TS=$(date -d "2026-02-03" +%s)
END_TS=$(date -d "2026-02-10" +%s)
DIFF_SECONDS=$((END_TS - START_TS))
DIFF_DAYS=$((DIFF_SECONDS / 86400))  # 7 dagen
```

### Is Datum Overdue?
```bash
DUE_DATE="2026-02-08"
TODAY=$(date +%Y-%m-%d)

DUE_TS=$(date -d "$DUE_DATE" +%s)
TODAY_TS=$(date -d "$TODAY" +%s)

if [ $TODAY_TS -gt $DUE_TS ]; then
  echo "Overdue"
fi
```

## Datum Formatting

### Maand Namen (Nederlands)
```bash
# Voor trend output format
MONTH_NAMES=("" "jan" "feb" "mrt" "apr" "mei" "jun" "jul" "aug" "sep" "okt" "nov" "dec")
MONTH_NUM=2  # februari
echo "${MONTH_NAMES[$MONTH_NUM]}"  # feb
```

### Dag + Maand Format
```bash
DATE="2026-02-10"
DAY=$(echo "$DATE" | cut -d'-' -f3 | sed 's/^0//')  # 10
MONTH=$(echo "$DATE" | cut -d'-' -f2 | sed 's/^0//')  # 2
MONTH_NAMES=("" "jan" "feb" "mrt" "apr" "mei" "jun" "jul" "aug" "sep" "okt" "nov" "dec")
echo "$DAY ${MONTH_NAMES[$MONTH]}"  # 10 feb
```

## Cross-Platform Compatibility

```bash
# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS (BSD date)
  YESTERDAY=$(date -v-1d +%Y-%m-%d)
else
  # Linux (GNU date)
  YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
fi
```

## Relevante Use Cases voor Daily Briefing

1. **Target datum bepalen** (Step 1): `date +%Y-%m-%d` of valideer argument
2. **Journal pad construeren** (Step 2): Extraheer YYYY/MM/DD uit datum
3. **Vorige briefing laden** (Step 3): Bereken gisteren met `date -v-1d`
4. **Git sliding window** (Step 4): `git log --since="7 days ago"`
5. **Overdue taken detecteren** (Step 5): Vergelijk due date met vandaag
6. **Trend regel format** (Step 6): "10 feb" format voor Nederlandse output
