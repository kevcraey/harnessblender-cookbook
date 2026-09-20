# Toegankelijkheidsaudit Resultaat

**Getest op:** 2026-01-28
**WCAG Niveau:** AA
**Getest door:** axe-core CLI + handmatige controle

---

## 🔴 Kritieke Problemen (3)

[Problemen die essentiële toegankelijkheid blokkeren - WCAG niveau A]

### 1. Formuliervelden zonder labels (WCAG 3.3.2)
- **Locatie:** src/components/ContactForm.tsx:45-52
- **Impact:** Screenreader gebruikers kunnen niet bepalen wat er in elk veld ingevuld moet worden. Dit blokkeert het gebruik van essentiële functionaliteit.
- **WCAG Niveau:** A

### 2. Afbeeldingen zonder alt-tekst (WCAG 1.1.1)
- **Locatie:** src/pages/products/index.tsx:128, 156, 203
- **Impact:** Blinde gebruikers krijgen geen informatie over productafbeeldingen, wat essentieel is voor het maken van een aankoopbeslissing.
- **WCAG Niveau:** A

### 3. Toetsenbord trap in modal dialoog (WCAG 2.1.2)
- **Locatie:** src/components/Modal.tsx:67-89
- **Impact:** Toetsenbordgebruikers kunnen de modal niet sluiten zonder muis, wat hen volledig blokkeert in de workflow.
- **WCAG Niveau:** A

---

## 🟠 Ernstige Problemen (5)

[Problemen die toegankelijkheid significant beperken - meestal WCAG niveau AA]

### 4. Onvoldoende kleurcontrast in knoppen (WCAG 1.4.3)
- **Locatie:** src/styles/buttons.css:23-27
- **Impact:** Gebruikers met slechtziendheid of kleurenblindheid kunnen knoppen niet goed onderscheiden van de achtergrond (contrast ratio 3.2:1, vereist 4.5:1).
- **WCAG Niveau:** AA

### 5. Geen skip link naar hoofdinhoud (WCAG 2.4.1)
- **Locatie:** src/components/Layout.tsx:12-89
- **Impact:** Toetsenbordgebruikers moeten door 30+ navigatie-items tabben voordat ze bij de hoofdinhoud komen op elke pagina.
- **WCAG Niveau:** A

### 6. Focus indicator niet zichtbaar (WCAG 2.4.7)
- **Locatie:** src/styles/global.css:8 (outline: none op *:focus)
- **Impact:** Toetsenbordgebruikers kunnen niet zien waar ze zich in de interface bevinden tijdens navigatie.
- **WCAG Niveau:** AA

### 7. Heading structuur overgeslagen (WCAG 1.3.1)
- **Locatie:** src/pages/about.tsx:45 (h1 naar h3 zonder h2)
- **Impact:** Screenreader gebruikers die door headings navigeren missen context en krijgen een verkeerde documentstructuur voorgelezen.
- **WCAG Niveau:** A

### 8. Foutmeldingen niet gelinkt aan velden (WCAG 3.3.1)
- **Locatie:** src/components/LoginForm.tsx:78-92
- **Impact:** Screenreader gebruikers horen niet welke velden fouten bevatten en kunnen deze niet efficiënt corrigeren.
- **WCAG Niveau:** A

---

## 🟡 Matige Problemen (4)

[Problemen die toegankelijkheid beperken maar niet blokkeren]

### 9. Link tekst niet beschrijvend (WCAG 2.4.4)
- **Locatie:** src/pages/blog/index.tsx:156, 178, 203 ("Lees meer" links)
- **Impact:** Screenreader gebruikers die door links navigeren krijgen alleen "Lees meer" te horen zonder context over waar de link naartoe gaat.
- **WCAG Niveau:** A

### 10. Taal van pagina niet opgegeven (WCAG 3.1.1)
- **Locatie:** public/index.html:2 (lang attribuut ontbreekt op html element)
- **Impact:** Screenreaders kunnen de verkeerde uitspraakregels gebruiken, wat begrijpbaarheid vermindert.
- **WCAG Niveau:** A

### 11. Geen page title in SPA navigatie (WCAG 2.4.2)
- **Locatie:** src/App.tsx:34-67 (route wijzigingen updaten document.title niet)
- **Impact:** Gebruikers weten niet op welke pagina ze zijn wanneer ze navigeren, vooral verwarrend bij gebruik van browser history.
- **WCAG Niveau:** A

### 12. Te kleine klikgebieden op mobiel (WCAG 2.5.5)
- **Locatie:** src/components/MobileNav.tsx:45-89
- **Impact:** Gebruikers met motorische beperkingen of dikke vingers kunnen klein knoppen in mobiele navigatie missen (24x24px, vereist 44x44px).
- **WCAG Niveau:** AAA

---

## ✅ Handmatige Controles Nog Te Doen

Deze items kunnen niet geautomatiseerd worden getest:

- [ ] Video's hebben accurate ondertiteling (4 video's geïdentificeerd in /src/pages/tutorials/)
- [ ] Alt-teksten zijn betekenisvol en beschrijvend (niet alleen aanwezig)
- [ ] Formulieren zijn logisch ingedeeld en groepen gerelateerde velden
- [ ] Toetsenbordnavigatie is intuïtief en volgt logische volgorde
- [ ] Screenreader ervaring is begrijpelijk (test met NVDA/JAWS/VoiceOver)
- [ ] Animaties respecteren prefers-reduced-motion
- [ ] Error recovery processen zijn duidelijk en toegankelijk

---

## Samenvatting

- **Kritieke problemen:** 3 (moeten opgelost)
- **Ernstige problemen:** 5 (zouden opgelost moeten worden)
- **Matige problemen:** 4 (nice to have)
- **Compliance status:** Niet conform
  - **Volledig conform**: Geen overtredingen op gekozen WCAG niveau
  - **Gedeeltelijk conform**: Enkele overtredingen, maar hoofdfunctionaliteit toegankelijk
  - **Niet conform**: Kritieke overtredingen blokkeren basale toegankelijkheid

## Volgende Stappen

1. Los kritieke problemen op met `/wcag-fix kritieke problemen`
2. Los ernstige problemen op met `/wcag-fix ernstige problemen`
3. Voer opnieuw audit uit om fixes te verifiëren
4. Update toegankelijkheidsverklaring met `/wcag-toegankelijkheidsverklaring`
