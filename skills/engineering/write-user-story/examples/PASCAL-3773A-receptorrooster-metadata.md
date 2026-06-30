# Receptorrooster-informatie meegeven met depositieresultaten

## User story

Als PAS-berekening wil ik bij het ontvangen van depositieresultaten van IMPACT ook weten welke receptorroosters zijn doorgerekend, zodat ik kan bepalen welke oppervlakte (celgrootte) bij elk receptorpunt hoort.

## Doel of resultaat

PAS-berekening kan deposities correct toekennen aan habitatgebieden. Hiervoor moet het weten welke oppervlakte elke depositiewaarde vertegenwoordigt. Door de roosterinformatie expliciet mee te geven, is dit eenvoudig en betrouwbaar te bepalen.

## Context

Bij een IMPACT-berekening definieert de gebruiker één of meerdere receptorroosters: rechthoekige gebieden met een bepaalde resolutie (afstand tussen receptorpunten). Dichter bij de bron wordt vaak een hogere resolutie gebruikt dan verder weg.

De depositiewaarde in een receptorpunt vertegenwoordigt de depositie over een vierkante cel rondom dat punt. De grootte van die cel hangt af van de resolutie van het rooster:

- Bij 25m resolutie hoort elk punt bij een cel van 25×25m
- Bij 100m resolutie hoort elk punt bij een cel van 100×100m

De huidige JSON-respons van IMPACT bevat enkel de receptorpunten en hun depositiewaarden. De roosterinformatie (welk rechthoekig gebied, welke resolutie) gaat verloren bij de overdracht.

Zonder deze informatie moet PAS-berekening de celgrootte afleiden uit de afstanden tussen punten. Dit is lastig (met name aan de randen van roosters of bij overgang tussen verschillende resoluties) en foutgevoelig.

## Acceptatiecriteria

### [1] IMPACT geeft roosterinformatie mee in de API-respons

De API-respons van IMPACT bevat naast de receptorpunten en deposities ook de receptorroosters. Per rooster wordt meegegeven:

- De geometrie: de rechthoekige omtrek van het rooster (polygon, Lambert 72)
- De resolutie: afstand tussen twee receptorpunten (in meter)

### [2] PAS-berekening leest de roosterinformatie in

PAS-berekening kan de roosterinformatie uit de API-respons inlezen en gebruiken voor verdere verwerking.

### [3] PAS-berekening valideert de roosterinformatie

Bij het inlezen controleert PAS-berekening of de roosterinformatie aanwezig en geldig is.

## Beslissingen

1. Er is gekozen om de receptorroosterinformatie expliciet mee te geven in de API-respons van IMPACT in plaats van deze te achterhalen uit de receptorpunten. Dit is efficienter en robuuster.
