# WCAG Toegankelijkheidsaudit Skills

Complete Nederlandse workflow voor WCAG 2.2 toegankelijkheidsaudits.

## Skills Overzicht

| Skill | Doel | Gebruik |
|-------|------|---------|
| **wcag-audit** | Voert audits uit, genereert rapporten | `/wcag-audit [URL]` |
| **wcag-fix** | Repareert overtredingen systematisch | `/wcag-fix kritieke problemen` |
| **wcag-toegankelijkheidsverklaring** | Creëert wettelijke verklaringen | `/wcag-toegankelijkheidsverklaring` |
| **wcag-tools** | Tool setup referentie (optioneel) | `/wcag-tools` |

## Developer Journey

```mermaid
graph LR
    A[Feature Development] --> B[/wcag-audit]
    B --> C{Problemen?}
    C -->|Ja| D[/wcag-fix kritieke problemen]
    D --> E[/wcag-fix ernstige problemen]
    E --> F[/wcag-audit opnieuw]
    F --> G[/wcag-toegankelijkheidsverklaring]
    C -->|Nee| G
    G --> H[Klaar!]
```

## Quick Start

### 1. Voer Audit Uit

```bash
/wcag-audit https://jouwwebsite.nl
```

Genereert rapport in `docs/audits/YYYY-MM-DD-audit.md` met:
- 🔴 Kritieke problemen (WCAG niveau A, blokkeert basale toegankelijkheid)
- 🟠 Ernstige problemen (WCAG niveau AA, significant impact)
- 🟡 Matige problemen (Best practices, nice to have)

### 2. Fix Problemen Systematisch

```bash
# Alle kritieke issues
/wcag-fix kritieke problemen

# Specifiek probleem nummer
/wcag-fix probleem 3

# Alle problemen
/wcag-fix alles
```

Voor elk probleem krijg je:
- Wat is het probleem en waarom is het belangrijk
- Voor/na code voorbeelden in Nederlands
- Test criteria om fix te verifiëren

### 3. Update Toegankelijkheidsverklaring

```bash
/wcag-toegankelijkheidsverklaring
```

Genereert of update `public/toegankelijkheidsverklaring.html` conform:
- EU richtlijn 2016/2102
- Tijdelijk besluit digitale toegankelijkheid overheid
- Automatisch gevuld met openstaande problemen uit audit

## Skill Details

### wcag-audit

**Input:** URL of bestandspad
**Output:** Markdown rapport met gecategoriseerde problemen

Voert uit:
- Geautomatiseerde tests (axe-core waar mogelijk)
- Kleurcontrast checks
- HTML validatie
- Handmatige check reminders

**Rapport locatie:** `docs/audits/YYYY-MM-DD-audit.md`

[Zie voorbeeld rapport](./examples/2026-02-01-example-audit.md)

---

### wcag-fix

**Modi:**
1. **Audit integration** (primair): Leest laatst audit rapport, fix systematisch
2. **Standalone**: Direct fix voor specifiek probleem

**Commando's:**
- `/wcag-fix alles` - Alle problemen uit laatste audit
- `/wcag-fix kritieke problemen` - Alleen 🔴 kritieke items
- `/wcag-fix ernstige problemen` - Alleen 🟠 ernstige items
- `/wcag-fix probleem 5` - Specifiek item nummer 5
- `/wcag-fix formulier labels` - Direct probleem (zonder audit)

**Remediation Patterns:**

Beschikbaar in `wcag-fix/patterns/`:
- `formulier-labels.md` - WCAG 3.3.2 form label issues
- `kleurcontrast.md` - WCAG 1.4.3 color contrast
- `toetsenbord-navigatie.md` - WCAG 2.1.1 keyboard accessibility
- `alt-teksten.md` - WCAG 1.1.1 non-text content

Elk pattern bevat:
- Probleem uitleg in Nederlands
- Impact op gebruikers
- Meerdere oplossingsopties met voor/na code
- Test criteria
- Veelgemaakte fouten

---

### wcag-toegankelijkheidsverklaring

**Modi:**
1. **Nieuwe verklaring** - Start from scratch
2. **Update bestaande** - Update met nieuwe audit resultaten
3. **Review** - Check completeness

**Output:** `public/toegankelijkheidsverklaring.html`

Genereert wettelijk compliant document met:
- Organisatie gegevens
- Compliance status (volledig/gedeeltelijk/niet conform)
- Niet-toegankelijke content (uit audit rapport)
  - Gegroepeerd per WCAG principe (Waarneembaar, Bedienbaar, Begrijpelijk, Robuust)
- Feedback contactgegevens
- Klachtenprocedure
- Handhavingsprocedure

---

### wcag-tools

**Optionele referentie** voor tool setup.

**Categorieën:**
- Browser extensies (axe DevTools, WAVE, Lighthouse)
- Screenreaders (NVDA, JAWS, VoiceOver, TalkBack)
- Geautomatiseerde testing (axe-core CLI, pa11y, Playwright)
- Kleurcontrast tools (WebAIM, Stark)

**Let op:** wcag-audit gebruikt axe-core automatisch. Deze skill is voor manual setup en referentie.

## Wettelijke Context

### Nederland

**Tijdelijk besluit digitale toegankelijkheid overheid** vereist:
- WCAG 2.1 niveau AA compliance
- Toegankelijkheidsverklaring op website
- Feedbackmechanisme voor gebruikers
- Regelmatige updates van verklaring

**Wie moet compliant zijn:**
- Alle overheidswebsites
- Websites van publieke instellingen
- Sommige commerciële websites die publieke diensten aanbieden

### EU

**Richtlijn 2016/2102** (European Accessibility Act) wordt geïmplementeerd in alle EU landen.

**Deadlines:**
- Nieuwe websites: 23 september 2019
- Bestaande websites: 23 september 2020
- Mobiele apps: 23 juni 2021

## WCAG 2.2 Levels

| Level | Beschrijving | Compliance |
|-------|--------------|------------|
| **A** | Minimale toegankelijkheid | Wettelijk verplicht, blokkeert basale gebruik |
| **AA** | Standaard compliance | Vereist voor overheid, aanbevolen voor iedereen |
| **AAA** | Enhanced toegankelijkheid | Optioneel, voor gespecialiseerde behoeften |

## Veelvoorkomende WCAG Overtredingen

Van meest naar minst voorkomend:

1. **Ontbrekende form labels** (WCAG 3.3.2, Level A)
2. **Onvoldoende kleurcontrast** (WCAG 1.4.3, Level AA)
3. **Afbeeldingen zonder alt-tekst** (WCAG 1.1.1, Level A)
4. **Geen keyboard navigatie** (WCAG 2.1.1, Level A)
5. **Onjuiste heading hiërarchie** (WCAG 1.3.1, Level A)
6. **Links zonder duidelijke tekst** (WCAG 2.4.4, Level A)
7. **Form errors niet toegankelijk** (WCAG 3.3.1, Level A)
8. **Missing skip links** (WCAG 2.4.1, Level A)

Deze skills helpen al deze problemen systematisch op te lossen.

## Referenties

- [WCAG 2.2 Guidelines](https://www.w3.org/TR/WCAG22/)
- [WebAIM](https://webaim.org/)
- [Tijdelijk besluit digitale toegankelijkheid overheid](https://wetten.overheid.nl/BWBR0040936/)
- [EU Richtlijn 2016/2102](https://eur-lex.europa.eu/legal-content/NL/TXT/?uri=CELEX%3A32016L2102)
