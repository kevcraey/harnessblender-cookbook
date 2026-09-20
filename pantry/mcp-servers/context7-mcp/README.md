# context7-mcp

Eigen wrapper rond de upstream server, geen vendored kopie — `npx` haalt die live op.

- **Origin**: npm-package `@upstash/context7-mcp` (geen lokale clone nodig, `npx -y` pullt bij elke start).
- **Credentials**: macOS Keychain, generic password item `context7-api-key` (account = `$(whoami)`).
- **Let op**: er lijkt ook een officiële Context7-marketplace-plugin geïnstalleerd te zijn
  (tools verschijnen als `mcp__plugin_context7_context7__*`) — check bij gebruik of je niet twee
  bronnen voor dezelfde server tegelijk actief hebt.
- **Nieuwe machine**: keychain-item aanmaken, dan werkt `mcp-context7.sh` meteen (node/npx moet geïnstalleerd zijn).

`.claude-plugin/.mcp.json` wijst met een absoluut pad naar `mcp-context7.sh` in deze map — niet
bundelbaar (zie harnessblender-conventie), dus enkel bruikbaar op deze machine.
