# google-calendar-mcp

Eigen wrapper rond de upstream server, geen vendored kopie — `npx` haalt die live op.

- **Origin**: npm-package `@cocal/google-calendar-mcp` (geen lokale clone nodig, `npx -y` pullt bij elke start).
- **Credentials**: macOS Keychain, generic password item `google-calendar-oauth-keys` (account = `$(whoami)`) — de OAuth-keys-JSON. De wrapper schrijft die bij elke start naar `~/.config/google-calendar-mcp/gcp-oauth.keys.json` (chmod 600).
- **Nieuwe machine**: keychain-item aanmaken met de OAuth-keys-JSON als waarde, dan werkt `google-calendar-mcp.sh` meteen (node/npx moet geïnstalleerd zijn).

`.claude-plugin/.mcp.json` wijst met een absoluut pad naar `google-calendar-mcp.sh` in deze map —
niet bundelbaar (zie harnessblender-conventie), dus enkel bruikbaar op deze machine.
