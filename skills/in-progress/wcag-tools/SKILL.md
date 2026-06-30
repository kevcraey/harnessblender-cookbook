---
name: wcag-tools
description: Optionele referentie voor het opzetten van WCAG toegankelijkheidstools
---

# WCAG Tools Setup

Overzicht en setup instructies voor WCAG toegankelijkheidstools. Deze skill is **optioneel** - de wcag-audit skill gebruikt axe-core automatisch waar mogelijk.

## Wanneer Deze Skill Te Gebruiken

**Gebruik wcag-tools wanneer:**
- Je tools wilt installeren voor handmatige toegankelijkheidstests
- Je een screenreader wilt leren gebruiken
- Je lokale development environment wilt opzetten voor accessibility testing
- Je wilt weten welke tools beschikbaar zijn

**Gebruik NIET wcag-tools wanneer:**
- Je alleen een audit wilt draaien (gebruik wcag-audit - heeft tools ingebouwd)
- Je problemen wilt fixen (gebruik wcag-fix)
- Je een toegankelijkheidsverklaring wilt maken (gebruik wcag-toegankelijkheidsverklaring)

## Tool Categorieën

### 1. Browser Extensies (Geautomatiseerd)
### 2. Screenreaders (Handmatig)
### 3. Geautomatiseerde Testing (CI/CD)
### 4. Kleurcontrast Tools
### 5. Keyboard Navigation Testing

---

## 1. Browser Extensies

Geautomatiseerde scans tijdens development.

### axe DevTools (Aanbevolen)

**Wat het doet:**
- Scant pagina op WCAG 2.2 problemen
- Geeft directe feedback in browser DevTools
- Toont waar problemen voorkomen in DOM
- Geeft oplossingsvoorstellen

**Installatie:**

**Chrome/Edge:**
```bash
# Via Chrome Web Store
# Zoek naar "axe DevTools" en klik Install
```

**Firefox:**
```bash
# Via Firefox Add-ons
# Zoek naar "axe DevTools" en klik Add to Firefox
```

**Gebruik:**
1. Open DevTools (F12)
2. Ga naar "axe DevTools" tab
3. Klik "Scan ALL of my page"
4. Bekijk gevonden issues

**Output:**
- Gegroepeerd per WCAG niveau (A, AA, AAA)
- Highlight element in page
- Code snippet met probleem
- "Learn more" links naar WCAG docs

### WAVE (Web Accessibility Evaluation Tool)

**Wat het doet:**
- Visuele overlay van accessibility issues
- Toont structuur van heading hierarchy
- Kleurcontrast checker
- ARIA attributes validator

**Installatie:**

**Chrome:**
```bash
# Chrome Web Store: "WAVE Evaluation Tool"
```

**Firefox:**
```bash
# Firefox Add-ons: "WAVE Evaluation Tool"
```

**Gebruik:**
1. Klik WAVE icoon in toolbar
2. Wacht op visuele overlay
3. Klik icons om details te zien
4. Check "Details" tab voor volledige lijst

**Sterke punten:**
- Zeer visueel (makkelijk te begrijpen)
- Toont heading structuur
- Gratis en open source

### Lighthouse (Chrome/Edge ingebouwd)

**Wat het doet:**
- Accessibility audit als onderdeel van performance tests
- Genereert rapport met score (0-100)
- Best practices checker

**Gebruik:**
1. Open DevTools (F12)
2. Ga naar "Lighthouse" tab
3. Selecteer "Accessibility"
4. Klik "Analyze page load"

**CLI Gebruik:**
```bash
npm install -g lighthouse

lighthouse https://example.com --only-categories=accessibility --output=html --output-path=./accessibility-report.html
```

**Output:**
- Score (0-100)
- Grouped by impact (critical, serious, moderate)
- Links naar docs voor elke issue

---

## 2. Screenreaders

Handmatige tests - essentieel voor echte gebruikerservaring.

### NVDA (Windows - Gratis)

**Wat het doet:**
- Meest gebruikte gratis screenreader
- Volledig keyboard navigation
- Leest alles op wat zichtbaar is

**Installatie:**

```bash
# Download van https://www.nvaccess.org/download/
# Run installer
# Start NVDA from desktop
```

**Basis Commando's:**

| Actie | Toets |
|-------|-------|
| Start/Stop NVDA | Ctrl + Alt + N |
| Stop spraak | Ctrl |
| Lees alles | NVDA + Down Arrow |
| Volgende heading | H |
| Vorige heading | Shift + H |
| Volgende link | K |
| Vorige link | Shift + K |
| Volgende landmark | D |
| Elements lijst | NVDA + F7 |

**NVDA key:** Standaard Insert of CapsLock

**Test Scenario:**
1. Start NVDA
2. Open je website
3. Probeer te navigeren zonder muis
4. Check of alles logisch voorgelezen wordt
5. Test formulieren en interactieve elementen

**Gebruik NVDA voor de meeste tests** - het is gratis en gedrag komt overeen met JAWS.

### JAWS (Windows - Betaald)

**Wat het doet:**
- Meest gebruikte professionele screenreader
- Zeer uitgebreid en krachtig
- Duur (€1000+)

**Installatie:**
```bash
# Download trial van https://www.freedomscientific.com/
# 40 minuten per sessie gratis
```

**Gebruik:**
Vergelijkbaar met NVDA. Alleen gebruiken als je specifiek JAWS moet testen.

### VoiceOver (macOS/iOS - Gratis)

**Wat het doet:**
- Ingebouwde macOS screenreader
- Meest gebruikte screenreader op Mac
- Ook op iPhone/iPad

**macOS Activatie:**
```
System Preferences → Accessibility → VoiceOver → Enable
Of: Cmd + F5
```

**Basis Commando's:**

| Actie | Toets |
|-------|-------|
| Start/Stop VoiceOver | Cmd + F5 |
| VoiceOver menu | VO + H (VO = Ctrl + Option) |
| Volgende item | VO + Right Arrow |
| Vorige item | VO + Left Arrow |
| Interactie starten | VO + Shift + Down Arrow |
| Interactie stoppen | VO + Shift + Up Arrow |
| Rotor openen | VO + U |
| Volgende heading | VO + Cmd + H |

**Web Rotor:**
- Open met VO + U
- Navigeer door headings, links, landmarks, forms

**iOS (iPhone/iPad):**
```
Settings → Accessibility → VoiceOver → On
```

**iOS Gebaren:**
- Swipe right: volgende element
- Swipe left: vorige element
- Two finger swipe down: lees alles
- Rotor: draai twee vingers om navigatie mode te kiezen

### TalkBack (Android - Gratis)

**Wat het doet:**
- Ingebouwde Android screenreader
- Meest gebruikte screenreader op Android

**Activatie:**
```
Settings → Accessibility → TalkBack → On
```

**Basis Gebaren:**
- Swipe right: volgende element
- Swipe left: vorige element
- Double tap: activeer element
- Two finger swipe down: lees alles

---

## 3. Geautomatiseerde Testing

Integreer in CI/CD pipeline.

### axe-core CLI

**Wat het doet:**
- Command-line versie van axe DevTools
- Integreerbaar in build scripts
- JSON/HTML output

**Installatie:**
```bash
npm install -g @axe-core/cli
```

**Gebruik:**
```bash
# Scan enkele URL
axe https://example.com

# Scan met specifieke WCAG tags
axe https://example.com --tags wcag2a,wcag2aa,wcag21aa,wcag22aa

# Output naar bestand
axe https://example.com --save results.json

# Scan lokale file
axe file:///path/to/page.html
```

**Output Formats:**
- JSON (default)
- CSV
- Markdown

**CI/CD Integratie:**
```bash
# package.json
{
  "scripts": {
    "test:a11y": "axe https://staging.example.com --exit"
  }
}

# Fails build als issues gevonden worden
npm run test:a11y
```

### pa11y

**Wat het doet:**
- CLI accessibility tester
- Kan meerdere URLs tegelijk testen
- Verschillende reporters

**Installatie:**
```bash
npm install -g pa11y
```

**Gebruik:**
```bash
# Basic scan
pa11y https://example.com

# Met WCAG 2.2 AA standaard
pa11y https://example.com --standard WCAG2AA

# Meerdere URLs
pa11y https://example.com https://example.com/about

# Wacht op JavaScript
pa11y https://example.com --wait 2000

# Ignore specific issues
pa11y https://example.com --ignore "notice;warning"
```

**Reporters:**
```bash
# JSON output
pa11y https://example.com --reporter json

# CSV output
pa11y https://example.com --reporter csv

# HTML report
pa11y https://example.com --reporter html > report.html
```

**Config File (pa11y.json):**
```json
{
  "standard": "WCAG2AA",
  "timeout": 10000,
  "wait": 1000,
  "chromeLaunchConfig": {
    "args": ["--no-sandbox"]
  }
}
```

### Playwright Accessibility Testing

**Wat het doet:**
- Integreert accessibility tests in end-to-end tests
- Gebruikt axe-core onder de motorkap

**Installatie:**
```bash
npm install -D @playwright/test @axe-core/playwright
```

**Voorbeeld Test:**
```javascript
// tests/accessibility.spec.js
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('homepage should not have accessibility violations', async ({ page }) => {
  await page.goto('https://example.com');

  const accessibilityScanResults = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
    .analyze();

  expect(accessibilityScanResults.violations).toEqual([]);
});

test('check specific component', async ({ page }) => {
  await page.goto('https://example.com');

  const results = await new AxeBuilder({ page })
    .include('#main-navigation')
    .analyze();

  expect(results.violations).toEqual([]);
});
```

**Run Tests:**
```bash
npx playwright test accessibility.spec.js
```

---

## 4. Kleurcontrast Tools

Specifieke tools voor WCAG 1.4.3 (kleurcontrast).

### WebAIM Contrast Checker

**Online tool:**
https://webaim.org/resources/contrastchecker/

**Gebruik:**
1. Voer voorgrondkleur in (bijv. #333333)
2. Voer achtergrondkleur in (bijv. #ffffff)
3. Check ratio voor normaal en groot tekst

**WCAG Vereisten:**
- Normaal tekst: 4.5:1 (niveau AA), 7:1 (niveau AAA)
- Groot tekst (18pt+): 3:1 (niveau AA), 4.5:1 (niveau AAA)

### Stark (Figma/Sketch Plugin)

**Wat het doet:**
- Contrast checker in design tools
- Colorblind simulator
- Focus order checker

**Installatie:**
- Figma: Plugins → Browse → "Stark"
- Sketch: Sketch Toolbox → "Stark"

**Gebruik in Figma:**
1. Selecteer text layer
2. Plugins → Stark → Contrast Checker
3. Check of ratio voldoet aan WCAG AA/AAA

### Chrome DevTools Contrast

**Ingebouwd in Chrome:**
1. Inspect element met tekst
2. Bekijk "Styles" panel
3. Klik kleur swatch naast color property
4. Zie contrast ratio onderaan color picker
5. Lijnen in picker tonen AA/AAA boundaries

---

## 5. Keyboard Navigation Testing

Check of alles bereikbaar is via keyboard.

### Browser Built-in

**Geen tools nodig:**
1. Sluit je muis aan (of ontkoppel)
2. Gebruik alleen keyboard:
   - Tab: volgende focusable element
   - Shift + Tab: vorige focusable element
   - Enter: activeer link/button
   - Space: toggle checkbox/button
   - Arrow keys: navigate within component

**Check:**
- [ ] Focus indicator altijd zichtbaar
- [ ] Logische tab volgorde
- [ ] Alle interactieve elementen bereikbaar
- [ ] Geen keyboard trap (kan altijd weg navigeren)
- [ ] Skip link aanwezig (spring naar main content)

### Tab Order Visualizer (Browser Extension)

**Chrome:**
- Search for "Visual Tab Order" in Chrome Web Store

**Gebruik:**
1. Activate extension
2. See numbered overlay showing tab order
3. Identify problematic tab sequences

---

## Aanbevolen Tool Stack

### Minimum Setup (Gratis)
✅ axe DevTools (browser extension)
✅ NVDA (Windows) of VoiceOver (Mac)
✅ Chrome DevTools Lighthouse
✅ Keyboard testing (geen tools nodig)

**Tijd: ~2 uur om te leren**

### Development Team Setup
✅ Minimum setup (zie boven)
✅ axe-core CLI (voor CI/CD)
✅ pa11y (voor bulk testing)
✅ Playwright met axe (voor E2E tests)

**Tijd: ~4 uur om te leren + setup**

### Professioneel Audit Setup
✅ Development team setup (zie boven)
✅ JAWS trial (Windows, voor JAWS-specifieke tests)
✅ VoiceOver (Mac + iPhone/iPad)
✅ TalkBack (Android)
✅ WAVE (voor visuele overlay)
✅ Stark (voor design handoff)

**Tijd: ~2 weken om te leren**

---

## Onboarding Checklist

Gebruik deze checklist om team members op te leiden:

### Week 1: Basis Tools (4-6 uur)

- [ ] **Installeer axe DevTools** (~15 min)
  - Chrome/Firefox extension
  - Scan test page
  - Bekijk verschillende issue types

- [ ] **Leer NVDA/VoiceOver basics** (~2 uur)
  - Installeer screenreader
  - Oefen basis navigatie commando's
  - Test je eigen website
  - Probeer formulier in te vullen zonder scherm

- [ ] **Lighthouse audit runnen** (~30 min)
  - Run audit op bekende website
  - Bekijk accessibility score
  - Lees recommendations

- [ ] **Keyboard navigatie oefenen** (~1 uur)
  - Navigeer websites zonder muis
  - Identificeer focus issues
  - Test je eigen website

### Week 2: Geautomatiseerde Tests (4-6 uur)

- [ ] **axe-core CLI setup** (~1 uur)
  - Installeer globally
  - Scan enkele URLs
  - Bekijk JSON output

- [ ] **pa11y setup** (~1 uur)
  - Installeer globally
  - Maak config file
  - Scan met verschillende reporters

- [ ] **Playwright integratie** (~2 uur)
  - Voeg toe aan bestaand project
  - Schrijf eerste a11y test
  - Run in CI/CD

### Week 3+: Professionele Tools (optioneel)

- [ ] **JAWS trial** (~3 uur)
  - Download en installeer
  - Vergelijk met NVDA
  - Test complexere interacties

- [ ] **Mobile screenreaders** (~2 uur)
  - VoiceOver op iPhone
  - TalkBack op Android
  - Test mobile website

- [ ] **Design tools** (~2 uur)
  - Stark in Figma
  - Contrast checking in design fase

---

## Workflow Integratie

### Development Workflow

```
Design → Code → Test → Deploy

Design:   Stark (contrast check)
Code:     axe DevTools (tijdens development)
Test:     Playwright + axe (automated)
          NVDA/VoiceOver (manual)
Deploy:   pa11y (pre-deploy scan)
```

### CI/CD Pipeline

```yaml
# .github/workflows/accessibility.yml
name: Accessibility Tests

on: [push, pull_request]

jobs:
  a11y:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build

      - name: Start server
        run: npm run serve &

      - name: Wait for server
        run: npx wait-on http://localhost:3000

      - name: Run axe-core tests
        run: npx @axe-core/cli http://localhost:3000 --exit

      - name: Run Playwright a11y tests
        run: npx playwright test accessibility.spec.js
```

---

## Veelgestelde Vragen

**Q: Moet ik alle tools installeren?**
A: Nee. Start met axe DevTools + screenreader (NVDA of VoiceOver). Dat is 80% van wat je nodig hebt.

**Q: Welke screenreader moet ik gebruiken?**
A:
- Windows: NVDA (gratis, goed genoeg)
- Mac: VoiceOver (gratis, ingebouwd)
- Voor professionele audits: test beide + JAWS

**Q: Vervangen geautomatiseerde tools handmatige tests?**
A: Nee! Geautomatiseerde tools vinden ~30-40% van problemen. Screenreader + keyboard tests zijn essentieel.

**Q: Hoe vaak moet ik testen?**
A:
- Tijdens development: axe DevTools bij elke wijziging
- Voor deploy: geautomatiseerde tests in CI/CD
- Per maand: handmatige screenreader test
- Na grote wijzigingen: volledige audit

**Q: Kan ik toegankelijkheid volledig automatiseren?**
A: Nee. Geautomatiseerde tools kunnen niet testen of:
- Alt-tekst betekenisvol is (wel of er alt-tekst IS)
- Screenreader ervaring logisch is
- Formulieren intuïtief zijn
- Toetsenbordnavigatie natuurlijk aanvoelt

---

## Referenties

**Tool Websites:**
- axe DevTools: https://www.deque.com/axe/devtools/
- WAVE: https://wave.webaim.org/
- pa11y: https://pa11y.org/
- NVDA: https://www.nvaccess.org/
- Playwright: https://playwright.dev/

**Learning Resources:**
- WebAIM: https://webaim.org/
- A11y Project: https://www.a11yproject.com/
- MDN Accessibility: https://developer.mozilla.org/en-US/docs/Web/Accessibility

**WCAG Resources:**
- WCAG 2.2: https://www.w3.org/TR/WCAG22/
- How to Meet WCAG: https://www.w3.org/WAI/WCAG22/quickref/
