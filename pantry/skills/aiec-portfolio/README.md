# aiec-portfolio

Claude Code-plugin voor het intakeproces en de portfolio-rapportage van het AI Expertisecentrum
(AIEC) van het Departement Omgeving.

De Confluence-space `AI` is het register: één pagina per initiatief met bovenaan een
`details`-blok. Jira levert status, uren en kost **live** — die worden nooit in Confluence
gedupliceerd. Eén schema (`aiec-core/schema.yaml`) bepaalt de velden, enums, pijlers en
statusmapping; alles wat erover gaat, komt daaruit.

## De vier skills

| skill | waarvoor | argument |
|---|---|---|
| `aiec-core` | contract en scripts; geen eigen gedrag, wordt door de andere drie gelezen | — |
| `aiec-initiatief` | één initiatief aanmaken of bijwerken; `retrofit` = hetzelfde over de hele space | `<AI-key>` · `nieuw "<titel>"` · `retrofit [AI-key …]` |
| `aiec-groom` | regelcheck over space + Jira, met fixes als voorstel; `kwartaal` doet ook de frigo-beslissingen | `[kwartaal]` |
| `aiec-rapport` | standvanzakenmail en kwartaaltoelichting, met cijfers uit één dataset | `stand` · `kwartaal [--since D]` |

Meegemixt: de agent `ai-track-intake-analyzer` (intakegesprek) en de skills `write-like-kenzo` en
`humanizer` (proza van `aiec-rapport`).

## Hoe het werkt

```
collect (aiec.py)  →  judge (Claude)  →  propose (bestand in de run-map)  →  apply (aiec.py, guard)
```

Scripts beslissen niets, Claude schrijft niets rechtstreeks weg. Elke wijziging passeert eerst een
voorstel-bestand in `~/.config/aiec/runs/<datum>-<skill>/` dat je zelf bewerkt; pas na "ok" voert
`aiec.py apply --proposal … --apply` het uit. Enige uitzondering: `aiec-rapport kwartaal`
publiceert de goedgekeurde markdown via de MCP-tool `confluence_create_page`, en enkel in
write-mode `production`.

## Guard en write-mode

`~/.config/aiec/config.toml` (`aiec.py config init` schrijft de defaults) bepaalt wat mag:

| mode | zonder `--apply` | met `--apply` |
|---|---|---|
| `dry-run` (default, ook zonder configbestand) | payload en diff op stdout | geweigerd, exit 3 |
| `test` | idem | Confluence enkel in `writes.test_space`; Jira altijd geweigerd |
| `production` | idem | Confluence in `atlassian.space`, Jira in `jira_project` / `eag_project` |

De guard zit in code, niet in proza: een REST-client is alleen-lezen tenzij hij via
`http.writer(…, apply=True)` en een toelatende mode is aangemaakt. `production` zetten is een
expliciete beslissing, geen bijwerking van een run.

Tokens: keychain-items `confluence-personal-token` en `jira-personal-token` (account = `$USER`),
of de omgevingsvariabelen `CONFLUENCE_PERSONAL_TOKEN` / `JIRA_PERSONAL_TOKEN`. Ze worden nooit
geprint. Een 302 op een REST-call is een auth- of VPN-probleem, geen redirect om te volgen.

## Installeren

Dit is de **bron**. De plugin zelf is een mix-variant; nooit in `custom-plugins/aiec-portfolio/`
bewerken, die map wordt overschreven.

```bash
cd ~/Library/CloudStorage/Dropbox/1-Kenzo/4-Coding/ai-tooling-repos/custom-plugins
./mix-plugin sync aiec-portfolio
```

Eerste keer, in het vault-project: `/plugin install aiec-portfolio@custom-plugins`, daarna een nieuwe
sessie. Na elke latere sync: `/plugin reload aiec-portfolio` en een nieuwe sessie. Zie `/mix-plugin`
voor de rest van de plugin-setup.

## Onderhoud

- Nieuw veld, andere enum, hernoemde Jira-status? Enkel `aiec-core/schema.yaml`. Het details-blok,
  de sjabloon- en overzichtspagina, de validatieregels en de rapportgroepering volgen mee.
- CLI-contract: `aiec-core/scripts/aiec.py --help`. Exitcodes: 0 ok · 1 fout · 2 gebruiksfout ·
  3 write geweigerd door de guard · 4 validatiefout in waarden.
- Globale vlaggen (`--json`, `--out`, `--config`, `--schema`) staan vóór het subcommando.
- Tests: `cd aiec-core/scripts && uv run --with pytest --with pyyaml python -m pytest tests -q`.
- Ontwerp en volledig contract: `DESIGN.md` (blijft in de bronrepo, gaat niet mee in de plugin).
