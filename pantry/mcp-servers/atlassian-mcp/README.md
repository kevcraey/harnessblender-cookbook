# atlassian-mcp

Eigen wrapper rond de upstream server, geen vendored kopie — `uvx` haalt die live op.

- **Origin**: PyPI-package `mcp-atlassian` (geen lokale clone nodig, `uvx` pullt bij elke start).
- **Credentials**: macOS Keychain, generic password items `jira-personal-token` en `confluence-personal-token` (account = `$(whoami)`).
- **Vaste config**: Jira/Confluence-URL's van Departement Omgeving zitten hardcoded in het script.
- **Nieuwe machine**: keychain-items aanmaken, dan werkt `mcp-atlassian.sh` meteen (uv/uvx moet geïnstalleerd zijn).

`.claude-plugin/.mcp.json` wijst met een absoluut pad naar `mcp-atlassian.sh` in deze map — niet
bundelbaar (zie harnessblender-conventie), dus enkel bruikbaar op deze machine.
