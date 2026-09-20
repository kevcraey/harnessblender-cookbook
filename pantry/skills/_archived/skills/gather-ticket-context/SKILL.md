---
name: gather-ticket-context
description: Verzamel alle relevante context voor een bepaald Jira ticket. Dit omvat ticketdetails (beschrijving, commentaar) en gerelateerde bestanden in de codebase.
context:fork
---

# Gather Ticket Context

Verzamel context voor een Jira ticket zodat andere skills (zoals `write-user-story` of `refine-user-story`) hiermee aan de slag kunnen.

## Workflow

### 1. Ticket Informatie Ophalen

- Gebruik de Atlassian MCP server om het Jira ticket op te halen.
- Haal op: Beschrijving, Samenvatting, Commentaren, Subtaken.
- *Tip*: Let op eventuele links naar andere tickets of Confluence pagina's in de beschrijving.

### 2. Gerelateerde Bestanden Zoeken

- Zoek naar bestanden die de ticket-key in hun bestandsnaam of inhoud hebben. Bijvoorbeeld: `PASCAL-123-feature.md`, `20260101-PASCAL-123-user-story.md`, `PASCAL-123-user-story.md`, `foo-PASCAL-123-bar.md`, ...

### 3. Gerelateerde Code Zoeken (optioneel)

Vraag aan de gebruiker of er in de codebases moet gezocht worden naar bestaande en gerelateerde functionaliteiten.

- Leidt af welke codebases relevant zijn voor de ticket.
- Zoek naar commits en branches die de ticket-key bevatten.
- Vat samen.

### 4. Reeds geimplementeerde functionaliteit

Vraag aan de gebruiker of er ook moet gezocht worden naar reeds geimplementeerde functionaliteit van het ticket.

- Leidt af welke codebases relevant zijn voor de ticket.
- Zoek naar commits en branches die de ticket-key bevatten.
- Vat samen.

### 5. Context Samenstellen

- Presenteer de verzamelde informatie in `tmp/{YYYY-MM-DD}-{ticketnummer}-context.md`.
