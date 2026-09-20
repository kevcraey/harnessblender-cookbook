"""Config, state, run-map en write-guard. Niets hierin praat met het netwerk.

Config: ~/.config/aiec/config.toml (override: AIEC_CONFIG_DIR). Zonder bestand gelden de
defaults, dus write-mode `dry-run`. `production` zetten is Kenzo's expliciete go.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import tomllib
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("AIEC_CONFIG_DIR", str(Path.home() / ".config" / "aiec")))

DEFAULT_CONFIG_TOML = """# aiec — configuratie. Write-mode: dry-run | test | production.
[atlassian]
confluence_url = "https://confluence.omgeving.vlaanderen.be/confluence"
jira_url = "https://jira.omgeving.vlaanderen.be/jira"
space = "AI"
jira_project = "AI"
eag_project = "EAG"
templates_parent = 411959725
briefings_parent = 398330761
space_home = 390605009
captatierapport_template = "Sjabloon AI-captatierapport"
# Jira-macro in Confluence: applink-naam en serverId, gekopieerd uit een bestaande pagina in de space
jira_server = "JIRA - taakopvolgingssysteem Omgeving"
jira_server_id = "56e4142a-0105-3cf7-b7a8-b308d7369863"

[writes]
mode = "dry-run"
test_space = "~vancrake"

[report]
uurtarief_eur = 0
frigo_dagen = 90

[vault]
path = "~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain"
"""

DEFAULTS: dict = tomllib.loads(DEFAULT_CONFIG_TOML)
MODES = ("dry-run", "test", "production")


class GuardRefused(Exception):
    """Write geweigerd door de guard (exit 3)."""


def config_path(path: str | None = None) -> Path:
    return Path(path).expanduser() if path else CONFIG_DIR / "config.toml"


def _merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        out[k] = _merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


def load(path: str | None = None) -> dict:
    p = config_path(path)
    cfg = _merge(DEFAULTS, tomllib.loads(p.read_text()) if p.exists() else {})
    cfg["_path"] = str(p)
    m = cfg["writes"]["mode"]
    if m not in MODES:
        raise ValueError(f"writes.mode '{m}' onbekend; kies uit {', '.join(MODES)}")
    return cfg


def init(path: str | None = None) -> Path:
    p = config_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text(DEFAULT_CONFIG_TOML)
    return p


def mode(cfg: dict) -> str:
    return cfg["writes"]["mode"]


def guard(cfg: dict, target: str, scope: str, apply: bool) -> None:
    """Weiger een write die de mode niet toelaat. target: 'confluence' | 'jira'; scope: space-key
    of projectsleutel. Zonder apply is alles toegestaan (er wordt niets geschreven)."""
    if not apply:
        return
    m = mode(cfg)
    a = cfg["atlassian"]
    if m == "dry-run":
        raise GuardRefused(f"writes.mode is dry-run: {target} {scope} niet geschreven "
                           f"(zet mode op test of production in {cfg['_path']})")
    if target == "confluence":
        allowed = {cfg["writes"]["test_space"]} | ({a["space"]} if m == "production" else set())
        if scope not in allowed:
            raise GuardRefused(f"mode {m}: Confluence-space '{scope}' niet toegestaan "
                               f"(wel: {', '.join(sorted(allowed))})")
        return
    if target == "jira":
        if m != "production":
            raise GuardRefused(f"mode {m}: Jira-writes zijn enkel toegestaan in production")
        if scope not in {a["jira_project"], a["eag_project"]}:
            raise GuardRefused(f"Jira-project '{scope}' niet toegestaan")
        return
    raise GuardRefused(f"onbekend doel '{target}'")


# --- state --------------------------------------------------------------------------------

def state_path() -> Path:
    return CONFIG_DIR / "state.json"


def state_load() -> dict:
    p = state_path()
    return json.loads(p.read_text()) if p.exists() else {}


def state_get(key: str):
    return state_load().get(key)


def state_set(key: str, value) -> None:
    s = state_load()
    s[key] = value
    state_path().parent.mkdir(parents=True, exist_ok=True)
    state_path().write_text(json.dumps(s, indent=1, ensure_ascii=False))


def run_dir(skill: str, day: dt.date | None = None) -> Path:
    d = (day or dt.date.today()).isoformat()
    p = CONFIG_DIR / "runs" / f"{d}-{skill}"
    p.mkdir(parents=True, exist_ok=True)
    return p


def vault_path(cfg: dict) -> Path:
    return Path(cfg["vault"]["path"]).expanduser()
