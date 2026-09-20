#!/bin/bash
CREDS_PATH="$HOME/.config/google-calendar-mcp/gcp-oauth.keys.json"
mkdir -p "$(dirname "$CREDS_PATH")"
security find-generic-password -a "$(whoami)" -s "google-calendar-oauth-keys" -w > "$CREDS_PATH"
chmod 600 "$CREDS_PATH"
export GOOGLE_OAUTH_CREDENTIALS="$CREDS_PATH"
exec npx -y @cocal/google-calendar-mcp "$@"
