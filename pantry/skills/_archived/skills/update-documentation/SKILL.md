---
name: update-documentation
description: Werkt de productdocumentatie bij volgens de richtlijnen in documentation-guidelines.md. Default scope = wijzigingen op de huidige git-branch t.o.v. main. Optioneel kan de gebruiker specifieke functionaliteit meegeven; die wordt eerst onderzocht door sub-agents (functional-analyst, domain-expert, tech-lead) vooraleer te documenteren. Roept altijd eerst de `grill-with-docs` skill aan om spraakverwarring te vermijden over wat er gedocumenteerd wordt.
---

# Documentatie bijwerken

## Rol

- [Technical Writer](../../agents/technical-writer.md) — primaire schrijver
- [Functional Analyst](../../agents/functional-analyst.md) — onderzoekt wat de functionaliteit doet
- [Domain Expert](../../agents/domain-expert.md) — bewaakt terminologie en domeinconsistentie
- [Tech Lead](../../agents/tech-lead.md) — bevestigt technische correctheid
- [Critic](../../agents/critic.md) — adversariële review van het eindresultaat

## Doel

Productdocumentatie up-to-date houden zodat ze de werkelijke werking van het systeem reflecteert, conform de richtlijnen in [[../../documentation-guidelines.md]].

## Input

- (default) De huidige git-branch. Scope = diff t.o.v. `main` (of de configured base branch).
- (optioneel) Een specifieke functionaliteit, feature of domein dat de gebruiker meegeeft.
- Bestaande documentatie in `/docs/`.
- De richtlijnen in [[../../documentation-guidelines.md]] (verplicht inlezen).

## Plan van aanpak

### Stap 1 — Scope bepalen

- **Geen argument** → bepaal de scope uit de huidige branch:
  - `git diff main...HEAD --name-only` voor gewijzigde bestanden
  - `git log main..HEAD --oneline` voor commit-context
  - Leid hieruit de geraakte functionaliteiten af
- **Argument meegegeven** (bv. "documenteer de nieuwe staltype-validatie"):
  - Dispatch sub-agents in parallel om de functionaliteit te onderzoeken:
    - `functional-analyst` — hoe werkt het in de code, welke flows
    - `domain-expert` — welke begrippen, welk domein, welke owner
    - `tech-lead` — technische details die in `/technical` of `####`-subsectie horen
  - Verzamel hun bevindingen voor de grill-fase

### Stap 2 — Grillen (verplicht)

Roep de `grill-with-docs` skill aan met de scope + onderzoeksbevindingen. Doel: terminologie scherpstellen, ambiguïteit elimineren, afstemmen op CONTEXT.md / glossary / ADRs vóór er één regel documentatie geschreven wordt.

Ga **niet** verder naar stap 3 zolang er nog openstaande grill-vragen zijn.

### Stap 3 — Documentatieplan opstellen

Per geraakte functionaliteit, bepaal:

- In welk domein hoort dit? (zie `/docs/{domein}/`)
- Nieuwe feature-pagina nodig of bestaande bijwerken?
- `CONTEXT.md`-entries (glossary) toevoegen/wijzigen? → **eerst voorstel indienen**, niet direct schrijven. `CONTEXT.md` blijft puur glossary — geen implementatiedetails.
- FAQ-entries toevoegen/wijzigen? → **eerst voorstel indienen**, niet direct schrijven.
- ADR nodig? Alleen wanneer beslissing moeilijk omkeerbaar + verrassend zonder context + echte trade-off. Plaats in `docs/adr/`.
- Technische details → `/technical` of `####`-subsectie.

Toon het plan aan de gebruiker en wacht op akkoord vóór schrijven.

### Stap 4 — Schrijven

Volg strikt [[../../documentation-guidelines.md]]:

- Nederlandstalig
- Doelgroep = eindgebruiker, niet ontwikkelaar
- Vermijd onnodig technische terminologie
- Sterk vereenvoudigde voorbeelden
- Aandacht voor randgevallen
- Markdownrichtlijnen respecteren
- Domein-`index.md` updaten als er een nieuwe feature-pagina bijkomt

### Stap 5 — Review

- Laat `critic` de wijzigingen reviewen op duidelijkheid, consistentie en volledigheid.
- Verifieer dat `CONTEXT.md` en FAQ in sync blijven met de domeinmappen.
- Verifieer dat geen ontwikkelaarsgerichte info buiten `/technical` staat.

## Beperkingen

- Verzin geen functionaliteit. Alles moet aantoonbaar volgen uit de code of de user story.
- Geen wijzigingen aan `CONTEXT.md` of `faq.md` zonder expliciete goedkeuring van de gebruiker (zie guidelines).
- Schrijf nooit ontwikkelaarsdocumentatie buiten `/technical`.
- Skip stap 2 (grillen) nooit, ook niet bij "kleine" wijzigingen.

## Output

- Bijgewerkte/nieuwe markdownbestanden in `/docs/...`
- Een samenvatting in `tmp/{branch-of-feature}-doc-update.md` met:
  - Scope (branch-diff of meegegeven feature)
  - Onderzoeksbevindingen van sub-agents (indien van toepassing)
  - Grill-uitkomsten (afgestemde terminologie, opgeloste ambiguïteiten)
  - Lijst gewijzigde/nieuwe documentatiebestanden
  - Voorstellen voor `CONTEXT.md`/FAQ/ADRs (ter goedkeuring)
  - Openstaande vragen
