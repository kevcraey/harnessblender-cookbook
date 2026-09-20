<!--
Algemene richtlijnen:
- Alles geschreven in heldere, beknopte taal.
- Vermijd onnodige herhaling in de story
- Vermijd technische terminologie
- Beschrijf WAT, niet HOE. Geen implementatieprescriptie (architectuur, datamodellen, libraries, endpoint-/klassenamen) in AC's of Context.
-->

# {titel}

<!--
Korte, duidelijke titel die het functionele doel samenvat.
Maximum 10 woorden.
Moet vlot leesbaar zijn op een Jira board en tegelijk beschrijvend genoeg zijn.
-->

## User story

Als {user} wil ik {goal_short}, zodat {benefit}.

<!--
Schrijf de kern van de user story in één zin volgens de standaardvorm:
Als rol of type gebruiker wil ik beschrijving van de behoefte of gewenste functionaliteit

Deze zin verduidelijkt wie de gebruiker is en wat hij nodig heeft. Het dient als startpunt voor de rest van het document.
-->

## Doel of resultaat

{goal_long}.

De waarde ligt in:

- **{value1}**: {omschrijving_value1}
- **{value2}**: {omschrijving_value2}
- **{value3}**: {omschrijving_value3}
- ...

<!--
Beschrijf kort wat de story wil bereiken.
Dit is een uitgebreide versie van het "zodat"-gedeelte van een user story en legt de waarde of het resultaat uit dat geleverd zal worden.
Het moet focussen op:
- Welk probleem lost deze story op?
- Wat is de waarde die de story zal leveren?
- Wat is de uitkomst die de story zal leveren?
-->

## Context

{context}

<!--
Ga ervan uit dat de lezer (ontwikkelaars, analisten, product owner en andere stakeholders) basiskennis van het domein heeft. Ze begrijpen de concepten maar niet het volledige plaatje.

Na het lezen van de context moet de lezer:
- begrijpen wat de aanleiding was voor de story (een bug, wettelijke vereisten, processen, feedback uit vorige iteraties)
- de toegevoegde waarde van deze story zien
- de bredere context kennen waarin het ticket bestaat

Een goed geschreven context helpt alle lezers om dezelfde aannames te delen en dient als opfrisser van hun bestaande domeinkennis.
De context moet een compleet beeld geven zodat de story op zichzelf staat. Richtlijnen: 10–20 regels; als er echt veel context is, mag je uitbreiden tot maximaal 30 regels.
-->

## Acceptatiecriteria

### [AC1] {acceptatiecriteria_1}

``` gherkin
Gegeven {voorwaarden}
Wanneer {actie}
Dan {resultaat}
```

<!--
Hier wordt de functionele specificatie geformaliseerd. Lijst de concrete en verifieerbare criteria op waaraan de oplevering moet voldoen.

- Gebruik Gherkin (https://cucumber.io/docs/gherkin/reference) waar mogelijk
- Houd de acceptatiecriteria beknopt. Een criterium mag gemiddeld niet langer zijn dan 5-10 regels.
- Hoe korter, hoe beter
- Gebruik een hiërarchie van criteria als er meer dan 5 zijn, door criteria met een gemeenschappelijk kenmerk te groeperen.
- Houd bij gebruik van een hiërarchie een evenwichtige boomstructuur aan (do: 3x5 criteria, don't: 10+4+1 criteria).
- Criteria worden genummerd met [AC1], [AC2], ...
-->

## Openstaande vragen (optioneel)

<!--
Noteer vragen of punten die nog verduidelijking behoeven voordat de implementatie kan worden voltooid. Geef aan welke vragen niet-blokkerend zijn en welke BLOKKEREND (🚫) zijn.
Dit zorgt ervoor dat onzekerheden zichtbaar blijven en opgevolgd kunnen worden.
-->

## Beslissingen

{beslissingen}

<!--
Noteer de belangrijkste beslissingen die zijn genomen voor deze story. Belangrijke beslissingen zijn beslissingen die bepalend zijn geweest voor de hoe en de waarom.
-->
