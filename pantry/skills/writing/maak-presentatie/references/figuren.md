# Figuren — scaffolds voor de figuur-slide

Kopieer een scaffold in `<figure>` op een `s-figure`-slide (of in een kolom van
`s-two`) en vervang de labels. Niets anders aanpassen: geen kleuren, geen
`fill=`-attributen, geen eigen radius.

## De maatregel

`viewBox="0 0 880 H"` — 880 is de contentbreedte van het canvas (1024 min tweemaal
72 padding). Daardoor is **één SVG-eenheid één canvas-px**:

| in de SVG          | is         |
|--------------------|------------|
| `font-size="18"`   | body       |
| `font-size="16"`   | text-small |
| `font-size="14"`   | text-xsmall|
| `rx="3"`           | de enige Flux-radius |

`H` blijft onder **300**, anders loopt de figuur uit de slide (kop + figuur +
onderschrift moeten binnen 456 px passen).

## Regels

- Kleur via de classes uit de template: `.box`, `.box-accent`, `.box-open`,
  `.box-faded`, `.arrow`, `.arrow-faded`, `.label`, `.toel`, `.op-accent`.
  `fill="var(--…)"` werkt niet in een SVG-presentatieattribuut.
- Nadruk = accent. Vervagen = de grijsschaal, niet `opacity`. Gestreept betekent
  iets: wat nog niet bestaat, wat wegvalt, wat niet afgedwongen wordt.
- Eén `<defs>` per SVG met een **uniek** marker-id: `ar-<slidenummer>`. Twee SVG's
  met hetzelfde id en de tweede pikt de marker van de eerste.
- `role="img"` en een `aria-label` die de figuur in één zin beschrijft. Verplicht;
  `afwerken.py` controleert het.
- **SVG-tekst breekt niet af en loopt stil over de rand.** Flanders Art Sans meet
  gemiddeld `0,45 × font-size` per teken, tot `0,59` voor labels vol hoofdletters
  (gemeten in de browser op deze scaffolds). Reken met **0,55**: een label past als
  `tekens × 0,55 × font-size + 24 ≤ breedte van de box`. Bij `font-size="18"` in een
  box van 250 breed is dat 22 tekens. Past het niet: kort het label in (max drie
  woorden), verklein het lettertype niet.

## 1. Keten — volgorde, stappen, verval

```html
<svg class="fig" viewBox="0 0 880 150" role="img" aria-label="…">
  <defs><marker id="ar-N" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path class="arrow-head" d="M0 0 L10 5 L0 10 z"/></marker></defs>
  <rect class="box" x="0" y="20" width="250" height="72" rx="3"/>
  <rect class="box" x="315" y="20" width="250" height="72" rx="3"/>
  <rect class="box-faded" x="630" y="20" width="250" height="72" rx="3"/>
  <path class="arrow" d="M258 56 H307" marker-end="url(#ar-N)"/>
  <path class="arrow" d="M573 56 H622" marker-end="url(#ar-N)"/>
  <g text-anchor="middle">
    <text class="label" x="125" y="52" font-size="18">Eerste</text>
    <text class="toel"  x="125" y="76" font-size="14">toelichting</text>
    <text class="label" x="440" y="52" font-size="18">Tweede</text>
    <text class="toel"  x="440" y="76" font-size="14">toelichting</text>
    <text class="label toel" x="755" y="52" font-size="18">Derde</text>
    <text class="toel"  x="755" y="76" font-size="14">toelichting</text>
  </g>
</svg>
```

Vier stappen: `width="196"`, x = 0, 228, 456, 684.
Lus terug (bv. "en het begint opnieuw"): `<path class="arrow-faded" d="M755 100 V130 H125 V100" marker-end="url(#ar-N)"/>`, viewBox-hoogte dan 150.

## 2. Fan-out — één naar veel naar één

```html
<svg class="fig" viewBox="0 0 880 250" role="img" aria-label="…">
  <defs><marker id="ar-N" …/></defs>
  <rect class="box-accent" x="0" y="85" width="200" height="80" rx="3"/>
  <rect class="box" x="300" y="10"  width="280" height="56" rx="3"/>
  <rect class="box" x="300" y="97"  width="280" height="56" rx="3"/>
  <rect class="box" x="300" y="184" width="280" height="56" rx="3"/>
  <rect class="box-accent" x="680" y="85" width="200" height="80" rx="3"/>
  <path class="arrow" d="M208 112 H254 V38 H292"  marker-end="url(#ar-N)"/>
  <path class="arrow" d="M208 125 H292"           marker-end="url(#ar-N)"/>
  <path class="arrow" d="M208 138 H254 V212 H292" marker-end="url(#ar-N)"/>
  <path class="arrow" d="M588 38 H634 V112 H672"  marker-end="url(#ar-N)"/>
  <path class="arrow" d="M588 125 H672"           marker-end="url(#ar-N)"/>
  <path class="arrow" d="M588 212 H634 V138 H672" marker-end="url(#ar-N)"/>
  <g text-anchor="middle">
    <text class="label op-accent" x="100" y="120" font-size="18">Bron</text>
    <text class="toel op-accent" x="100" y="142" font-size="14">toelichting</text>
    <text class="label" x="440" y="44"  font-size="18">Eerste weg</text>
    <text class="label" x="440" y="131" font-size="18">Tweede weg</text>
    <text class="label" x="440" y="218" font-size="18">Derde weg</text>
    <text class="label op-accent" x="780" y="120" font-size="18">Resultaat</text>
    <text class="toel op-accent" x="780" y="142" font-size="14">toelichting</text>
  </g>
</svg>
```

## 3. Lagen — hiërarchie, wat centraal ligt en wat erbovenop komt

```html
<svg class="fig" viewBox="0 0 880 262" role="img" aria-label="…">
  <defs><marker id="ar-N" …/></defs>
  <rect class="box-faded"  x="0" y="0"   width="800" height="56" rx="3"/>
  <rect class="box-faded"  x="0" y="68"  width="800" height="56" rx="3"/>
  <rect class="box-accent" x="0" y="136" width="800" height="56" rx="3"/>
  <rect class="box-accent" x="0" y="204" width="800" height="56" rx="3"/>
  <path class="arrow" d="M840 252 V14" marker-end="url(#ar-N)"/>
  <g>
    <text class="label" x="20" y="26" font-size="18">Bovenste laag</text>
    <text class="toel"  x="20" y="46" font-size="14">toelichting</text>
    <text class="label" x="20" y="94"  font-size="18">Derde laag</text>
    <text class="toel"  x="20" y="114" font-size="14">toelichting</text>
    <text class="label op-accent" x="20" y="162" font-size="18">Tweede laag</text>
    <text class="toel op-accent"  x="20" y="182" font-size="14">centraal</text>
    <text class="label op-accent" x="20" y="230" font-size="18">Onderste laag</text>
    <text class="toel op-accent"  x="20" y="250" font-size="14">centraal</text>
  </g>
  <text class="toel" x="855" y="130" font-size="14" text-anchor="middle" transform="rotate(-90 855 130)">richting</text>
</svg>
```

## 4. Gradiënt — spectrum, afnemend vertrouwen of toenemende kost

```html
<svg class="fig" viewBox="0 0 880 132" role="img" aria-label="…">
  <defs><marker id="ar-N" …/></defs>
  <rect class="box"        x="0"   y="0" width="202" height="76" rx="3"/>
  <rect class="box"        x="226" y="0" width="202" height="76" rx="3"/>
  <rect class="box-faded"  x="452" y="0" width="202" height="76" rx="3"/>
  <rect class="box-faded"  x="678" y="0" width="202" height="76" rx="3"/>
  <path class="arrow-faded" d="M0 108 H870" marker-end="url(#ar-N)"/>
  <g text-anchor="middle">
    <text class="label" x="101" y="34" font-size="16">Sterkste</text>
    <text class="toel"  x="101" y="56" font-size="14">toelichting</text>
    <text class="label" x="327" y="34" font-size="16">Tweede</text>
    <text class="toel"  x="327" y="56" font-size="14">toelichting</text>
    <text class="label" x="553" y="34" font-size="16">Derde</text>
    <text class="toel"  x="553" y="56" font-size="14">toelichting</text>
    <text class="label" x="779" y="34" font-size="16">Zwakste</text>
    <text class="toel"  x="779" y="56" font-size="14">toelichting</text>
  </g>
  <text class="toel" x="440" y="128" font-size="14" text-anchor="middle">wat afneemt</text>
</svg>
```

Vier boxen van 202 breed: bij `font-size="16"` past ongeveer 20 tekens per regel.

## 5. Raster 2×2 — vergelijking, vier losse punten

```html
<svg class="fig" viewBox="0 0 880 240" role="img" aria-label="…">
  <rect class="box-open" x="0"   y="0"   width="428" height="110" rx="3"/>
  <rect class="box-open" x="452" y="0"   width="428" height="110" rx="3"/>
  <rect class="box-open" x="0"   y="130" width="428" height="110" rx="3"/>
  <rect class="box-open" x="452" y="130" width="428" height="110" rx="3"/>
  <g>
    <text class="label" x="24" y="44"  font-size="18">Eerste punt</text>
    <text class="toel"  x="24" y="70"  font-size="14">toelichting</text>
    <text class="label" x="476" y="44" font-size="18">Tweede punt</text>
    <text class="toel"  x="476" y="70" font-size="14">toelichting</text>
    <text class="label" x="24" y="174"  font-size="18">Derde punt</text>
    <text class="toel"  x="24" y="200"  font-size="14">toelichting</text>
    <text class="label" x="476" y="174" font-size="18">Vierde punt</text>
    <text class="toel"  x="476" y="200" font-size="14">toelichting</text>
  </g>
</svg>
```

Een cel is 428 breed: bij `font-size="18"` past ongeveer 40 tekens, bij 14 ongeveer
52. Eén regel per cel — twee regels vraagt een tweede `<text>` op `y + 22`.

## 6. Staafgrafiek — echte getallen

Voor cijfers die je met elkaar vergelijkt. Liggende balken: de labels staan links
en mogen lang zijn, wat bij staande balken niet gaat. Maximum zes rijen.

Reken de balkbreedte uit: `breedte = waarde / hoogste waarde × 550`. Rond af op een
geheel getal. Zet nooit een balk zonder zijn getal ernaast, en noem de bron in het
onderschrift van de slide.

```html
<svg class="fig" viewBox="0 0 880 200" role="img" aria-label="…">
  <!-- rij 1, y = 0; rij 2, y = 56; rij 3, y = 112; rij 4, y = 168 -->
  <g>
    <text class="label" x="250" y="26" font-size="18" text-anchor="end">Eerste reeks</text>
    <rect class="box-accent" x="270" y="6" width="550" height="28" rx="3"/>
    <text class="label" x="832" y="26" font-size="16">25</text>

    <text class="label" x="250" y="82" font-size="18" text-anchor="end">Tweede reeks</text>
    <rect class="box-accent" x="270" y="62" width="264" height="28" rx="3"/>
    <text class="label" x="546" y="82" font-size="16">12</text>

    <text class="label" x="250" y="138" font-size="18" text-anchor="end">Derde reeks</text>
    <rect class="box" x="270" y="118" width="154" height="28" rx="3"/>
    <text class="toel" x="436" y="138" font-size="16">7</text>
  </g>
  <path class="arrow" d="M270 0 V160"/>
</svg>
```

- Eén accentkleur. Gebruik `.box` in plaats van `.box-accent` voor de reeksen die
  je níét benadrukt; maak geen regenboog van de DOMG-kleuren.
- Het getal staat altijd rechts van de balk, op `x = 270 + breedte + 12`.
- Staande balken (voor een tijdreeks): kolommen van 80 breed met 40 ertussen,
  nulllijn op `y = 160`, hoogte `waarde / hoogste × 140`, label eronder op `y = 184`.
- **Verzin nooit een getal.** Staat het niet in de bron, dan is er geen grafiek.
