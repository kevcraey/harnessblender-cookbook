"""Confluence-kant: registerpagina's lezen, details-blok parsen en renderen, pagina's aanmaken of
bijwerken. Contract: DESIGN.md §3 en §6 (register.json).

Storage-XML wordt als tekst behandeld, nooit door een XML-parser: de `ac:`- en `ri:`-prefixen zijn
niet gedeclareerd en elke parser herschrijft attribuutvolgorde, entities en `<br />`. Alleen
tekst-splicing houdt de rest van de body byte-gelijk (acceptatie van upsert_details).

Alle macro-vormen komen uit echte pagina's op de instance (live opgehaald 2026-09-16), zie de
constanten hieronder. Geschreven wordt er enkel via http.writer(cfg, "confluence", <space>, apply);
zonder apply wordt de meegegeven leesclient gebruikt en enkel de payload + diff teruggegeven.
"""
from __future__ import annotations

import datetime as dt
import difflib
import html
import re

from aiec_lib import config
from aiec_lib import http
from aiec_lib import schema as sch

# --- macro-vormen (bron: echte pagina's, live gelezen 2026-09-16) ------------------------------
#
# details + id      bron: pagina 450265417 ("Project - 2026 - Hardware - Vervanging loadbalancers")
#                   <ac:structured-macro ac:name="details" ac:schema-version="1">
#                     <ac:parameter ac:name="id">infraprojecteigenschappen</ac:parameter> …
# detailssummary    bron: pagina 346424270 (zelfde id-waarde, rapporteert op die blokken) en
#                   pagina 505839625 ("[AI-49] Beslissingen"); schema-version 2 met firstcolumn,
#                   headings, sortBy, reverseSort, cql.
#                   Het "id"-filter is bevestigd in de Confluence DC 9.2-docs (Page Properties
#                   Report Macro, parameter "Page Properties ID": "Specify an ID to include only
#                   data from Page Properties macros with the same ID") én door dat levende paar.
# children          bron: pagina 470876484 (zonder parameters, self-closing) en 396689632 (met
#                   <ac:parameter ac:name="all">true</ac:parameter>); schema-version 2.
# jira              bron: pagina 411959720 (mini-space-template), incl. server + serverId.
#
# ac:macro-id wordt bij het renderen weggelaten: een willekeurige UUID maakt elke round-trip en
# elke diff onstabiel. Bij upsert blijft de macro-id van het bestaande blok behouden.
# ONGEVERIFIEERD: dat Confluence zelf een macro-id toekent bij het opslaan van een blok zonder
# ac:macro-id is niet getest — daarvoor is een write nodig (mode staat op dry-run).

MACRO_TAG_RE = re.compile(r"<(/?)ac:structured-macro\b([^>]*?)(/?)>")
OPEN_MACRO_RE = re.compile(r"<ac:structured-macro\b[^>]*>")
NAME_RE = re.compile(r'ac:name="([^"]*)"')
MACRO_ID_RE = re.compile(r'ac:macro-id="([^"]*)"')
ROW_RE = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.S)
CELL_RE = re.compile(r"<(th|td)\b[^>]*>(.*?)</\1>|<(th|td)\b[^>]*/>", re.S)
AI_KEY_RE = re.compile(r"(?<![A-Za-z])(AI-\d+)")
TAGS_BLOCK_RE = re.compile(r"<br\s*/?>|</(?:p|li|div|tr|h[1-6])>", re.I)


def esc(text: str) -> str:
    """Tekst in een cel of parameter. Attributen krijgen &quot; via quote=True."""
    return html.escape(str(text or ""), quote=False)


# --- storage-XML: blokken zoeken ---------------------------------------------------------------

def _macro_span(xml: str, start: int) -> tuple[int, int]:
    """(start, eind) van het structured-macro dat op `start` begint, nesting meegeteld."""
    depth = 0
    for m in MACRO_TAG_RE.finditer(xml, start):
        if m.group(1):                       # </ac:structured-macro>
            depth -= 1
            if depth == 0:
                return start, m.end()
        elif m.group(3):                     # <ac:structured-macro … />
            if m.start() == start:
                return start, m.end()
        else:
            depth += 1
    raise ValueError("niet-gesloten ac:structured-macro in de storage-body")


def _macro_head(block: str) -> str:
    """Het stuk vóór de rich-text-body: daar staan de eigen parameters, niet die van geneste macro's."""
    return block.split("<ac:rich-text-body", 1)[0]


def find_details_blocks(schema: dict, storage_xml: str, details_id: str | None = None) -> list[tuple[int, int]]:
    """Posities van alle details-blokken met id details_id (standaard schema['details_id']), zichtbaar en verborgen."""
    want = details_id or schema["details_id"]
    param = re.compile(r'<ac:parameter ac:name="id"\s*>\s*' + re.escape(want) + r'\s*</ac:parameter>')
    out = []
    for m in OPEN_MACRO_RE.finditer(storage_xml):
        name = NAME_RE.search(m.group(0))
        if not name or name.group(1) != "details":
            continue
        s, e = _macro_span(storage_xml, m.start())
        if param.search(_macro_head(storage_xml[s:e])):
            out.append((s, e))
    return out


def find_details_block(schema: dict, storage_xml: str) -> tuple[int, int] | None:
    """Positie van het eerste details-blok met id schema['details_id'], of None."""
    blocks = find_details_blocks(schema, storage_xml)
    return blocks[0] if blocks else None


HIDDEN_RE = re.compile(r'<ac:parameter ac:name="hidden"\s*>\s*true\s*</ac:parameter>')


def details_hidden(block: str) -> bool:
    """Is dit details-blok verborgen (parameter hidden=true)?"""
    return bool(HIDDEN_RE.search(_macro_head(block)))


def insert_position(storage_xml: str) -> int:
    """Waar een nieuw blok vooraan komt. Bij een layout-pagina in de eerste layout-cell, anders
    helemaal vooraan.
    # ONGEVERIFIEERD: het invoegen in een <ac:layout> is niet op een echte pagina opgeslagen."""
    if storage_xml.lstrip().startswith("<ac:layout"):
        m = re.search(r"<ac:layout-cell\b[^>]*>", storage_xml)
        if m:
            return m.end()
    return 0


def _cell_text(fragment: str) -> str:
    """Celtekst uit storage-XML: <br/> en blok-einden worden regeleinden (multi-velden splitsen
    daarop), de rest van de markup verdwijnt."""
    s = TAGS_BLOCK_RE.sub("\n", fragment)
    s = re.sub(r"<[^>]*>", "", s)
    s = html.unescape(s)
    lines = [re.sub(r"[ \t\xa0]+", " ", ln).strip() for ln in s.split("\n")]
    return "\n".join(ln for ln in lines if ln)


def _rows(block: str) -> list[tuple[str, str]]:
    """(labeltekst, ruwe cel-XML) per tabelrij van het blok."""
    out = []
    for r in ROW_RE.finditer(block):
        cells = [(m.group(2) if m.group(1) else "") for m in CELL_RE.finditer(r.group(1))]
        if len(cells) >= 2:
            out.append((_cell_text(cells[0]), cells[1]))
    return out


# --- parser en renderer -------------------------------------------------------------------------

def parse_properties(schema: dict, storage_xml: str, details_id: str) -> dict:
    """{rijlabel: celtekst} uit alle details-blokken met dit id; leeg als er geen is."""
    return {label: _cell_text(cell) for s, e in find_details_blocks(schema, storage_xml or "", details_id)
            for label, cell in _rows(storage_xml[s:e])}


def parse_details(schema: dict, storage_xml: str) -> tuple[dict | None, dict, list[str]]:
    """(values genormaliseerd | None als er geen blok is, raw {label: celtekst}, problems)."""
    spans = find_details_blocks(schema, storage_xml or "")
    if not spans:
        return None, {}, []
    rows = [row for s, e in spans for row in _rows(storage_xml[s:e])]
    raw, values, problems = {}, {}, []
    for label, cell in rows:
        text = _cell_text(cell)
        if label in raw:
            problems.append(f"label '{label}' staat meer dan eens in de kenmerkenblokken")
        raw[label] = text
        f = sch.field_by_label(schema, label)
        if f is None:
            problems.append(f"onbekend label '{label}' in het details-blok")
            continue
        values[f["key"]] = text
    vals, probs = sch.normalize_values(schema, values)
    return vals, raw, problems + probs


def details_macro(schema: dict, rows: str, macro_id: str | None = None, hidden: bool = False,
                  details_id: str | None = None) -> str:
    """Eén details-macro met id details_id (standaard schema['details_id']) rond de gegeven tabelrijen."""
    mid = f' ac:macro-id="{html.escape(macro_id, quote=True)}"' if macro_id else ""
    verborgen = '<ac:parameter ac:name="hidden">true</ac:parameter>' if hidden else ""
    return (f'<ac:structured-macro ac:name="details" ac:schema-version="1"{mid}>{verborgen}'
            f'<ac:parameter ac:name="id">{esc(details_id or schema["details_id"])}</ac:parameter>'
            f"<ac:rich-text-body><table><tbody>{rows}</tbody></table>"
            f"</ac:rich-text-body></ac:structured-macro>")


def _split_details(schema: dict, row, macro_id: str | None = None) -> str:
    """Zichtbaar blok met de gewone velden, daarna een verborgen blok voor velden met verborgen: true."""
    zichtbaar = "".join(row(f) for f in sch.fields(schema) if not f.get("verborgen"))
    verborgen = "".join(row(f) for f in sch.fields(schema) if f.get("verborgen"))
    return details_macro(schema, zichtbaar, macro_id) + (details_macro(schema, verborgen, hidden=True) if verborgen else "")


def render_details(schema: dict, values: dict, macro_id: str | None = None) -> str:
    """Kenmerkenblok(ken): één rij per veld in schema-volgorde. Round-trip met parse_details is identiek.
    macro_id geldt voor het zichtbare blok."""
    def row(f):
        return f"<tr><th>{esc(f['label'])}</th><td>{esc(sch.display_value(schema, f, values.get(f['key'], '')))}</td></tr>"
    return _split_details(schema, row, macro_id)


def _jira_macro(atlassian: dict, jql: str, kolommen: list[str] | None = None, maximum: int = 20) -> str:
    """Jira-macro zoals op pagina 411959720. Zonder serverId toont Confluence de macro niet; dan
    geven we een lege string terug en meldt de aanroeper het."""
    server, server_id = atlassian.get("jira_server"), atlassian.get("jira_server_id")
    if not server_id:
        return ""
    cols = kolommen or ["key", "summary", "status", "assignee", "updated"]
    # ONGEVERIFIEERD: columnIds voor standaardvelden (issuekey voor key, de rest gelijk aan de
    # kolomnaam); het voorbeeld op 411959720 gebruikt customfield-ids voor de custom kolommen.
    ids = ",".join("issuekey" if c == "key" else c for c in cols)
    return (f'<ac:structured-macro ac:name="jira" ac:schema-version="1">'
            f'<ac:parameter ac:name="server">{esc(server)}</ac:parameter>'
            f'<ac:parameter ac:name="columnIds">{esc(ids)}</ac:parameter>'
            f'<ac:parameter ac:name="columns">{esc(",".join(cols))}</ac:parameter>'
            f'<ac:parameter ac:name="maximumIssues">{maximum}</ac:parameter>'
            f'<ac:parameter ac:name="jqlQuery">{esc(jql)}</ac:parameter>'
            f'<ac:parameter ac:name="serverId">{esc(server_id)}</ac:parameter>'
            f"</ac:structured-macro>")


def _detailssummary_macro(cql: str, firstcolumn: str, headings: list[str], details_id: str | None = None,
                          sort_by: str | None = None) -> str:
    """Page Properties Report zoals op pagina 346424270 (met id) en 505839625 (zonder)."""
    parts = [f'<ac:parameter ac:name="firstcolumn">{esc(firstcolumn)}</ac:parameter>',
             f'<ac:parameter ac:name="headings">{esc(", ".join(headings))}</ac:parameter>']
    if details_id:
        parts.append(f'<ac:parameter ac:name="id">{esc(details_id)}</ac:parameter>')
    if sort_by:
        parts.append(f'<ac:parameter ac:name="sortBy">{esc(sort_by)}</ac:parameter>')
    parts.append(f'<ac:parameter ac:name="cql">{html.escape(cql, quote=True)}</ac:parameter>')
    return ('<ac:structured-macro ac:name="detailssummary" ac:schema-version="2">'
            + "".join(parts) + "</ac:structured-macro>")


def _artefacts_macro(schema: dict, exclude: list[str]) -> str:
    """Content by label: alleen pagina's met een gekend artefactlabel onder deze pagina, nieuwste titel eerst."""
    labels = ", ".join(f'"{l}"' for l in schema["artefact_labels"] if l not in exclude)
    cql = f"label in ({labels}) and space = currentSpace() and ancestor = currentContent()"
    params = {"cql": cql, "max": "100", "sort": "title", "reverse": "true", "showLabels": "true",
              "showSpace": "false", "excerptType": "none"}
    return ('<ac:structured-macro ac:name="contentbylabel" ac:schema-version="3">'
            + "".join(f'<ac:parameter ac:name="{k}">{html.escape(v, quote=True)}</ac:parameter>' for k, v in params.items())
            + "</ac:structured-macro>")


CHILDREN_MACRO = '<ac:structured-macro ac:name="children" ac:schema-version="2" />'


def _section_body(schema: dict, section: dict, values: dict, atlassian: dict, samenvatting: str) -> str:
    t = section["type"]
    if t == "tekst":
        return f"<p>{esc(samenvatting) if samenvatting else esc(section.get('placeholder', ''))}</p>"
    if t == "jira-issue":
        key = values.get("ai_key") or ""
        macro = _jira_macro(atlassian, f"key = {key} OR issue in linkedIssues({key})") if key else ""
        return f"<p>{macro}</p>" if macro else "<p>(Jira-macro ontbreekt: geen AI-key of geen serverId)</p>"
    if t == "children":
        return f"<p>{CHILDREN_MACRO}</p>"
    if t == "artefacten":
        return f"<p>{_artefacts_macro(schema, section.get('exclude', []))}</p>"
    if t == "detailssummary":
        label = section.get("label", "decisions")
        cql = f'label = "{label}" and space = currentSpace() and ancestor = currentContent()'
        return f'<p>{_detailssummary_macro(cql, "Beslissing", section.get("headings", ["Outcome", "Status"]))}</p>'
    raise ValueError(f"page_sections-type '{t}' onbekend")


def render_page(schema: dict, values: dict, samenvatting: str = "", cfg: dict | None = None) -> str:
    """Volledige initiatiefpagina: details-blok + de vaste kopjes uit het schema. cfg levert de
    applink van de Jira-macro; zonder cfg gelden de defaults uit config."""
    atlassian = (cfg or config.DEFAULTS)["atlassian"]
    out = []
    for s in schema["page_sections"]:
        if s["type"] == "details":
            if s.get("kop"):
                out.append(f"<h2>{esc(s['kop'])}</h2>")
            out.append(render_details(schema, values))
            continue
        out.append(f"<h2>{esc(s['kop'])}</h2>")
        out.append(_section_body(schema, s, values, atlassian, samenvatting))
    return "".join(out)


def _template_hint(schema: dict, f: dict) -> str:
    if f["type"] in ("enum", "multi"):
        keuze = " | ".join(f["values"])
        return f"({keuze})" if f["type"] == "enum" else f"(komma-gescheiden: {keuze})"
    if f["type"] == "pijler":
        return "(" + " | ".join(f"{p['code']} — {p['naam']}" for p in schema["pijlers"]) + ")"
    return f"({f.get('hint') or f.get('pattern') or 'tekst'})"


def render_template(schema: dict, cfg: dict | None = None) -> str:
    """Sjabloonpagina: instructie-macro, leeg details-blok met de keuzes per veld, de vaste kopjes."""
    # info-macro: zelfde vorm als de warning-macro op pagina 470876655 (enkel een rich-text-body)
    info = ('<ac:structured-macro ac:name="info" ac:schema-version="1"><ac:rich-text-body>'
            "<p>Kopieer deze pagina voor een nieuw AI-initiatief. Titel: "
            f"<code>{esc(schema['page_title'])}</code>. Vervang de tekst tussen haakjes door de "
            f"waarde, voeg het label <code>{esc(schema['label'])}</code> toe en laat de kopjes en het "
            "eigenschappenblok in deze volgorde staan. Status staat nooit in het blok: die komt live "
            "uit Jira.</p></ac:rich-text-body></ac:structured-macro>")
    block = _split_details(schema, lambda f: f"<tr><th>{esc(f['label'])}</th><td>{esc(_template_hint(schema, f))}</td></tr>")
    out = [info]
    atlassian = (cfg or config.DEFAULTS)["atlassian"]
    for s in schema["page_sections"]:
        if s["type"] == "details":
            if s.get("kop"):
                out.append(f"<h2>{esc(s['kop'])}</h2>")
            out.append(block)
            continue
        out.append(f"<h2>{esc(s['kop'])}</h2>")
        if s["type"] == "jira-issue":
            # sjabloon: nog geen key, dus een leesbare plaatshouder in plaats van de macro
            out.append("<p>(Jira-macro op de AI-key; wordt gezet door <code>aiec.py "
                       "conf create-initiative</code>.)</p>")
        else:
            out.append(_section_body(schema, s, {}, atlassian, ""))
    return "".join(out)


def render_overview(schema: dict, cfg: dict, jira_server: dict | None = None) -> str:
    """Overzichtspagina: één detailssummary over alle initiatiefpagina's met Pijler als kolom en
    sorteersleutel, plus één Jira-macro voor live status.

    Afwijking van DESIGN.md §3 ("per pijler een detailssummary"): Page Properties Report kan niet
    op een celwaarde filteren (cql zoekt op pagina's, niet op rijen). Eén rapport, gesorteerd op
    Pijler, geeft dezelfde groepering."""
    ov = schema["overzicht"]
    atlassian = dict(cfg["atlassian"])
    if jira_server:
        atlassian.update({"jira_server": jira_server.get("server"), "jira_server_id": jira_server.get("serverId")})
    pijler_label = sch.field(schema, "pijler")["label"]
    headings = [pijler_label] + [sch.field(schema, k)["label"] for k in ov["kolommen"]]
    cql = f'label = "{schema["label"]}" and space = currentSpace()'
    summary = _detailssummary_macro(cql, "Initiatief", headings, details_id=schema["details_id"],
                                    sort_by=pijler_label)
    jira = _jira_macro(atlassian, ov["jira_jql"], ov.get("jira_kolommen"), maximum=500)
    out = [f"<h2>Eigenschappen</h2><p>{summary}</p>", "<h2>Status in Jira</h2>"]
    out.append(f"<p>{jira}</p>" if jira else "<p>(Jira-macro weggelaten: geen serverId in de config.)</p>")
    return "".join(out)


# --- lezen ---------------------------------------------------------------------------------------

def _key_of(title: str) -> str:
    """AI-key uit een paginatitel ('[AI-25] …' of 'AI-8: …'), anders ''."""
    m = AI_KEY_RE.search(title or "")
    return m.group(1) if m else ""


def _url(cfg: dict, page_id: str) -> str:
    return f"{cfg['atlassian']['confluence_url'].rstrip('/')}/pages/viewpage.action?pageId={page_id}"


def _when(value: str | None) -> str:
    """Confluence-tijdstempel → '2026-09-02T09:12:00' (vergelijkbaar als string)."""
    return (value or "")[:19]


def _labels(content: dict) -> list[str]:
    res = ((content.get("metadata") or {}).get("labels") or {}).get("results") or []
    return [l["name"] for l in res]


def _paged(client, path: str, params: dict, limit: int = 100) -> list[dict]:
    """Alle resultaten ophalen. Confluence knijpt de limit af zodra er expand bij zit (gevraagd 100,
    gekregen 50 op /content/search met body.storage), dus tellen we met wat er effectief terugkwam
    en met totalSize — niet met de gevraagde limit."""
    out, start = [], 0
    while True:
        data = client.get(path, dict(params, limit=limit, start=start)) or {}
        results = data.get("results") or []
        out += results
        total = data.get("totalSize")
        if not results:
            return out
        start += len(results)
        if total is not None:
            if len(out) >= total:
                return out
        elif len(results) < (data.get("limit") or limit):
            return out


def _children(client, page_id: str) -> list[dict]:
    res = _paged(client, f"/rest/api/content/{page_id}/child/page",
                 {"expand": "version,metadata.labels"}, limit=100)
    return [{"page_id": c["id"], "title": c["title"], "labels": _labels(c),
             "last_modified": _when((c.get("version") or {}).get("when"))} for c in res]


def _page_record(cfg: dict, schema: dict, content: dict, children: list[dict]) -> dict:
    storage = (((content.get("body") or {}).get("storage")) or {}).get("value") or ""
    values, raw, problems = parse_details(schema, storage)
    title = content["title"]
    key_title = _key_of(title)
    ai_key = (values or {}).get("ai_key") or key_title
    if values and values.get("ai_key") and key_title and values["ai_key"] != key_title:
        problems = problems + [f"ai_key: blok zegt {values['ai_key']}, titel zegt {key_title}"]
    last = max([_when((content.get("version") or {}).get("when"))] + [c["last_modified"] for c in children])
    return {"page_id": content["id"], "title": title, "ai_key": ai_key,
            "version": (content.get("version") or {}).get("number"),
            "last_modified": _when((content.get("version") or {}).get("when")),
            "labels": _labels(content), "url": _url(cfg, content["id"]),
            "has_details": values is not None, "details": values, "details_raw": raw,
            "details_problems": problems, "children": children, "last_activity": last}


PAGE_EXPAND = "body.storage,version,space,metadata.labels,ancestors"


def _root_of_minispace(content: dict) -> bool:
    """Discovery-heuristiek (DESIGN §10): de rootpagina van een mini-space is de [AI-n]-pagina
    waarvan de parenttitel zelf niet op [AI-\\d+] matcht."""
    anc = content.get("ancestors") or []
    parent = anc[-1]["title"] if anc else ""
    return not re.match(r"\s*\[AI-\d+\]", parent)


def list_pages(cfg: dict, client, schema: dict, discover: bool = False) -> dict:
    """register.json (DESIGN §6). Zonder discover: pagina's met het label. Met discover: ook
    kandidaten zonder label, op titel, één pagina per AI-key."""
    space = cfg["atlassian"]["space"]
    cql = f'space = "{space}" and type = page and label = "{schema["label"]}"'
    found = _paged(client, "/rest/api/content/search", {"cql": cql, "expand": PAGE_EXPAND})
    by_key: dict[str, dict] = {}
    pages = []
    for c in found:
        rec = _page_record(cfg, schema, c, _children(client, c["id"]))
        pages.append(rec)
        by_key[rec["ai_key"]] = rec
    if discover:
        cql = f'space = "{space}" and type = page and title ~ "AI-"'
        for c in _paged(client, "/rest/api/content/search", {"cql": cql, "expand": PAGE_EXPAND}):
            key = _key_of(c["title"])
            if not key or key in by_key:
                continue
            if not _root_of_minispace(c):
                continue
            rec = _page_record(cfg, schema, c, _children(client, c["id"]))
            by_key[rec["ai_key"]] = rec
            pages.append(rec)
    pages.sort(key=lambda r: (int(r["ai_key"].split("-")[1]) if "-" in r["ai_key"] else 0, r["title"]))
    return {"generated": _now(), "space": space, "pages": pages}


def _now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def get_page(cfg: dict, client, schema: dict, ident: str) -> dict:
    """Pagina op page-id of AI-key. Geeft de velden van list_pages plus 'storage'."""
    ident = str(ident or "").strip()
    if ident.isdigit():
        content = client.get(f"/rest/api/content/{ident}", {"expand": PAGE_EXPAND})
    else:
        key = _key_of(ident.upper()) or ident.upper()
        space = cfg["atlassian"]["space"]
        hits = _paged(client, "/rest/api/content/search",
                      {"cql": f'space = "{space}" and type = page and title ~ "{key}"',
                       "expand": PAGE_EXPAND}, limit=50)
        cands = [c for c in hits if _key_of(c["title"]) == key and _root_of_minispace(c)]
        if not cands:
            raise KeyError(f"geen pagina gevonden voor {ident}")
        content = cands[0]
    rec = _page_record(cfg, schema, content, _children(client, content["id"]))
    rec["storage"] = (((content.get("body") or {}).get("storage")) or {}).get("value") or ""
    rec["space"] = ((content.get("space") or {}).get("key")) or cfg["atlassian"]["space"]
    return rec


def search(cfg: dict, client, cql: str, limit: int = 100) -> list[dict]:
    """Ruwe CQL: {page_id, title, space, labels, last_modified, url}."""
    res = _paged(client, "/rest/api/content/search",
                 {"cql": cql, "expand": "version,space,metadata.labels"}, limit=min(limit, 100))
    out = []
    for c in res[:limit]:
        out.append({"page_id": c["id"], "title": c["title"],
                    "space": ((c.get("space") or {}).get("key")),
                    "labels": _labels(c), "last_modified": _when((c.get("version") or {}).get("when")),
                    "url": _url(cfg, c["id"])})
    return out


# --- schrijven (payload + diff; echt schrijven enkel via http.writer) ----------------------------

def _split_xml(xml: str) -> list[str]:
    """Storage-XML staat op één regel; voor een leesbare diff opbreken tussen de tags."""
    return re.split(r"(?<=>)(?=<)", xml)


def _diff(old: str, new: str, label: str) -> str:
    return "\n".join(difflib.unified_diff(_split_xml(old), _split_xml(new),
                                          fromfile=f"{label} (huidig)", tofile=f"{label} (nieuw)", lineterm=""))


def _page_payload(title: str, storage: str, version: int) -> dict:
    return {"type": "page", "title": title, "version": {"number": version},
            "body": {"storage": {"value": storage, "representation": "storage"}}}


def _put_page(cfg: dict, space: str, page_id: str, payload: dict, apply: bool):
    w = http.writer(cfg, "confluence", space, apply)
    return w.put(f"/rest/api/content/{page_id}", payload)


def _add_labels(cfg: dict, space: str, page_id: str, labels: list[str], apply: bool):
    w = http.writer(cfg, "confluence", space, apply)
    return w.post(f"/rest/api/content/{page_id}/label",
                  [{"prefix": "global", "name": n} for n in labels])


def upsert_details(cfg: dict, client, schema: dict, page_id: str, values: dict, apply: bool = False) -> dict:
    """Blok met id schema['details_id'] vervangen of vooraan invoegen; de rest van de body blijft
    byte-gelijk. Label toevoegen als het ontbreekt."""
    content = client.get(f"/rest/api/content/{page_id}", {"expand": PAGE_EXPAND})
    storage = (((content.get("body") or {}).get("storage")) or {}).get("value") or ""
    space = ((content.get("space") or {}).get("key")) or cfg["atlassian"]["space"]
    version = (content.get("version") or {}).get("number") or 0
    spans = find_details_blocks(schema, storage)
    # Zichtbaar + verborgen blok staan naast elkaar: samen vervangen. Verspreide blokken: weigeren.
    if any(storage[a[1]:b[0]].strip() for a, b in zip(spans, spans[1:])):
        raise ValueError("Kenmerkenblokken staan niet naast elkaar; eerst de structuur reviewen")
    span = (spans[0][0], spans[-1][1]) if spans else None
    if span:
        old_block = storage[span[0]:span[1]]
        mid = MACRO_ID_RE.search(_macro_head(old_block))
        new_block = render_details(schema, values, macro_id=mid.group(1) if mid else None)
        new_storage = storage[:span[0]] + new_block + storage[span[1]:]
        actie = "blok vervangen"
    else:
        old_block = ""
        new_block = render_details(schema, values)
        pos = insert_position(storage)
        new_storage = storage[:pos] + new_block + storage[pos:]
        actie = "blok vooraan ingevoegd"
    labels = _labels(content)
    to_add = [schema["label"]] if schema["label"] not in labels else []
    payload = _page_payload(content["title"], new_storage, version + 1)
    result = {"page_id": str(page_id), "title": content["title"], "space": space, "actie": actie,
              "applied": False, "version_before": version, "version_after": version + 1,
              "labels_toegevoegd": to_add, "diff": _diff(old_block, new_block, "details-blok"),
              "payload": payload, "url": _url(cfg, page_id), "unchanged": old_block == new_block}
    if apply:
        _put_page(cfg, space, page_id, payload, apply)
        if to_add:
            _add_labels(cfg, space, page_id, to_add, apply)
        result["applied"] = True
    return result


def _find_by_title(cfg: dict, client, title: str, space: str | None = None) -> dict | None:
    space = space or cfg["atlassian"]["space"]
    res = client.get("/rest/api/content", {"spaceKey": space, "title": title, "type": "page",
                                           "expand": PAGE_EXPAND, "limit": 5}) or {}
    results = res.get("results") or []
    return results[0] if results else None


def create_initiative(cfg: dict, client, schema: dict, values: dict, titel: str, parent_id: str | None = None,
                      samenvatting: str = "", apply: bool = False) -> dict:
    """Nieuwe initiatiefpagina. Weigert als er al een pagina met dezelfde AI-key bestaat."""
    space = cfg["atlassian"]["space"]
    ai_key = values.get("ai_key") or ""
    bestaand = None
    if ai_key:
        try:
            bestaand = get_page(cfg, client, schema, ai_key)
        except KeyError:
            bestaand = None
    if bestaand:
        raise ValueError(f"{ai_key} heeft al een pagina ({bestaand['page_id']} — "
                         f"{bestaand['title']}); geen tweede pagina aangemaakt")
    title = schema["page_title"].format(ai_key=ai_key, titel=titel)
    storage = render_page(schema, values, samenvatting=samenvatting, cfg=cfg)
    payload = {"type": "page", "title": title, "space": {"key": space},
               "body": {"storage": {"value": storage, "representation": "storage"}}}
    if parent_id:
        payload["ancestors"] = [{"id": str(parent_id)}]
    result = {"page_id": None, "title": title, "space": space, "actie": "pagina aanmaken",
              "applied": False, "labels_toegevoegd": [schema["label"]], "payload": payload,
              "diff": _diff("", storage, title)}
    if apply:
        w = http.writer(cfg, "confluence", space, apply)
        created = w.post("/rest/api/content", payload) or {}
        result["page_id"] = created.get("id")
        if result["page_id"]:
            _add_labels(cfg, space, result["page_id"], [schema["label"]], apply)
            result["url"] = _url(cfg, result["page_id"])
        result["applied"] = True
    return result


def create_child(cfg: dict, client, schema: dict, parent_id: str, title: str,
                 labels: list[str] | None = None, body_from_title: str | None = None,
                 apply: bool = False) -> dict:
    """Kindpagina onder parent_id, in de space van de parent. De body komt uit de pagina met titel
    body_from_title in die space (de sjabloonpagina, bv. het captatierapport) als die bestaat,
    anders één lege alinea. Weigert als er onder die parent al een kind met deze titel staat."""
    parent = client.get(f"/rest/api/content/{parent_id}", {"expand": "version,space"})
    space = ((parent.get("space") or {}).get("key")) or cfg["atlassian"]["space"]
    titel = title.strip()
    dubbel = next((c for c in _children(client, parent_id) if c["title"].strip() == titel), None)
    if dubbel:
        raise ValueError(f"onder {parent_id} ({parent['title']}) staat al een kind '{titel}' "
                         f"({dubbel['page_id']}); geen tweede pagina aangemaakt")
    bron = _find_by_title(cfg, client, body_from_title, space) if body_from_title else None
    storage = (((bron.get("body") or {}).get("storage")) or {}).get("value") or "" if bron else ""
    melding = None
    if bron:
        melding = f"body overgenomen van '{bron['title']}' ({bron['id']})"
    elif body_from_title:
        melding = f"geen pagina '{body_from_title}' in space {space}; lege body"
    if not storage:
        storage = "<p><br /></p>"
    labels = list(labels or [])
    payload = {"type": "page", "title": titel, "space": {"key": space},
               "ancestors": [{"id": str(parent_id)}],
               "body": {"storage": {"value": storage, "representation": "storage"}}}
    res = {"page_id": None, "title": titel, "space": space, "actie": "kindpagina aanmaken",
           "applied": False, "parent_id": str(parent_id), "parent_title": parent["title"],
           "labels_toegevoegd": labels, "melding": melding, "payload": payload,
           "diff": _diff("", storage, titel)}
    if apply:
        w = http.writer(cfg, "confluence", space, apply)
        created = w.post("/rest/api/content", payload) or {}
        res["page_id"] = created.get("id")
        if res["page_id"]:
            res["url"] = _url(cfg, res["page_id"])
            if labels:
                _add_labels(cfg, space, res["page_id"], labels, apply)
        res["applied"] = True
    return res


def _publish(cfg: dict, client, title: str, storage: str, space: str, parent_id=None,
             labels: list[str] | None = None, apply: bool = False) -> dict:
    """Create-or-update op titel."""
    bestaand = _find_by_title(cfg, client, title, space)
    labels = labels or []
    if bestaand:
        version = (bestaand.get("version") or {}).get("number") or 0
        old = (((bestaand.get("body") or {}).get("storage")) or {}).get("value") or ""
        payload = _page_payload(title, storage, version + 1)
        res = {"page_id": bestaand["id"], "title": title, "space": space, "actie": "pagina bijwerken",
               "applied": False, "version_before": version, "version_after": version + 1,
               "diff": _diff(old, storage, title), "payload": payload, "url": _url(cfg, bestaand["id"]),
               "unchanged": old == storage,
               "labels_toegevoegd": [l for l in labels if l not in _labels(bestaand)]}
        if apply:
            _put_page(cfg, space, bestaand["id"], payload, apply)
            if res["labels_toegevoegd"]:
                _add_labels(cfg, space, bestaand["id"], res["labels_toegevoegd"], apply)
            res["applied"] = True
        return res
    payload = {"type": "page", "title": title, "space": {"key": space},
               "body": {"storage": {"value": storage, "representation": "storage"}}}
    if parent_id:
        payload["ancestors"] = [{"id": str(parent_id)}]
    res = {"page_id": None, "title": title, "space": space, "actie": "pagina aanmaken",
           "applied": False, "diff": _diff("", storage, title), "payload": payload,
           "labels_toegevoegd": labels}
    if apply:
        w = http.writer(cfg, "confluence", space, apply)
        created = w.post("/rest/api/content", payload) or {}
        res["page_id"] = created.get("id")
        if res["page_id"] and labels:
            _add_labels(cfg, space, res["page_id"], labels, apply)
        res["applied"] = True
    return res


def publish_template(cfg: dict, client, schema: dict, apply: bool = False) -> dict:
    return _publish(cfg, client, schema["template_title"], render_template(schema, cfg),
                    cfg["atlassian"]["space"], parent_id=cfg["atlassian"].get("templates_parent"),
                    apply=apply)


def publish_overview(cfg: dict, client, schema: dict, apply: bool = False) -> dict:
    return _publish(cfg, client, schema["overview_title"], render_overview(schema, cfg),
                    cfg["atlassian"]["space"], parent_id=cfg["atlassian"].get("space_home"),
                    apply=apply)


def set_labels(cfg: dict, client, page_id: str, labels: list[str], apply: bool = False) -> dict:
    content = client.get(f"/rest/api/content/{page_id}", {"expand": "version,space,metadata.labels"})
    space = ((content.get("space") or {}).get("key")) or cfg["atlassian"]["space"]
    huidig = _labels(content)
    to_add = [l for l in labels if l not in huidig]
    res = {"page_id": str(page_id), "title": content["title"], "space": space, "actie": "labels toevoegen",
           "applied": False, "labels_huidig": huidig, "labels_toegevoegd": to_add,
           "url": _url(cfg, page_id), "unchanged": not to_add}
    if apply and to_add:
        _add_labels(cfg, space, page_id, to_add, apply)
        res["applied"] = True
    elif apply:
        http.writer(cfg, "confluence", space, apply)   # guard ook zonder werk
        res["applied"] = True
    return res


# --- markdown --------------------------------------------------------------------------------

def pages_markdown(register: dict) -> str:
    out = [f"# Registerpagina's — space {register.get('space', '')}", "",
           f"{len(register.get('pages') or [])} pagina's · gegenereerd {register.get('generated', '')}", "",
           "| key | titel | blok | problemen | kinderen | laatste activiteit |", "|---|---|---|---|---|---|"]
    for p in register.get("pages") or []:
        kinderen = ", ".join(f"{c['title']} ({', '.join(c['labels']) or 'geen label'})"
                             for c in p.get("children") or []) or "—"
        problemen = "; ".join(p.get("details_problems") or []) or "—"
        out.append(f"| {p.get('ai_key') or '—'} | [{p['title']}]({p['url']}) | "
                   f"{'ja' if p.get('has_details') else 'nee'} | {problemen} | {kinderen} | "
                   f"{p.get('last_activity', '')} |")
    return "\n".join(out) + "\n"


def change_markdown(result: dict) -> str:
    st = "toegepast" if result.get("applied") else "dry-run (niets geschreven)"
    out = [f"# {result.get('actie', 'wijziging')} — {result.get('title', '')}", "",
           f"- pagina: {result.get('page_id') or '(nieuw)'} · space {result.get('space', '')}",
           f"- status: {st}"]
    if result.get("version_before") is not None:
        out.append(f"- versie: {result['version_before']} → {result['version_after']}")
    if result.get("parent_id"):
        out.append(f"- onder: {result.get('parent_title', '')} ({result['parent_id']})")
    if result.get("labels_toegevoegd"):
        out.append(f"- labels toe te voegen: {', '.join(result['labels_toegevoegd'])}")
    if result.get("melding"):
        out.append(f"- {result['melding']}")
    if result.get("unchanged"):
        out.append("- geen inhoudelijke wijziging")
    if result.get("url"):
        out.append(f"- {result['url']}")
    if result.get("diff"):
        out += ["", "```diff", result["diff"], "```"]
    return "\n".join(out) + "\n"
