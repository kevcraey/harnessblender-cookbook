#!/bin/bash
# Mermaid MCP server — genereert diagrammen vanuit Mermaid markup
# Geen API-key nodig, draait volledig lokaal via npx
exec npx -y @narasimhaponnada/mermaid-mcp-server "$@"
