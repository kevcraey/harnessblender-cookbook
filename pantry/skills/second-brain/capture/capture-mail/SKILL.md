---
name: capture-mail
description: |
  Haal de bewaarwaardige kennis uit mail en push ze als atomaire thoughts naar
  Open Brain. Twee bronnen: persoonlijke Gmail (read-only, window + dedup) en de
  DOMG-werkmailbox via Microsoft Graph (on-demand token; opt-out — alle werk-mail
  behalve ICR2/ICR3/ICR4 en prullenbak). Claude oordeelt; geen smart-ingest, geen
  cron. Voorstel +
  bevestiging in bulk, dan pas capturen.
---

# Capture Mail

Derde zusje van `capture-vault` en `capture-session`. Bron = mail. Twee bronnen
met een **gedeelde kern** (oordeel → dedup → voorstel → capture); enkel het
verzamelen en de marker verschillen per bron. Claude doet het oordeel, Open Brain
is domme opslag; geen pay-per-token smart-ingest.

Zonder argument → **Gmail** (bron A). Argument **`werk`** → **Graph** (bron B).

## Bronnen

### A. Persoonlijke Gmail — read-only

Connector (`kenzo.van.craeynest@gmail.com`) is **read-only** geautoriseerd: geen
labels, nooit verwijderen/verplaatsen/beantwoorden. Geen server-side marker dus.
Idempotentie leunt op **rolling window** (`newer_than:30d`) + **brein-dedup**
(stap 3). Een herhaalrun binnen het venster stelt geskipte mail opnieuw voor — de
dedup stopt dubbele *captures*, niet de her-review. Voor on-demand laag-frequent
gebruik oké. `backfill <YYYY/MM/DD>` → `newer_than:30d` wordt `after:<datum>`.

De Gmail-query is de deterministische voorfilter (ruis serverside weg):

```
newer_than:30d {in:inbox in:sent} -category:promotions -category:social -category:forums -category:updates -from:noreply -from:no-reply
```

### B. DOMG-werkmailbox — Microsoft Graph, on-demand token

De `vlaanderen.be`-tenant blokkeert publieke clients (device-code faalt met
"user assignment required"). Een **Graph Explorer access-token** werkt wél: het
draait op Graph Explorers eigen toegelaten app. Manuele brug, geen staande
automatie — token leeft kort en heeft geen refresh, dus per run opnieuw.

**Token via clipboard.** Kenzo kopieert een vers token (Graph Explorer →
*Access token*-tab) naar het **clipboard** — dat is de hele input. De skill leest
het zelf met `pbpaste` naar een tijdelijk scratch-bestand, strip whitespace, en
gebruikt het van daaruit. **Toon het token nooit** (het is breed geprivilegieerd),
gebruik het **enkel** voor mail-lezen + de categorie-marker, en **wis het
scratch-bestand na de run**. Nooit iets anders met het token doen. Faalt een call
met 401 → token verlopen; vraag een vers token (opnieuw kopiëren).

**Selectie = opt-out.** Verwerk **alle** in- en uitgaande werk-mail binnen het
venster, **behalve**:
- categorie `ICR2`, `ICR3` of `ICR4` — ICR2 = EU-only → blijft thuis; ICR3/4 = nooit;
- mail in de prullenbak (`DeletedItems`);
- mail die al `synced` draagt (reeds verwerkt).

Ongetagd en `ICR1` gaan **default-in**. Dit leunt op de discipline dat àlles
gevoeligs al `ICR2/3/4` draagt vóór een run — een vergeten tag = inhoud die tóch
naar Claude gaat (fail-open). Dat is een bewuste keuze; respecteer 'm strikt.

**Venster.** Heel de mailbox is te veel; bound met een rolling window op
`receivedDateTime` (default laatste **30 dagen**) + de `synced`-marker voor
incrementaliteit. Backfill = vroegere `after`-datum als argument. Query **per
folder** (inbox + sentitems → prullenbak valt vanzelf weg); pas de exclusies
**client-side** toe (robuuster dan Graph `not/any`-filters):

```
GET https://graph.microsoft.com/v1.0/me/mailFolders/{inbox|sentitems}/messages
    ?$filter=receivedDateTime ge <cutoff>
    &$select=id,subject,from,receivedDateTime,categories,conversationId
    &$orderby=receivedDateTime desc &$top=50   (Authorization: Bearer <token>)
```

Filter daarna weg: categorie ∈ {`ICR2`,`ICR3`,`ICR4`} of `synced` aanwezig.

**Marker.** Categorie `synced` markeert verwerkt. Herverwerken bij nieuwe info in
een thread → Kenzo haalt `synced` eraf → hij komt terug. Categorieën zitten op
**berichten**, niet op de conversatie — een nieuwe reply draagt de tag niet
automatisch.

## Stappen

1. **Verzamelen.**
   - **Gmail:** `search_threads` met de query hierboven. Max ~30 threads/run;
     meer → meld en laat de rest voor later.
   - **Graph:** haal inbox + sentitems op binnen het venster (zie bron B); filter
     client-side de exclusies weg (categorie ICR2/3/4, `synced`; prullenbak valt
     via de folder-keuze weg). Max ~30 threads/run; meer → meld en laat de rest
     voor later. Voor context mag je de conversatie ophalen (`conversationId`).
   - Niets te verwerken → "geen nieuwe mail-kennis"; **stop hier**.

2. **Oordelen & extraheren.** Haal de volledige inhoud op en trek er de
   zelfstandige, bewaarwaardige feiten uit als atomaire thoughts (beslissing,
   afspraak/commitment, deadline, persoon-feit, referentie). Eén thought = één los
   leesbare uitspraak. Laat vallen: pure logistiek, bevestigingen, bonnen/tickets,
   nieuwsbrieven die door de filter glipten, vluchtige status/beleefdheden, en wat
   de vault/repo al vastlegt of wat al live gecaptured is.

3. **Dedup tegen het brein.** Roep vóór het voorstellen voor elke kandidaat
   `search_thoughts` aan. Al gekend / semantisch dubbel → weg uit het voorstel.

4. **Voorstellen.** Eén genummerde lijst, gegroepeerd per type, met per kandidaat
   de **bron** (afzender + onderwerp + datum). Wacht op akkoord. Kenzo beslist in
   bulk ("alles", of "alles behalve 3, 7").

5. **Pushen + marker.** Push de goedgekeurde kandidaten via `capture_thought`.
   Dan de marker:
   - **Gmail:** geen marker (read-only) → volgende run leunt op window + dedup.
   - **Graph:** voeg categorie **`synced`** toe aan **alle verwerkte berichten**
     — captured én na-review-geskipt — met bestaande categorieën behouden:

     ```
     PATCH https://graph.microsoft.com/v1.0/me/messages/<id>
     {"categories": [<bestaande...>, "synced"]}
     ```

     Captured én skipped markeren, anders duikt een bewust-geskipte mail elke run
     opnieuw op. Doe dit als laatste, ná de push. Wis daarna het token-bestand.

## Grenzen & residency

- **Residency.** Werk-mail-thoughts landen in de hosted Supabase-instance. Check
  de **regio** (Supabase dashboard → Project Settings) tegen de ICR-eis vóór er
  werk-mail-thoughts gecaptured worden. De opt-out sluit `ICR2` (EU-only) uit, maar
  `ICR1` + ongetagd gaan naar Claude (Anthropic, US default) — laat enkel passeren
  wat die verwerking mag ondergaan. Nooit omzeilen via forwarding overheidsmail.
- **Gmail-corpus** is grotendeels privé (vakantie, bonnen) → dunne, ruizige oogst.

## Regels

- **Voorstel eerst, push pas na akkoord** — nooit capturen wat daarna nog
  gereviewd moet worden.
- **Mutaties:** Gmail nooit. Graph enkel de `synced`-categorie als marker — nooit
  mail verwijderen, verplaatsen of beantwoorden. Het Graph-token nooit tonen en na
  de run wissen.
- Bron-referenties in de terminal: afzender + onderwerp + datum.
