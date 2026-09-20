---
name: wcag-fix
description: Verhelp WCAG toegankelijkheidsproblemen met gevalideerde remediation patterns
---

# WCAG Fix

Deze skill helpt bij het systematisch verhelpen van WCAG toegankelijkheidsproblemen door middel van:
- **Gevalideerde remediation patterns** voor veelvoorkomende problemen
- **Integratie met audit rapporten** (van wcag-audit skill)
- **Code voorbeelden** die direct toepasbaar zijn
- **Testing guidance** om de fix te verifiëren

## Wanneer Deze Skill Te Gebruiken

**Gebruik wcag-fix wanneer je:**
- Een WCAG audit rapport hebt ontvangen en issues wilt fixen
- Specifieke toegankelijkheidsproblemen wilt oplossen
- Best practices wilt toepassen voor formulieren, navigatie, focus management, etc.
- Wilt leren hoe je toegankelijkheidsproblemen correct verhelpt

**Gebruik NIET wcag-fix wanneer:**
- Je alleen wilt scannen op problemen (gebruik wcag-audit)
- Je algemene toegankelijkheidsvragen hebt (stel ze direct)

## Workflow

### Modus 1: Audit Report Integration (Aanbevolen)

Wanneer je een audit rapport hebt van wcag-audit:

1. **Toon het rapport**:
   ```
   /wcag-fix [pad-naar-rapport.json]
   ```

2. **Claude analyseert en toont**:
   - Alle gevonden issues met prioriteit
   - Gegroepeerd per type (bijv. alle form label issues samen)
   - Met count per issue type

3. **Gebruiker kiest focus**:
   ```
   Fix alle form label issues
   ```
   OF specifieke file:
   ```
   Fix issues in src/components/ContactForm.tsx
   ```

4. **Claude past remediation toe**:
   - Selecteert juiste pattern uit `patterns/` directory
   - Past aan op context (React, Vue, vanilla JS, etc.)
   - Implementeert de fix
   - Voegt testing instructies toe

5. **Verifieer en herhaal**:
   - Test de fix
   - Run wcag-audit opnieuw om te verifiëren
   - Ga door naar volgende issue

### Modus 2: Standalone Fix (Zonder Rapport)

Gebruik voor individuele problemen:

```
/wcag-fix "form inputs hebben geen labels"
```

OF met specifieke file:

```
/wcag-fix src/components/SearchBar.tsx "zoek formulier heeft geen labels"
```

Claude zal:
1. Pattern identificeren (bijv. `patterns/formulier-labels.md`)
2. Code analyseren (als path gegeven)
3. Juiste remediation voorstellen
4. Implementeren en testing instructies geven

## Audit Report Integratie

### Verwachte Report Locatie

wcag-fix zoekt audit rapporten in deze volgorde:
1. `docs/audits/.current-audit` (symlink naar meest recente)
2. Nieuwste bestand in `docs/audits/` (op basis van datum in bestandsnaam)
3. Vraagt gebruiker om pad als geen rapport gevonden

### Verwachte Report Format

Audit rapporten moeten deze structuur hebben:

```markdown
## 🔴 Kritieke Problemen (aantal)

### N. [Probleem beschrijving] (WCAG X.X.X)
- **Locatie:** [bestand:regel of URL]
- **Impact:** [beschrijving]
- **WCAG Niveau:** [A/AA/AAA]
```

Pattern detectie gebeurt op basis van:
- Keywords in probleem beschrijving (bijv. "label", "contrast", "toetsenbord")
- WCAG criterium nummer
- Bestandsextensie/technologie in locatie pad

## Remediation Format

Elke remediation volgt dit format:

```markdown
## Fix: [Issue Beschrijving]

**Locatie**: [File:Line of Component]
**WCAG Criterium**: [bijv. 1.3.1 Info and Relationships]
**Prioriteit**: [A/AA/AAA]

### Probleem
[Korte uitleg wat er mis is]

### Oplossing
[Code diff of nieuwe code]

### Testing
- [ ] Toetsenbord navigatie werkt
- [ ] Screenreader test (VoiceOver/NVDA)
- [ ] Visuele verificatie
- [ ] [Specifieke test voor deze fix]

### Referentie
- Pattern: [link naar pattern file]
- WCAG: [link naar criterium]
```

## Smart Features

### 1. Duplicate Detection
Als meerdere files hetzelfde probleem hebben (bijv. 10 forms zonder labels), groupeert Claude deze:

```
Gevonden: 10x "Form input zonder label"

Files:
- ContactForm.tsx (3 inputs)
- SearchBar.tsx (2 inputs)
- LoginForm.tsx (5 inputs)

Wil je:
1. Alles in één keer fixen
2. File per file doorlopen
3. Pattern tonen en zelf implementeren
```

### 2. Progress Tracking
Bij bulk fixes:

```
Fix Progress: Form Labels
├─ ✅ ContactForm.tsx (3/3 fixed)
├─ ⏳ SearchBar.tsx (0/2 fixed)
└─ ⏹️ LoginForm.tsx (not started)
```

## Remediation Patterns

Patterns bevinden zich in `patterns/` directory. Elke pattern bevat:
- **Probleem beschrijving** (in Nederlands)
- **Impact uitleg** (waarom dit toegankelijkheidsprobleem is)
- **Oplossingsopties** (met voor/nadelen)
- **Code voorbeelden** (React, Vue, vanilla JS waar relevant)
- **Testing instructies** (keyboard, screenreader, automated)
- **Veelgemaakte fouten** (wat NIET te doen)
- **Referenties** (WCAG docs, MDN, A11Y Project)

**Beschikbare patterns:**
- `formulier-labels.md` - Form inputs zonder labels
- (meer patterns worden toegevoegd)

## Tips voor Effectief Gebruik

1. **Start met audit rapport**: `wcag-audit` → `wcag-fix` → verify → repeat
2. **Fix per type**: Groepeer soortgelijke issues voor consistentie
3. **Test altijd**: Automated tests vangen niet alles, test handmatig
4. **Leer patterns**: Bekijk pattern files om te begrijpen waarom bepaalde fixes werken
5. **Commit per fix type**: Houd fixes atomic voor betere review

## Voorbeeld Sessie

```
# Stap 1: Run audit
/wcag-audit src/components --output reports/audit-2024-01.json

# Stap 2: Open fix skill met rapport
/wcag-fix reports/audit-2024-01.json

# Claude toont:
# "Gevonden 15 issues:
#  - 8x Form input zonder label (Niveau A - Kritiek)
#  - 5x Link zonder duidelijke tekst (Niveau A)
#  - 2x Kleurcontrast te laag (Niveau AA)"

# Stap 3: Focus op hoogste prioriteit
User: Fix alle form label issues

# Claude implementeert fixes en toont progress

# Stap 4: Verifieer
/wcag-audit src/components --only forms

# Herhaal voor andere issue types
```
