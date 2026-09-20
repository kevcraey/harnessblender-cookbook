# browser-mcp

Eigen wrapper rond de upstream server, geen vendored kopie — `npx` haalt die live op.

- **Origin**: npm-package `@browsermcp/mcp@latest` (geen lokale clone nodig, `npx -y` pullt bij elke start).
- **Credentials**: geen — draait volledig lokaal, geen API-key nodig.
- **Nieuwe machine**: `mcp-browser.sh` werkt meteen zonder setup (node/npx moet geïnstalleerd zijn).

`.claude-plugin/.mcp.json` wijst met een absoluut pad naar `mcp-browser.sh` in deze map — niet
bundelbaar (zie harnessblender-conventie), dus enkel bruikbaar op deze machine.
