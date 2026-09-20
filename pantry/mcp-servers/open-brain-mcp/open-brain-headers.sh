#!/bin/bash
# headersHelper voor open-brain-mcp: haalt de brain-key uit Keychain, print headers-JSON.
KEY=$(security find-generic-password -a "$(whoami)" -s "open-brain-key" -w)
printf '{"x-brain-key": "%s"}' "$KEY"
