---
name: wcag-audit
description: Voert een diepgaande, rol-gebaseerde WCAG 2.2 audit uit. Orchestreert expert sub-agents (Visual, Interaction, Code) om een applicatie te beoordelen op toegankelijkheid.
---

# WCAG Audit (Role-Based)

Een geavanceerde audit workflow die toegankelijkheid evalueert vanuit drie expert-perspectieven: Visueel Design, Interactie/QA, en Code/Screenreader.

## Workflow

### 1. Context Verzamelen

Verzamel eerst alle benodigde informatie om de audit uit te voeren.

**Actie:** Vraag de gebruiker om de volgende input:

1. **URL of Bestandspad**: Wat gaan we auditen?
2. **Context**: "Is dit een live website, een lokaal component, of een design mockup?"
3. **Key Views**: "Welke specifieke statussen moeten getest worden? (bijv. Homepage, Modal open, Error state, Loading state)"
4. **Technische Stack**: (Optioneel) React, Vue, HTML, etc?

> [!TIP]
> Als de gebruiker een URL geeft, probeer de pagina inhoud (HTML/CSS) op te halen via relevante tools of vraag de gebruiker om de broncode/screenshots te plakken. Zonder code/visuele context kunnen de experts hun werk niet doen.

### 2. Expert Audit (Persona Simulatie)

Neem voor elk van de onderstaande rollen het bijbehorende **persona** aan. Geef hen de verzamelde context en hun specifieke rol-instructies.

#### 2.1 Visual Designer (Esthetiek & Leesbaarheid)

* **Rol:** `references/role-visual-designer.md`
* **Taak:** Analyseer kleurcontrast, font-groottes, witruimte, reflow en layout stabiliteit.
* **Bron:** Screenshots, CSS, berekende stijlen.

#### 2.2 Interaction Tester (Functionaliteit & Flow)

* **Rol:** `references/role-interaction-tester.md`
* **Taak:** Analyseer keyboard navigatie, focus management, formulieren en foutafhandeling.
* **Bron:** HTML (event handlers), JS logica, beschrijving van user flows.

#### 2.3 Screenreader Developer (Code & Semantiek)

* **Rol:** `references/role-screenreader-dev.md`
* **Taak:** Analyseer HTML semantiek, ARIA gebruik, naam/rol/waarde en landmarks.
* **Bron:** Raw HTML, DOM structuur.

### 3. Synthese & Rapportage

Verzamel de output van de drie experts en stel het eindrapport samen in `docs/audits/{YYYY-MM-DD}-{onderwerp}-full-audit.md`.

Gebruik dit format:

```markdown
# WCAG 2.2 Audit Rapport: [Onderwerp]

**Datum:** [Datum]
**Status:** [Concept/Final]
**Compliance Status:** [Critical Fail / Major Issues / Minor Issues / Pass]

---

## 🎨 Visuele Toegankelijkheid
> Review door Visual Designer

**Compliance:** [Pass/Fail/Critical]

**Kritieke Problemen:**
- [ ] [Probleem] (WCAG X.X.X) - [Oplossing]

**Aanbevelingen:**
...

---

## ⌨️ Interactie & Navigatie
> Review door Interaction Tester

**Compliance:** [Pass/Fail/Critical]

**Kritieke Problemen:**
- [ ] [Probleem] (WCAG X.X.X) - [Oplossing]

**Test Scenario's:**
...

---

## 🗣️ Code & Screenreader
> Review door Screenreader Dev

**Compliance:** [Pass/Fail/Critical]

**Kritieke Problemen:**
- [ ] [Probleem] (WCAG X.X.X) - [Oplossing]

**Code Fixes:**
...

---

## ✅ Geconsolideerde Actielijst

[Geprioriteerde lijst van alle kritieke issues van alle experts samengevoegd]
```

### 4. Vervolgstappen (Fixes)

Vraag de gebruiker of ze specifieke problemen direct willen oplossen.
Zo ja, gebruik de `wcag-fix` skill met de context van het zojuist gegenereerde rapport.
