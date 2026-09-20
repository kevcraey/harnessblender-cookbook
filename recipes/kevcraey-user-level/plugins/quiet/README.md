# quiet

Een conversation-only transcriptweergave voor Claude Code. `/quiet` schakelt ze aan en uit.

Poort van de Calm-feature van [Firstmate](https://github.com/kunchenguid/firstmate)
(`docs/calm.md`, `.claude/mods/firstmate-calm`). Alleen die feature: de rest van
Firstmate, de Pi-extensie en de firstmate-eigen operational-input-rijen zitten er niet in.

## Wat je ziet terwijl quiet aan staat

- De werkregel (`Sauteing... (12s · 300 tokens)`) wordt een tweerijig zeilbootje dat over
  een lage deining vaart: één kolom per 880 ms, water elke 220 ms. Het bootje krijgt de
  Claude-oranje van de standaardspinner, het water het spinnerblauw van je thema
  (`dark*` → donker, al de rest → licht), en volgt een themawissel via `/config`.
- `ToolUse`-, `ToolResult`- en `ToolGroup`-rijen tekenen op hoogte nul. Een beurt met
  tools neemt evenveel plaats in als een beurt zonder.
- Korte tussendoor-narratie van het model verdwijnt: een tekstblok uit een modelstap die
  stopte om tools te roepen, zonder newline en korter dan 240 getrimde tekens. Een
  newline of 240+ tekens blijft staan, en het echte antwoord aan het eind van een beurt
  blijft altijd staan.

Er wordt niets herschreven. Verborgen rijen blijven in het bericht, in de modelcontext,
in de sessieopslag en in exports; enkel de tekening verandert. Toggelen hertekent ook
rijen die al op het scherm staan.

## Vereisten

De function-hooks-API van Claude Code is early access en staat standaard uit. Zet
`CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1` in je shell (`set -Ux` in fish) en start Claude
Code opnieuw. Zonder die vlag laadt de module niet en verandert er niets. Het `env`-blok
van `settings.json` kan werken, maar of de module dan op tijd laadt is niet nagegaan.

Claude Code 2.1.258 heeft `session.start`, `command.run` en `ui.blit` nog niet; in de
binary van 2.1.278 bestaan ze wel. De bron waar dit van geport is draaide op 2.1.272.

Verificatiestatus: de zuivere libs (sprite, raster, voorkeur, werknotitie-regel) zijn met
een smoke-script nagelopen en `hooks/register.ts` transpileert schoon. Het gedrag tegen
een echte engine is nog nergens gedraaid — dat is `claude plugin test` na de upgrade.

De keuze wordt bewaard in `~/.claude/quiet` (`on` of `off`) en geldt voor volgende
sessies. Lukt het schrijven niet, dan blijft de huidige keuze staan en zegt een notitie
onder de prompt waarom.

## Grenzen

- Het gedetailleerde transcript (`ctrl+o`) houdt zijn timestamp- en modelkoppen op de
  plaats van verborgen assistentrijen: die koppen zijn geen hookbare tekening.
- Op de gewone schermindeling (niet fullscreen) hertekent een toggle het scherm door het
  te wissen en opnieuw te printen; de scrollback van je terminal houdt de oude weergave
  erboven.
- De boot wordt via het Raster-element getekend, met RGB-kleuren die de terminal naar
  256 kleuren kwantiseert.

## Structuur

- `hooks/register.ts` — de enige plaats waar de engine-interface `$` wordt aangeraakt.
- `lib/quiet-presentation.ts` — waar de voorkeur staat en welke tekst een werknotitie is.
- `lib/quiet-preservation.ts` — de drempel van 240 tekens.
- `lib/quiet-working-ship-sprite.ts` — geometrie en cadans van de boot.
- `lib/quiet-ship-raster.ts` — het packen van een frame als Raster-cellen, plus palet.
- `tests/` — `CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1 claude plugin test <pad naar deze map>`,
  plus `claude plugin validate --strict <pad>`.
