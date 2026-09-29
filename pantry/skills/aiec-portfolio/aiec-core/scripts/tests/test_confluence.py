"""Tests voor aiec_lib.confluence (WP-A). Geen netwerk: de client is een stub met canned antwoorden.
Draaien: cd scripts && uv run --with pytest --with pyyaml python -m pytest tests -q"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiec_lib import config, http, schema as sch  # noqa: E402
from aiec_lib import confluence as conf  # noqa: E402

S = sch.load()
FIX = Path(__file__).resolve().parent / "fixtures"


def cfg(mode="dry-run"):
    c = config._merge(config.DEFAULTS, {"writes": {"mode": mode}})
    c["_path"] = "<test>"
    return c


VALUES = {
    "ai_key": "AI-25", "eag_key": "EAG-927", "soort": "afgebakend", "pijler": "P2",
    "vrager": "de aanvrager", "afdeling": "Team Digitalisering", "herkomst": "management",
    "toepassingstype": ["Documentverwerking", "Beslissingsondersteuning"],
    "ai_techniek": ["Generative AI"], "delivery_mode": "eigen bouw", "ai_act_klasse": "beperkt",
    "persoonsgegevens": "ja", "batenclaim": "", "aanname": "", "opgeleverd": "", "gebruikers": "",
    "stopreden": "",
}


class FakeClient:
    """Alleen-lezen stub: get() geeft canned antwoorden, post/put laten een spoor achter."""

    def __init__(self, content=None, search=None, children=None, label_search=None, by_title=None):
        self.content = content or {}
        self.search = search or {"results": []}
        self.label_search = label_search or {"results": []}    # cql met label = …
        self.by_title = by_title                               # /rest/api/content?title=…
        self.children = children or {"results": []}
        self.calls = []

    def get(self, path, params=None):
        self.calls.append(("GET", path, params))
        if path.endswith("/child/page"):
            return self.children
        if path.startswith("/rest/api/content/search"):
            return self.label_search if "label = " in (params or {}).get("cql", "") else self.search
        if path == "/rest/api/content":
            if self.by_title is not None:
                hit = self.by_title if self.by_title["title"] == (params or {}).get("title") else None
                return {"results": [hit] if hit else []}
            return self.search
        return self.content

    def post(self, path, body=None, params=None):      # pragma: no cover - mag nooit gebeuren
        self.calls.append(("POST", path, body))
        raise AssertionError("de leesclient mag nooit schrijven")

    def put(self, path, body=None, params=None):       # pragma: no cover - mag nooit gebeuren
        self.calls.append(("PUT", path, body))
        raise AssertionError("de leesclient mag nooit schrijven")


class PagingClient:
    """Stub die pagineert zoals Confluence het doet: met expand knijpt de server de gevraagde limit
    af (100 gevraagd, 50 terug) en zet totalSize. Regressie op de discovery die daardoor stopte."""

    def __init__(self, total, server_limit=50, met_totalsize=True):
        self.pages = [page_content("<p>x</p>", page_id=str(i), title=f"[AI-{i}] pagina") for i in range(total)]
        self.server_limit = server_limit
        self.met_totalsize = met_totalsize
        self.calls = 0

    def get(self, path, params=None):
        self.calls += 1
        start = (params or {}).get("start", 0)
        stuk = self.pages[start:start + self.server_limit]
        out = {"results": stuk, "start": start, "limit": self.server_limit, "size": len(stuk)}
        if self.met_totalsize:
            out["totalSize"] = len(self.pages)
        return out


def test_paged_volgt_de_limit_van_de_server():
    c = PagingClient(111)
    assert len(conf._paged(c, "/rest/api/content/search", {"cql": "x"}, limit=100)) == 111
    assert c.calls == 3                                   # 50 + 50 + 11
    zonder = PagingClient(100, met_totalsize=False)
    assert len(conf._paged(zonder, "/rest/api/content/search", {"cql": "x"}, limit=50)) == 100
    assert zonder.calls == 3                              # 50 + 50 + lege pagina


def page_content(storage, page_id="431293025", title="[AI-25] AI-ondersteuning MIA", version=6,
                 labels=(), ancestors=(("390605009", "Maatwerk & processoptimalisaties"),)):
    return {"id": page_id, "title": title,
            "body": {"storage": {"value": storage, "representation": "storage"}},
            "version": {"number": version, "when": "2026-07-16T12:25:28.164+02:00"},
            "space": {"key": "AI"},
            "metadata": {"labels": {"results": [{"name": n} for n in labels]}},
            "ancestors": [{"id": i, "title": t} for i, t in ancestors]}


# --- parser ⇄ renderer -------------------------------------------------------------------------

def test_round_trip_identiek():
    xml = conf.render_details(S, VALUES)
    values, raw, problems = conf.parse_details(S, xml)
    assert problems == []
    assert values == VALUES
    assert raw["AI-key"] == "AI-25"
    assert raw["Pijler"] == "P2 — Mens & Adoptie"
    assert conf.render_details(S, values) == xml          # byte-gelijk


def test_round_trip_leeg_blok():
    leeg = sch.empty_values(S)
    xml = conf.render_details(S, leeg)
    values, _, problems = conf.parse_details(S, xml)
    assert values == leeg and problems == []
    assert conf.render_details(S, values) == xml


def test_blok_heeft_id_parameter():
    xml = conf.render_details(S, VALUES)
    assert f'<ac:parameter ac:name="id">{S["details_id"]}</ac:parameter>' in xml
    assert "ac:macro-id" not in xml                        # deterministisch renderen


def test_parser_is_tolerant():
    """Cellen zoals Confluence ze zelf schrijft: content-wrapper, <p>, <br/>, entities, leeg."""
    block = (
        '<ac:structured-macro ac:name="details" ac:schema-version="1" ac:macro-id="abc">'
        '<ac:parameter ac:name="id">aiec-initiatief</ac:parameter><ac:rich-text-body>'
        '<table class="wrapped"><tbody>'
        "<tr><th>AI-key</th><td><div class=\"content-wrapper\"><p>AI-25</p></div></td></tr>"
        "<tr><th>Soort</th><td> Afgebakend </td></tr>"
        "<tr><th>Pijler</th><td>P2 — Mens &amp; Adoptie</td></tr>"
        "<tr><th>Toepassingstype</th><td>Documentverwerking<br />Beslissingsondersteuning</td></tr>"
        "<tr><th>AI-techniek</th><td>generative ai, NLP</td></tr>"
        "<tr><th colspan=\"1\">Afdeling</th><td colspan=\"1\">Team R&amp;D</td></tr>"
        "<tr><th>Batenclaim</th><td><div class=\"content-wrapper\"><p><br /></p></div></td></tr>"
        "<tr><th>Onbekend veld</th><td>iets</td></tr>"
        "</tbody></table></ac:rich-text-body></ac:structured-macro>")
    values, raw, problems = conf.parse_details(S, "<p>voor</p>" + block + "<p>na</p>")
    assert values["ai_key"] == "AI-25" and values["soort"] == "afgebakend"
    assert values["pijler"] == "P2"
    assert values["toepassingstype"] == ["Documentverwerking", "Beslissingsondersteuning"]
    assert values["ai_techniek"] == ["Generative AI", "NLP"]
    assert values["afdeling"] == "Team R&D"
    assert values["batenclaim"] == ""
    assert raw["Onbekend veld"] == "iets"
    assert problems == ["onbekend label 'Onbekend veld' in het details-blok"]


def test_productfiche_heeft_ons_blok_niet():
    """Zes details-blokken zonder onze id, met een geneste status-macro: geen blok, geen fout."""
    body = (FIX / "conf-details-productfiche.xml").read_text()
    assert body.count('<ac:structured-macro ac:name="details"') == 6
    assert conf.find_details_block(S, body) is None
    values, raw, problems = conf.parse_details(S, body)
    assert (values, raw, problems) == (None, {}, [])


def test_macro_span_telt_nesting():
    body = (FIX / "conf-details-productfiche.xml").read_text()
    start = body.index('<ac:structured-macro ac:name="details"')
    s, e = conf._macro_span(body, start)
    blok = body[s:e]
    assert blok.endswith("</ac:structured-macro>")
    assert 'ac:name="status"' in blok                       # geneste macro zit erin
    assert blok.count("<ac:structured-macro") == 2 == blok.count("</ac:structured-macro>")


# --- render_page / template / overview ---------------------------------------------------------

def test_render_page_volgt_page_sections():
    xml = conf.render_page(S, VALUES, samenvatting="Twee zinnen uitleg.", cfg=cfg())
    koppen = [s["kop"] for s in S["page_sections"] if s["type"] != "details"]
    for kop in koppen:
        assert f"<h2>{kop}</h2>" in xml
    # paginavolgorde = volgorde van page_sections, met het details-blok op zijn plaats
    posities = [xml.index('ac:name="details"') if s["type"] == "details" else xml.index(f"<h2>{s['kop']}</h2>")
                for s in S["page_sections"]]
    assert posities == sorted(posities)
    assert xml.startswith('<h2>Stand van zaken</h2>')
    assert '<ac:parameter ac:name="jqlQuery">(key = AI-25 OR issue in linkedIssues(AI-25)) AND project in (PROD, POR, EAG, AI)</ac:parameter>' in xml
    assert '<ac:parameter ac:name="serverId">56e4142a-0105-3cf7-b7a8-b308d7369863</ac:parameter>' in xml
    assert 'ac:name="contentbylabel"' in xml and conf.CHILDREN_MACRO not in xml
    assert '&quot;captatierapport&quot;' in xml and '&quot;decisions&quot;, ' not in xml   # beslissingen apart
    assert 'ancestor = currentContent()' in xml
    assert "label = &quot;decisions&quot; and space = currentSpace() and ancestor = currentContent()" in xml
    assert '<ac:parameter ac:name="maximumIssues">20</ac:parameter>' in xml
    assert "Twee zinnen uitleg." in xml
    assert "<h2>Status</h2>" not in xml                     # status staat nooit op de pagina


def test_render_template_en_overview():
    tpl = conf.render_template(S, cfg())
    assert '<ac:structured-macro ac:name="info"' in tpl
    assert "afgebakend | doorlopend" in tpl
    assert f'<ac:parameter ac:name="id">{S["details_id"]}</ac:parameter>' in tpl
    assert tpl.index('ac:name="info"') < tpl.index('<h2>Stand van zaken</h2>') < tpl.index('ac:name="details"')
    ov = conf.render_overview(S, cfg())
    assert '<ac:structured-macro ac:name="detailssummary" ac:schema-version="2">' in ov
    assert f'<ac:parameter ac:name="id">{S["details_id"]}</ac:parameter>' in ov
    assert '<ac:parameter ac:name="sortBy">Pijler</ac:parameter>' in ov
    assert f'label = &quot;{S["label"]}&quot; and space = currentSpace()' in ov
    for k in S["overzicht"]["kolommen"]:
        assert sch.field(S, k)["label"] in ov
    assert S["overzicht"]["jira_jql"] in ov
    assert '<ac:parameter ac:name="maximumIssues">500</ac:parameter>' in ov   # niet afkappen op 20


def test_render_overview_zonder_serverid():
    c = cfg()
    c["atlassian"] = dict(c["atlassian"], jira_server_id="")
    ov = conf.render_overview(S, c)
    assert 'ac:name="jira"' not in ov and "geen serverId" in ov


# --- upsert: de rest van de body blijft byte-gelijk ---------------------------------------------

def test_upsert_voegt_blok_vooraan_in():
    body = (FIX / "conf-minispace-template.xml").read_text()
    client = FakeClient(page_content(body))
    res = conf.upsert_details(cfg(), client, S, "411959720", VALUES)
    nieuw = res["payload"]["body"]["storage"]["value"]
    blok = conf.render_details(S, VALUES)
    assert nieuw == blok + body                              # rest byte-gelijk, blok vooraan
    assert res["actie"] == "blok vooraan ingevoegd"
    assert res["applied"] is False
    assert res["version_before"] == 6 and res["version_after"] == 7
    assert res["labels_toegevoegd"] == [S["label"]]
    assert res["diff"]
    assert all(c[0] == "GET" for c in client.calls)          # niets geschreven


def test_upsert_vervangt_enkel_het_eigen_blok():
    oud = conf.render_details(S, dict(VALUES, soort="doorlopend", ai_act_klasse="te bepalen"))
    oud = oud.replace('ac:schema-version="1"', 'ac:schema-version="1" ac:macro-id="bewaar-mij"')
    prefix = (FIX / "conf-minispace-template.xml").read_text()
    suffix = (FIX / "conf-detailssummary.xml").read_text()
    body = prefix + oud + suffix
    client = FakeClient(page_content(body, labels=(S["label"],)))
    res = conf.upsert_details(cfg(), client, S, "431293025", VALUES)
    nieuw = res["payload"]["body"]["storage"]["value"]
    assert nieuw.startswith(prefix) and nieuw.endswith(suffix)
    assert nieuw[len(prefix):len(nieuw) - len(suffix)] == \
        conf.render_details(S, VALUES, macro_id="bewaar-mij")
    assert res["actie"] == "blok vervangen"
    assert res["labels_toegevoegd"] == []
    assert 'ac:macro-id="bewaar-mij"' in nieuw               # macro-id blijft van het bestaande blok


def test_upsert_in_layout_pagina_laat_de_andere_blokken_staan():
    body = (FIX / "conf-details-productfiche.xml").read_text()
    client = FakeClient(page_content(body))
    nieuw = conf.upsert_details(cfg(), client, S, "470876655", VALUES)["payload"]["body"]["storage"]["value"]
    blok = conf.render_details(S, VALUES)
    assert blok in nieuw
    assert nieuw.replace(blok, "", 1) == body                # enkel het blok is erbij gekomen
    assert nieuw.count('<ac:structured-macro ac:name="details"') == 6 + blok.count('<ac:structured-macro ac:name="details"')
    assert nieuw.startswith("<ac:layout><ac:layout-section")  # blok komt in de eerste layout-cell

    # tweede keer upserten vervangt het eigen blok en laat de rest opnieuw byte-gelijk
    client2 = FakeClient(page_content(nieuw))
    anders = dict(VALUES, persoonsgegevens="nee")
    nieuw2 = conf.upsert_details(cfg(), client2, S, "470876655", anders)["payload"]["body"]["storage"]["value"]
    assert nieuw2 == nieuw.replace(blok, conf.render_details(S, anders), 1)
    assert nieuw2.count('<ac:structured-macro ac:name="details"') == nieuw.count('<ac:structured-macro ac:name="details"')


def test_upsert_zonder_wijziging_is_zichtbaar():
    body = "<p>x</p>" + conf.render_details(S, VALUES) + "<p>y</p>"
    res = conf.upsert_details(cfg(), FakeClient(page_content(body, labels=(S["label"],))), S, "1", VALUES)
    assert res["unchanged"] is True and res["diff"] == ""


def test_upsert_met_apply_in_dry_run_wordt_geweigerd(monkeypatch):
    monkeypatch.setattr(http, "token", lambda kind: "t")
    client = FakeClient(page_content("<p>x</p>"))
    with pytest.raises(config.GuardRefused):
        conf.upsert_details(cfg("dry-run"), client, S, "431293025", VALUES, apply=True)
    # ook in test-mode: space AI is daar niet toegestaan
    with pytest.raises(config.GuardRefused):
        conf.upsert_details(cfg("test"), client, S, "431293025", VALUES, apply=True)


def test_create_initiative_payload(monkeypatch):
    client = FakeClient(page_content("<p>x</p>"), search={"results": []})
    res = conf.create_initiative(cfg(), client, S, VALUES, "AI-ondersteuning MIA", parent_id="411075022")
    assert res["applied"] is False
    assert res["title"] == "[AI-25] AI-ondersteuning MIA"
    assert res["payload"]["space"] == {"key": "AI"}
    assert res["payload"]["ancestors"] == [{"id": "411075022"}]
    assert '<ac:structured-macro ac:name="details"' in res["payload"]["body"]["storage"]["value"]
    assert res["labels_toegevoegd"] == [S["label"]]


def test_create_initiative_weigert_dubbele_key():
    bestaand = page_content(conf.render_details(S, VALUES), title="[AI-25] Bestaand")
    client = FakeClient(bestaand, search={"results": [bestaand]})
    with pytest.raises(ValueError):                 # aiec.py vertaalt ValueError naar exit 4
        conf.create_initiative(cfg(), client, S, VALUES, "Nog eens MIA")


def test_set_labels_dry_run():
    client = FakeClient(page_content("<p>x</p>", labels=("idee",)))
    res = conf.set_labels(cfg(), client, "431293025", [S["label"], "idee"])
    assert res["labels_toegevoegd"] == [S["label"]] and res["applied"] is False


def _parent(space="AI", title="[AI-25] AI-ondersteuning MIA", page_id="431293025"):
    return {"id": page_id, "title": title, "space": {"key": space},
            "version": {"number": 3, "when": "2026-07-16T12:25:28.164+02:00"}}


SJABLOON = {"id": "411959726", "title": "Sjabloon AI-captatierapport",
            "body": {"storage": {"value": "<h2>Vraag</h2><p>…</p>", "representation": "storage"}},
            "version": {"number": 2, "when": "2026-05-01T10:00:00.000+02:00"},
            "space": {"key": "AI"}, "metadata": {"labels": {"results": []}}, "ancestors": []}


def test_create_child_neemt_de_body_van_de_sjabloonpagina_over():
    client = FakeClient(_parent(), by_title=SJABLOON)
    res = conf.create_child(cfg(), client, S, "431293025", "[AI-25] Captatierapport",
                            labels=["captatierapport"], body_from_title="Sjabloon AI-captatierapport")
    assert res["applied"] is False
    assert res["payload"]["body"]["storage"]["value"] == "<h2>Vraag</h2><p>…</p>"
    assert res["payload"]["ancestors"] == [{"id": "431293025"}]
    assert res["payload"]["space"] == {"key": "AI"}
    assert res["payload"]["title"] == "[AI-25] Captatierapport"
    assert res["labels_toegevoegd"] == ["captatierapport"]
    assert "411959726" in res["melding"]
    assert all(c[0] == "GET" for c in client.calls)
    assert "onder: [AI-25] AI-ondersteuning MIA (431293025)" in conf.change_markdown(res)


def test_create_child_zonder_sjabloon_krijgt_een_lege_alinea():
    client = FakeClient(_parent())
    res = conf.create_child(cfg(), client, S, "431293025", "[AI-25] Logboek")
    assert res["payload"]["body"]["storage"]["value"] == "<p><br /></p>"
    assert res["melding"] is None and res["labels_toegevoegd"] == []


def test_create_child_meldt_een_ontbrekende_sjabloonpagina():
    client = FakeClient(_parent(), by_title=SJABLOON)
    res = conf.create_child(cfg(), client, S, "431293025", "[AI-25] Captatierapport",
                            body_from_title="Sjabloon dat niet bestaat")
    assert res["payload"]["body"]["storage"]["value"] == "<p><br /></p>"
    assert "niet bestaat" in res["melding"] and "lege body" in res["melding"]


def test_create_child_volgt_de_space_van_de_parent():
    client = FakeClient(_parent(space="~vancrake"))
    res = conf.create_child(cfg(), client, S, "431293025", "[AI-25] Logboek")
    assert res["space"] == "~vancrake" and res["payload"]["space"] == {"key": "~vancrake"}


def test_create_child_weigert_een_dubbele_titel():
    client = FakeClient(_parent(), children={"results": [
        {"id": "505839625", "title": "[AI-25] Captatierapport ",
         "version": {"when": "2026-09-02T09:12:00.000+02:00"},
         "metadata": {"labels": {"results": []}}}]})
    with pytest.raises(ValueError):                 # aiec.py vertaalt ValueError naar exit 4
        conf.create_child(cfg(), client, S, "431293025", "[AI-25] Captatierapport")


def test_create_child_met_apply_in_dry_run_wordt_geweigerd(monkeypatch):
    monkeypatch.setattr(http, "token", lambda kind: "t")
    client = FakeClient(_parent())
    with pytest.raises(config.GuardRefused):
        conf.create_child(cfg("dry-run"), client, S, "431293025", "[AI-25] Logboek", apply=True)
    with pytest.raises(config.GuardRefused):        # test-mode: space AI is niet toegestaan
        conf.create_child(cfg("test"), client, S, "431293025", "[AI-25] Logboek", apply=True)


# --- lezen ---------------------------------------------------------------------------------------

def test_get_page_en_markdown():
    body = "<p>kop</p>" + conf.render_details(S, VALUES)
    client = FakeClient(page_content(body, labels=(S["label"],)),
                        children={"results": [{"id": "505839625", "title": "[AI-25] Beslissingen",
                                               "version": {"when": "2026-09-02T09:12:00.000+02:00"},
                                               "metadata": {"labels": {"results": [{"name": "decisions"}]}}}]})
    rec = conf.get_page(cfg(), client, S, "431293025")
    assert rec["ai_key"] == "AI-25" and rec["has_details"] is True
    assert rec["details"]["pijler"] == "P2"
    assert rec["version"] == 6 and rec["last_modified"] == "2026-07-16T12:25:28"
    assert rec["children"][0]["labels"] == ["decisions"]
    assert rec["last_activity"] == "2026-09-02T09:12:00"     # kind is recenter dan de pagina
    assert rec["storage"] == body
    md = conf.pages_markdown({"space": "AI", "generated": "nu", "pages": [rec]})
    assert "AI-25" in md and "decisions" in md


def test_get_page_zonder_blok_haalt_de_key_uit_de_titel():
    client = FakeClient(page_content("<p>niets</p>", title="[AI-25] AI-ondersteuning MIA"))
    rec = conf.get_page(cfg(), client, S, "431293025")
    assert rec["ai_key"] == "AI-25" and rec["has_details"] is False and rec["details"] is None


def test_discover_kiest_de_rootpagina_van_de_mini_space():
    root = page_content("<p>x</p>", page_id="505839624", title="[AI-49] AI-assistent voor school",
                        ancestors=(("411075022", "Maatwerk & processoptimalisaties"),))
    kind = page_content("<p>x</p>", page_id="505839625", title="[AI-49] Beslissingen",
                        ancestors=(("411075022", "Maatwerk"), ("505839624", "[AI-49] AI-assistent voor school")))
    client = FakeClient(search={"results": [kind, root]})
    reg = conf.list_pages(cfg(), client, S, discover=True)
    assert [p["page_id"] for p in reg["pages"]] == ["505839624"]
    assert reg["pages"][0]["ai_key"] == "AI-49"
    assert reg["space"] == "AI"


def test_list_pages_zonder_discover_gebruikt_het_label():
    client = FakeClient(search={"results": []})
    reg = conf.list_pages(cfg(), client, S)
    cql = client.calls[0][2]["cql"]
    assert f'label = "{S["label"]}"' in cql and 'space = "AI"' in cql
    assert reg["pages"] == []


def test_search_vorm():
    page = page_content("<p>x</p>")
    client = FakeClient(search={"results": [page]})
    hits = conf.search(cfg(), client, 'type = page and title ~ "AI-"')
    assert hits[0]["page_id"] == "431293025" and hits[0]["space"] == "AI"
    assert hits[0]["last_modified"] == "2026-07-16T12:25:28"
    assert hits[0]["url"].endswith("pageId=431293025")


def test_change_markdown_toont_dry_run():
    res = conf.upsert_details(cfg(), FakeClient(page_content("<p>x</p>")), S, "1", VALUES)
    md = conf.change_markdown(res)
    assert "dry-run (niets geschreven)" in md and "```diff" in md
