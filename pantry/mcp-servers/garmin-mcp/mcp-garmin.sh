#!/bin/bash
# 1. Haal de Garmin credentials uit de Keychain
export GARMIN_EMAIL=$(security find-generic-password -a "$(whoami)" -s "garmin-email" -w)
export GARMIN_PASSWORD=$(security find-generic-password -a "$(whoami)" -s "garmin-password" -w)

# 2. Voer uvx uit met exact dezelfde parameters als je werkende config
# We voegen "$@" toe aan het einde zodat Claude eventuele extra argumenten kan doorgeven
exec uvx \
  --python 3.12 \
  --from git+https://github.com/Taxuspt/garmin_mcp \
  garmin-mcp "$@"