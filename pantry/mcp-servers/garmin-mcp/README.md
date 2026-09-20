# garmin-mcp

Eigen wrapper rond de upstream server, geen vendored kopie — `uvx` haalt die live op.

- **Origin**: `git+https://github.com/Taxuspt/garmin_mcp` (geen lokale clone nodig, `uvx --from` pullt bij elke start).
- **Credentials**: macOS Keychain, generic password items `garmin-email` en `garmin-password` (account = `$(whoami)`).
- **Nieuwe machine**: keychain-items aanmaken, dan werkt `mcp-garmin.sh` meteen (uv + uvx moeten geïnstalleerd zijn).

`.claude-plugin/.mcp.json` wijst met een absoluut pad naar `mcp-garmin.sh` in deze map — niet
bundelbaar (zie harnessblender-conventie), dus enkel bruikbaar op deze machine.
