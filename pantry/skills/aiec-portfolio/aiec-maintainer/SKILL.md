---
name: aiec-maintainer
description: >-
  Breid AIEC-portfolio uit met een regel, rapport, processtap of technische handeling.
  Maak een gecontroleerd wijzigingsvoorstel, test het en activeer uitsluitend na akkoord.
argument-hint: '[gewenste regel, rapportsoort of capability]'
---
# AIEC — uitbreiden

Lees `../aiec-core/SKILL.md`. Onderhoud gebeurt in de **bron**:
`/Users/kenzo/Library/CloudStorage/Dropbox/1-Kenzo/4-Coding/ai-tooling-repos/cookbook/pantry/skills/aiec-portfolio`.
Wijzig nooit de geïnstalleerde plugincache of `recipes/aiec-portfolio/blend` met de hand.

## Regel of rapport zonder nieuwe code

1. Vraag alleen wat nodig is: wat moet worden gecontroleerd of gemaakt, voor welk object, welke bronnen,
   wanneer, wat ontbrekend mag zijn en wie de inhoud levert. Een rapport toevoegen maakt het niet
   automatisch verplicht. Een nieuwe deadline of verplichting is een inhoudelijke beslissing.
2. Lees `A catalog`. Gebruik bestaande bronnen en operatoren. Maak een concept met:
   `A scaffold report retrospectieve-team --out concept.yaml` (of `rule` / `capability`).
3. Werk het concept in de tijdelijke werkmap uit. `input` is menselijke tekst, `choice` een keuze uit een
   rapportlokale enum, `input_table` een menselijke tabel met getypeerde kolommen. Dezelfde enum kan in
   een sectie en tabelkolom worden hergebruikt, zoals de gezondheidsvlaggen van het maandrapport.
   `table` en `count` komen uit brondatasets; houd ze gescheiden van menselijke invoer. YAML is data,
   geen Python en geen shell.
4. Gebruik de CLI uit de bron: `A extend propose report --file concept.yaml --out voorstel.json`.
   Die valideert de definitie samen met de hele catalogus in een tijdelijke kopie. Doe daarnaast een
   gerichte fixtureproef: bijvoorbeeld een dossier met en zonder het vereiste artefact.
5. Toon de wijziging, het verwachte gedrag, de proef en eventuele beperkingen. **Vraag akkoord en stop.**
6. Na expliciet akkoord:
   `A extend approve --plan voorstel.json --by Kenzo --evidence "akkoord in gesprek" --ack <hash> --out akkoord.json`
   en `A extend apply --plan voorstel.json --approval akkoord.json`.
7. Genereer de leesbare catalogus, bouw de plugin opnieuw en controleer documentatie en voorbeelden.
   Een definitie in de bron is pas in de geïnstalleerde plugin beschikbaar na rebuild/update.

## Wanneer wel code nodig is

Een nieuwe databron, type schrijfactie of rekenbewerking is geen nieuwe YAML-regel maar een codewijziging.
Maak die in een tijdelijke kopie of branch. Toon code-diff, tests, effect op goedkeuring en de documentatie.
Vraag akkoord vóór je de actieve bron vervangt. Maak een back-up vóór vervangen of verwijderen.

Voeg alleen een expliciete handler toe, geen eval, dynamische Python-import uit definities, generieke
REST-write of willekeurige shellactie. Nieuwe schrijfacties moeten dezelfde voorstel-, revisie-,
goedkeurings-, back-up- en journaalcontroles doorlopen. Bewijs met tests dat ongeautoriseerde writes,
gewijzigde bronnen, verlopen voorstellen en herhalingen worden geweigerd.

## Proceswijzigingen

Naslag en Kenzo’s bevestigde correcties zijn de recentste basis. Oudere teksten zijn geen reden om een
regel stilzwijgend terug te draaien. Bespreek tegenstrijdigheden. Een onvolledige gate blijft onvolledig
tot de bevoegde persoon haar vastlegt. Pas proces, controles, sjablonen en uitleg samen aan.

## Publiceren en documenteren

De cookbook-recipe `recipes/aiec-portfolio/recipe.yaml` maakt de Claude Code-plugin. Gebruik de lokale
harnessblender, met een back-up van de bestaande blend. Zie de bron-README voor het precieze commando.
De praktische ingang is de vault-note `aiec-portfolio`; de technische uitleg staat in
`aiec-portfolio-techniek`. De HTML-rondleiding beschrijft dezelfde werking. Vermeld wat echt is getest;
een geslaagde fixturetest is geen geslaagde live-integratie.
