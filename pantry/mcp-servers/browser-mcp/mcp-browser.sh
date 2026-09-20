#!/bin/bash
# 1. Mocht dit pakket ooit een browser-token of API-key nodig hebben,
# kun je die hier weer uit de Keychain vissen.

# 2. Voer npx uit met de specifieke package en versie
# We voegen -y toe zodat hij niet blijft hangen op een 'install' prompt
exec npx -y @browsermcp/mcp@latest "$@"