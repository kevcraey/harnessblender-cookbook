---
name: verwerk-meeting
description: |
  Verwerk een .whisper meeting-transcript tot een uitgebreid verslag in de vault
  en een korte samenvatting in de daily note. Gebruik bij: transcript verwerken,
  meeting verwerken, whisper verwerken, vergadering uitwerken.
---

# Meeting-verwerker

Verwerk een opgenomen meeting (`.whisper`-bestand) tot een verslag in de vault en een korte samenvatting in de daily note. Werk autonoom waar de match eenduidig is; verduidelijk waar niet (zie stap 3).

## Configuratie

```
config.vault: "~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain"
config.transcripts_inbox: "~/Documents"
```

Alle andere paden (journal/daily notes, areas, people, templates, archief) **niet hardcoden**: lees ze bij elke run uit `${config.vault}/README.md`. Verandert de vault-indeling, dan verandert deze skill niet mee.

## Stap 1: Intake

- Geen argument → vandaag (`date +%Y-%m-%d`).
- Datum meegegeven → die datum.
- Transcript-pad meegegeven → verwerk specifiek dat bestand.
- Zoek `.whisper`-bestanden: `ls ~/Documents/*.whisper`, filter op datum indien opgegeven.
- Niets gevonden → geen blocker: ga verder zonder transcript, via de ondervraging in 4a. Stap 2 (matchen) vervalt dan grotendeels — vraag als onderdeel van diezelfde ondervraging welke meeting het betreft (bestaande open header, of nieuw).

## Stap 2: Matchen met daily note

Open de daily note (pad via README) en zoek `##`-headers zonder `Verslag: [[...]]`-link eronder.

- Eén transcript, één open header → koppel autonoom.
- Eén transcript, geen header → analyseer transcript-inhoud, match met bestaande project-MOC's, doe een voorstel, verduidelijk (stap 3).
- Meerdere transcripts en/of headers → toon de opties, verduidelijk (stap 3).
- Niets in de daily note → raadpleeg de agenda (screenshot, of browser naar Teams/Outlook indien beschikbaar) enkel als extra bron; niets beschikbaar → ga verder zonder.

## Stap 3: Verduidelijken

Wanneer een keuze niet eenduidig is (matching, ontbrekende header, twijfel over aanwezigen, welke acties concreet genoeg zijn, ...): zoek verduidelijking bij de gebruiker. Gebruik daarvoor het formaat dat de gebruiker typisch gebruikt (grilling, brainstorm, pick-brain, ...). Zoek in recente sessies naar kandidaten of vraag het.

De bevestigingsmomenten zelf blijven wel verplicht: nooit een ambigue match doorvoeren, nooit een taak aanmaken zonder akkoord. Enkel de vorm van het vragen is vrij.

## Stap 4: Per meeting verwerken

### 4a. Input verkrijgen

**Er is een `.whisper`-bestand**: parseer het. Dit is een ZIP met `metadata.json`. Extraheer en zet om naar leesbare tekst met sprekerslabels en tijdstempels:

```bash
python3 -c "
import zipfile, json, sys

def ms_to_time(ms):
    s = ms // 1000
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f'{h:02d}:{m:02d}:{s:02d}'

with zipfile.ZipFile(sys.argv[1], 'r') as z:
    with z.open('metadata.json') as f:
        data = json.load(f)

prev_speaker = None
for seg in data.get('transcripts', []):
    text = seg.get('text', '').strip()
    if not text:
        continue
    speaker = seg.get('speaker', {}).get('name', 'Unknown')
    if speaker in ('Microphone', 'Kenzo'):
        speaker = 'Kenzo'
    start = ms_to_time(seg.get('start', 0))
    if speaker != prev_speaker:
        print(f'\n[{start}] **{speaker}**:')
        prev_speaker = speaker
    print(text)
" "/pad/naar/bestand.whisper"
```

> [!WARNING]
> `metadata.json` kan enorm groot zijn (200k+ tokens) — dump nooit de ruwe JSON, gebruik enkel dit extractiescript.

Sprekerslabels: enkel "Kenzo" (microfoonkanaal) is betrouwbaar; overige sprekers komen uit één gedeelde Teams-audiostream — diarisatie is best-effort. Ken nooit een uitspraak toe aan een specifieke naam enkel op basis van het sprekerslabel.

**Er is geen `.whisper`-bestand**: geen blocker, geen reden om te stoppen. Ondervraag de gebruiker rechtstreeks om tot de essentie van de meeting te komen — welke meeting, doel/aanleiding, aanwezigen, belangrijkste besproken punten, beslissingen, acties, openstaande vragen. Gebruik dezelfde verduidelijkings-aanpak als stap 3. Het resultaat vervangt de geparste transcript als basis voor 4b-4h; stappen 4e en 4f (transcript archiveren, origineel opruimen) vervallen dan vanzelf — er is niets om te archiveren of op te ruimen.

### 4b. Aanwezigen bepalen

Combineer, in volgorde: daily-note-header (`Aanwezigen:` met wikilinks) → Teams-agenda → transcript-analyse (begroetingen, genoemde namen) → people-index (`ls <people-map>/` voor correcte spelling). Bij twijfel: verduidelijk (stap 3). Resultaat: lijst `[[Persoon]]`-wikilinks.

### 4c. Gronden

Zoek relevante bestaande vault-notities op (personen, project-MOC, eerdere verslagen) voor twee doelen: transcriptiefouten herkennen en corrigeren (bv. "VMM" dat als "veemen" getranscribeerd wordt), en context om de samenvatting inhoudelijk correct te maken.

### 4d. Verslag schrijven

Bepaal via README de templates-map en zoek daarin het meeting-note-template (bestandsnaam bevat "meeting"). Geen template gevonden → stop, meld dit expliciet — verzin zelf geen frontmatter.

Vul het template aan tot deze structuur:

```markdown
# {Korte titel}

{Doel & korte samenvatting — kale paragraaf, één à twee zinnen, geen kopje}

## Aanwezigen
- [[Persoon 1]]

## Aanleiding overleg
{...}

## Verloop
### {Topic 1 — afgeleid uit de inhoud}
{...}

## Beslissingen
- {...}

## Actiepunten
- {wie, wat, wanneer indien gekend}

## Risico's & openstaande vragen
- {...}

## Aanbevolen vervolgstap
{...}

Ruwe transcript: [[YYYY-MM-DD-korte-beschrijving-transcript]]
```

De kale paragraaf vlak onder de H1 (in plaats van meteen `## Aanwezigen`) is bewust: de project-MOC pikt die op als summary in zijn "Meetings"-overzicht.

Frontmatter: `is-part-of` naar de project-MOC als de meeting daaraan hangt (anders die regel weglaten), `related-to` met de aanwezigen-links (+ vorig overleg indien te vinden), `tags: [type/meeting]`, het datumveld op de echte datum — dat sorteert de MOC's meetingslijst. Placeholder-regels die niet van toepassing zijn: weglaten, niet laten staan.

Stijl: topic-based, niet speaker-based. Voor eigen consumptie — schrijf als eigen notities, interne bedenkingen/twijfels mogen erin. Nederlands, Vlaams register. Geen AI-stijl: geen overmatige bullets/vetgedrukt, geen "samenvattend"/"concluderend"-taalgebruik. Attributie aan een naam enkel als dat expliciet uit de inhoud blijkt.

Bestandsnaam: `YYYY-MM-DD-korte-beschrijving.md`, in de areas-map (via README).

### 4e. Transcript archiveren

Schrijf de ruwe transcript-tekst uit 4a weg als `YYYY-MM-DD-korte-beschrijving-transcript.md` in de archief-map (via README). Geen `type/meeting`-tag, geen MOC-link — anders duikt hij zelf op als tweede "meeting" in de MOC-dataview.

Dit wijkt bewust af van de vault-conventie dat skills niet naar het archief schrijven: uitzondering, enkel voor deze rauwe transcripten.

### 4f. Origineel opruimen

Pas nadat 4d en 4e allebei geslaagd zijn (beide bestanden bestaan en zijn niet leeg): verwijder het originele `.whisper`-bestand.

```bash
test -s "<pad verslag>" && test -s "<pad transcript-note>" && rm -- "<pad naar het .whisper-bestand>"
```

Exact pad, geen glob. Faalt een van beide checks: origineel laten staan, meld het probleem.

### 4g. Daily note bijwerken

Vervang de inhoud onder de gekoppelde `##`-header (tot de volgende header of `## Logs`) door, in deze strikte volgorde:

```markdown
{Oneliner — zelfstandig leesbaar, zonder de rest}
- [[Aanwezige 1]]
- [[Aanwezige 2]]
{Hele korte samenvatting, hooguit enkele zinnen}
Verslag: [[YYYY-MM-DD-korte-beschrijving]]
```

De oneliner moet letterlijk de eerste regel zijn: de project-MOC-dataview pikt de eerste niet-lege regel na de header op als "recent activity".

Bestond de header nog niet en is het voorstel (stap 2) goedgekeurd: voeg de nieuwe `##`-header toe boven `## Logs`. Hangt de meeting aan een project, dan moet die header de project-MOC als `[[wikilink]]` bevatten — daarop matcht de dataview.

### 4h. Opvolgacties voorstellen

Overloop de actiepunten uit het verslag; filter op acties met een concrete eigenaar/deadline of duidelijke opvolging (geen louter informatieve punten, geen acties die al als taak bestaan). Stel via een klikbare multi-select (nu beschikbaar als `AskUserQuestion` met multiSelect) voor welke als vault-taak (`- [ ] ...`) aangemaakt worden, met voorgestelde locatie en `due::`-datum. Meer dan 4 kandidaten: groepeer in blokken van 4. Maak enkel aan na akkoord.

Doe dit per meeting, ná 4a-4g voor die meeting — niet gebundeld op het einde. Stopt de sessie halverwege een multi-select, dan is de meeting zelf (verslag, transcript, daily note) al volledig verwerkt.

## Stap 5: Afsluiting

Kort overzicht per meeting: link naar verslag, link naar transcript-archief, daily note bijgewerkt (ja/nee), aantal voorgestelde/aangemaakte taken.

## Beperkingen

- Nooit rode `[[wikilinks]]` — enkel linken naar bestaande notes.
- Nederlands.
- Origineel `.whisper` alleen verwijderen ná de checks in 4f.
