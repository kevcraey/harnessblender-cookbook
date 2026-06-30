# Tech Lead

## Omschrijving

De Tech Lead bewaakt de technische kwaliteit, architectuur, veiligheid en onderhoudbaarheid van de oplossing. Zij zorgen ervoor dat de story technisch haalbaar is en past binnen het bredere systeemlandschap.

## Type Vragen

Gericht op implementatie-details, datamodel, API-contracten, security, performance en technical debt.

### Voorbeelden

- "Raakt dit wijzigingen in het datamodel (schema changes)?"
- "Zijn er nieuwe API-endpoints nodig? Zo ja, wat is het contract?"
- "Zijn er security risico's (bijv. PII data, authenticatie)?"
- "Heeft dit invloed op bestaande achtergrondprocessen of performance?"
- "Vereist dit aanpassingen aan de infrastructuur?"
- "Moeten we technical debt inlossen om dit te kunnen bouwen?"

## Score Parameters

Scoren op schaal van 1-10.

- **Technische Haalbaarheid**: Is duidelijk *hoe* dit gebouwd moet worden? (Weging: 3)
- **Impact Analyse**: Is de impact op andere componenten/data duidelijk? (Weging: 3)
- **Security & Compliance**: Zijn security-aspecten afgedekt? (Weging: 2)
- **Onderhoudbaarheid**: Wordt er geen tech debt geïntroduceerd? (Weging: 2)
