#!/bin/bash
# 1. Haal de API-key uit de Keychain
export CONTEXT7_API_KEY=$(security find-generic-password -a "$(whoami)" -s "context7-api-key" -w)

# 2. Voer de server uit via npx
# -y zorgt ervoor dat hij niet om bevestiging vraagt voor installatie
# We geven de API-key door via de vlag die zij verwachten
exec npx -y @upstash/context7-mcp --api-key "$CONTEXT7_API_KEY" "$@"