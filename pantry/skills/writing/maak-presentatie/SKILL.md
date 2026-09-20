---
name: maak-presentatie
description: |
  Maak een standalone HTML-presentatie in de huisstijl van het Departement Omgeving
  (design system Flux): één bestand, fysiek scrollende slides, teller, toetsenbord-
  navigatie en print naar 16:9 of A4. Gebruik bij "maak een presentatie", "slidedeck",
  "deck van deze note", "presentatie voor het overleg".
argument-hint: '[pad naar bronnote] | "<onderwerp>" [--a4] [--stijl stencil]'
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(date), Bash(python3:*)
---

# Presentatie maken

Eén HTML-bestand, geen externe resources, opent overal. De vormgeving komt volledig
uit [assets/template.html](assets/template.html) — dat is wat elke presentatie op
elkaar doet lijken. **Verzin geen eigen CSS en geen eigen kleuren.**

## Twee stijlen

`data-stijl` op `<html>` kiest de huid. De slidetypes, de scaffolds en al je markup
zijn identiek; alleen tokens en lettertypes verschillen.

| stijl | waarvoor | kenmerk |
|-------|----------|---------|
| `domg` (standaard) | alles wat namens het departement naar buiten gaat | Flux-tokens, Flanders Art Sans, wit vlak, DOMG-groen |
| `stencil` | intern, informeel, een werksessie of een deck dat niet als huisstijl mag lezen | beenwit vlak, zwarte sectieschermen, gecondenseerde kapitalen, verzadigde kleurkaarten |

De stencilvariant is neutraal: geen logo's, geen merkverwijzingen, geen
overheidshuisstijl. Gebruik ze niet voor externe communicatie van de Vlaamse
overheid — daar is `domg` de enige juiste.

Wat de stencilvariant overneemt van het bronsjabloon (stencil-tablet): het
kleurenpalet, kapitalen in elke kop, vlakke kleurblokken zonder schaduw en het
reusachtige sectienummer. Twee bewuste afwijkingen:

- **De kop is Bebas Neue, niet Stardos Stencil.** Een sjabloonletter heeft in elke
  letter onderbrekingen; op een beamer op afstand kost dat leesbaarheid. Bebas houdt
  de gecondenseerde poservorm zonder die gaten. De naam `stencil` verwijst naar het
  bronsjabloon, niet naar de letter.
- **Lopende tekst blijft op Flux-maat.** De bron rekent op een canvas van 1920 met
  tekst van 22px; omgerekend naar dit canvas is dat 12px en onleesbaar.

`afwerken.py` bakt alleen de fonts van de gekozen stijl in en gooit de `@font-face`
van de andere weg: een deck sleept nooit twee sets mee.

Design system voor `domg`: **Flux** (Departement Omgeving, Vlaamse overheid), release 2.19.0 —
`https://claude.ai/code/artifact/03ba8e3a-b7b7-47d1-9e06-34671e367b04`. De tokens
staan bevroren in de template. Wijzigt Flux, dan herlees je dat artifact en pas je
de token-block aan, niet de individuele presentatie.

## Proces

```
- [ ] Fase 1: Bron lezen
- [ ] Fase 2: Verhaallijn en slide-indeling
- [ ] Fase 3: Template invullen
- [ ] Fase 4: Afwerken en controleren
- [ ] Fase 5: Rapporteren
```

### Fase 1: Bron lezen

- **Argument = pad naar een note of document**: lees het volledig, inclusief wat de
  frontmatter en de wikilinks eraan hangen als dat nodig is om het verhaal te snappen.
- **Argument = onderwerp tussen aanhalingstekens, of niets**: werk met wat de
  gebruiker in het gesprek gaf. Ontbreekt de kern, vraag ernaar — verzin geen inhoud.
- `--a4` in het argument zet `data-format="a4"` op `<html>`. Standaard is 16:9.
- `--stijl stencil` zet `data-stijl="stencil"` op `<html>`. Standaard is `domg`.

Markdown uit een bronnote mapt zo:

| markdown            | wordt                                   |
|---------------------|------------------------------------------|
| `#` (h1)            | titelslide                               |
| `##` (h2)           | nieuwe slide, de h2 is de kop            |
| `###` (h3)          | sectiedivider (nieuw deel)               |
| bullets             | `ul.bullets`                             |
| genummerde lijst    | `ol.bullets` (alleen als volgorde telt)  |
| tabel               | tabelslide                               |
| blockquote          | statement-slide                          |
| `---`               | expliciete slidebreuk                    |

### Fase 2: Verhaallijn en slide-indeling

Richtgrootte: **8–15 slides**. Eén boodschap per slide. Past de inhoud van één boodschap
niet op één slide, splits ze over twee in plaats van tekst of figuur te verkleinen.

**Figuur eerst, tekst als het niet anders kan.** Benoem per slide welke structuur de
inhoud heeft en kies daarna pas het type. Een lijst is wat je overhoudt als er geen
structuur is, niet je startpunt.

| structuur in de inhoud      | wordt                                    |
|-----------------------------|------------------------------------------|
| volgorde, stappen, verval   | figuur — keten                           |
| één naar veel naar één      | figuur — fan-out                         |
| hiërarchie, lagen           | figuur — lagen                           |
| spectrum, toe- of afname    | figuur — gradiënt                        |
| vier losse punten           | figuur — raster 2×2                      |
| vergelijking van twee       | twee kolommen                            |
| getallen die je vergelijkt  | figuur — staafgrafiek                    |
| losse kerncijfers           | cijfers                                  |
| één uitspraak               | statement                                |
| geen van die                | bullets                                  |

Blijft het bullets, dan: **maximum 3 bullets, maximum 8 woorden per bullet**, en
`<span class="sub">` alleen als de slide zonder die zin niet klopt. Een slide is geen
paragraaf met opsommingstekens ervoor.

Kies per slide een type uit de tien in de template. Verwijder de `<section>`-blokken
van de types die je niet gebruikt; dupliceer de types die je meermaals nodig hebt.

| class         | slide            | waarvoor                                              |
|---------------|------------------|-------------------------------------------------------|
| `s-title`     | titel            | altijd slide 1: titel, één zin, spreker, datum         |
| `s-section`   | sectiedivider    | groen volvlak, markeert een nieuw deel                 |
| `s-bullets`   | kop + bullets    | de werkpaard-slide: 3–5 punten                         |
| `s-two`       | twee kolommen    | vergelijking, voor/na, gekozen vs. verworpen           |
| `s-statement` | statement        | één uitspraak of kernboodschap, groot                  |
| `s-kpi`       | cijfers          | 2–4 getallen met label en bron                         |
| `s-table`     | tabel            | gestructureerde opsomming; `<caption>` is verplicht    |
| `s-figure`    | figuur           | schema als inline SVG; scaffolds in [references/figuren.md](references/figuren.md) |
| `s-image`     | beeld volvlak    | foto, base64 ingebed                                   |
| `s-end`       | slot             | de vraag, het besluit, of wat u van hen verwacht       |

Gebruikt u meerdere `s-section`-slides, laat elk deel op zich een afgerond stuk van het
verhaal zijn — een hoofdstuk, geen tussenkopje. Fragmenteer één verhaallijn niet in veel
kleine secties: dat maakt hem net moeilijker te volgen, niet makkelijker.

### Fase 3: Template invullen

Kopieer de template naar het doelpad en vul in. Bewaar de structuur
`<section class="slide" id="slide-N"><div class="canvas s-…">` en nummer de ids
oplopend zonder gaten.

**Schrijfregels** (uit de Flux-richtlijnen):

- Nederlands, u-vorm, zakelijk en vriendelijk. Technische termen blijven Engels.
- Zinsbouw, geen hoofdlettertitels: "Stand van zaken", niet "Stand Van Zaken".
- Geen emoji, geen uitroeptekens. Datum `dd.mm.jjjj`, tijd `H:i`.
- Bullets zijn volzinnen of strakke fragmenten, nooit alinea's. Maximum twee regels
  per bullet; wat langer moet, gaat in `<span class="sub">`.
- Nummer alleen waar de volgorde echt betekenis heeft.

**Vormregels:**

- Alle maten zijn Flux-px op een canvas van 1024 breed, geschreven als
  `calc(<px> * var(--px))`. Voeg nooit een vaste `px`-waarde toe binnen een slide —
  die schaalt niet mee.
- Accent is altijd `var(--accent)` — in `domg` DOMG-groen `#447a6d`, in `stencil`
  oranje `#ee7a2e`. Schrijf nooit een kleur uit: dan breekt de andere stijl.
- In `domg` is Vlaams geel uitsluitend de band onder de titelslide en de streep op
  groene vlakken; nooit tekstkleur, nooit decoratie elders. Actieblauw is voor links.
- Kleur is nooit het enige signaal: zet er tekst bij.
- Stapel een figuur, grafiek of tabel **nooit onder een blok tekst**. Gebruik een
  volle slide of twee kolommen — anders leest niemand het onderste deel.
- Getallen: geen grafiek zonder bron in het onderschrift, en geen getal dat niet in
  de bron staat. Ontbreken de cijfers, dan wordt het geen grafiek.
- Eén radius (3px), randen van 1px, geen schaduwen. Geen gradients, geen
  emoji-iconen, geen kaartjes met gekleurde linkerrand.
- Tekst op groen is wit; tekst op geel is `--vl-color--on-primary` (grijs), nooit wit.
- Beelden: base64 ingebed via `data:`-URI, met een echte `alt`. Geen externe URL's,
  geen CDN, geen webfont-links.
- Figuren: kopieer een scaffold uit [references/figuren.md](references/figuren.md).
  `viewBox="0 0 880 H"` met H onder 300 — dan is één SVG-eenheid één canvas-px en is
  `font-size="18"` exact Flux' body. Kleur uitsluitend via de `.fig`-classes;
  `fill="var(--…)"` werkt niet in een SVG-attribuut. Eén `<defs>` per SVG met een
  uniek marker-id `ar-<slidenummer>`. Elke SVG krijgt `role="img"` en een `aria-label`.
- SVG-tekst breekt niet af en loopt stil over de rand: reken
  `tekens × 0,55 × font-size + 24 ≤ boxbreedte`. Past het niet, kort het label in
  (maximum drie woorden), verklein het lettertype niet.

**Beeld.** De skill haalt zelf geen beelden op: geen stock-API, geen beeldgeneratie.
Levert de gebruiker een bestand, dan bed je het in als `data:`-URI met een echte
`alt`. Levert hij niets, dan maak je de slide zonder beeld — een deck zonder foto's
is prima, een deck met een verzonnen sfeerbeeld niet. Vraag nooit om een logo na te
tekenen.

**Een graaf die in geen enkel scaffold past.** Render hem dan met Mermaid of D2 naar
SVG, verwijder het meegeleverde thema en hang er de `.fig`-classes aan. Dat is de
noodklep, niet de gewone weg: een gerenderd thema vecht met Flux en de layout-engine
kiest afmetingen die niet op een slide passen.

**Opslaglocatie:**

- Bronnote gegeven → naast die note: `<map van de note>/jjjj-mm-dd-<slug>.html`
- Anders → de huidige werkmap, zelfde naamconventie.
- Bestaat het doelbestand al, overschrijf dan niet stilzwijgend: vraag of gebruik `-v2`.

Datum via `date +%Y-%m-%d`.

### Fase 4: Afwerken en controleren

Twee stappen, allebei verplicht.

```bash
scripts/afwerken.py <pad naar de presentatie>      # inhoud en bestand
node scripts/controleer.js <pad naar de presentatie>   # geometrie
```

`afwerken.py` bakt de drie woff2's in als data-URI en controleert slides, ids,
placeholders, externe resources, `role="img"` en dubbele id's.

`controleer.js` opent het deck in headless Chrome en meet wat geen enkele regex ziet:
inhoud die onder de slide wegvalt en SVG-labels die buiten hun box of buiten de
figuur steken. Het draait op drie venstermaten, want een slide die op een laptop past
kan op een beamer overlopen. Geen npm-dependencies; het praat rechtstreeks met Chrome
via het DevTools-protocol.

Exit 1 = er staat nog iets open; fix en draai opnieuw tot beide scripts schoon zijn.

Daarna zelf nakijken — de scripts zien dit niet:

- Klopt de leesvolgorde van de koppen (h1 op de titelslide, h2 per slide)?
- Heeft elke tabel een `<caption>` en elk beeld een `alt`?
- Staat er nergens een hardcoded kleur of `px`-waarde binnen een slide?
- Is er minstens één figuur? Een deck van louter bullets is een mislukte indeling,
  geen stijlkeuze.
- Bewerk je een bestaand deck uit een oudere template, kopieer er dan geen nieuwe
  scaffold in: dat deck mist de `.fig`-classes en de figuur valt terug op zwart.
  Genereer opnieuw uit de huidige template. `controleer.js` betrapt dit, maar pas
  nadat je het al gemaakt hebt.

### Fase 5: Rapporteren

```
Presentatie: <pad>

Slides: <aantal>
  1. <type> — <kop>
  2. <type> — <kop>
  ...

Openen: dubbelklik het bestand.
Navigatie: cmd+> en cmd+< , of gewoon scrollen.
Printen: cmd+P geeft één slide per pagina (<formaat>). Zet "achtergronden
afdrukken" aan, anders verdwijnen de groene en gele vlakken.
```

Bij een vault-note: geef ook de `obsidian://`-link naar de bronnote.

## Wat de template zelf al doet

Niet opnieuw bouwen, niet weghalen:

- **Scrollen, niet verbergen.** Alle slides staan fysiek in het document, onder
  elkaar, met `scroll-snap`. Ctrl+F en printen werken daardoor gewoon.
- **Teller** rechtsonder via een IntersectionObserver, plus `#slide-N` in de URL zodat
  een reload op dezelfde slide opent.
- **Toetsen**: uitsluitend `cmd+>` en `cmd+<` (op `event.key`, want op AZERTY delen
  `<` en `>` één toets). Bewust geen pijltjes, spatie of PageUp/PageDown: die blijven
  gewoon scrollen. Voeg ze niet toe.
- **Print**: `@page` wordt bij het laden gezet volgens `data-format` — 16:9
  (338,66 × 190,5 mm) of A4 landscape. Eén slide per pagina.
- **Fonts**: `domg` gebruikt Flanders Art Sans 400/500/700, `stencil` gebruikt
  Stardos Stencil, Barlow Condensed en Inter (SIL OFL — zie
  `assets/fonts/LICENTIES.md`). `scripts/afwerken.py` bakt alleen de juiste set in.
- **Twee huiden**: alle slide-CSS loopt via tokens, dus één attribuut wisselt de hele
  stijl. Voeg geen stijlregels toe buiten het `[data-stijl="…"]`-blok.
- **Figuren**: de `.fig`-classes zetten kleur, rand en radius van elke SVG. Scaffolds
  staan in [references/figuren.md](references/figuren.md), niet in de template zelf.

## Foutafhandeling

- Bronpad bestaat niet → meld het en vraag het juiste pad; ga niet zoeken in de vault
  tenzij de gebruiker daarom vraagt.
- Inhoud voor minder dan 6 slides → maak geen opvulslides. Meld dat het kort wordt.
- Gevraagd om een logo → de Flux-Storybook bevat er geen; header en footer van
  Digitaal Vlaanderen laden een externe dienst en kunnen dus niet in een standalone
  bestand. Zet de organisatienaam als tekst in de eyebrow, of vraag om een SVG die je
  inline zet. Teken het leeuwenlogo nooit na.
