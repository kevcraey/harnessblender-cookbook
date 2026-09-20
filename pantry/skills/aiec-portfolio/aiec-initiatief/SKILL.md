---
name: aiec-initiatief
description: |
  Eén AI-initiatief van het AI Expertisecentrum aanmaken of bijwerken: intake van een nieuwe
  vraag, het details-blok van een bestaande Confluence-pagina invullen of corrigeren, of in
  batch alle initiatieven retro-fitten. Gebruik bij: nieuw AI-initiatief, initiatief
  registreren, intake AI-vraag, AI-25 bijwerken, details-blok aanvullen, retrofit register.
argument-hint: '<AI-key> | nieuw "<titel>" | retrofit [AI-key …]'
---

# AIEC — initiatief

Kern: lees `../aiec-core/SKILL.md`; `A` = `../aiec-core/scripts/aiec.py`.

Velden, enums, pijlers en statussen staan **enkel** in het schema: `A schema`. Herhaal ze nooit
in je antwoord uit het hoofd. Globale vlaggen (`--json`, `--out`, `--config`) staan **vóór** het
subcommando: `A --json --out $RUN/x.json jira get AI-25`.

| argument | modus |
|---|---|
| `<AI-key>` | één bestaand initiatief bijwerken |
| `nieuw "<titel>"` | intake: Jira-initiatief + Confluence-pagina aanmaken |
| `retrofit [AI-key …]` | dezelfde motor over alle (of de genoemde) initiatieven |

## Stappen

1. **Run-map**: `RUN=$(A state run-dir aiec-initiatief)`.
2. **Verzamelen** (alles read-only; bij `nieuw` bestaat er nog geen key — sla de twee
   key-commando's over, je bronnen zijn het gesprek, de briefings en de vault):
   - `A --json --out $RUN/jira.json jira get <AI-key>` — status, resolution, links, EAG-keys.
   - `A --json --out $RUN/page.json conf get <AI-key>` — storage-body, geparsed blok, kindpagina's.
   - retrofit: in plaats daarvan één keer
     `A --json --out $RUN/register.json conf pages --discover` en
     `A --json --out $RUN/initiatives.json jira list --all`.
   - vault: `grep -ril "<AI-key>" "<vault-pad uit ../aiec-core/SKILL.md>"`; lees enkel de treffers.
   - briefings en verslagen: MCP-**lees**tools. Nooit een MCP-schrijftool in deze skill.
3. **Nieuw** — alleen in modus `nieuw`, vóór stap 4:
   - Vraag Kenzo of hij het intakegesprek via de agent `ai-track-intake-analyzer` wil voeren.
     Stel die vraag zeker bij een vraag die meer dan één gesprek en meer dan vier uur kost;
     beslis het niet zelf.
   - Zoek de EAG-counterpart en stel hem voor; Kenzo bevestigt:
     `A --json jira search 'project = EAG AND summary ~ "<kernwoorden>" ORDER BY updated DESC'`.
4. **Voorstellen**: per veld uit `A schema` een waarde met **bron** (jira / pagina / briefing
   <datum> / gesprek) en **zekerheid** (hoog / midden / laag). Velden met `not_inferable` in het
   schema blijven leeg met zekerheid `KENZO`. Verzin niets: geen bron = leeg.
   Schrijf `$RUN/initiatief.md` (één initiatief) of `$RUN/retrofit.md` (batch), formaat hieronder.
   Toon het pad en één samenvattende regel per initiatief. Wil Kenzo de echte paginadiff zien
   (de droogloop van `apply` toont die niet): `A conf upsert-details --page <page-id> --values '<json>'`
   op één initiatief. **Stop hier tot Kenzo "ok" zegt.**
5. **Droogloop en uitvoeren**, na "ok". Voer altijd eerst de droogloop en toon het verslag:
   `A apply --proposal $RUN/<bestand>.md`.
   - **`<AI-key>` en `retrofit`**: `A apply --proposal $RUN/<bestand>.md --apply`. Dat doet het
     `upsert-details` en de aangevinkte acties. Exit 3 = de write-mode staat op `dry-run`; meld dat
     en stop. De mode verzetten is Kenzo's beslissing, niet de jouwe.
   - **`nieuw`**, in deze volgorde, en dus *niet* via `create-page` in het voorstel:
     1. `A jira create --title "<titel>" --description "<tekst>" [--eag EAG-n] [--verantwoordelijke U] [--trekker U] --apply`
        → de nieuwe AI-key.
     2. Zet die key als `ai_key` in de goedgekeurde waarden en schrijf ze weg als
        `$RUN/values.json` (sleutels = veldsleutels uit `A schema`; `ai_key` is verplicht, dus dit
        kan pas na stap 1 — anders exit 4).
     3. `A conf create-initiative --values $RUN/values.json --title "<titel>" [--parent <page-id>] --samenvatting "<2-3 zinnen>" --apply`.
     4. Daarna pas `A apply --proposal … --apply`, enkel nog voor de aangevinkte acties.
   - Captatierapport als kindpagina, enkel bij `soort` = afgebakend (doorlopende werking krijgt er
     geen): `A conf create-child --parent <page-id> --title "[<AI-key>] AI-captatierapport" --label captatierapport --from-title "<captatierapport_template uit A config show>" --apply`.
     Bestaat de sjabloonpagina niet, dan krijgt het kind een lege body; meld dat.
6. **Afronden**: bij retrofit `A state set last_retrofit <YYYY-MM-DD>` (datum, geen tijdstempel —
   `report data --since` leest een datum). Meld wat bleef staan. Op dossiers van Rik is hij tweede
   reviewer: zeg dat Kenzo het voorstel naar hem doorstuurt; doe dat niet zelf.

## Voorstel-formaat

```markdown
# aiec voorstel — retrofit — 2026-09-16
<!-- aiec:proposal v1 -->

## AI-25 — AI-ondersteuning Milieu-Investerings-Aftrek
- pagina: 431293025
- actie: upsert-details

| veld | waarde | bron | zekerheid |
|---|---|---|---|
| soort | afgebakend | jira | hoog |
| batenclaim |  | — | KENZO |

### Acties
- [x] label ai-initiatief
- [ ] jira link AI-25 EAG-927
```

Het woord na `# aiec voorstel —` is de soort van het bestand: `initiatief`, `retrofit` of `groom`.
`actie:` is `upsert-details`, `create-page` of `skip`; `pagina:` is verplicht bij `upsert-details`.
Eerste tabelkolom is de veldsleutel of het veldlabel uit het schema; lege waarde = niet zetten;
een rij met `~~` wordt overgeslagen. `bron` en `zekerheid` zijn voor Kenzo; `apply` negeert ze.
Enkel aangevinkte actie-bullets worden uitgevoerd.

## Grenzen

- Geen mutatie buiten `A`. Nooit rechtstreeks naar Confluence of Jira via MCP.
- Status nooit in het details-blok zetten; die komt live uit Jira.
- Een transitie volgt altijd op een aangevinkte beslissing van Kenzo, nooit automatisch.
- 302 of exit 1 met `auth:` = token of VPN; melden, niet omzeilen.
