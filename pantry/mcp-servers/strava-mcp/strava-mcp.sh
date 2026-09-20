#!/bin/bash
export STRAVA_CLIENT_ID=$(security find-generic-password -a "$(whoami)" -s "strava-client-id" -w)
export STRAVA_CLIENT_SECRET=$(security find-generic-password -a "$(whoami)" -s "strava-client-secret" -w)
exec npx -y @r-huijts/strava-mcp-server "$@"
