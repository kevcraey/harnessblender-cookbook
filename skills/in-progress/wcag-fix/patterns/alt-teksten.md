# Oplossing: Ontbrekende of Slechte Alt-teksten (WCAG 1.1.1)

## Wat is het probleem?

Afbeeldingen zonder alt-tekst zijn onzichtbaar voor screenreader gebruikers. Slechte alt-tekst geeft niet genoeg context.

## Impact

- Blinde gebruikers missen essentiële informatie
- Zoekmachines kunnen afbeeldingen niet indexeren
- Afbeeldingen die niet laden tonen geen nuttige tekst
- **WCAG Niveau:** A - Dit blokkeert basale toegankelijkheid

## Oplossing

### Optie 1: Informatieve Afbeeldingen

```html
<!-- Voor -->
<img src="chart.png">

<!-- FOUT - te generiek -->
<img src="chart.png" alt="grafiek">

<!-- GOED - beschrijvend -->
<img src="chart.png" alt="Verkoopcijfers stegen met 25% van Q1 naar Q2 2026">
```

**Richtlijnen voor goede alt-tekst:**
- Beschrijf wat de afbeelding communiceert, niet hoe het eruitziet
- Wees specifiek en bondig (max ~150 karakters voor kort)
- Herhaal geen informatie die al in omliggende tekst staat
- Gebruik geen "afbeelding van" of "foto van" - screenreader zegt dat al

### Optie 2: Decoratieve Afbeeldingen

```html
<!-- Voor -->
<img src="decorative-line.png">

<!-- FOUT - onnodige info -->
<img src="decorative-line.png" alt="decoratieve lijn">

<!-- GOED - lege alt voor decoratie -->
<img src="decorative-line.png" alt="">
```

**Wanneer `alt=""`:**
- Puur decoratieve elementen (lijnen, spacers, achtergrond patronen)
- Afbeeldingen waarvan info al in tekst staat
- Icons met aangrenzend tekstlabel

**Let op:** Gebruik `alt=""`, NIET weglaten van alt attribuut!

### Optie 3: Functionele Afbeeldingen (buttons, links)

```html
<!-- Voor -->
<a href="/search">
  <img src="search-icon.png">
</a>

<!-- FOUT - beschrijft uiterlijk -->
<a href="/search">
  <img src="search-icon.png" alt="vergrootglas icon">
</a>

<!-- GOED - beschrijft functie -->
<a href="/search">
  <img src="search-icon.png" alt="Zoeken">
</a>
```

**Voor functionele afbeeldingen:**
- Beschrijf de actie, niet de afbeelding
- Denk: wat gebeurt er als ik klik?

### Optie 4: Complexe Afbeeldingen (grafieken, diagrammen)

```html
<!-- Voor een complexe grafiek -->
<figure>
  <img src="complex-chart.png"
       alt="Verkoopcijfers per regio 2023-2026">
  <figcaption>
    <details>
      <summary>Gedetailleerde beschrijving</summary>
      <p>Dit staafdiagram toont de verkoopcijfers voor drie regio's over vier jaar:</p>
      <ul>
        <li>Noord-Europa: €2.3M (2023) → €3.1M (2026), +35% groei</li>
        <li>Zuid-Europa: €1.8M (2023) → €2.2M (2026), +22% groei</li>
        <li>Oost-Europa: €1.2M (2023) → €1.9M (2026), +58% groei</li>
      </ul>
      <p>Oost-Europa toont de sterkste groei trend.</p>
    </details>
  </figcaption>
</figure>
```

**Voor complexe visualisaties:**
- Korte alt-tekst met onderwerp
- Langere beschrijving in `<figcaption>` of met `aria-describedby`
- Overweeg data table als alternatief

### Optie 5: Logo's

```html
<!-- Voor -->
<img src="logo.png">

<!-- FOUT - te technisch -->
<img src="logo.png" alt="logo.png 250x80 pixels">

<!-- GOED - bedrijfsnaam -->
<img src="logo.png" alt="Acme Corporation">

<!-- In navigatie context -->
<a href="/">
  <img src="logo.png" alt="Acme Corporation homepage">
</a>
```

### Optie 6: Icon Met Tekst

```html
<!-- Pattern 1: Icon is decoratief -->
<button>
  <img src="save-icon.png" alt="">
  Opslaan
</button>

<!-- Pattern 2: Icon staat alleen (geen visuele tekst) -->
<button>
  <img src="save-icon.png" alt="Opslaan">
</button>

<!-- Pattern 3: Met aria-label -->
<button aria-label="Opslaan">
  <img src="save-icon.png" alt="">
</button>
```

## Testen

### Handmatig

1. **Turn off images** in browser
2. Is alle informatie nog steeds begrijpelijk?
3. Lees alt-teksten hardop - klinken ze natuurlijk?

### Met Screenreader

**macOS VoiceOver:**
```
Cmd + F5 (activeer VoiceOver)
VO + Right Arrow (navigeer door pagina)
# Luister naar hoe afbeeldingen aangekondigd worden
```

### Automated

```bash
# axe DevTools checkt ontbrekende alt
npx @axe-core/cli https://example.com --tags wcag2a
```

## Checklist

- [ ] Alle `<img>` elementen hebben `alt` attribuut
- [ ] Informatieve afbeeldingen hebben beschrijvende alt-tekst
- [ ] Decoratieve afbeeldingen hebben `alt=""`
- [ ] Functionele afbeeldingen beschrijven de actie
- [ ] Complexe afbeeldingen hebben lange beschrijving
- [ ] Alt-tekst is bondig (<150 chars waar mogelijk)
- [ ] Geen "afbeelding van" of "foto van" in alt-tekst
- [ ] SVG's hebben `<title>` of `aria-label`

## Veelgemaakte Fouten

### ❌ Weglaten van alt attribuut

```html
<!-- FOUT - geen alt -->
<img src="important.png">

<!-- GOED - zelfs als leeg -->
<img src="decorative.png" alt="">
```

Ontbrekend alt is ALTIJD fout, zelfs voor decoratie.

### ❌ Bestandsnaam als alt

```html
<!-- FOUT -->
<img src="IMG_20231215_143022.jpg" alt="IMG_20231215_143022">

<!-- GOED -->
<img src="IMG_20231215_143022.jpg" alt="Teamfoto bij kerstborrel 2023">
```

### ❌ Onnuttige alt-tekst

```html
<!-- FOUT - zegt niks -->
<img src="graph.png" alt="afbeelding">
<img src="diagram.png" alt="zie afbeelding hieronder">

<!-- GOED - beschrijvend -->
<img src="graph.png" alt="Websiteverkeer verdubbelde in december">
```

### ❌ Alt-tekst herhaalt omliggende tekst

```html
<!-- FOUT - alt herhaalt heading -->
<h2>Onze Missie</h2>
<img src="mission.jpg" alt="Onze missie">

<!-- GOED - alt is leeg of aanvullend -->
<h2>Onze Missie</h2>
<img src="mission.jpg" alt="">

<!-- OF -->
<h2>Onze Missie</h2>
<img src="mission.jpg" alt="Team dat samenwerkt aan innovatieve oplossingen">
```

### ❌ SVG zonder toegankelijkheid

```html
<!-- FOUT - SVG zonder alt equivalent -->
<svg>
  <path d="..."/>
</svg>

<!-- GOED - SVG met title -->
<svg role="img" aria-labelledby="svg-title">
  <title id="svg-title">Verkoopgroei 2026</title>
  <path d="..."/>
</svg>

<!-- OF decoratief SVG -->
<svg aria-hidden="true">
  <path d="..."/>
</svg>
```

## Voorbeelden per Context

### E-commerce Product

```html
<img src="blue-tshirt.jpg"
     alt="Navy blauwe T-shirt met V-hals, 100% katoen">
```

### Blog Hero Image

```html
<!-- Als afbeelding puur sfeer is -->
<img src="laptop-coffee.jpg" alt="">

<!-- Als afbeelding context geeft -->
<img src="speaker-stage.jpg"
     alt="Keynote spreker presenteert voor volle zaal op Tech Conference 2026">
```

### Data Visualisatie

```html
<img src="pie-chart.png"
     alt="Taartdiagram: 60% tevreden, 30% neutraal, 10% ontevreden"
     longdesc="#chart-description">

<div id="chart-description">
  <p>Klanttevredenheidsonderzoek Q4 2026 (n=1000):</p>
  <ul>
    <li>Zeer tevreden: 40%</li>
    <li>Tevreden: 20%</li>
    <li>Neutraal: 30%</li>
    <li>Ontevreden: 7%</li>
    <li>Zeer ontevreden: 3%</li>
  </ul>
</div>
```

### Icon Buttons

```html
<!-- Favoriet toggle -->
<button aria-label="Toevoegen aan favorieten">
  <img src="heart-icon.svg" alt="">
</button>

<!-- Met visuele staat -->
<button aria-label="Verwijderen uit favorieten" aria-pressed="true">
  <img src="heart-filled-icon.svg" alt="">
</button>
```

## Referenties

- [WCAG 1.1.1: Non-text Content](https://www.w3.org/WAI/WCAG22/Understanding/non-text-content.html)
- [WebAIM: Alternative Text](https://webaim.org/techniques/alttext/)
- [W3C Alt Decision Tree](https://www.w3.org/WAI/tutorials/images/decision-tree/)
- [Axess Lab: Alt-texts: The Ultimate Guide](https://axesslab.com/alt-texts/)
