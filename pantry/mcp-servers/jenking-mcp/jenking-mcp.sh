#!/bin/bash
# Wrapper rond de Jenking MCP-server (github.com/Breina/Jenking).
# Installeert bij eerste start zelf de gepinde release-binary (checksum-geverifieerd),
# maakt indien nodig de jenking-config aan en leest de PAT uit de Keychain.
# Alle output naar stderr: stdout is voorbehouden aan MCP JSON-RPC.
set -euo pipefail

VERSION="v1.0.1"
SHA256_DARWIN_ARM64="e4d73a4c57137757288b996814dbf7f02d0212768a0e59f05563e319997cb9b4"
JENKINS_URL="https://jenkins.cumuli.be"
CONTEXT="cumuli"
KEYCHAIN_SERVICE="jenkins-pat"

INSTALL_DIR="$HOME/.local/share/jenking-mcp/$VERSION"
BIN="$INSTALL_DIR/jenking"
CONFIG="$HOME/.config/jenking/config.yaml"

# 1. Binary installeren als die nog ontbreekt
if [ ! -x "$BIN" ]; then
  if [ "$(uname -s)-$(uname -m)" != "Darwin-arm64" ]; then
    echo "jenking-mcp: enkel darwin/arm64 is gepind" >&2
    exit 1
  fi
  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' EXIT
  asset="Jenking_darwin_arm64.tar.gz"
  echo "jenking-mcp: download $VERSION" >&2
  curl -fsSL --proto '=https' -o "$tmp/$asset" \
    "https://github.com/Breina/Jenking/releases/download/$VERSION/$asset" >&2
  echo "$SHA256_DARWIN_ARM64  $tmp/$asset" | shasum -a 256 -c - >&2
  tar -xzf "$tmp/$asset" -C "$tmp" jenking
  mkdir -p "$INSTALL_DIR"
  mv "$tmp/jenking" "$BIN"
  chmod u+x "$BIN"
fi

# 2. Credentials uit de Keychain: account = Jenkins-username, wachtwoord = PAT
JENKINS_USER=$(security find-generic-password -s "$KEYCHAIN_SERVICE" | sed -n 's/.*"acct"<blob>="\(.*\)"/\1/p')
JENKINS_TOKEN=$(security find-generic-password -s "$KEYCHAIN_SERVICE" -w)
export JENKINS_TOKEN

# 3. Config enkel aanmaken als die ontbreekt (jenking schrijft er zelf ook in)
if [ ! -f "$CONFIG" ]; then
  mkdir -p "$(dirname "$CONFIG")"
  cat > "$CONFIG" <<YAML
contexts:
  - name: $CONTEXT
    url: $JENKINS_URL
    username: $JENKINS_USER
    token: \$JENKINS_TOKEN
current_context: $CONTEXT
YAML
  chmod 600 "$CONFIG"
fi

exec "$BIN" mcp --context "$CONTEXT" --read-only "$@"
