#!/bin/bash
# Mermaid MCP server — genereert diagrammen vanuit Mermaid markup
# Geen API-key nodig, draait volledig lokaal via npx
# Upstream start enkel als import.meta.url === file://argv[1]; via de npx-bin-symlink
# faalt die check en sluit het proces stil af. Daarom de bin via realpath starten.
exec npx -y -p @narasimhaponnada/mermaid-mcp-server sh -c 'exec node "$(realpath "$(command -v mermaid-mcp)")" "$@"' sh "$@"
