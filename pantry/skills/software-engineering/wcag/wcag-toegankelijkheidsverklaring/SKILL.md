---
name: wcag-toegankelijkheidsverklaring
description: Creëert of update wettelijk verplichte toegankelijkheidsverklaringen conform EU richtlijn 2016/2102
---

# WCAG Toegankelijkheidsverklaring

Genereert of update wettelijk verplichte toegankelijkheidsverklaringen conform:
- EU richtlijn 2016/2102 (European Accessibility Act)
- Tijdelijk besluit digitale toegankelijkheid overheid
- WCAG 2.1/2.2 niveau AA standaard

## Wanneer Deze Skill Te Gebruiken

**Gebruik wcag-toegankelijkheidsverklaring wanneer:**
- Je een nieuwe toegankelijkheidsverklaring moet maken
- Je een bestaande verklaring wilt updaten met nieuwe audit resultaten
- Je wilt verifiëren of je verklaring compleet en actueel is
- Na het uitvoeren van wcag-audit en wcag-fix

**Gebruik NIET wanneer:**
- Je alleen een audit wilt uitvoeren (gebruik wcag-audit)
- Je toegankelijkheidsproblemen wilt fixen (gebruik wcag-fix)

## Wettelijke Context

### Nederland

**Tijdelijk besluit digitale toegankelijkheid overheid** vereist:
- WCAG 2.1 niveau AA compliance (WCAG 2.2 aanbevolen)
- Toegankelijkheidsverklaring op elke website
- Feedbackmechanisme voor gebruikers
- Regelmatige updates van de verklaring

**Wie moet compliant zijn:**
- Alle overheidswebsites en -apps
- Websites van publieke instellingen
- Sommige commerciële websites die publieke diensten aanbieden

### EU

**Richtlijn 2016/2102** verplicht toegankelijkheidsverklaringen voor:
- Publieke websites (vanaf 23 september 2020)
- Mobiele apps (vanaf 23 juni 2021)

## Workflow

### Modus 1: Nieuwe Verklaring

Wanneer er nog geen toegankelijkheidsverklaring bestaat:

1. **Verzamel informatie**

Claude vraagt naar:
- **Organisatie naam**
- **Website URL**
- **Contactgegevens** (email, telefoon optioneel)
- **Datum publicatie website**
- **Laatst getest op** (datum)

2. **Detecteer audit rapport**

Zoekt automatisch naar audit rapport in:
- `docs/audits/.current-audit` (symlink)
- Nieuwste bestand in `docs/audits/`
- Vraagt om pad als niet gevonden

3. **Bepaal compliance status**

Op basis van audit rapport:
- **Volledig conform**: 0 kritieke en ernstige problemen
- **Gedeeltelijk conform**: Wel problemen, maar gedocumenteerd
- **Niet conform**: Ernstige problemen en geen actieplan

4. **Genereer verklaring**

Maakt `public/toegankelijkheidsverklaring.html` met:
- Organisatie informatie
- Compliance status
- Niet-toegankelijke content (uit audit)
- Feedback mechanisme
- Klachtenprocedure
- Handhavingsprocedure
- Publicatiedatum

5. **Voeg toe aan website**

Geeft instructies om link toe te voegen aan footer:
```html
<a href="/toegankelijkheidsverklaring.html">Toegankelijkheid</a>
```

### Modus 2: Update Bestaande Verklaring

Wanneer `public/toegankelijkheidsverklaring.html` bestaat:

1. **Lees huidige verklaring**
2. **Detecteer nieuwste audit rapport**
3. **Vergelijk met vorige status**
4. **Update secties**:
   - Compliance status (als veranderd)
   - Niet-toegankelijke content
   - Laatst herzien datum
5. **Behoud organisatie info** (niet overschrijven)

### Modus 3: Review Verklaring

Controleert bestaande verklaring op:
- ✅ Alle verplichte elementen aanwezig
- ✅ Recente test datum (< 1 jaar oud)
- ✅ Compliance status klopt met audit
- ✅ Contactgegevens up-to-date
- ⚠️ Waarschuwingen voor ontbrekende elementen

## Verklaring Template

De gegenereerde verklaring bevat:

### 1. Inleiding
```
[Organisatie] streeft ernaar haar website toegankelijk te maken,
conform het Tijdelijk besluit digitale toegankelijkheid overheid en
EU richtlijn 2016/2102.
```

### 2. Compliance Status

**Volledig conform**:
```
Deze website is volledig conform met WCAG 2.1 niveau AA / WCAG 2.2 niveau AA.
```

**Gedeeltelijk conform**:
```
Deze website is gedeeltelijk conform met WCAG 2.1 niveau AA / WCAG 2.2 niveau AA
vanwege de hieronder vermelde uitzonderingen.
```

**Niet conform**:
```
Deze website is niet conform met WCAG 2.1 niveau AA / WCAG 2.2 niveau AA
vanwege de hieronder vermelde problemen.
```

### 3. Niet-toegankelijke Content

Gegroepeerd per WCAG principe:

**🔍 Waarneembaar** (Perceivable)
- WCAG 1.1.1 - Niet-tekstuele content
- WCAG 1.4.3 - Kleurcontrast

**⌨️ Bedienbaar** (Operable)
- WCAG 2.1.1 - Toetsenbordtoegankelijkheid
- WCAG 2.4.4 - Linkdoel in context

**💡 Begrijpelijk** (Understandable)
- WCAG 3.3.2 - Labels en instructies

**🏗️ Robuust** (Robust)
- WCAG 4.1.2 - Naam, rol, waarde

Voor elk probleem:
```markdown
- **[Probleem beschrijving]** (WCAG X.X.X)
  - Locatie: [waar het voorkomt]
  - Status: Gepland / In behandeling / Uitzondering
  - Verwachte oplossing: [datum of "Onbepaald"]
```

### 4. Feedback Mechanisme

```
Heeft u een toegankelijkheidsprobleem gevonden?
Neem contact met ons op:

Email: [contact@organisatie.nl]
Telefoon: [optioneel]

Wij streven ernaar binnen [X werkdagen] te reageren.
```

### 5. Klachtenprocedure

```
Bent u niet tevreden met onze reactie? Dan kunt u een klacht indienen bij:

[Organisatie interne klachtenprocedure]
```

### 6. Handhavingsprocedure

```
Als laatste optie kunt u een klacht indienen bij:

Stichting Internet Toegankelijk
https://www.internettoegankelijk.nl/contact
```

### 7. Technische Informatie

```
Deze verklaring is opgesteld op: [datum]
Laatst herzien op: [datum]
Laatst getest op: [datum]
Testmethode: [Geautomatiseerd + handmatig / WCAG-EM]
```

## WCAG Principe Mapping

Gebruik deze mapping om audit problemen te categoriseren:

| WCAG Criterium | Principe | Niveau | Veelvoorkomend |
|----------------|----------|--------|----------------|
| 1.1.1 | 🔍 Waarneembaar | A | Alt-teksten |
| 1.3.1 | 🔍 Waarneembaar | A | Heading structuur |
| 1.4.3 | 🔍 Waarneembaar | AA | Kleurcontrast |
| 2.1.1 | ⌨️ Bedienbaar | A | Toetsenbord navigatie |
| 2.4.1 | ⌨️ Bedienbaar | A | Skip links |
| 2.4.4 | ⌨️ Bedienbaar | A | Link tekst |
| 3.3.1 | 💡 Begrijpelijk | A | Error identificatie |
| 3.3.2 | 💡 Begrijpelijk | A | Form labels |
| 4.1.2 | 🏗️ Robuust | A | ARIA attributes |

## Audit Rapport Integratie

### Verwachte Rapport Locatie

1. `docs/audits/.current-audit` (symlink naar meest recente)
2. Nieuwste bestand in `docs/audits/` (op basis van datum)
3. Vraagt gebruiker om pad als geen rapport gevonden

### Rapport Parsing

Van audit rapport naar verklaring:

```markdown
# Audit rapport:
## 🔴 Kritieke Problemen
### 1. Afbeeldingen zonder alt-tekst (WCAG 1.1.1)
- Locatie: src/pages/Home.tsx:45

# Wordt in verklaring:
## Niet-toegankelijke Content
### 🔍 Waarneembaar
- **Afbeeldingen zonder alternatieve tekst** (WCAG 1.1.1)
  - Locatie: Homepage, productpagina's
  - Status: In behandeling
  - Verwachte oplossing: [huidige datum + 2 weken]
```

**Automatische categorisatie:**
- 🔴 Kritieke problemen → Status: "In behandeling", deadline: +2 weken
- 🟠 Ernstige problemen → Status: "Gepland", deadline: +1 maand
- 🟡 Matige problemen → Optioneel vermelden

## Output Locatie

Genereert bestand in:
```
public/toegankelijkheidsverklaring.html
```

## Tips voor Effectief Gebruik

1. **Update regelmatig**: Na elke audit of grote wijziging
2. **Wees specifiek**: Vermeld exacte locaties van problemen
3. **Geef realistische deadlines**: Plan 2-4 weken voor kritieke issues
4. **Test de verklaring**: Moet zelf toegankelijk zijn (WCAG compliant)
5. **Link prominent**: Zet link in footer van elke pagina

## Voorbeeld Workflow

```bash
# Stap 1: Run audit
/wcag-audit https://example.nl

# Stap 2: Fix kritieke problemen
/wcag-fix kritieke problemen

# Stap 3: Update toegankelijkheidsverklaring
/wcag-toegankelijkheidsverklaring

# Claude vraagt:
# - Organisatie: "Gemeente Amsterdam"
# - URL: "https://amsterdam.nl"
# - Contact: "toegankelijkheid@amsterdam.nl"

# Claude genereert public/toegankelijkheidsverklaring.html
```

## Veelgestelde Vragen

**Q: Moet ik alle problemen vermelden?**
A: Vermeld minimaal alle niveau A en AA problemen. Niveau AAA is optioneel.

**Q: Wat als er veel problemen zijn?**
A: Groepeer soortgelijke problemen en geef een schatting van aantallen.

**Q: Hoe vaak updaten?**
A: Minimaal 1x per jaar. Bij grote wijzigingen of na nieuwe audits direct updaten.

**Q: Moet de verklaring in HTML?**
A: HTML wordt aanbevolen voor beste toegankelijkheid. PDF is toegestaan maar minder toegankelijk.

**Q: Kan ik problemen als "uitzondering" markeren?**
A: Alleen in zeer specifieke gevallen (bijv. archiefmateriaal). Nieuwe content moet conform zijn.

## Referenties

- [Tijdelijk besluit digitale toegankelijkheid overheid](https://wetten.overheid.nl/BWBR0040936/)
- [EU Richtlijn 2016/2102](https://eur-lex.europa.eu/legal-content/NL/TXT/?uri=CELEX%3A32016L2102)
- [Model toegankelijkheidsverklaring](https://www.digitoegankelijk.nl/aan-de-slag/toegankelijkheidsverklaring)
- [WCAG 2.2 Guidelines](https://www.w3.org/TR/WCAG22/)
