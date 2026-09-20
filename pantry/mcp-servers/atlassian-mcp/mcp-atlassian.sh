#!/bin/bash
export JIRA_URL="https://jira.omgeving.vlaanderen.be/jira"
export JIRA_PERSONAL_TOKEN=$(security find-generic-password -a "$(whoami)" -s "jira-personal-token" -w)
export CONFLUENCE_URL="https://confluence.omgeving.vlaanderen.be/confluence/"
export CONFLUENCE_PERSONAL_TOKEN=$(security find-generic-password -a "$(whoami)" -s "confluence-personal-token" -w)
exec uvx mcp-atlassian "$@"
