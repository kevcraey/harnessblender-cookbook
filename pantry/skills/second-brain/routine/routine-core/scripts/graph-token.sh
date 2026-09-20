#!/usr/bin/env bash
# graph-token.sh — Graph-token van het klembord naar een bestand in de run-map.
#
#   graph-token.sh save <run-dir>    klembord -> <run-dir>/.gtok (mode 600); exit 1 als
#                                    er geen geldig token op het klembord staat, 2 als
#                                    Graph het afwijst (verlopen)
#   graph-token.sh clear <run-dir>   verwijdert het tokenbestand
#
# Het token wordt nooit geprint. Wat er wél geprint wordt: OK / GEEN TOKEN / ONGELDIG.
# Het openen van Graph Explorer op de Access token-tab doet de orchestrator via de
# Chrome-plugin; de klik op Copy blijft van Kenzo (automatisering krijgt geen
# user-gesture, dus geen klembord).
set -euo pipefail
cmd="${1:-}"; dir="${2:-}"
[ -n "$dir" ] || { sed -n '2,12p' "$0"; exit 2; }
f="$dir/.gtok"
case "$cmd" in
  save)
    t=$(pbpaste | tr -d '[:space:]')
    if [ "${#t}" -lt 500 ] || [ "$(printf '%s' "$t" | tr -cd '.' | wc -c | tr -d ' ')" != "2" ]; then
      echo "GEEN TOKEN op het klembord (Graph Explorer -> tab 'Access token' -> Copy)."; exit 1
    fi
    code=$(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $t" \
      'https://graph.microsoft.com/v1.0/me?$select=id')
    if [ "$code" != "200" ]; then echo "ONGELDIG ($code) — kopieer een vers token."; exit 2; fi
    umask 077; printf '%s' "$t" > "$f"; chmod 600 "$f"
    echo "OK — token in $f"
    ;;
  clear) rm -f "$f"; echo "token gewist" ;;
  *) sed -n '2,12p' "$0"; exit 2 ;;
esac
