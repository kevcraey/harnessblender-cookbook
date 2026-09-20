# strava-mcp

Eigen wrapper rond de upstream server, geen vendored kopie — `npx` haalt die live op.

- **Origin**: npm-package `@r-huijts/strava-mcp-server` (geen lokale clone nodig, `npx -y` pullt bij elke start).
- **Credentials**: macOS Keychain, generic password items `strava-client-id` en `strava-client-secret` (account = `$(whoami)`).
- **Nieuwe machine**: keychain-items aanmaken, dan werkt `strava-mcp.sh` meteen (node/npx moet geïnstalleerd zijn).

`.claude-plugin/.mcp.json` wijst met een absoluut pad naar `strava-mcp.sh` in deze map — niet
bundelbaar (zie harnessblender-conventie), dus enkel bruikbaar op deze machine.
