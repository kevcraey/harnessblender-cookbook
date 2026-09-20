---
name: onthouden
description: |
  Haal bewaarwaardige kennis (beslissingen met argument, cijfers, deadlines,
  persoon-feiten, referenties) uit de verzamelde dag — mail, Teams, Rocket.Chat,
  vault-diff, Jira/Confluence, Claude-sessies — of uit deze conversatie, dedup ze
  tegen Open Brain, stel een lijst voor en push na akkoord; markeer verwerkte mail
  met `synced`. Gebruik bij: onthou dit, help mij onthouden, noteer in brain/brein,
  naar open brain, capture, kennis bewaren, sessie capturen. Onderdeel van de
  ochtend-/avondroutine; los aanroepbaar.
---

# Onthouden

Vault: `~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain`
Kern: lees `../routine-core/SKILL.md`. `S` = `../routine-core/scripts`.

Opvolger van capture-mail, capture-vault en capture-session in één. Claude oordeelt, Open Brain is domme opslag (`search_thoughts`, `capture_thought` via de Open Brain MCP). Geen smart-ingest.

## Bron

- **Met run-map** (argument of `$ROUTINE_RUN_DIR`): per dag in `days/<dag>/` lees `graph.md` (mail zonder `[synced]`, Teams), `rocketchat.md`, `vault.md`, `atlassian.md`, `claude.md`. Niet `chrome.md` (browsegeschiedenis is geen kennis) en niet `notes.md` (de digest verwerkt dat al).
- **Zonder run-map**: de bron is **deze conversatie**. Loop ze door zoals vroeger capture-session: wat hier neergeschreven of beslist is en later terug te vinden moet zijn. Gecompacteerde beurten zie je enkel als samenvatting — zeg dat als het relevant is.

## Stappen

1. **Extraheer** atomaire thoughts: één thought = één zelfstandige, herbruikbare uitspraak, los leesbaar zonder de bron erbij. Datum en namen in de tekst zelf ("Op 2026-09-09 besliste Steven De Bock dat …"). Laat vallen: logistiek, bevestigingen, bonnen/tickets, nieuwsbrieven, vluchtige status, sessiemechaniek (debuggen, tool-gedoe), en wat vault of git al vastlegt.
2. **Dedup**: voor elke kandidaat `search_thoughts`. Al gekend of semantisch dubbel → weg. Zonder dedup stel je elke run dezelfde feiten voor.
3. **Voorstel** naar `<run>/onthouden.md` én in de terminal: één genummerde lijst, gegroepeerd per type (beslissing, inzicht, cijfer/deadline, persoon, referentie), per kandidaat de **bron** (afzender + onderwerp + datum; kanaal + datum; vault-relatief pad — geen wikilinks, niet klikbaar). Gevoelig of twijfelachtig (privé, HR, persoonlijke omstandigheden van collega's) → niet voorstellen, wel melden dat je het liet liggen.
4. **Wacht op akkoord.** Bulk: "alles", "alles behalve 3, 7", of Kenzo bewerkt het bestand.
5. **Push** de goedgekeurde via `capture_thought`. Bij een tijdelijke fout: dezelfde call één keer herhalen.
6. **Marker**: `S/mail_sync.py --from-md days/<dag>/graph.md` voor elke dag — zet `synced` op **alle** verwerkte mail, gecaptured én geskipt, anders duikt bewust-geskipte mail elke run opnieuw op. Herverwerken kan door in Outlook `synced` weg te halen. Dit is de enige Graph-mutatie.
7. **Rapport** als laatste stap naar `<run>/onthouden.done.md`: aantal gepusht, aantal geskipt, aantal mails gemarkeerd, wat je om gevoeligheidsredenen liet liggen (categorie).

## Grenzen

- **Residency**: werkmail-thoughts landen in de hosted Open Brain. `ICR2/3/4` zit er nooit in (collector filtert); ongetagd en `ICR1` gaan default mee. Laat enkel passeren wat die verwerking mag ondergaan.
- Deze skill raakt **geen vault-bestanden** aan en zet geen git-markers; de state van de routine is de dagmap.
- Voorstel eerst, push na akkoord — nooit capturen wat daarna nog gereviewd moet worden.
