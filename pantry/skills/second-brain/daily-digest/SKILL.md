---
name: daily-digest
description: |
  Verzamel de werkactiviteit van de voorbije dagen uit alle bronnen (mail, agenda,
  Teams, Rocket.Chat, Jira, Confluence, Chrome, git, Claude-sessies, vault) en vul
  daarmee de daily notes aan die je zelf niet volledig kreeg. Een deterministisch
  script doet het hele verzamelwerk; de LLM oordeelt wat de moeite is, consolideert
  met wat er al staat, en schrijft. Push daarna optioneel het bewaarwaardige naar
  Open Brain. On-demand; geen cron.
---

# Daily Digest

Vault: `~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain`

Kenzo noteert gaandeweg zelf in zijn daily note — vaak een ruwe brain dump die
nergens anders staat — maar hij capteert niet alles. Deze skill vult de gaten met
wat de systemen wél weten.

Doel van de daily note: **je geheugen opporren**, en bij een weekoverzicht kunnen
zien wat er ligt te verwateren. Geen archiefdocument. Dat bepaalt de lat: liever
een leesbaar, geconsolideerd verhaal dan een volledige log.

## Werkverdeling

- **Script (`scripts/collect.py`)** — deterministisch: venster berekenen, credentials
  uit de keychain halen, tien bronnen bevragen, tijdstempels naar lokale tijd, ruis
  wegfilteren (auth-redirects, `.obsidian`-UI-state, systeemberichten, afgevinkte
  taken, repo's zonder activiteit), en alles in één markdown-bundel gieten.
- **LLM (deze skill)** — oordeel: wat is het vermelden waard, hoe hoort het samen,
  wat staat er al, en wat is de beslissing achter het gepingpong.

## Venster

Standaard vanaf **00:00 van twee dagen geleden**; **op maandag vier dagen**, zodat
het weekend en vrijdag meekomen. Override met `--days N` of `--since 2026-07-28T00:00`.

Het venster overlapt bewust met dagen die al een note hebben. Het script haalt die
notes zelf op (sectie *AL VASTGELEGD*) — dat is de dedup-input en meteen de reden
dat de skill idempotent is: twee keer draaien voegt niets dubbel toe.

## Bronnen en credentials

| Bron | Weg |
|---|---|
| Rocket.Chat | keychain `rocketchat-personal-access-token` (token = wachtwoord, userId = `acct`) |
| Jira | keychain `jira-personal-token` — activity stream (eigen acties) + JQL (bewogen issues) |
| Confluence | keychain `confluence-personal-token` — CQL `contributor = currentUser()` |
| Graph (mail, agenda, Teams-chats) | `GRAPH_TOKEN`, anders clipboard |
| Chrome | kopie van de History-sqlite |
| git | **enkel git-repo's** onder `~/Dropbox`: commits in het venster + niet-gecommit werk dat in het venster gewijzigd is |
| Claude-sessies | `~/.claude/projects/**/*.jsonl` |
| Vault | `git diff` in de vault |

Geen enkele bron faalt stil: wat ontbreekt of misgaat komt onderaan de bundel onder
*Bronnen die ontbraken of faalden*. **Rapporteer die lijst altijd mee** — een digest
met een onvermelde blinde vlek leest als een volledige dag.

Eén uitzondering: de **structurele** gaten uit *Bekende gaten* hieronder (Teams-kanaal-
berichten, meeting-transcripts, GitLab-discussies, andere browsers, andere machines)
hoef je niet elke keer op te sommen — Kenzo kent ze. Meld ze alleen als er die dag
iets van afhangt. Wat je wél altijd meldt, is een bron die deze keer stukging terwijl
ze normaal werkt.

Het Graph-token is kortlevend en heeft geen refresh: vraag Kenzo een vers token uit
Graph Explorer (tab *Access token*) naar het klembord te kopiëren. Toon het nooit.

## Stappen

1. **Graph-token eerst.** Draai `scripts/collect.py --check-graph` vóór het echte
   verzamelen. Is er geen geldig token, vraag Kenzo er dan meteen een te kopiëren uit
   Graph Explorer (tab *Access token*) en wacht tot hij bevestigt — begin niet aan een
   digest zonder mail en agenda. Blijft het token ook na een tweede poging ongeldig,
   zeg dat en draai verder zonder Graph, met de blinde vlek expliciet in je rapport.

2. **Verzamelen.** Draai `scripts/collect.py` (met `--days`/`--since` als Kenzo een
   ander venster vraagt). Werk verder uitsluitend met de bundel.

3. **Mail uitdiepen waar het telt.** De bundel geeft previews van 255 tekens; de
   beslissende inhoud staat daar vaak voorbij. Kies de handvol mails die er echt toe
   doen en haal hun volledige tekst met `scripts/collect.py --mail-body <id>` (het id
   staat bij elke mail in de bundel). Niet standaard voor alles doen — dat was precies
   de reden om previews te nemen.

4. **Oordelen.** Per dag: wat is er *gebeurd* en wat is er *beslist*? Groepeer per
   onderwerp, niet per bron — een beslissing die in Rocket.Chat begint, in Jira landt
   en per mail bevestigd wordt, is één punt. Bewaar: beslissingen mét het argument
   eronder, afspraken met een naam en een datum, cijfers die later nog gelden, en
   open discussies met wie welk standpunt inneemt. Laat vallen: statusgepingpong,
   "ok"/"bedankt", agenda-accepts, en herhaling van wat al genoteerd staat.

5. **Consolideren met wat er al staat.** Alles in *AL VASTGELEGD* is al genoteerd.
   Je mag Kenzo's eigen tekst **herschrijven, samenvoegen en verplaatsen** om er één
   samenhangend verhaal per onderwerp van te maken — vorm is vrij. Eén harde grens:
   **er mag geen informatie verloren gaan**. Staat er een detail in zijn brain dump
   dat je niet in je consolidatie kwijt kan, dan blijft die regel staan zoals hij is.

6. **Schrijven.** Direct, zonder tussentijdse goedkeuring — dat is een bewuste
   uitzondering op Kenzo's staande regel "vault-wijzigingen eerst voorstellen", omdat
   het punt van deze skill is dat hij niet alles hoeft na te lopen. Wel eerst stil de
   vault committen (`git add -A && git commit -m "digest: snapshot voor <datum>"`),
   zodat `git revert` altijd kan.
   - Schrijf **per dag** in `04 - Journal/YYYY/MM/DD/YYYY-MM-DD.md`, boven `## 📋 Logs`.
   - Bestaat de note niet: alleen aanmaken **als er werkinhoud is** voor die dag —
     geen lege notes voor stille weekenddagen. Volg het vault-template (`#daily
     [[YYYY-MM]]`, `# 📥 Daily Note` + blockquote, secties, dan de Logs-blokken).
   - Rapporteer daarna per dag wat je toevoegde of herschreef, met `obsidian://`-links.

7. **Open Brain.** Vraag of het bewaarwaardige mee naar het brein moet. Zo ja: oordeel
   **opnieuw over de bundel**, niet over de geschreven note — de note is bewust
   gecomprimeerd, en veel brein-waardigs (een referentie, een cijfer, een persoonsfeit)
   hoort niet in een dagverslag. Dedup met `search_thoughts`, push met `capture_thought`.
   Dit is de hoofdweg naar Open Brain: draai je de digest, dan hoef je `capture-mail`
   en `capture-vault` niet meer routineus te draaien voor hetzelfde venster.

## Regels

- **Geen informatieverlies.** Consolideren mag, schrappen niet.
- **Privé blijft buiten de note.** Het script classificeert *niet* — of iets werk of
  privé is, is oordeel. De Chrome-geschiedenis komt ongesorteerd binnen; jij beslist
  wat de note haalt en meldt achteraf welke privé-sporen je liet liggen. Wil Kenzo
  domeinen structureel niet eens verzameld hebben, dan zet hij ze in
  `~/.config/daily-digest/exclude-domains.txt`; het script meldt hoeveel het weglaat.
- **ICR.** Mail met `ICR2`/`ICR3`/`ICR4` slaat het script over. Rocket.Chat, agenda en
  Teams dragen die tags niet — daar is geen filter, dus wat je verwerkt gaat integraal
  naar Claude. Bewuste keuze; respecteer ze strikt.
- **Lezen, niet beheren.** De digest zet geen markers: geen `synced`-categorie op mail,
  geen tags, geen verplaatsingen. Idempotentie komt van het venster plus *AL VASTGELEGD*.

## Bekende gaten

- **Teams-kanaalberichten** en meeting-transcripts — het Graph Explorer-token heeft
  `ChannelMessage.Read.All` noch `OnlineMeetingTranscript.Read.All`, en de tenant laat
  geen bijkomende consent toe.
- **Rocket.Chat-threadantwoorden** — `*.history` geeft de room-tijdlijn; antwoorden
  binnen een thread kunnen ontbreken. Niet geverifieerd.
- **GitLab** (`git.omgeving.vlaanderen.be`) — MR-discussies en reviews. Deels zichtbaar
  via Jira: GitLab-commits en merge requests komen als `RemoteIssueLink` in de
  issue-historiek. Volledig dekken vraagt een GitLab-PAT.
- **M365 Copilot-conversaties**, andere browsers dan Chrome-profiel *Default*, en
  Claude-sessies op andere machines.
- Alles wat mondeling gebeurde.
