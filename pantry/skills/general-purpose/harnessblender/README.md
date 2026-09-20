# harnessblender

Blend ingredients (skills, agents, richtlijnen, mcp servers) from a cookbook into installable
Claude Code plugins ("blends"), and pour them into projects. harnessblender itself is generic and
carries no personal content — everything specific lives in a cookbook.

## Layout

```
ai-tooling-repos/
├── harnessblender/           # the tool
│   ├── harnessblender            # the script (uv shebang)
│   └── web/                      # browser picker (index.html + app.js + style.css)
├── cookbook/                 # a cookbook (this one: Kenzo's)
│   ├── cookbook.yaml              # marker file: name, owner, exclude_dirs
│   ├── store.yaml                 # declared external sources (name + git url)
│   ├── pantry/                    # own ingredients
│   │   ├── skills/<namespace>/<skill>/
│   │   ├── skills/<namespace>/agents/<naam>.md
│   │   ├── mcp-servers/<naam>/
│   │   └── richtlijnen/<naam>.md
│   ├── store/<naam>/              # gitignored checkouts of store.yaml entries
│   ├── recipes/<naam>/
│   │   ├── recipe.yaml            # tracked: the selection
│   │   └── blend/                 # gitignored: generated plugin (real copies, plugin.json, provenance)
│   └── .claude-plugin/
│       └── marketplace.json       # auto-generated; lists every recipe's blend
└── custom-plugins/            # the OLD system (mix-plugin) — still live, not touched
```

## Requirements

- Python ≥3.11 + [`uv`](https://docs.astral.sh/uv/) (deps resolved automatically via PEP 723 shebang)
- `claude` CLI on PATH (for `pour`)

## Commands

```bash
harnessblender new-recipe <naam>          # picker → recipe.yaml → blend
harnessblender edit-recipe <naam>         # picker, pre-checked → re-blend
harnessblender blend <naam>               # rebuild blend/ from recipe.yaml, no picker
harnessblender list                       # all recipes + blended status
harnessblender fetch                      # clone-if-missing + ff-only pull every store.yaml source
harnessblender pour <naam> <drinker...>   # install a blend into project folder(s)
harnessblender web                        # browser picker
```

All commands resolve the cookbook by walking up from the current directory for a `cookbook.yaml`
marker file. Pass `--cookbook <path>` to override (e.g. when running from inside a drinker).

## `pour`, concretely

```bash
harnessblender pour user-level ~/Coding/some-project --scope local
```

Shells out to:

```bash
claude plugin marketplace add <cookbook-path>
claude plugin install user-level@<cookbook-name> --scope local -y
```

Both verified to work fully non-interactively. `--scope`: `local` (personal, not committed),
`project` (shared, committed), `user` (global, every project).

## `fetch`, concretely

Reads `store.yaml`. Per source: if `store/<naam>/.git` is missing, `git clone`s it; if present,
fetches + fast-forwards only (never force-merges or auto-stashes — a dirty tree, detached HEAD, or
diverged branch is reported and left untouched). Reports which blends reference a source that just
moved ("stale blends") — re-run `harnessblender blend <naam>` for those.

## Manifests

### `cookbook.yaml`

```yaml
name: kevcraey-cookbook   # marketplace name; recipes install as <recipe>@<name>
owner:
  name: Kenzo
  url: ""
exclude_dirs:
  - _archived
```

### `store.yaml`

```yaml
sources:
  - name: caveman
    url: git@github.com:JuliusBrussee/caveman.git
```

### `recipes/<naam>/recipe.yaml`

```yaml
description: Skills + agents for second-brain workflow
version: 0.1.0
selections:
  skills:
    - source: pantry/skills/second-brain/verwerk-meeting
      as: verwerk-meeting
  agents:
    - source: pantry/skills/aiec-portfolio/agents/ai-track-intake-analyzer.md
      as: ai-track-intake-analyzer.md
  mcps:
    - source: pantry/mcp-servers/garmin-mcp/.claude-plugin/.mcp.json
      as: garmin-mcp
```

`source` is relative to the cookbook root. `as` is the final copy name inside the blend.

## Conventions

- A **skill** = a directory containing `SKILL.md`, anywhere under `pantry/` or `store/<naam>/` — no
  requirement to sit under a folder literally named `skills`.
- An **agent** = a `.md` file directly under a folder literally named `agents`.
- A **richtlijn** = a `.md` file directly under a folder literally named `richtlijnen`.
- An **mcp** = an immediate subdir of an `mcp-servers/` dir that declares `mcpServers`. `command` is
  referenced as-is — the binary must be installed on the target machine (no bundling).
- Hidden directories and `exclude_dirs` entries are not scanned.
- Slash commands are **out of scope** — only skills, agents, richtlijnen, and MCP servers are blended.

## Known limitations

- Absolute paths in `pantry/mcp-servers/*/.mcp.json` (`command`) are machine-specific — a cookbook
  clone on a new machine needs those paths (and the referenced keychain items) reprovisioned.
  `${CLAUDE_PLUGIN_ROOT}`-based bundling would fix this; not implemented yet.
- The old `custom-plugins/` (mix-plugin, "variant" language) is untouched and still the live
  marketplace for already-installed plugins like `kevcraey-user-level`. It is not migrated —
  existing variants are being rebuilt as recipes deliberately, not ported.
