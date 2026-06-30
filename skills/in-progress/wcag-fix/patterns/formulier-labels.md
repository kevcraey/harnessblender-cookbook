# Remediation Pattern: Formulier Labels

## Wat is het probleem?

Form inputs (text, checkbox, radio, etc.) hebben geen geassocieerd label dat door screenreaders wordt voorgelezen.

**WCAG Criterium**: 3.3.2 Labels or Instructions (Niveau A)
**Impact**: Kritiek - gebruikers met screenreaders weten niet wat ze moeten invullen

## Symptomen

- Input field heeft wel placeholder, maar geen `<label>` element
- Label staat visueel naast input, maar is niet programmatisch gekoppeld
- Knop of icon gebruikt als "label" zonder tekst alternatief
- Meerdere inputs zonder onderscheidende labels (bijv. meerdere "email" velden)

## Impact

**Voor screenreader gebruikers:**
- Weten niet wat een input field verwacht
- Kunnen niet navigeren tussen form fields via labels
- Krijgen geen feedback over required/optional status
- Missen validatie instructies

**Voor spraakgestuurde software:**
- Gebruikers kunnen niet zeggen "click email" om field te focussen
- Moeten moeizaam navigeren met "tab tab tab"

**Voor iedereen:**
- Label clicking om input te focussen werkt niet
- Kleinere hit area (vooral problematisch voor checkboxes/radios op mobiel)

## Oplossing 1: Visible Label (Aanbevolen)

**Gebruik wanneer**: Standaard oplossing voor de meeste formulieren

```html
<!-- ❌ Fout: Geen label -->
<input type="text" placeholder="Je naam" />

<!-- ✅ Correct: Expliciete koppeling met for/id -->
<label for="user-name">Naam</label>
<input type="text" id="user-name" placeholder="bijv. Jan Jansen" />
```

**React/JSX:**
```jsx
// ❌ Fout
<input type="email" placeholder="Email adres" />

// ✅ Correct
<label htmlFor="user-email">Email adres</label>
<input
  type="email"
  id="user-email"
  placeholder="naam@voorbeeld.nl"
/>
```

**Voordelen:**
- Duidelijkst voor alle gebruikers
- Grotere click area
- Beter voor cognitieve toegankelijkheid

**Nadelen:**
- Neemt visuele ruimte in (maar dit is meestal geen echt nadeel)

## Oplossing 2: aria-label (Als Visible Label Onmogelijk Is)

**Gebruik wanneer**: Visueel label echt niet kan (bijv. zoekformulier met alleen icon)

```html
<!-- ✅ Correct voor icon-only search -->
<input
  type="search"
  aria-label="Zoek op deze website"
  placeholder="Zoeken..."
/>
<button type="submit">
  <svg aria-hidden="true"><!-- search icon --></svg>
  <span class="sr-only">Zoeken</span>
</button>
```

**React component:**
```jsx
function SearchBar() {
  return (
    <form role="search">
      <input
        type="search"
        aria-label="Zoek producten"
        placeholder="Zoeken..."
      />
      <button type="submit">
        <SearchIcon aria-hidden="true" />
        <span className="sr-only">Zoeken</span>
      </button>
    </form>
  );
}
```

**Voordelen:**
- Geen visuele impact
- Goed voor minimalistische designs

**Nadelen:**
- Niet zichtbaar voor cognitieve gebruikers die de tekst moeten kunnen zien
- aria-label wordt niet vertaald door browser translate features
- Minder ontdekbaar voor alle gebruikers

## Oplossing 3: Visually Hidden Label

**Gebruik wanneer**: Je wilt een "schone" UI maar toegankelijkheid behouden

```html
<label for="email" class="sr-only">Email adres</label>
<input
  type="email"
  id="email"
  placeholder="naam@voorbeeld.nl"
/>
```

**CSS voor sr-only:**
```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
```

**Tailwind CSS:**
```jsx
<label htmlFor="email" className="sr-only">
  Email adres
</label>
<input type="email" id="email" />
```

**Voordelen:**
- Toegankelijk voor screenreaders
- Visueel "schoon"
- Betere click area dan aria-label

**Nadelen:**
- Nog steeds niet zichtbaar voor cognitieve gebruikers

## Oplossing 4: Label Wrapping

**Gebruik wanneer**: Custom checkbox/radio designs, of compacte forms

```html
<!-- ✅ Correct: Impliciete associatie door wrapping -->
<label>
  <input type="checkbox" name="terms" />
  Ik ga akkoord met de voorwaarden
</label>

<!-- ✅ Ook correct met styling flexibility -->
<label class="custom-checkbox">
  <input type="checkbox" />
  <span class="checkbox-label">Nieuwsbrief ontvangen</span>
</label>
```

**React met custom checkbox:**
```jsx
function Checkbox({ children, ...props }) {
  return (
    <label className="flex items-center gap-2 cursor-pointer">
      <input type="checkbox" className="sr-only" {...props} />
      <span className="custom-checkbox-visual" aria-hidden="true">
        {/* Custom checkbox SVG */}
      </span>
      <span>{children}</span>
    </label>
  );
}

// Gebruik:
<Checkbox name="newsletter">
  Stuur me de wekelijkse nieuwsbrief
</Checkbox>
```

**Voordelen:**
- Geen for/id nodig
- Grote click area automatisch
- Prima voor checkboxes en radios

**Nadelen:**
- Styling constraints (label moet parent zijn)

## Testing

### 1. Screenreader Test

**VoiceOver (Mac):**
```
Cmd+F5 → Tab door form
✅ Verwacht: "Naam, edit text" of "Email adres, edit text"
❌ Fout: "Edit text" (geen label genoemd)
```

**NVDA (Windows):**
```
NVDA+Ctrl → Tab door form
✅ Verwacht: Leest label + field type + value
❌ Fout: Alleen "edit, blank" zonder label
```

### 2. Keyboard Test

```
1. Tab naar input → moet focussen
2. Shift+Tab terug → moet terugfocussen
3. Click op label → moet input focussen (voor visible labels)
```

### 3. Automated Test

**Jest + Testing Library:**
```jsx
import { render, screen } from '@testing-library/react';

test('form inputs have accessible labels', () => {
  render(<ContactForm />);

  // Deze zal falen als er geen label is:
  const nameInput = screen.getByLabelText('Naam');
  const emailInput = screen.getByLabelText(/email/i);

  expect(nameInput).toBeInTheDocument();
  expect(emailInput).toBeInTheDocument();
});
```

**Axe DevTools:**
```
1. Open DevTools
2. Ga naar Axe tab
3. Scan page
4. Zoek naar "Form elements must have labels"
```

## Veelgemaakte Fouten

### ❌ Fout 1: Alleen Placeholder Gebruiken

```html
<!-- FOUT: Placeholder is geen label -->
<input type="text" placeholder="Je naam" />
```

**Waarom fout:**
- Placeholder verdwijnt bij typen
- Niet alle screenreaders lezen placeholder
- Placeholder is voor voorbeeldwaarde, niet voor label

### ❌ Fout 2: Label Zonder Associatie

```html
<!-- FOUT: Label niet gekoppeld -->
<label>Naam</label>
<input type="text" id="different-id" />
```

**Fix:**
```html
<label for="name">Naam</label>
<input type="text" id="name" />
```

### ❌ Fout 3: Aria-label EN Visible Label

```html
<!-- FOUT: Conflicterende labels -->
<label for="email">Email</label>
<input type="email" id="email" aria-label="Email adres" />
```

**Waarom fout:**
- aria-label overschrijft de visible label
- Screenreader leest "Email adres", maar visueel staat "Email"
- Verwarring tussen screenreader en visuele gebruikers

**Fix:**
```html
<!-- Kies één: Óf visible label -->
<label for="email">Email adres</label>
<input type="email" id="email" />

<!-- Óf aria-label (alleen als geen visible label mogelijk is) -->
<input type="email" aria-label="Email adres" />
```

### ❌ Fout 4: Generieke Labels

```html
<!-- FOUT: Meerdere "Email" labels -->
<label for="email1">Email</label>
<input id="email1" />

<label for="email2">Email</label>
<input id="email2" />
```

**Fix:**
```html
<label for="personal-email">Persoonlijk email adres</label>
<input id="personal-email" />

<label for="work-email">Werk email adres</label>
<input id="work-email" />
```

## Referenties

- [WCAG 3.3.2 Labels or Instructions](https://www.w3.org/WAI/WCAG22/Understanding/labels-or-instructions.html)
- [WCAG 1.3.1 Info and Relationships](https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html) (related - voor label associatie)
- [MDN: \<label\>](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/label)
- [WebAIM: Creating Accessible Forms](https://webaim.org/techniques/forms/)
- [A11Y Project: How to use ARIA labels](https://www.a11yproject.com/posts/how-to-use-aria-label/)
