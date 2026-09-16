# Fixtures

Echte, ingekorte data zonder gevoelige inhoud. Geen netwerk in tests.

| bestand | bron | gebruikt door |
|---|---|---|
| `conf-details-productfiche.xml` | storage-body van pagina 470876655 (zes `details`-blokken in layout-cellen) | WP-A parser |
| `conf-detailssummary.xml` | een `[AI-xx] Beslissingen`-pagina (detailssummary-macro) | WP-A renderer |
| `conf-minispace-template.xml` | pagina 411959720 | WP-A upsert (blok invoegen in bestaande body) |
| `jira-search-initiatives.json` | `/rest/api/2/search` project AI: vijf initiatieven mét hun subtree (epics, stories, subtask, één cross-project kind), ingekort en geanonimiseerd | WP-B, WP-D |
| `jira-changelog-initiatives.json` | changelog per issue (enkel de items `status`, `resolution`, `Link`) | WP-B changes |
| `jira-worklog-*.json` | worklogs van één issue | WP-B hours |
| `register-sample.json` · `initiatives-sample.json` | handgemaakt volgens DESIGN.md §6 | WP-D rules/proposal |
