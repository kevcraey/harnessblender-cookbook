#!/usr/bin/env bash
# scan-changes.sh — deterministische voorfilter voor update-open-brain.
#
# Doet al het werk dat GEEN oordeel vereist, zodat de LLM enkel wordt
# ingeschakeld als er echte nieuwe proza in de vault staat:
#   1. bootstrap (eerste run zet enkel de marker, forward-only)
#   2. snapshot-commit van de working tree
#   3. git-diff sinds de marker, met pathspec-excludes
#   4. per file enkel toegevoegde regels; frontmatter/links/scaffolding weg
#   5. files onder de proza-drempel vallen weg
#   6. leeg resultaat -> "EMPTY" (LLM hoeft niks te doen)
#
# De marker (tag brain-sync-last) wordt hier NIET verzet — dat doet de skill
# pas na de review, zodat een afgebroken run niks verliest.
#
# Uitvoer op stdout: per overlevende file een blok
#   ===FILE=== <vault-relatief-pad>
#   <toegevoegde prozaregels>
# of de losse regel  EMPTY  als er niks zinvols is.
#
# Env:
#   VAULT           vault-root (default: Kenzo's Second Brain)
#   BRAIN_MIN_WORDS netto prozawoorden-drempel per file (default 12)
#   BRAIN_SINCE     override startpunt i.p.v. de marker (voor backfill)

set -euo pipefail

VAULT="${VAULT:-$HOME/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain}"
MIN_WORDS="${BRAIN_MIN_WORDS:-12}"
MARKER="brain-sync-last"

cd "$VAULT"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "FOUT: $VAULT is geen git-repo." >&2
  exit 1
fi

# ── 1. bootstrap ─────────────────────────────────────────────────────────────
if ! git rev-parse -q --verify "refs/tags/$MARKER" >/dev/null 2>&1; then
  if [ -n "${BRAIN_SINCE:-}" ]; then
    git tag "$MARKER" "$BRAIN_SINCE"
    echo "BOOTSTRAP: marker gezet op $BRAIN_SINCE. Draai opnieuw om die changes te scannen." >&2
  else
    git tag "$MARKER" HEAD
    echo "BOOTSTRAP: marker gezet op HEAD (forward-only). Geen historische scan; draai opnieuw na wijzigingen." >&2
  fi
  echo "EMPTY"
  exit 0
fi

BASE="${BRAIN_SINCE:-$MARKER}"

# ── 2. snapshot-commit ───────────────────────────────────────────────────────
if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git commit -q -m "brain-sync: snapshot $(date +%F)" || true
fi

# ── 3./4./5. diff + deterministische filter ──────────────────────────────────
# Pathspec-excludes: structurele/ruis-paden die nooit kennis dragen.
git -c core.quotepath=false diff "$BASE"..HEAD --unified=0 --no-color -- \
  '*.md' \
  ':(exclude).obsidian/**' \
  ':(exclude).trash/**' \
  ':(exclude)99 - Attachments/**' \
  ':(exclude).smart-env/**' \
  ':(exclude)**/mcp-tools/**' \
  ':(exclude)00 - Maps of Content/**' \
  ':(exclude)03 - Resources/030 - Templates/**' \
| awk -v MIN="$MIN_WORDS" '
  # nieuwe file
  /^\+\+\+ b\// {
    flush()
    path = substr($0, 7)          # strip "+++ b/"
    sub(/[ \t]+$/, "", path)      # git plakt een tab achter paden met spaties
    gsub(/^"|"$/, "", path)       # quotepath-quotes weg
    next
  }
  /^\+\+\+ \/dev\/null/ { flush(); path=""; next }   # deletion target
  # enkel echte toegevoegde regels (niet de +++ header)
  /^\+/ && !/^\+\+\+/ {
    if (path == "") next
    line = substr($0, 2)          # strip leidende +
    if (keep(line)) { buf[path] = buf[path] line "\n"; words[path] += nwords(line) }
    next
  }
  END { flush() }

  # ── helpers ──
  function keep(l,   t) {
    t = l
    gsub(/^[ \t]+|[ \t]+$/, "", t)
    if (t == "") return 0
    if (t == "---") return 0                       # frontmatter-grens / hr
    if (l ~ /^[ \t]+-[ \t]/) return 0              # ingesprongen YAML-seq-item
    if (t ~ /^[a-z][a-z0-9_-]*::?([ \t].*)?$/) return 0  # lowercase frontmatter/dataview-key (met of zonder waarde)
    if (t ~ /^#{1,6}[ \t]/) return 0               # kop
    if (t ~ /^> \[!/) return 0                     # callout-marker
    if (t ~ /^\|/) return 0                        # tabelrij
    if (t ~ /^(-{3,}|`{3,}|~{3,})/) return 0       # hr / codefence
    if (t ~ /^[-*+][ \t]+\[[ xX]\][ \t]*$/) return 0  # lege checkbox
    # kale metadata-regel: enkel #tags en/of [[links]] en leestekens
    if (t ~ /^([#][A-Za-z0-9_\/-]+|\[\[[^]]*\]\]|[[:space:],.;:-])+$/) return 0
    return 1
  }
  function nwords(l,   a) { return split(l, a, /[[:space:]]+/) }
  function flush() {
    if (path != "" && words[path] >= MIN && buf[path] != "") {
      printf "===FILE=== %s\n%s", path, buf[path]
    }
    if (path != "") { delete buf[path]; delete words[path] }
  }
' > /tmp/brain-scan-out.$$ || true

if [ -s /tmp/brain-scan-out.$$ ]; then
  cat /tmp/brain-scan-out.$$
else
  echo "EMPTY"
fi
rm -f /tmp/brain-scan-out.$$
