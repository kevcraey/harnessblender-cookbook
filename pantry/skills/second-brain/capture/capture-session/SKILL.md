---
name: capture-session
description: |
  Haal de bewaarwaardige kennis uit de HUIDIGE Claude-sessie en push ze als
  atomaire thoughts naar Open Brain. Claude oordeelt (geen smart-ingest, geen
  transcript-dump); voorstel + bevestiging in bulk, dan pas capturen. On-demand,
  aan het eind van een zinvolle sessie. Zusje van capture-vault (bron = vault-diff).
---

# Capture Session

Zusje van `capture-vault`, maar de bron is **deze conversatie zelf** — niet de
vault-diff. Geen script, geen hook, geen file parsen: alles staat al in de
context. Enkel `capture_thought` / `search_thoughts` (Open Brain MCP).

Doel: wat je deze sessie neerschreef of besliste en later wil terugvinden, in
Open Brain krijgen — **zonder** pay-per-token smart-ingest. Claude doet het
oordeel; Open Brain is domme opslag.

## Stappen

1. **Oordelen & extraheren.** Loop deze conversatie door en haal er de
   zelfstandige, bewaarwaardige feiten uit als atomaire thoughts (beslissing,
   inzicht, referentie, persoon, observatie). Eén thought = één zelfstandige,
   herbruikbare uitspraak, los leesbaar zonder de sessie erbij.

   Laat vallen:
   - de mechaniek van de sessie zelf (debuggen, tool-gedoe, wat-werkt-niet)
   - vluchtige status/voortgang
   - wat de repo/git/vault al vastlegt
   - wat je deze sessie al live liet capturen ("voor brein: …")

2. **Dedup tegen het brein.** Roep vóór het voorstellen voor elke kandidaat
   `search_thoughts` aan. Al gekend / semantisch dubbel → weg uit het voorstel.
   Zonder dedup stel je bij elke run dezelfde feiten opnieuw voor.

3. **Voorstellen.** Toon één genummerde lijst, gegroepeerd per type. Verwijs naar
   vault-notes met **vault-relatieve paden**, nooit `[[wikilinks]]` (niet klikbaar
   in de terminal). Wacht op akkoord. Kenzo beslist in bulk ("alles", of "alles
   behalve 3, 7").

4. **Pushen.** Push de goedgekeurde kandidaten via `capture_thought`.

## Grens: compaction

De sessie leeft in de context. Is de conversatie **gecompacteerd**, dan zie je de
vroege beurten enkel als samenvatting, niet woordelijk — de oudste sessie-kennis
kan dan wegvallen. Draai deze skill dus liefst vóór een compaction, of weet dat
gecompacteerde inhoud enkel samengevat wordt meegenomen.

## Regels

- **Voorstel eerst, push pas na akkoord** — nooit capturen wat daarna nog
  gereviewd moet worden.
- Bron is de conversatie, niet de vault: deze skill raakt geen vault-bestanden
  aan en schrijft enkel naar Open Brain. Geen git, geen marker.
- Terminal-output verwijst naar notes met vault-relatieve paden, nooit wikilinks.
