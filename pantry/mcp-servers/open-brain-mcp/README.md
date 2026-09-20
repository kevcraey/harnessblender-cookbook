# open-brain-mcp

Geen wrapper-script (`command`) maar drie HTTP-type MCP-declaraties naar Supabase edge functions.

- **Origin**: eigen Supabase-project (`sprcigogvwvulkkbevxj`), geen upstream om te pullen.
- **Credentials**: macOS Keychain, generic password item `open-brain-key` (account = `$(whoami)`).
  HTTP-type servers ondersteunen geen `command`-wrapper, dus de key wordt via
  [`headersHelper`](https://code.claude.com/docs/en/mcp.md) opgehaald: `open-brain-headers.sh`
  print de headers-JSON dynamisch bij elke start — geen plaintext key meer in `.mcp.json`.
- **Nieuwe machine**: keychain-item `open-brain-key` aanmaken.

Voorheen stond de key hier hardcoded in `.mcp.json` — verplaatst naar keychain op 2026-09-20.
