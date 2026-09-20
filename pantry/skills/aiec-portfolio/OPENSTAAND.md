# Openstaand — plugin volgt het ontwerp

Het proces wordt eerst fase per fase ontworpen in Confluence (space AI). Deze lijst houdt bij wat
daaruit volgt voor de plugin. **Niets hiervan is geïmplementeerd.** Pas uitvoeren als de fase
waarin de beslissing viel, vastligt.

Bron van de beslissingen: ontwerpsessie 2026-09-16 met Kenzo, aan de hand van AI-49
(Natuur in je school) als doorgewerkt voorbeeld.

## Uit fase 1 (Captatie), 2026-09-16

### 1. Veldtype `jira-key` voor AI-key en EAG-key

De keys staan in het details-blok als Jira-macro, zodat de status zichtbaar is zonder door te
klikken. De parser leest een macrocel vandaag als platte tekst en plakt alle parameters aan elkaar.

Geverifieerd op de voorbeeldpagina (`aiec.py conf get 514425672`):

```
"ai_key": "JIRA - taakopvolgingssysteem Omgeving56e4142a-0105-3cf7-b7a8-b308d7369863AI-49"
```

De AI-key is de join-sleutel naar Jira; zonder fix koppelt het register aan niets.

- `schema.yaml`: `type: jira-key` op `ai_key` en `eag_key`
- `confluence.py` › `render_details`: moet de atlassian-config krijgen (server + serverId) om een
  macro te kunnen renderen — heeft nu alleen `(schema, values, macro_id)`
- `confluence.py` › `parse_details`: een cel met een jira-macro levert de `key`-parameter, niet de
  samengeplakte celtekst
- Test: round-trip `parse_details(render_details(v)) == v` met een macro-cel

### 2. `Stand van zaken` uit `page_sections`

Dubbel geworden: de Jira-macro's in het details-blok tonen de status al.

- `schema.yaml` › `page_sections`: de sectie `Stand van zaken` (type `jira-issue`) verwijderen

### 3. `Waarover gaat het` — placeholder aanpassen

Nu: "probleem en beoogde oplossing in twee of drie zinnen". De beoogde oplossing veroudert en hoort
in het captatierapport; de rootpagina moet over een jaar nog kloppen.

- `schema.yaml` › `page_sections`: placeholder wordt "het probleem en de vraag"

### 4. Datum in de titel van artefacten

`[AI-49] Captatierapport — 2026-07`. De children-macro op de rootpagina toont dan vanzelf hoe oud
het laatste oordeel is. Zelfde conventie voor verkennings- en opleveringsrapporten.

- `confluence.py` › `create_child`: titelconventie met datum
- Eventueel een regel die een artefactpagina zonder datum in de titel meldt

### 5. Beslissingen worden een tabel, niet een kindpagina per beslissing

De sectie `Beslissingen` op de initiatiefpagina gebruikte een `detailssummary`-macro over
kindpagina's met label `decisions`. Die dwingt een pagina per beslissing af. Vervangen door één
gewone tabel op de initiatiefpagina zelf, die met het initiatief meegroeit:

| Datum | Fase | Uitkomst | Reden | Bron |

De beslissing valt in het EAG-rapport (bij Kris), niet bij ons — de kolom `Bron` linkt daarheen en
de redenering wordt niet overgetypt. Wat wij bijhouden is wat we moeten kunnen optellen: datum,
uitkomst, reden. Uitkomsten: `goedgekeurd | geparkeerd tot JJJJ-MM | afgewezen | stopgezet`.

Reden om dit aan onze kant te houden, ondanks dat de beslissing elders valt: het EAG-sjabloon heeft
precies twee beslissingstabellen (Initiatie en Verkenning). Alles vanaf fase 3 heeft daar geen
plaats. En de funnel-cijfers en de regelcheck moeten machineleesbaar zijn.

- `schema.yaml` › `page_sections`: `Beslissingen` wordt type `tabel` met vaste kolommen, niet
  `detailssummary`
- `confluence.py`: renderer voor dat tabeltype, plus een parser die de rijen terugleest
- `rules.py`: nieuwe regel **`geen-beslissing`** — fase ≥ Analyse zonder rij in de
  beslissingstabel → waarschuwing. Bij AI-49 schoof het traject na de verkenning zonder formele
  beslissing naar implementatie omdat het "maar een paar mandagen" was; de bestaande regels kijken
  naar het *rapport*, niet naar de *beslissing*.
- `report.py`: funnel-cijfers uit de beslissingstabel (doorgestroomd / geparkeerd / afgewezen, met
  reden)
- `artefact_labels.decisions` blijft bestaan voor de ≥25 bestaande Beslissingen-pagina's, maar is
  niet langer het haakje voor deze regel. Bij de retro-fit beslissen wat daarmee gebeurt.

Let op de bestaande koppeling: alle artefact- en EAG-regels hangen achter `soort == afgebakend`, en
`soort` komt uit het details-blok. Zolang een pagina geen blok heeft, zwijgen ze allemaal. Dat is
correct (zonder soort kan de checker niets weten), maar het betekent dat de retro-fit écht eerst moet.

### 6. Sjabloontitels gelijkzetten

De sjablonen staan in Confluence onder 📄 Templates (pageId 411959725), in de huisconventie die er
al was:

- `(initiatief-template) [AI-XX] <TITEL>` — pageId 514425760
- `(captatierapport-template) [AI-XX] Captatierapport — JJJJ-MM` — pageId 514425762

De plugin verwacht namen die niet bestaan:

- `config.py`: `captatierapport_template = "Sjabloon AI-captatierapport"`
- `schema.yaml`: `template_title: "Sjabloon AI-initiatief"`

### 7. Wie bezit de sjabloonpagina?

`conf publish-template` rendert de sjabloon uit `schema.yaml` en schrijft ze naar Confluence. De
sjablonen zijn nu met de hand in Confluence gemaakt en daar verder verfijnd. Twee bronnen voor
dezelfde pagina werkt niet.

Te beslissen: ofwel blijft `schema.yaml` de bron en wordt de handgemaakte pagina eruit
geregenereerd, ofwel is Confluence de bron en vervalt `render_template` / `publish-template`.
Het ontwerpprincipe van het geheel ("alles in Confluence, leesbaar en schrijfbaar voor wie dat
moet kunnen") wijst naar het tweede.

### 8. Het oude mini-space-sjabloon

`(mini-space-template) [AI-XX] <TITEL>` (pageId 411959720, v14) leverde de mini-spaces met de lege
containerpagina's `[AI-XX] Verslagen / Beslissingen / Rapporten / Portfoliobeheer dOMG`. Vervangen
door het nieuwe initiatief-sjabloon. Kenzo beslist: hernoemen naar `(verouderd) …` of verwijderen.
Onder het nieuwe model zijn artefacten subpagina's mét label, geen mappen.

## Wacht op een beslissing van Kenzo

Uit de bouwfase, nog niet beantwoord (zie ook `02 - Areas/handleiding-aiec-portfolio.md`):

- Jira-statussen hernoemen of niet — de mapping in `schema.yaml` werkt in beide gevallen
- Resolution-mapping bevestigen (`schema.yaml` › `resoluties` is een voorstel)
- Uurtarief voor euro's in de kwartaaltoelichting, of uren-only
- Veldsplitsingen akkoord (14 velden werden er 17)

## Uit fase 1 — beslissingsmoment, 2026-09-16

### 9. Status volgt het werk, niet de beslissing

Bij de beslissing "verkenning goedgekeurd" gaat **EAG** naar Verkenning; het **AI-ticket blijft in
Captatie**. Captatie → In Analyse gebeurt wanneer de verkenning effectief begint. Bij AI-49 zat daar
één dag tussen (beslissing 22/07, transitie 23/07).

Gevolg voor het datamodel: de gate Captatie → Analyse is niet "de beslissing is gevallen" maar "het
werk start". De beslissing is de toestemming.

- `02 - Areas/expertisecentrum-ai-jira-datamodel.md` §5.1 aanpassen
- Mogelijke nieuwe regel: EAG in Verkenning terwijl AI al weken in Captatie staat = goedgekeurd maar
  niet gestart. Zinvol signaal, geen ruis.

### 10. Gate Captatie → Analyse valt samen met de EAG-beslissing

Herziening van punt 9. De beslissing van Kris zet EAG op Verkenning én het AI-ticket op In Analyse.
Eén beslissing, twee systemen, hetzelfde moment. Reden: anders vallen er twee beslissingen binnen
captatie, en de tweede hoort in de volgende fase. AIEC maakt geen statusonderscheid tussen een korte
verkenning en de analyse van een volwaardig project.

Symmetrie: EAG initiatie-beslissing = AI Captatie → Analyse · EAG verkennings-beslissing =
AI Analyse → Planning.

- `expertisecentrum-ai-jira-datamodel.md` §5.1: de gate herschrijven
- Mogelijke regel: **niet-gestart** — In Analyse zonder geboekte uren sinds de beslissingsdatum.
  Vervangt het signaal dat wegvalt doordat de status nu "goedgekeurd" zegt en niet "gestart".

### 11. Doorlopende werking krijgt geen Confluence-pagina

Omkadering, kennisdeling, governance: enkel een Jira-ticket, zodat de uren geboekt en gerapporteerd
worden. Geen EAG-ticket, geen captatierapport, geen initiatiefpagina, geen kenmerken. Valt buiten
de funnel.

Gevolg: elke pagina met het label `ai-initiatief` is per definitie `soort: afgebakend`.

- `schema.yaml`: het kenmerk `soort` verliest zijn functie in het blok — schrappen of behouden als
  documentatie van de scope? Schrappen betekent 16 kenmerken.
- `rules.py` › `geen-pagina` meldt nu élk doorlopend Jira-ticket. Er moet een manier zijn om een
  doorlopend ticket te herkennen zónder pagina: een Jira-label `doorlopend`, of de keys expliciet in
  `schema.yaml`. Vandaag staan AI-48 (Algemene Omkadering), AI-52 (Kennisdeling) en AI-59
  (AI-governance & beleid) in die categorie.
- Alle `required_when: [soort: afgebakend]`-voorwaarden worden daarmee onvoorwaardelijk.

### 12. Drie uitkomsten bij de captatie-beslissing

- **goedgekeurd** → zie punt 10
- **afgewezen** → AI-ticket naar Closed met resolution, kenmerk `Stopreden` invullen (categorie om
  op te tellen) plus één zin in de beslissingstabel (om terug te vinden)
- **geparkeerd** → AI-ticket blijft in Captatie, uitkomst `geparkeerd tot JJJJ-MM`. Frigo-regel:
  drie maanden zonder beweging dwingt een beslismoment af tijdens de kwartaalreview — verkennen,
  opnieuw parkeren met nieuwe datum, of afsluiten met reden. Nooit automatisch sluiten.

- `rules.py`: frigo-regel koppelen aan de uitkomst `geparkeerd tot …` in de beslissingstabel in
  plaats van aan de laatste activiteit alleen
- `report.py`: funnel-cijfers per uitkomst, met de stopreden-categorieën

## Uit fase 2 (Analyse), 2026-09-16

### 13. `verkenningsrapport` wordt `analyserapport`

De fase heet Analyse, dus het rapport heet analyserapport — zoals Captatie het captatierapport
oplevert. "Verkenning" is EAG-taal en dekt bovendien maar de korte variant: een analyse-project
levert precies hetzelfde rapport op, alleen na meer werk.

- `schema.yaml` › `artefact_labels`: `verkenningsrapport` → `analyserapport`
- `rules.py`: de regel die een initiatief voorbij Captatie zonder verkenningsrapport meldt, volgt
  het nieuwe label
- Sjabloon onder 📄 Templates: `(analyserapport-template) [AI-XX] Analyserapport — JJJJ-MM`
- Vault: de todo "AI-beoordelingsrapport → AI-verkenningsrapport"
  (`05 - Tasks/intakeproces-formalisering-todo.md`) wordt "→ AI-analyserapport"

### 14. Een kenmerk is verplicht op het einde van de fase die het bepaalt

Vandaag staat `toepassingstype` en `ai_techniek` op `fase_min: Analyse`, dus verplicht zodra het
ticket op In Analyse springt. Dat is precies het moment waarop je ze nog aan het uitzoeken bent —
groom zou klagen over het werk dat de fase moet doen.

Het principe: een kenmerk wordt gemeld wanneer het *gekend* moet zijn, niet wanneer eraan begonnen
wordt. Analyse bepaalt toepassingstype, AI-techniek, delivery-mode, batenclaim, aanname en de
definitieve AI Act-klasse; alle zes zijn dus verplicht bij het verlaten van Analyse. Dat is dezelfde
regel die AI Act-klasse al volgde ("te bepalen mag tot en met Analyse"), nu consequent.

- `schema.yaml`: `toepassingstype` en `ai_techniek` van `fase_min: Analyse` naar `fase_min: Planning`
- Gevolg voor de matrix Kenmerken per fase: de kolom Analyse loopt leeg, alles schuift naar Planning.
  Negen kenmerken bij het ingaan van Analyse, veertien bij het verlaten.

### 15. Beslissingstabel krijgt een kolom `Gevolg`

Bij de uitkomsten die werk in gang zetten hoort een ticket buiten het AI-project: een
projectportfolio-ticket (POR-taken) bij een analyse-project of een projectdefinitie. Kenzo wil die
bijhouden via de beslissing, niet als kenmerk.

| Datum | Fase | Uitkomst | Reden | Bron | Gevolg |

- `Gevolg` bevat nul, één of meerdere Jira-macro's — er kunnen meerdere analyse-projecten lopen,
  parallel of sequentieel
- `schema.yaml` › `page_sections` › `Beslissingen`: kolom toevoegen (zie punt 5)
- Sjabloon 514425760 en voorbeeld 514425672 moeten de kolom krijgen

### 16. Uitkomsten en gate van fase 2

Instroom = de gate van fase 1. Geen aparte drempel. De verkenning heeft een richttijd van maximaal
vijf werkdagen; loopt ze uit, dan is dat zelf het signaal dat er een analyse-project nodig is.

Deliverables zijn altijd dezelfde, of het nu vijf dagen of drie analyse-projecten waren:
analyserapport, het deel Verkenning van de EAG-beoordeling, de kenmerken, en een rij in de
beslissingstabel.

Vijf uitkomsten:

- **projectdefinitie** → In Analyse → Prioritering en planning, projectportfolio-ticket in `Gevolg`
- **reguliere werking** → In Analyse → Prioritering en planning, geen project. Bewust ook langs
  Planning: ook klein werk moet geprioriteerd worden — bij AI-49 is precies dat misgelopen.
- **analyse-project** → blijft In Analyse, ticket in `Gevolg`, komt later terug bij dezelfde
  beslissing. Een lus, geen tweede gate: er kunnen meerdere beslissingsrijen met fase Analyse staan.
- **geparkeerd** → blijft In Analyse, `geparkeerd tot JJJJ-MM`, frigo-regel zoals bij captatie
- **afgewezen** → Closed + resolution + kenmerk Stopreden

EAG-kant: de statussen op de instance zijn `Open · Beoordeling · Klaar voor verkenning ·
Verkenning (2) · Afsluiten` (gelezen via de transities van EAG-940 op 2026-09-16). Er is geen
stadium na verkenning: EAG sluit af zodra het projectportfolio overneemt. De gatetekst van fase 1 in
het datamodel moet die echte statusnamen gebruiken, niet "Initiatie → Verkenning".

- Mogelijke regel **analyse-uitgelopen**: In Analyse, meer dan 40 u geboekt, geen rij met fase
  Analyse in de beslissingstabel
- `report.py`: funnel-cijfers krijgen de fase-2-uitkomsten erbij

### 17. Volledige kenmerkenreview — na fase 5

Kenzo: "we moeten nog goed scherp stellen wat we allemaal willen opnemen als kenmerken van een
AI-initiatief en wat de mogelijke waarden zijn en wanneer ze gekend moeten zijn." Uitgesteld tot de
fases 3 tot 5 ontworpen zijn, want het moment waarop een kenmerk gekend moet zijn volgt uit de fase
die het bepaalt (punt 14).

Meteen mee te nemen in die ronde: `persoonsgegevens` heeft vandaag geen fase-limiet op de waarde
`onbekend`, terwijl `ai_act_klasse` die wel heeft op `te bepalen`.
