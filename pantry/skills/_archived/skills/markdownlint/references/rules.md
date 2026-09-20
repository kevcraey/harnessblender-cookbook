# Richtlijnen voor Markdownstijl en lintregels

Bij het genereren van Markdown moet strikt worden voldaan aan onderstaande `markdownlint`-regels zodat de inhoud geldig, schoon en goed te parsen is.

## 1. Koppen (structuur)

- **MD001 / Heading levels**: Kopniveaus mogen slechts één stap verhogen (bijvoorbeeld van h1 naar h2, niet van h1 naar h3).
- **MD003 / Heading style**: Gebruik altijd ATX-stijl (`#`-tekens) voor koppen. Gebruik geen Setext-stijl (onderlijning).
- **MD025 / Single H1**: Het document bevat exact één H1-kop, als hoofdtitel helemaal bovenaan.
- **MD018 / Space after hash**: Plaats altijd een spatie tussen `#` en de koptekst (bijvoorbeeld `# Titel`, niet `#Titel`).

## 2. Lijsten (ongeordend en geordend)

- **MD004 / Unordered list style**: Gebruik één marker voor ongeordende lijsten, gebruik enkel een liggend streepje (`-`). Meng nooit verschillende markers in dezelfde lijst.
- **MD007 / List indentation**: Geneste lijsten worden met 2 spaties ingesprongen.
- **MD030 / Spaces after list markers**: Zorg voor precies één spatie na het lijstteken.
- **MD032 / Lists and code**: Als een lijstitem een codeblok bevat, zorg dan voor de juiste inspringing zodat het blok bij het item hoort.

## 3. Codeblokken

- **MD031 / Fenced code blocks**: Afgebakende codeblokken worden omringd door lege regels (één ervoor en één erna).
- **MD040 / Language specification**: Afgebakende codeblokken geven altijd een taalidentifier op (bijvoorbeeld `python`, `bash`, `text`) voor syntax highlighting.
- **MD046 / Code block style**: Gebruik altijd afgebakende codeblokken (drievoudige backticks ```), nooit ingesprongen codeblokken.

## 4. Witruimte en opmaak

- **MD009 / Trailing spaces**: Geen spaties aan het einde van regels.
- **MD010 / Hard tabs**: Gebruik spaties voor inspringing, geen tabs.
- **MD012 / Multiple blank lines**: Vermijd opeenvolgende lege regels. Gebruik één lege regel om paragrafen te scheiden.
- **MD022 / Headings spacing**: Koppen worden omringd door lege regels (één ervoor, één erna).
- **MD039 / Spaces inside links**: Plaats geen spaties binnen de linktekst (bijvoorbeeld `[ Text ]` is fout, `[Text]` is correct).

## 5. Ruwe HTML

- **MD033 / Inline HTML**: Vermijd ruwe HTML-tags (zoals `<br>`, `<div>`) tenzij onmisbaar voor opmaak die Markdown niet ondersteunt. Gebruik standaard Markdown-syntaxis.

## 6. Tabellen

- **MD060 / Table Column Style**: Gebruik altijd de style 'aligned' voor tabellen.
