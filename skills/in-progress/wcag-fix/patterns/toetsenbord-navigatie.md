# Oplossing: Toetsenbord Navigatie Problemen (WCAG 2.1.1)

## Wat is het probleem?

Gebruikers die niet kunnen of willen gebruiken van een muis moeten alle functionaliteit kunnen bereiken met alleen het toetsenbord.

## Impact

- Blinde gebruikers (screenreader + toetsenbord) kunnen interface niet gebruiken
- Gebruikers met motorische beperkingen die alleen toetsenbord gebruiken zijn uitgesloten
- Power users die sneltoetsen prefereren worden gehinderd
- **WCAG Niveau:** A - Dit blokkeert basale toegankelijkheid

## Oplossing

### Optie 1: Gebruik Native HTML Elementen (aanbevolen)

```html
<!-- Voor - niet toetsenbord toegankelijk -->
<div onclick="submitForm()">Verzenden</div>

<!-- Na - native button is toetsenbord toegankelijk -->
<button onclick="submitForm()">Verzenden</button>
```

**Uitleg:** Native HTML elementen (`<button>`, `<a>`, `<input>`) zijn standaard toetsenbord toegankelijk.

**Voordelen:**
- Werkt automatisch met Tab, Enter, Space
- Krijgt automatisch focus styling
- Screenreaders herkennen het als interactief element

### Optie 2: Custom Element Met ARIA

Als je echt een custom element moet gebruiken:

```html
<!-- Voor - div is niet focusbaar -->
<div class="button" onclick="doSomething()">Klik hier</div>

<!-- Na - maak focusbaar en toegankelijk -->
<div role="button" tabindex="0" class="button"
     onclick="doSomething()"
     onkeydown="if(event.key === 'Enter' || event.key === ' ') { event.preventDefault(); doSomething(); }">
  Klik hier
</div>
```

**Vereisten voor custom interactive elements:**
- `role="button"` - vertelt screenreaders dat het een button is
- `tabindex="0"` - maakt element focusbaar met Tab
- `onkeydown` handler - reageert op Enter en Space toetsen
- `event.preventDefault()` voor Space - voorkomt scrollen

### Optie 3: Focus Management in Modals

```javascript
// Modal dialog met focus trap
class AccessibleModal {
  constructor(modalElement) {
    this.modal = modalElement;
    this.focusableElements = null;
    this.firstFocusable = null;
    this.lastFocusable = null;
  }

  open() {
    // Sla huidige focus op
    this.previousFocus = document.activeElement;

    // Vind alle focusbare elementen in modal
    this.focusableElements = this.modal.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    this.firstFocusable = this.focusableElements[0];
    this.lastFocusable = this.focusableElements[this.focusableElements.length - 1];

    // Trap focus in modal
    this.modal.addEventListener('keydown', this.handleKeyDown.bind(this));

    // Focus eerste element
    this.firstFocusable.focus();

    // Toon modal
    this.modal.style.display = 'block';
    this.modal.setAttribute('aria-hidden', 'false');
  }

  handleKeyDown(event) {
    // Escape sluit modal
    if (event.key === 'Escape') {
      this.close();
      return;
    }

    // Tab trap - blijf binnen modal
    if (event.key === 'Tab') {
      if (event.shiftKey) { // Shift + Tab
        if (document.activeElement === this.firstFocusable) {
          event.preventDefault();
          this.lastFocusable.focus();
        }
      } else { // Tab
        if (document.activeElement === this.lastFocusable) {
          event.preventDefault();
          this.firstFocusable.focus();
        }
      }
    }
  }

  close() {
    this.modal.style.display = 'none';
    this.modal.setAttribute('aria-hidden', 'true');

    // Herstel focus naar waar het was
    if (this.previousFocus) {
      this.previousFocus.focus();
    }
  }
}
```

### Optie 4: Skip Links

```html
<!-- Skip link voor toetsenbord gebruikers -->
<a href="#main-content" class="skip-link">
  Spring naar hoofdinhoud
</a>

<!-- Later in de pagina -->
<main id="main-content" tabindex="-1">
  <!-- Content -->
</main>

<style>
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: #000;
  color: #fff;
  padding: 8px;
  text-decoration: none;
  z-index: 100;
}

.skip-link:focus {
  top: 0;
}
</style>
```

**Wanneer te gebruiken:** Op elke pagina met navigatie menu, om toetsenbord gebruikers snel naar content te laten springen.

## Testen

### Handmatig Testen

1. **Verberg je muis** of gebruik alleen toetsenbord
2. **Tab door de hele interface:**
   - Kun je bij elk interactief element komen?
   - Is de tab volgorde logisch?
   - Zie je waar focus is? (focus indicator)
3. **Test alle functionaliteit:**
   - Buttons met Enter en Space
   - Links met Enter
   - Dropdowns met pijltjes toetsen
   - Modals kunnen gesloten met Escape
4. **Focus blijft niet vast:**
   - Geen keyboard traps (behalve in modals)
   - Focus keert terug na modal sluiten

### Toetsenbord Shortcuts

| Toets | Verwachte Actie |
|-------|----------------|
| Tab | Volgende focusbare element |
| Shift + Tab | Vorige focusbare element |
| Enter | Activeer link of button |
| Space | Activeer button, toggle checkbox |
| Escape | Sluit modal/dropdown |
| Arrow keys | Navigeer in dropdown/menu |
| Home/End | Eerste/laatste item in lijst |

### Automated Testing

```javascript
// Test of element focusbaar is
const button = document.querySelector('.custom-button');
console.log(button.tabIndex >= 0); // Should be true

// Test of alle interactive elements focusbaar zijn
document.querySelectorAll('button, a, input').forEach(el => {
  if (el.tabIndex < 0 && !el.disabled) {
    console.error('Not keyboard accessible:', el);
  }
});
```

## Checklist

- [ ] Alle functionaliteit bereikbaar met alleen toetsenbord
- [ ] Tab volgorde is logisch (matches visuele volgorde)
- [ ] Focus is altijd zichtbaar (geen `outline: none` zonder vervanging)
- [ ] Enter/Space activeert buttons
- [ ] Escape sluit modals
- [ ] Geen keyboard traps (focus kan altijd wegbewegen)
- [ ] Skip links aanwezig voor lange navigatie
- [ ] Custom widgets reageren op Arrow keys waar logisch

## Veelgemaakte Fouten

### ❌ `outline: none` zonder vervanging

```css
/* FOUT - verwijdert focus indicator */
button:focus {
  outline: none;
}

/* GOED - custom focus indicator */
button:focus {
  outline: 3px solid #005fcc;
  outline-offset: 2px;
}

/* OF gebruik :focus-visible voor muis vs toetsenbord */
button:focus:not(:focus-visible) {
  outline: none;
}

button:focus-visible {
  outline: 3px solid #005fcc;
  outline-offset: 2px;
}
```

### ❌ Click handlers zonder keyboard support

```javascript
// FOUT
div.addEventListener('click', () => {
  // Werkt niet met toetsenbord
});

// GOED - gebruik button element
button.addEventListener('click', () => {
  // Werkt met click, Enter, en Space
});
```

### ❌ Negatieve tabindex op interactieve elementen

```html
<!-- FOUT - maakt link onbereikbaar voor toetsenbord -->
<a href="/page" tabindex="-1">Link</a>

<!-- GOED - tabindex="-1" alleen voor programmatic focus -->
<div id="error-message" tabindex="-1">Error occurred</div>
<script>
  // Focus op error na validatie
  document.getElementById('error-message').focus();
</script>
```

### ❌ Onlogische tab volgorde

```html
<!-- FOUT - tab order matches DOM, not visual order -->
<div style="display: flex; flex-direction: column-reverse;">
  <button>Laatste actie</button>
  <button>Tweede actie</button>
  <button>Eerste actie</button>
</div>

<!-- GOED - DOM order matches visual order -->
<div style="display: flex; flex-direction: column;">
  <button>Eerste actie</button>
  <button>Tweede actie</button>
  <button>Laatste actie</button>
</div>
```

## Referenties

- [WCAG 2.1.1: Keyboard](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html)
- [WCAG 2.1.2: No Keyboard Trap](https://www.w3.org/WAI/WCAG22/Understanding/no-keyboard-trap.html)
- [MDN: Keyboard-navigable JavaScript widgets](https://developer.mozilla.org/en-US/docs/Web/Accessibility/Keyboard-navigable_JavaScript_widgets)
- [WebAIM: Keyboard Accessibility](https://webaim.org/techniques/keyboard/)
