# Valkuilen

Lessen uit eerdere beoordelingen (eerste bron: Obscuro, AI-5, 2026-09-29; aanvullen bij elke nieuwe casus). Loop ze na vóór het oordeel.

- **Verkeerde lijst.** Vlaamse bestuursinstantie → VTC O/2020/01, niet GBA 01/2019. De VTC-lijst is strenger (o.a. punt 18 leveranciers, punt 20 depseudonimiseren).
- **"Geen data naar externe modellen / on-prem" ≠ geen DPIA-plicht.** De criteria hangen niet af van doorgifte. Het verlaagt het risico en schakelt VTC 18 uit, meer niet.
- **Pseudonimisering is geen anonimisering.** Gepseudonimiseerde gegevens blijven persoonsgegevens (overweging 26 AVG). Reversibele pseudonimisering (mapping, herstelfunctie) → VTC 20.
- **Sleutel en output samen bewaard** ondermijnt art. 4(5) ("aanvullende gegevens apart bewaard").
- **TTL is geen bewaartermijn** als er back-ups (Barman, snapshots, WAL-archief) of logs (ELK) bestaan. Effectieve bewaring = langste van die termijnen.
- **Incidentele gevoelige gegevens tellen — maar niet overal even zwaar.** Een dienst waar iedereen willekeurige documenten in kan stoppen verwerkt ook pv's (art. 10), gezondheids- en financiële gegevens, ook al is dat niet het doel. Dat volstaat voor WP248-criterium 4. Art. 35(3)(b) ("grootschalig") en VTC 3 ("systematisch uitgewisseld tussen VV's") vragen meer: zonder volumecijfers of vaste gegevensstroom → twijfel + open vraag.
- **Generieke tool zonder doel.** Een UI voor alle medewerkers is een zelfstandige verwerking die een doel, registerregel en bewaartermijn nodig heeft — niet louter een "maatregel" van afnemers.
- **Rechtspersoonlijkheid in de Vlaamse overheid.** Departementen en IVA's zonder rechtspersoonlijkheid vallen onder dezelfde rechtspersoon (Vlaamse Gemeenschap/Vlaams Gewest); IVA's met rechtspersoonlijkheid en EVA's zijn aparte rechtspersonen, dus aparte VV's. Dat bepaalt of er een verwerkersrelatie (art. 28) of uitwisseling tussen VV's (VTC 3) is. Status van een entiteit onbekend → open vraag.
- **Dienst vs. afnemer.** Een privacy-verhogende dienst heeft zelden een eigen doel; de afnemer draagt de DPIA voor zijn verwerking en gebruikt de betrouwbaarheid van de dienst als input. Buiten de eigen rechtspersoon wordt de dienstverlener verwerker (art. 28).
- **Eerder DPO-advies kan een andere scope hebben gehad** (andere afnemer, "anonimisering" i.p.v. pseudonimisering, voorwaarde van validatie die nadien faalde). Toets of de premissen nog kloppen.
- **Al in productie.** DPIA is "voorafgaand" (art. 35(1)); te laat is geen reden om ze over te slaan. Stel tussentijdse maatregelen voor. Een "prototype"-banner verandert juridisch niets.
- **Stille fouten.** Een dienst die "succes" meldt zonder iets te doen, of een foutmarge die niet gemeten is, maakt "correct gepseudonimiseerd" (bv. ICR2-status) onbewijsbaar.
- **Publicatie-afnemers** (openbaarheid van bestuur): een lek is onomkeerbare openbaarmaking → aparte risicoklasse. Controleer dat redactie in pdf's echt tekst verwijdert, geen overlay.
- **Rijksregisternummer** heeft een eigen regime (wet 8 augustus 1983, art. 8) — laten bevestigen door DPO.
- **Interne standaarden** (bv. DOMG-STD-260): controleer versie, goedkeuringsstatus en scope voor je ze als bindend opvoert.
- **Feiten uit fiches vs. code** kunnen verschillen (limieten, opslag, modellen). Code gaat voor; vlag het verschil.
