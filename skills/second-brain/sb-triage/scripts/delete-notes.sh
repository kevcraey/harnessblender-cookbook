#!/usr/bin/env bash
# Verwijdert vault-notes uit de lijst die sb-triage na goedkeuring wegschrijft.
# Gebruik: delete-notes.sh [lijstbestand]   (default: ~/.sb-triage-delete-list.txt)
set -euo pipefail

LIST="${1:-$HOME/.sb-triage-delete-list.txt}"

if [ ! -f "$LIST" ]; then
    echo "Geen lijst gevonden: $LIST"
    exit 1
fi

echo "Te verwijderen:"
nl -ba "$LIST"
echo
read -r -p "Verwijderen? [y/N] " answer
if [ "$answer" != "y" ] && [ "$answer" != "Y" ]; then
    echo "Afgebroken — niets verwijderd, lijst blijft staan."
    exit 0
fi

while IFS= read -r f; do
    [ -z "$f" ] && continue
    if [ -f "$f" ]; then
        rm "$f"
        echo "verwijderd: $f"
    else
        echo "niet gevonden (overgeslagen): $f"
    fi
done < "$LIST"

rm "$LIST"
echo "Klaar — lijst opgeruimd."
