---
name: sb-write-meeting-note
user-invocable: false
description: Generate a structured meeting note for the Obsidian vault from a parsed transcript, attendee list, and meeting context.
---

# Write Meeting Note

## Input

This skill expects the following context to be available in the conversation:

1. **Parsed transcript** (output from `sb-parse-whisper`)
2. **Aanwezigenlijst** with correct names as `[[wikilinks]]`
3. **Meeting context**: titel, datum (YYYY-MM-DD), doel/aanleiding
4. **Meeting note filename**: `YYYY-MM-DD-beschrijving.md` (determined by the agent)

## Vault Location

Write the meeting note to:
```
~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain/02 - Areas/{filename}
```

## Template

Use the vault template `03 - Resources/030 - Templates/template-01-meeting-minutes.md` as basis. The output must follow this structure:

### Frontmatter

```yaml
---
is-part-of:
  - "[[project-moc-naam]]"   # if meeting relates to a project
related-to:
  - "[[vorig-overleg]]"       # if this is a recurring meeting
  - "[[Person 1]]"
  - "[[Person 2]]"
tags:
  - meeting-minutes
  - type/event
  - type/meeting
timeline: "[[YYYY-MM-DD]]"
created: "[[YYYY-MM-DD]]"
source: "[[YYYY-MM-DD]]"
aliases:
last-review:
---
```

### Body

```markdown
# {Korte Titel}

## Aanwezigen
- [[Persoon 1]]
- [[Persoon 2]]
- [[Persoon 3]]

## Aanleiding overleg
{Waarom vindt dit overleg plaats? Wat is het doel?}

## Agenda
### {Topic 1 - afgeleid uit de transcript-inhoud}

{Topic-gebaseerd verslag. Beschrijf wat besproken werd, welke standpunten er waren, en wat de conclusie is. Interne bedenkingen en observaties van Kenzo mogen erbij.}

### {Topic 2}

{Idem}

## Acties
- {Actie 1 - wie, wat, wanneer indien bekend}
- {Actie 2}
```

## Stijlregels

- **Topic-gebaseerd**, niet speaker-gebaseerd (speaker diarization is onbetrouwbaar)
- **Voor eigen consumptie** (Kenzo): schrijf alsof je notities maakt voor jezelf
- **Interne bedenkingen** welkom: observaties, twijfels, strategische overwegingen mogen erin
- **Nederlands** (Vlaams register)
- **Geen AI-stijl**: vermijd opsommingstekens waar een korte paragraaf volstaat, geen overmatig gebruik van vetgedrukte tekst, geen "samenvattend" of "concluderend" taalgebruik
- Attributie van uitspraken aan specifieke personen **alleen** als dit duidelijk uit de inhoud blijkt (niet op basis van speaker labels)
- Beslissingen en concrete actiepunten in aparte secties

## Few-shot voorbeeld

Voorbeeld van een goed gestructureerde meeting note. Let op:
- Aanwezigen met functie/organisatie tussen haakjes; ook afwezigen-die-uitgenodigd-waren vermeld
- Aanleiding overleg geeft volledige context (waarom, wie, wat staat er op het spel)
- Agenda-secties zijn inhoudelijk benoemd (geen "Punt 1, Punt 2"), volgen het natuurlijke verloop van het gesprek
- Vetgedrukte termen alleen voor sleutelconcepten die later terugkomen (`**samenwerkingsakkoord**`, `**VTS-oplossing**`)
- Interne bedenkingen in *cursief* met "note to self" of "bedenking voor mezelf" markering
- Eigen inbreng/standpunten expliciet gemarkeerd ("Ik heb stevig ingebracht", "Mijn punt")
- Acties met expliciete verantwoordelijke + deliverable + timing waar bekend
- Geen samenvattende slotparagraaf, geen "concluderend"-taal

````markdown
---
is-part-of:
  - "[[project-moc-MIA]]"
related-to:
  - "[[2026-05-12-afstemming-vk-domg-prep-overleg-digitaal-vlaanderen-mia]]"
  - "[[Milieu-investeringsaftrek]]"
  - "[[Kenzo Van Craeynest]]"
  - "[[Katrijn Coeckelberghs]]"
  - "[[Koen Coupe]]"
  - "[[Paul Zeebroek]]"
tags:
  - meeting-minutes
  - type/event
  - type/meeting
timeline: "[[2026-05-20]]"
created: "[[2026-05-20]]"
source: "[[2026-05-20]]"
aliases:
last-review:
---
# Overleg DV - MIA: efficiëntiewinst met AI

## Aanwezigen
- [[Kenzo Van Craeynest]] (dOMG, AI-coördinator)
- [[Katrijn Coeckelberghs]] (dOMG, inhoudelijk MIA)
- [[Koen Coupe]] (VEKA, interne IT-coördinator, AI-SPOC voor Copilot)
- [[Paul Zeebroek]] (VEKA, energie-investeringsaftrek)
- Pieter Breyne (Digitaal Vlaanderen, business partner, projectleider opdracht minister-president)
- Tom Van Herck (Digitaal Vlaanderen, AI Expertisecentrum, pijler innovatie)

Afwezig hoewel uitgenodigd: Tom Talpe, Tony Vanderstraete, Gert De Gelder.

## Aanleiding overleg
Het [[voorzitterscollege]] heeft 500k vrijgemaakt voor een stappenplan rond AI-inzet voor productiviteit en efficiëntie binnen de Vlaamse Overheid. Digitaal Vlaanderen is trekker van de digitale roadmap; de [[Milieu-investeringsaftrek|MIA]] staat **expliciet vermeld** in de opdracht van minister-president Diependaal als pilootcase. Verantwoordelijkheid MIA ligt bij VEKA (energie) en dOMG (milieu). Verkennend gesprek om te zien hoe DV ons kan ondersteunen en welke AI-pistes haalbaar zijn.

## Agenda

### Context van de opdracht en de MIA-case
Pieter schetst dat DV een ganse waslijst use cases heeft binnengekregen via de VOCO-bevraging. Vier domeinen springen eruit: productiviteit van de kenniswerker (Copilot), dossiergebonden administratieve processen (subsidies, klachten, adviezen, erkenningen, vergunningen), herbruikbare componenten (documentverwerking, anonimisering, kennisontsluiting) en software-ontwikkeling (out of scope voor deze opdracht).

MIA is een speciaal geval omdat het expliciet benoemd staat in de opdracht. Toch is het géén exclusieve focus — DV wil breder kijken naar efficiëntiewinst.

Katrijn legt de stand van zaken uit: MIA is volledig nieuw (de energie-investeringsaftrek loopt al sinds 1988). Verwachte volume: in de buurt van de 3000 aanvragen/jaar zoals bij EIA, maar potentieel veel meer omdat de lijst breed is en ook kleine zelfstandigen kan aanspreken.

Belangrijk: er is een **samenwerkingsakkoord met de federale overheid**. Federaal wil een federaal investeringsloket bouwen, maar pas zodra het samenwerkingsakkoord ondertekend is. Op termijn dus mogelijk één federaal loket. Dat creëert onzekerheid over hoe lang Vlaanderen z'n eigen systeem moet blijven uitbouwen, en welke taken (front/back) ons zullen toekomen. Standpunt VEKA + dOMG: het federale systeem moet minstens evengoed zijn als wat we nu in eigen beheer ontwikkelen.

### Energie-investeringsaftrek vandaag (Paul)
Paul draait een eigen Access-systeem met front office (webformulier) en back office, sinds 2010 stelselmatig verder geautomatiseerd. Voor corona zo'n 200-300 dossiers/jaar; sinds de energiecrisis 1500-2000 dossiers/jaar met 1.3 VTE. Voor de nieuwe regelgeving (investeringen vanaf 1 januari 2025) is hij volop bezig met front-office-ontwikkeling, maar testen kan pas zodra het samenwerkingsakkoord er is.

Belangrijke kanttekening van Paul: een MIA/EIA-beslissing is een **attest voor de belastingcontroleur**. Die kan tot tien jaar later nog opvraging doen via een bijzondere belastinginspectie (BBI). Alles moet dus onderbouwd en gedocumenteerd zijn — ook AI-beslissingen.

### Pistes voor AI-inzet
De inputkant zijn vooral facturen, terugverdientijdberekeningen in Excel, en energieaudits. Drie pistes besproken:

**Factuurcontrole als generieke bouwsteen.** Koen volgt de **VTS-oplossing** (auditeurs Inspectie van Financiën), een Power Apps-oplossing gebouwd door CGI. Daar zit factuurcontrole + balansgegevens-ophalen in. Het claim is: handmatig kon één auditor 4 dossiers/dag, met AI nog steeds 4 maar wel de juiste vier (door AI gevlagd als verdacht), en daarnaast 100+ extra dossiers die anders nooit gezien zouden zijn. Logging van elke AI-beslissing zit erin.

VTS staat ook op DV's longlist. Pieter stelt voor om VTS samen te bekijken (demo + onze vragen rond betrouwbaarheid + architecturale integreerbaarheid). Koens kanttekening: VTS draait in een Microsoft Power Platform stack. VEKA gaat ook naar Power Platform, maar dOMG zit niet in Microsoft-stack — dus integratie is een open vraag.

**Volledigheidscheck van aanvraagdossiers** (voorgesteld door Tom Van Herck). Een agent die de indiener vóór indiening een vergunningscheck laat doen: zijn alle juiste documenten aanwezig, is het dossier volledig? Niet blokkerend, gebruiker kan toch indienen. Verschuift werk van back- naar frontoffice. Kenzo's reactie: dit is een ideale use case omdat fouten van de AI niet kritiek zijn (gebruiker kan overrulen). Katrijn vraagt of er ook gecheckt wordt of het opgeladen document wel écht een factuur of technische beschrijving is — dat moet nog uitgewerkt worden, maar ja, daar wordt vanuit gegaan.

**Anonimisering/pseudonimisering als bouwsteen.** DV ontwikkelt dit als generieke bouwsteen. Kenzo's bedenking: drie weken geleden hoorde ik nog dat de pseudonimiseringsservice niet productieklaar was. Pieter denkt dat het er ondertussen is, maar bevestigt niet hard. *Bedenking voor mezelf: opnieuw checken voor we hier in de bezwaarschriften-architectuur op rekenen.*

### Mijn architecturaal punt over betrouwbaarheid
Ik heb stevig ingebracht dat het kernprobleem bij AI-inzet de validatie van correctheid is. Een factuurcontrole klinkt eenvoudig, maar als je een bedrag eruit haalt en daar 10% subsidie op berekent, mag er gewoon geen fout in zitten. Het gevolg van een fout schaalt met de aard van de use case.

Ik heb mijn raamwerk uitgelegd:
- Voor simpele/lage-risico use cases: vertrouwen op AI + zelf-gerapporteerde confidence, benchmarken tegen een gold dataset, drift-detectie tijdens productie.
- Voor complexere/hoge-risico use cases: meerdere modellen tegelijk aansturen (multi-model orchestration), licht andere prompts om model- en promptbiases eruit te filteren via consensus.
- Uitkomst: per ja-nee-beslissing een confidence-score, en de gebruiker stelt zelf de drempel (80%, 95%) op basis van een kosten-baten-analyse: het risico van een foute beslissing zonder volledige manuele validatie versus de winst van veel meer werk verzetten.

Pieter en Tom Van Herck pikten dit goed op — Tom verwees expliciet naar betrouwbaarheid als een van de zes principes uit het AI playbook. Koen voegde toe dat DV-team van Pieter / het Expertisecentrum een rol heeft om bouwblokken zoals VTS kritisch te evalueren tegen die principes ("zijn er bochten afgesneden bij CGI?").

### Methodologische zorg
Ik heb tegen het einde gewezen op een fundamentele blinde vlek: we gaan ervan uit dat AI ons hier efficiëntiewinst gaat opleveren, maar dat is een *buikgevoel*. We zijn nog niet gewandeld voor we beginnen te lopen. Voor MIA komt daar nog bij dat de inhoudelijke expertise nog opgebouwd moet worden — Katrijn weet zelfs nog niet hoe ze de dossiers überhaupt gaat binnenkrijgen of welke vorm de bijlagen zullen aannemen.

Mijn punt: zonder validators en zonder referentiedataset kun je AI-output niet benchmarken. Zeker bij hoge BBI-gevoeligheid is voorzichtigheid geboden. Focus op kleine, herbruikbare bouwstenen, niet op totaaloplossingen — temeer omdat VEKA en dOMG technologisch niet op elkaar afgestemd zijn (Power Platform vs. niet-Microsoft).

Pieter gaf aan dat DV bezig is met een **business case framework / efficiëntieraamwerk** dat ze ook op deze case willen toepassen. Twee sporen: (1) framework opbouwen, (2) parallel met VTS aan de slag om het framework op te af te toetsen.

### Bijkomende generieke bouwstenen waar DV op werkt
- Klantencontactcenter (1700, ANB-Kivit-project): routering van vragen/mails.
- Parlementaire assistent (DV samen met kabinet, voor parlementaire vragen).
- Wetgevingstechniek-agent: aftoetsen van wetteksten aan de 150 pagina's omzendbrief.
- Inspectie/handhaving + fraudedetectie (gelinkt aan VTS).
- Vergunningsaanvragen: volledigheidscheck en relevantie-extractie uit bijlagen.

Koen wees aan dat het routerings-project bij ANB ook in Power Apps zit en generiek wordt opgezet. *Note to self: hier eventueel inhaken voor onze klachtenbehandeling.*

### Rapportering voorzitterscollege
Katrijn moet tegen 5 juni rapporteren aan het voorzitterscollege namens VEKA+dOMG over MIA (digitalisering + AI samen, ééncombineerd document). Pieter rapporteert vanuit DV in het kader van de bredere AI-opdracht. Afspraak: aparte rapporten, maar inhoudelijk afgestemd voor consistentie.

## Acties
- Pieter Breyne: kort verslag opmaken van dit overleg en delen.
- Pieter Breyne: VTS-demo organiseren met VEKA en dOMG, inclusief beantwoording van onze betrouwbaarheids- en architectuurvragen — korte termijn ("niet laten aanslepen", want het is de case met grootste aandacht uit de opdracht).
- Pieter Breyne: efficiëntieraamwerk / business case framework toepassen op de MIA-case.
- Katrijn Coeckelberghs: rapportering aan voorzitterscollege opmaken tegen 5 juni; afstemmen met Pieter zodat VEKA+dOMG-rapport en DV-rapport consistent zijn.
- Kenzo: opvolgen of DV's pseudonimiseringsservice productieklaar is (relevant voor bezwaarschriften).
- Kenzo: bij VTS-demo de architectuurvragen op tafel leggen — vooral platformonafhankelijkheid (dOMG zit niet in Microsoft-stack).
````
