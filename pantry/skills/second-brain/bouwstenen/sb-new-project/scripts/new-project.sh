#!/usr/bin/env bash
# Maakt een nieuw project aan: subfolder in "01 - Projects" + project-MOC uit template.
# Gebruik: new-project.sh <slug> "<Titel>"
#   slug  = kebab-case projectnaam (wordt foldernaam en project-moc-<slug>.md)
#   Titel = H1 van de MOC
set -euo pipefail

VAULT="$HOME/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain"
TEMPLATE="$VAULT/03 - Resources/030 - Templates/template-project-moc.md"

if [ $# -lt 2 ]; then
    echo "Gebruik: new-project.sh <slug> \"<Titel>\"" >&2
    exit 1
fi

SLUG="$1"
TITLE="$2"
DIR="$VAULT/01 - Projects/$SLUG"
FILE="$DIR/project-moc-$SLUG.md"

if [ -e "$FILE" ]; then
    echo "Bestaat al: $FILE" >&2
    exit 1
fi

mkdir -p "$DIR"
TODAY="$(date +%F)"
sed -e "s/\[\[YYYY-MM-DD\]\]/[[${TODAY}]]/" \
    -e "s|^# Project/Program Name|# ${TITLE}|" \
    "$TEMPLATE" > "$FILE"

echo "Aangemaakt: $FILE"
