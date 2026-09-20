#!/usr/bin/env bash
# advance-marker.sh — verzet de marker naar HEAD. Draai dit pas NA de review,
# zodat een afgebroken run niks verliest. Idempotent.
set -euo pipefail
VAULT="${VAULT:-$HOME/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain}"
cd "$VAULT"
git tag -f brain-sync-last HEAD >/dev/null
echo "marker brain-sync-last -> $(git rev-parse --short HEAD)"
