---
name: is-dpia-nodig
description: Beoordeel of een verwerking of toepassing een DPIA (gegevensbeschermingseffectbeoordeling, art. 35 AVG) vereist, in Belgische/Vlaamse overheidscontext — toetsing aan art. 35(3), de negen WP248-criteria en de bindende lijst van VTC (Vlaamse bestuursinstanties) of GBA. Gebruik bij "is een DPIA nodig", "DPIA-oordeel", "moet hier een GEB voor", "pre-PIA of DPIA", of het DPIA-veld van een analyserapport.
---

# Is een DPIA nodig?

Onderbouwd advies of een DPIA vereist is. Je adviseert; de verwerkingsverantwoordelijke beslist, de DPO geeft advies (art. 35(2)). Model oordeelt per criterium; de toetsingskaders staan letterlijk in `references/` — citeer daaruit, niet uit geheugen.

## Workflow

1. **Feiten verzamelen** — wat wordt verwerkt (categorieën, ook incidentele zoals RRN, rekeningnummers, pv's), van wie, door wie (toegang), waar (on-prem/cloud, leveranciers), hoe lang (opslag, TTL, **back-ups**, logs), omkeerbaar of niet, afnemers. Code/config in productie gaat boven fiches; vlag tegenstrijdigheden. Niet-gedeployde code (feature branch) → apart als "gepland", niet als huidige toestand. Vermeld repo/branch als bron. Ontbrekende feiten → open vraag, niet invullen. Interne standaarden of documenten buiten `references/`: read-only opzoeken als ze vindbaar zijn, anders open vraag.
2. **Bevoegde toezichthouder** — Vlaamse bestuursinstantie (e-govdecreet art. 2, 10°) → **VTC**, lijst O/2020/01 is bindend. Anders → **GBA**, besluit 01/2019. Zie `references/lijst-vtc.md`, `references/lijst-gba.md`. Vraagt de opdrachtgever een andere lijst dan de bevoegde: toets beide volledig, zeg welke bindend is en waarom.
3. **Art. 35(3)** a/b/c — tabel ja/nee/twijfel + reden.
4. **WP248 negen criteria** (`references/wp248-criteria.md`) — tabel per criterium, telling. ≥2 criteria → in de meeste gevallen DPIA; soms volstaat 1.
5. **Lijst van de bevoegde toezichthouder** — elk punt ja/nee/twijfel. Eén "ja" = DPIA verplicht. Afwezigheid op de lijst sluit een DPIA niet uit.
6. **Rollen scheiden** — dienst/verwerkingsmiddel vs. verwerkingen van afnemers; wie is VV, waar is er een verwerker (art. 28)? Een generieke UI zonder afgebakend doel is een zelfstandige verwerking.
7. **Oordeel** — `vereist` / `niet vereist` / `niet vereist maar aanbevolen (pre-PIA)`. Zeg welke configuratiewijziging het oordeel zou omkeren, en welke tussentijdse maatregelen nodig zijn als de verwerking al loopt (DPIA is "voorafgaand").
8. **Andere verplichtingen** los van de DPIA en **open vragen** voor team en DPO.
9. Loop `references/valkuilen.md` na vóór je afrondt.

## Output

Volg `references/output-sjabloon.md`: toetsingstabellen, rollen, oordeel met een kopieerklare motivering van 3–6 zinnen (blockquote, voor "Risico en compliance" in een analyserapport), andere verplichtingen, open vragen, bronnen. Schrijf naar een bestand als de vraag dat vraagt; anders in chat.

## Beperkingen

- Geen juridisch bindend advies; formuleer als advies aan VV en DPO.
- Lijsten evolueren (VTC herbevestigde O/2020/01 op 2026-07-14). Is `gecontroleerd` in een reference ouder dan 12 maanden, verifieer de bron-URL en vermeld dat.
- Stel geen AI Act-klasse of ICR-classificatie vast; vlag ze als apart te beoordelen. Wel mag je zeggen dat een claim (bv. "correct gepseudonimiseerd = ICR2") met de beschikbare feiten niet onderbouwd is.
