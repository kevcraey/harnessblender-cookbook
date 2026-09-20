# Wegen semantisch configureren in PAS-berekening

## User story

Als gebruiker van PAS-berekening wil ik wegen kunnen beschrijven in termen van verkeer (voertuigen, snelheid, wegtype), zodat het systeem de emissies voor mij berekent en ik niet zelf hoef te rekenen.

## Doel of resultaat

Deze story maakt het mogelijk om wegen te beschrijven in termen die gebruikers kennen: hoeveel voertuigen van welk type rijden aan welke snelheid over welk type weg. Dit verhoogt de begrijpelijkheid en controleerbaarheid van de berekening.

De waarde ligt in:

- **Herkenbaarheid**: Gebruikers denken in "auto's en snelheden", niet in "gram NOx per seconde"
- **Consistentie**: Werkt hetzelfde als in IMPACT, wat gebruikers al kennen
- **Toekomstbestendigheid**: Bij gewijzigde emissiefactoren kan herberekend worden zonder nieuwe invoer
- **Transparantie**: Beoordelaars kunnen makkelijker controleren of de invoer realistisch is

## Context

In de huidige situatie moeten gebruikers de emissies van een weg rechtstreeks invoeren. Dit vereist voorkennis en berekeningen die de gebruiker zelf moet uitvoeren. Voor stallen en stookinstallaties werkt dit anders: daar vult de gebruiker semantische gegevens in en berekent het systeem de emissies.

Door deze story krijgt PAS-berekening dezelfde mogelijkheid voor wegen, met fastrace als rekentool.

## Acceptatiecriteria

### [1] Weg configureren

Gegeven dat ik een weg wil toevoegen als bron
Wanneer ik de wegconfiguratie invul
Dan kan ik kiezen tussen:

- Handmatige invoer van emissies (huidige werking)
- Berekening op basis van verkeersgegevens (nieuw)

### [2] Verkeersgegevens invoeren

Gegeven dat ik kies voor berekening op basis van verkeersgegevens
Wanneer ik de wegconfiguratie invul
Dan kan ik de volgende gegevens invoeren:

- Aantal licht verkeer per uur
- Aantal zwaar verkeer per uur
- Wegtype (snelweg, landelijk, stedelijk)
- Gemiddelde snelheid (km/u)

### [3] Emissies berekenen

Gegeven dat ik geldige verkeersgegevens heb ingevuld
Wanneer ik de berekening start
Dan worden de gegevens naar fastrace gestuurd via de JSON API
En worden de berekende emissies gebruikt in de PAS-berekening
En wordt de versie van de gebruikte emissiefactoren opgeslagen

### [4] Databronversie tonen

Gegeven een rapport van een berekening waarin een weg met verkeersgegevens is gebruikt
Wanneer ik de databronversies bekijk
Dan zie ik ook de databronversie van de gebruikte fastrace emissiefactoren (type `EMISSIEFACTOREN_FASTRACE`)

### [5] Validatie

Gegeven dat ik verkeersgegevens invul
Wanneer ik ongeldige waarden invoer
Dan krijg ik een duidelijke foutmelding
En worden de volgende validaties uitgevoerd:

- Aantal voertuigen >= 0
- Snelheid > 0
- Wegtype is geselecteerd

### [6] Foutafhandeling

Gegeven dat fastrace niet bereikbaar is
Wanneer ik een berekening probeer te starten
Dan krijg ik een duidelijke foutmelding
En kan ik de berekening later opnieuw proberen

### [7] Bestaande wegen

Bestaande wegen waarbij de emissies handmatig zijn ingevoerd zijn gemigreerd naar vrije invoer lijnbron

### [8] Rechtstreekse invoer blijft mogelijk

Gegeven dat ik een weg wil configureren
Wanneer ik de emissies direct weet
Dan moet ik kiezen voor een vrije invoer lijnbron

## Beslissingen

1. **Emissies ad-hoc berekend**: Emissies worden altijd opnieuw berekend op basis van de opgeslagen verkeersgegevens en de vaste fastrace-versie. Ze worden niet opgeslagen in PAS-berekening.
2. **Hoogte en breedte**: Blijven voorlopig op kaartniveau want onderdeel van de geometrie, niet per weg(segment) configureerbaar in deze story.
3. **Snelheid**: We gebruiken dezelfde definitie als IMPACT (gemiddeld aantal voertuigen per dag gedurende de spits).
4. **Migratie**: Bestaande wegen met handmatige emissies worden gemigreerd naar vrije invoer lijnbron.
