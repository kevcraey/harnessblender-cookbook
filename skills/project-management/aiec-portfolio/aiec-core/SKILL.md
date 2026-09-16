---
name: aiec-core
user-invocable: false
description: |
  Contract en scripts van de AIEC-portfolio-plugin (schema van een AI-initiatief, Confluence-
  register met details-blokken, Jira live, guard voor writes, voorstel-bestanden). Geen eigen
  gedrag; wordt gelezen door aiec-initiatief, aiec-groom en aiec-rapport.
---

# AIEC — kern

Vault: `~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain`
Scripts: `scripts/aiec.py` naast dit bestand. Vanuit een zuster-skill: `<base>/../aiec-core/scripts/aiec.py`.
Model: `schema.yaml` naast dit bestand — de enige plek met velden, enums, pijlers en statusmapping.
Ontwerp en CLI-contract: `../DESIGN.md` in de bronrepo (niet meegekopieerd in de plugin).

## Lagen

```
collect (aiec.py)  →  judge (LLM, in de skill)  →  propose (bestand in de run-map)  →  apply (aiec.py, guard)
```

- Scripts beslissen niets. Ze lezen Confluence en Jira, renderen storage-XML uit het schema,
  valideren, en schrijven enkel met `--apply` én een toelatende write-mode.
- De LLM schrijft **nooit** rechtstreeks naar Confluence of Jira via MCP-tools. Enige uitzondering:
  `aiec-rapport kwartaal` publiceert goedgekeurde markdown met `confluence_create_page`, en pas na
  `aiec.py config mode` = `production`.
- Elk voorstel is een bestand (`retrofit.md`, `initiatief.md`, `groom.md`) dat Kenzo bewerkt vóór
  "ok". Formaat: DESIGN.md §8; `aiec.py apply --proposal <f>` toont zonder `--apply` wat er zou
  gebeuren.

## Run-map en state

`aiec.py state run-dir <skill>` maakt `~/.config/aiec/runs/<YYYY-MM-DD>-<skill>/` en print het pad.
State in `~/.config/aiec/state.json`: `last_stand`, `last_kwartaal`, `last_groom`, `last_retrofit`.
Config in `~/.config/aiec/config.toml` (`aiec.py config init`); write-mode `dry-run` | `test` |
`production`. Zonder configbestand geldt `dry-run`.

## Veelgebruikte commando's

| doel | commando |
|---|---|
| model tonen | `aiec.py schema` |
| initiatieven live | `aiec.py --json --out <run>/initiatives.json jira list [--all]` |
| register lezen | `aiec.py --json --out <run>/register.json conf pages [--discover]` |
| regels checken | `aiec.py --out <run> validate [--discover]` |
| dataset rapport | `aiec.py --out <run> report data --since <D>` |
| voorstel uitvoeren | `aiec.py apply --proposal <run>/<f>.md [--apply]` |

Globale vlaggen (`--json`, `--out`, `--config`, `--schema`) mogen vóór of ná het subcommando.
Volledig contract: `aiec.py --help` en DESIGN.md §6. Exitcodes: 0 ok · 1 fout · 2 gebruiksfout ·
3 write geweigerd door guard · 4 validatiefout in waarden.

## Grenzen (gelden voor elke skill)

- Geen mutaties buiten `aiec.py` (uitzondering hierboven). Geen Jira custom fields. Nooit
  automatisch sluiten; een transitie volgt altijd op een aangevinkte beslissing van Kenzo.
- Status, uren en kost worden nooit in Confluence gedupliceerd; ze komen live uit Jira.
- Tokens nooit tonen. 302 op een REST-call = auth- of VPN-probleem; melden, niet omzeilen.
- Vault-mutaties beperkt tot nieuwe conceptnotes in `02 - Areas/` (aiec-rapport), review-first.
