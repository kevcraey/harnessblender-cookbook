# Documentatiearchitectuur en -structuur

Gebruik de onderstaande richtlijnen en mappenstructuur bij het opstellen of bijwerken van documentatie voor een product. We hanteren een vaste hiërarchie.

## Doelgroep

De gebruikers van het product.
Hun domeinkennis varieert van "heeft er al van gehoord" tot "is domeinexpert".
Ze gebruiken de documentatie als naslagwerk en willen vooral weten: hoe iets werkt en waarom iets gedaan is.
Ondubbelzinnigheid is cruciaal; de lezer verkiest duidelijke, eenvoudige voorbeelden om ambiguïteit te vermijden.

Let op: de doelgroep is niet de ontwikkelaar. De ontwikkelaar schrijft de code, maar is niet de gebruiker van de documentatie. Documentatie voor ontwikkelaars hoort uitsluitend in de map `/technical`.

## Mappenstructuur

De documentatie volgt een strikte hiërarchie met topleveldossiers en per-domein documentatie.

```` plaintext
/
├── CONTEXT.md              # Centrale begrippenlijst (glossary)
├── docs/
│   ├── adr/                # Architecture Decision Records
│   │   ├── 0001-...md
│   │   └── 0002-...md
│   ├── faq.md              # Algemene vragen
│   │
│   ├── /technical          # Technische documentatie
│   │   ├── index.md
│   │   ├── /api
│   │   └── ...
│   │
│   ├── /persona            # Personadocumentatie
│   │   ├── persona-a.md
│   │   └── persona-b.md
│   │
│   ├── /domein-1           # Domeinmap
│   │   ├── index.md        # Domeinlanding
│   │   ├── feature1.md
│   │   └── ...
│   └── /domein-2
│       └── ...
````

Lazy aanmaken: `CONTEXT.md` of `docs/adr/` pas aanmaken wanneer eerste term resp. eerste beslissing erin moet.

## De begrippenlijst (CONTEXT.md)

De begrippenlijst staat in [[CONTEXT.md]] aan de repo-root. Het is het belangrijkste document en fungeert als ubiquitous language: één canonieke term per concept.

Elke entry bestaat uit een term (`###`-kop) met daaronder de definitie. Volg het format uit `grill-with-docs/CONTEXT-FORMAT.md`.

`CONTEXT.md` is **uitsluitend** een glossary — geen spec, geen scratchpad, geen implementatiebeslissingen. Implementatiekeuzes horen in een ADR (`docs/adr/`), technische details in `/technical`.

Als een term toch een (IT-)technisch onderdeel vereist voor begrip, voeg dat toe in een eigen `####`-subsectie — beknopt en alleen wanneer noodzakelijk voor de definitie.

Dien bij het toevoegen of wijzigen van een item altijd eerst een voorstel in; er worden geen wijzigingen aangebracht zonder goedkeuring.

Groepeer items functioneel per domein met `##`-koppen. Als er geen passende groep bestaat, stel een nieuwe voor of plaats onder `## Algemeen`. Domeinen blijven in sync met de domeinmappen onder `docs/`.

## De FAQ

De FAQ [[docs/faq.md]] is eveneens cruciaal. Elke entry bevat een vraag (`###`-kop) met daaronder het antwoord.

Als de beschrijving een (IT-)technisch onderdeel bevat, voeg dat dan toe in een eigen `####`-subsectie.

Bij het toevoegen of wijzigen van een entry: dien altijd eerst een voorstel in; er worden geen wijzigingen aangebracht zonder goedkeuring.

Groepeer vragen functioneel per domein met `##`-koppen. Als er geen passende groep bestaat, stel dan voor om een nieuwe toe te voegen of plaats het onder `## Algemeen`. Domeinen blijven in sync met de domeinmappen.

De vraag: schrijf vanuit het perspectief van de eindgebruiker ("Ik kan niet...", "Hoe doe ik...", "Waar vind ik...?").

Het antwoord:

- Houd het kort.
- Verwijs rechtstreeks naar de domeinen en featurepagina's waar de stap-voor-stap uitleg staat.

Doel: de FAQ is een wegwijzer, geen handleiding.

## Definities van de niveaus

### Toplevel: root

Fungeert als toegangspoort tot de documentatie. Verwijst naar de domeinen en:

- de centrale FAQ in [[docs/faq.md]]
- de centrale begrippenlijst in [[CONTEXT.md]] (repo-root)
- de ADRs in [[docs/adr/]]

### Niveau 1: domein (map)

Groepeert de belangrijkste functionele gebieden van de applicatie (bijvoorbeeld beheer, impactscore, depositieruimte).

De `index.md` geeft een samenvatting van het domein en fungeert als ingang naar de domeindocumentatie.

### Niveau 2: feature (bestand)

De gedetailleerde specificatie van één functionele eenheid, actie of flow.

### Twijfelgeval (komt in twee subdomeinen voor)?

Kies het (sub)domein waar de term of functionaliteit zijn "owner" heeft (waar de data vandaan komt) en plaats het daar in [[CONTEXT.md]] onder de juiste `##`-groep. Bij grote twijfel: vraag het.

## ADRs (Architecture Decision Records)

ADRs staan in `docs/adr/` (genummerd: `0001-...md`, `0002-...md`, ...). Volg het format uit `grill-with-docs/ADR-FORMAT.md`.

Schrijf een ADR alleen wanneer **alle drie** waar zijn:

1. **Moeilijk omkeerbaar** — terugdraaien kost reële inspanning.
2. **Verrassend zonder context** — toekomstige lezer vraagt zich af "waarom hebben ze dit zo gedaan?".
3. **Resultaat van een echte trade-off** — er waren reële alternatieven en er is bewust gekozen.

Ontbreekt één van de drie: geen ADR.

## Belangrijke principes

- Schrijf documentatie altijd in het Nederlands.
- Vermijd technische terminologie (coding, IT, ...) tenzij noodzakelijk.
- Voeg altijd sterk vereenvoudigde voorbeelden toe om de functionaliteit uit te leggen.
- Besteed extra aandacht aan randgevallen.
- Houd je strikt aan de markdownrichtlijnen.
