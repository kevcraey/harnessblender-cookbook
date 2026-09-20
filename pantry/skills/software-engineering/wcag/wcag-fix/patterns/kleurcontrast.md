# Oplossing: Onvoldoende Kleurcontrast (WCAG 1.4.3)

## Wat is het probleem?

Tekst met te weinig contrast ten opzichte van de achtergrond is moeilijk te lezen voor gebruikers met slechtziendheid of kleurenblindheid.

## Impact

- Slechtziende gebruikers kunnen tekst niet lezen
- Gebruikers met kleurenblindheid hebben moeite met lezen
- Gebruikers in fel zonlicht (bijv. buiten op mobiel) kunnen tekst niet zien
- **WCAG Niveau:** AA - Wettelijk verplicht voor overheid en grote organisaties

## Contrast Ratios

| Type Tekst | Minimaal Contrast | WCAG Niveau |
|-----------|------------------|-------------|
| Normale tekst (<18pt) | 4.5:1 | AA |
| Grote tekst (≥18pt of ≥14pt bold) | 3:1 | AA |
| Normale tekst | 7:1 | AAA |
| Grote tekst | 4.5:1 | AAA |
| UI componenten | 3:1 | AA |

## Oplossing

### Optie 1: Donkerder Maken (aanbevolen)

```css
/* Voor - 2.8:1 contrast */
.text {
  color: #767676;
  background: #FFFFFF;
}

/* Na - 4.52:1 contrast ✓ */
.text {
  color: #595959;
  background: #FFFFFF;
}
```

**Uitleg:** Maak de voorgrondkleur donkerder totdat het contrast voldoende is.

### Optie 2: Achtergrond Aanpassen

```css
/* Voor - 2.8:1 contrast */
.text {
  color: #767676;
  background: #FFFFFF;
}

/* Na - 4.54:1 contrast ✓ */
.text {
  color: #767676;
  background: #F0F0F0;
}
```

**Wanneer te gebruiken:** Als de tekstkleur een brand color is die niet veranderd mag worden.

### Optie 3: Grotere Tekst

```css
/* Voor - 2.8:1 contrast met 14px tekst */
.text {
  font-size: 14px;
  color: #959595;
  background: #FFFFFF;
}

/* Na - 3.3:1 contrast is OK voor grote tekst */
.text {
  font-size: 18px; /* Minimaal 18pt/24px voor body text */
  font-weight: normal;
  color: #959595;
  background: #FFFFFF;
}
```

**Wanneer te gebruiken:** Voor headings of grote UI elementen waar grotere tekst acceptabel is.

## Testen

### Online Tools

**WebAIM Contrast Checker:**
```
https://webaim.org/resources/contrastchecker/

Input:
- Foreground: #767676
- Background: #FFFFFF
- Result: 4.54:1 (WCAG AA ✓)
```

**Coolors Contrast Checker:**
```
https://coolors.co/contrast-checker
```

### Browser Tools

**Chrome DevTools:**
```
1. Inspect element met tekst
2. Ga naar "Styles" panel
3. Klik op kleur square naast color property
4. Zie "Contrast ratio" onderaan color picker
5. DevTools toont of het voldoet aan AA/AAA
```

**Firefox DevTools:**
```
1. Inspect element
2. Ga naar "Accessibility" panel
3. Zie "Contrast" sectie met ratio
```

### Automated Testing

```bash
# axe DevTools checkt automatisch contrast
npx @axe-core/cli https://example.com --tags wcag2aa

# pa11y
npx pa11y https://example.com --standard WCAG2AA
```

## Checklist

- [ ] Contrast ratio is minimaal 4.5:1 voor normale tekst
- [ ] Contrast ratio is minimaal 3:1 voor grote tekst (18pt+)
- [ ] Contrast ratio is minimaal 3:1 voor UI componenten (buttons, borders)
- [ ] Contrast blijft voldoende in dark mode (als aanwezig)
- [ ] Brand colors zijn waar mogelijk behouden
- [ ] Getest met color blindness simulator

## Veelgemaakte Fouten

### ❌ Alleen focus op brand colors

```css
/* FOUT - mooie brand color maar onleesbaar */
.primary-text {
  color: #FF6B9D; /* Lichte pink */
  background: #FFFFFF;
  /* Contrast: 2.1:1 ✗ */
}
```

Brand colors zijn belangrijk, maar toegankelijkheid gaat voor.

### ❌ Placeholder text met laag contrast

```css
/* FOUT - placeholders vaak te licht */
::placeholder {
  color: #CCCCCC; /* 1.6:1 contrast ✗ */
}

/* GOED */
::placeholder {
  color: #767676; /* 4.5:1 contrast ✓ */
}
```

### ❌ Link text zonder voldoende contrast

```css
/* FOUT */
a {
  color: #4A90E2; /* 3.4:1 contrast ✗ */
}

/* GOED */
a {
  color: #0066CC; /* 4.5:1 contrast ✓ */
  text-decoration: underline; /* Extra indicator */
}
```

## Dark Mode Overwegingen

```css
/* Light mode */
@media (prefers-color-scheme: light) {
  .text {
    color: #2C3E50; /* Donker op licht */
    background: #FFFFFF;
    /* 12.6:1 contrast ✓ */
  }
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  .text {
    color: #E8E8E8; /* Licht op donker */
    background: #1A1A1A;
    /* 11.8:1 contrast ✓ */
  }
}
```

**Let op:** Test BEIDE modes voor voldoende contrast!

## Referenties

- [WCAG 1.4.3: Contrast (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
