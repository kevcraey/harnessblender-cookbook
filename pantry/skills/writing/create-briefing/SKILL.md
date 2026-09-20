---
name: create-briefing
description: |
  Genereer een periodieke leidinggevende-briefing (CIO Tom Van Gulck, Kris
  Peirlinck) uit de eigen kennis, in de stijl van de bestaande Confluence-reeks.
  Spiegelbeeld van de capture-familie: leest UIT Open Brain i.p.v. erin te
  schrijven. Getrapt: initiatief-lijst → proza in een vault-note → op expliciete
  go publiceren als kindpagina onder Briefings. Claude oordeelt; on-demand.
---

# Create Briefing

Vault: `~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain`

Doel: een **periodieke briefing** aan de leidinggevenden (CIO **Tom Van Gulck**,
**Kris Peirlinck**) opstellen die de voortgang van het AI-innovatiecentrum
samenvat, in de vorm en toon van de bestaande reeks op Confluence (space `AI`,
onder de ouderpagina **Briefings**, id `398330761`).

Dit is het **spiegelbeeld** van `capture-vault` / `capture-session` /
`capture-mail`: die schrijven kennis *naar* Open Brain, deze skill leest *uit*
Open Brain (+ aanvullende bronnen) om er een artefact van te maken. De skill
schrijft **niets terug** naar Open Brain.

## Taal: initiatieven

De briefing is een **lopende status per initiatief**, geen losse digest. Drie
toestanden:

- **bestaand** — stond in een vorige briefing; rapporteer enkel de *beweging*.
- **nieuw** — in geen enkele van de laatste 10 briefings; volledig nieuw blok.
- **afgerond** — was bestaand, nu klaar; laatste vermelding, valt daarna weg.

Classificatie nieuw vs. bestaand gebeurt tegen de **unie van de laatste 10
briefings** (kindpagina's onder `398330761`). De meest recente briefing levert
enkel de ondergrens-datum.

## Periode

- **Ondergrens** = datum van de meest recente briefing. Override met argument
  `sinds <YYYY-MM-DD>`.
- **Bovengrens** = altijd vandaag.
- De delta is **semantisch per-initiatief**, geen datumsnede. In Open Brain is de
  *capture-datum ≈ nu* (alles recent geïngest); de echte gebeurtenisdatum staat in
  de **proza** ("Op 2026-04-27 …"). Een `sinds`-ondergrens wordt dus afgedwongen
  op die **in-tekst-datum**, wat fuzzy is — wees daar eerlijk over. De robuuste
  default is niet de datum maar de **inhouds-diff tegen de vorige briefing**.

## Bronnen — cascade, geen parallelle scans

Open Brain wordt al gevoed door de capture-familie en is dus grotendeels de
consolidatie van de andere bronnen. Herscan ze niet wholesale (dubbel werk, dubbel
tokens, werkmail nogmaals naar Claude).

1. **Open Brain = spine.** Initiatief-ontdekking én het narratief komen hier
   vandaan (`search_thoughts`, `list_thoughts`, `thought_stats`).
2. **Vault = gericht bijladen** per initiatief waar OB te dun is (de meeting-notes
   hebben diepte die OB samenperst). Zoeken via **grep / Obsidian-tekstzoek op
   keywords** in de vault-map — *niet* de codebase-memory MCP (die is code-only en
   raakt vault-proza niet). Geen volledige scan, enkel de relevante notes.
3. **Werkmail (Graph) + sessielogs = staart-aanvulling**, secundair. Enkel wat nog
   niet in OB zit, en werkmail enkel binnen de opt-out ICR-grenzen (zie
   `capture-mail`). Voor v1 is **OB + vault de dragende spine**; laat de eerste run
   niet afhangen van een Graph-token.

Optioneel argument **`diep <bron>`** (`vault` | `werkmail` | `sessielogs`): loop
die ene bron **één-per-één** door als controle op wat OB miste. `diep werkmail`
hergebruikt de capture-mail-tokenflow (token via clipboard, enkel lezen, wissen na
de run — nooit tonen).

## Workflow — drie trappen

### Trap 1 — Initiatief-lijst (goedkoop; hier ligt de curatie)

De heropstart-briefing dekt maanden → potentieel veel initiatieven. Schrijf hier
**geen proza**; lever enkel een lijst zodat Kenzo cureert vóór er dure proza komt.

1. **Lees de laatste ≤10 briefings** (kindpagina's onder `398330761`, gesorteerd
   op datum-in-titel). Extraheer per briefing de initiatief-titels + hun openstaande
   *Next steps* → dit is de set **bekende initiatieven** + de laatst-gerapporteerde
   staat. De nieuwste titel-datum = de ondergrens.

2. **Bestaande initiatieven — beweging.** Doe per bekend initiatief één gerichte
   `search_thoughts` (+ vault-grep waar nodig). Vergelijk met wat de vorige briefing
   al zei. Enkel echte beweging telt.

3. **Nieuwe initiatieven — subtract-known-cluster-rest** (het dure hart). Haal een
   brede recente set op (`list_thoughts` op recentheid + werk-topics zoals `AI`,
   `project`, `governance`, `overleg`, `Departement Omgeving`). **Trek de reeds
   bekende initiatieven eraf** en **cluster de rest** tot samenhangende nieuwe
   initiatieven. Laat puur persoonlijke ruis (verlof, hobby's) en losse feiten die
   geen initiatief vormen vallen.

4. **Mogelijk afgerond.** Markeer een bekend initiatief als afgerond **alleen bij
   positief bewijs** van afronding (expliciete "afgerond/live/in productie/gesloten"-
   signalen). **Nooit** op louter afwezigheid van recent signaal — een stil
   initiatief is niet hetzelfde als een afgesloten initiatief.

5. **Toon één genummerde lijst**, gegroepeerd: *Bestaand — met beweging* /
   *Nieuw* / *Mogelijk afgerond*. Eén regel per initiatief + bron. Wacht op akkoord.
   Kenzo snoeit in bulk ("alles behalve 3, 7"). **Stop hier tot hij goedkeurt.**
   Bij een lange inhaal-periode wordt de lijst lang: geef dan een **prioriteitshint**
   (welke initiatieven het belangrijkst zijn voor de CIO, welke overkoepelende
   thema's eventueel te schrappen voor de lengte) — maar Kenzo beslist. Een briefing
   moet niet exhaustief zijn; de belangrijkste initiatieven volstaan.

### Trap 2 — Proza (duur; pas na akkoord)

Schrijf de goedgekeurde initiatieven uit naar een vault-note.

- **Titel-conventie:** `## <Naam initiatief> (AI-<n>, EAG-<n>)` — vermeld zowel het
  interne AI-nummer als het Jira/EAG-demandnummer. Vind het EAG-nummer via Open
  Brain (er bestaat een AI↔EAG-mapping-thought) of desnoods via Jira (project EAG).
  Voeg een tekstlabel toe waar relevant: `(nieuw)` voor nieuwe initiatieven, niets
  voor lopende, `(afgerond)` voor afgeronde (laatste vermelding). Geen emoji
  (botst met humanizer).
- **Optioneel bovenaan een TL;DR "Kernboodschappen"** (3-4 bullets); Kenzo laat 'm
  soms weg.
- **Bouw per initiatief meerdere korte alinea's**, één deelonderwerp per alinea
  (bv. techniek / status & productie / betrokkenen / duiding), gescheiden door een
  witregel. Geen enkel dicht blok.
- **Lengte volgt het nieuws:** veel beweging → meerdere alinea's; weinig → één à
  twee zinnen. Niet opvullen.
- **Nuchter en feitelijk, geen promotie over de eigen oplossingen** — schrap
  superlatieven ("vlaggenschip", "mooi voorbeeld"). Droge editorial asides mogen
  wél (dat is Kenzo's stem, bv. "Dierenwelzijn not amused").
- **Bullets onder een `**Volgende stappen:**`-label** (Nederlands). Vet enkel op dat
  label, niet in de lopende tekst.
- **Vloeiend proza, geen telegramstijl.** Weinig em-dashes. Jaag de tekst door de
  `humanizer`-skill vóór je oplevert.
- **De proza is een steiger, geen eindproduct.** Kenzo verrijkt ze nadien met
  interne feiten die Open Brain niet kent (servicenamen als "Rosetta", budgetten,
  extra namen, verse status). Lever een correcte, volledige basis; verzin nooit
  details om een blok voller te doen lijken.
- **Schrijf naar** `02 - Areas/<YYYY-MM-DD>-briefing-<slug>.md` (bv.
  `2026-07-23-briefing-cio.md`). Vault-mutatie → valt onder review-first.
- Kenzo reviewt/edit in Obsidian. **Stop hier tot hij "publiceer" zegt.**

### Trap 3 — Publiceren (mutatie; enkel op expliciete go)

Publiceer de (mogelijk ge-edite) vault-note als **kindpagina** onder Briefings:

- Parent: `398330761`, space `AI`.
- **Titel = `<YYYY-MM-DD>-briefing`** (kleine letters, bv. `2026-07-23-briefing`) —
  timestamp-dash-briefing. "briefing" hoort óók in de Confluence-titel.
- Body = de briefing-inhoud (`confluence_create_page`).
- Nooit auto-publiceren; nooit een bestaande briefing overschrijven zonder dat
  expliciet gevraagd is.

## Argumenten

- **geen** → default run: ondergrens = datum vorige briefing, diff tegen de vorige
  briefing (robuust).
- **`sinds <YYYY-MM-DD>`** → override ondergrens (fuzzy, op in-tekst-datum).
- **`diep <bron>`** (`vault` | `werkmail` | `sessielogs`) → die bron één-per-één
  doorlopen als controle.

## Grenzen

- **Geen capture.** De skill schrijft niets naar Open Brain. Enige mutaties:
  de vault-note (trap 2) en de Confluence-publish (trap 3), beide met expliciete go.
- **Residency.** Genereren stuurt OB-inhoud naar Claude. OB sloot `ICR2+`-werkmail
  al uit; vault-/sessie-gapfill kan gevoelige info oppikken → Kenzo cureert in
  trap 1. Nooit omzeilen via forwarding van overheidsmail.
- **Voorstel eerst, publiceren pas na akkoord** — trap 1 en trap 2 zijn harde stops.
- Terminal-output verwijst naar notes met **vault-relatieve paden**, nooit
  `[[wikilinks]]`.
