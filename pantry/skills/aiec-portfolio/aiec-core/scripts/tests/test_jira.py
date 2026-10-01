"""Tests voor aiec_lib.jira (WP-B). Geen netwerk: FakeClient bedient /search, /issue/{key},
/worklog en /transitions uit de fixtures. De JQL-vormen die jira.py uitstuurt zijn beperkt tot
`key in (...)`, `cf[10510] in (...)`, `project = X AND issuetype = Initiative [AND status != ...]
[AND updated >= ...]`; de fake begrijpt precies die.

Draaien: cd scripts && uv run --with pytest --with pyyaml python -m pytest tests -q
"""
import datetime as dt
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiec_lib import config, http, schema as sch  # noqa: E402
from aiec_lib import jira as jira_mod  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"
S = sch.load()


def cfg(mode="dry-run"):
    c = config._merge(config.DEFAULTS, {"writes": {"mode": mode}})
    c["_path"] = "<test>"
    return c


class FakeClient:
    """Alleen-lezen fake met een minimale JQL-lezer. `calls` houdt bij wat er opgevraagd is,
    zodat een test kan controleren dat er geen worklog-call gebeurt voor issues zonder timespent."""

    def __init__(self):
        self.issues = {i["key"]: i
                       for i in json.loads((FIX / "jira-search-initiatives.json").read_text())["issues"]}
        self.changelogs = json.loads((FIX / "jira-changelog-initiatives.json").read_text())
        self.calls = []
        self.transitions = [{"id": "21", "name": "In Analyse", "to": {"name": "In Analyse"}, "fields": {}},
                            {"id": "71", "name": "Closed", "to": {"name": "Closed"}, "fields": {}}]

    # --- JQL ---------------------------------------------------------------------------------
    def _match(self, jql: str) -> list[dict]:
        m = re.search(r"key in \(([^)]*)\)", jql)
        if m:
            wanted = {k.strip() for k in m.group(1).split(",")}
            return [self.issues[k] for k in sorted(wanted) if k in self.issues]
        m = re.search(r"cf\[10510\] in \(([^)]*)\)", jql)
        if m:
            epics = {k.strip() for k in m.group(1).split(",")}
            return [i for i in self.issues.values() if i["fields"].get("customfield_10510") in epics]
        out = list(self.issues.values())
        m = re.search(r"project = (\w+)", jql)
        if m:
            out = [i for i in out if i["key"].startswith(m.group(1) + "-")]
        m = re.search(r"issuetype = (\w+)", jql)
        if m:
            out = [i for i in out if i["fields"]["issuetype"]["name"] == m.group(1)]
        m = re.search(r'status != "([^"]+)"', jql)
        if m:
            out = [i for i in out if i["fields"]["status"]["name"] != m.group(1)]
        m = re.search(r'updated >= "([^"]+)"', jql)
        if m:
            out = [i for i in out if i["fields"]["updated"][:10] >= m.group(1)]
        return sorted(out, key=lambda i: jira_mod.key_sort(i["key"]))

    def _with_changelog(self, issue, expand):
        if not expand or "changelog" not in expand:
            return issue
        return dict(issue, changelog=self.changelogs.get(issue["key"],
                                                         {"total": 0, "histories": []}))

    def get(self, path, params=None):
        params = params or {}
        self.calls.append((path, params.get("jql")))
        if path == "/rest/api/2/search":
            hits = [self._with_changelog(i, params.get("expand")) for i in self._match(params["jql"])]
            start, mx = int(params.get("startAt", 0)), int(params.get("maxResults", 100))
            page = hits[start:start + mx]
            return {"startAt": start, "maxResults": mx, "total": len(hits), "issues": page}
        m = re.match(r"^/rest/api/2/issue/([A-Z0-9_-]+)/worklog$", path)
        if m:
            f = FIX / f"jira-worklog-{m.group(1)}.json"
            return json.loads(f.read_text()) if f.exists() else {"total": 0, "worklogs": []}
        m = re.match(r"^/rest/api/2/issue/([A-Z0-9_-]+)/transitions$", path)
        if m:
            return {"transitions": self.transitions}
        m = re.match(r"^/rest/api/2/issue/([A-Z0-9_-]+)$", path)
        if m:
            return self._with_changelog(self.issues[m.group(1)], params.get("expand"))
        raise AssertionError(f"onverwachte call: {path}")

    def post(self, *a, **k):
        raise AssertionError("de fake leesclient mag nooit schrijven")

    put = post


@pytest.fixture
def client():
    return FakeClient()


@pytest.fixture(autouse=True)
def geen_echt_token(monkeypatch):
    """http.writer() mag in tests nooit de keychain aanspreken."""
    monkeypatch.setattr(http, "token", lambda kind: "test-token")


# --- lezen -------------------------------------------------------------------------------------

def test_list_initiatives_vorm_en_afgesloten_filter(client):
    data = jira_mod.list_initiatives(cfg(), client, S)
    keys = [i["key"] for i in data["issues"]]
    assert keys == ["AI-4", "AI-5", "AI-25", "AI-48"]        # AI-6 is Closed
    assert [i["key"] for i in jira_mod.list_initiatives(cfg(), client, S, include_closed=True)["issues"]] \
        == ["AI-4", "AI-5", "AI-6", "AI-25", "AI-48"]

    ai25 = next(i for i in data["issues"] if i["key"] == "AI-25")
    assert set(ai25) == {"key", "summary", "status_raw", "status", "fase", "resolution", "created",
                         "updated", "last_transition", "eag_keys", "links", "children", "billingkey",
                         "labels", "assignee", "trekker", "verantwoordelijke", "werkorganisatie", "confluence_page_ids",
                         "url"}
    assert ai25["status_raw"] == "In Analyse" and ai25["status"] == "Analyse" and ai25["fase"] == 1
    assert ai25["eag_keys"] == ["EAG-927"]
    assert ai25["children"] == ["AI-92"]                      # Hierarchy "includes" = inward
    assert ai25["confluence_page_ids"] == ["431293025"]
    assert ai25["url"].endswith("/browse/AI-25")
    assert ai25["last_transition"] is None or ai25["last_transition"] > ai25["created"]


def test_status_buiten_de_mapping_blijft_leesbaar(client):
    """Jira kent statussen die niet in het schema staan (Backlog, In Progress); die komen
    onvertaald door met fase None."""
    ai4 = next(i for i in jira_mod.list_initiatives(cfg(), client, S)["issues"] if i["key"] == "AI-4")
    naam, fase = sch.status_from_jira(S, ai4["status_raw"])
    assert ai4["status"] == naam and ai4["fase"] == fase


def test_get_initiative_heeft_description(client):
    d = jira_mod.get_initiative(cfg(), client, S, "AI-25")
    assert d["key"] == "AI-25" and "pageId=431293025" in d["description"]
    assert d["confluence_page_ids"] == ["431293025"]


def test_confluence_page_ids_vangt_beide_urlvormen(client):
    """AI-4 heeft /pages/<id> én ?pageId=<id> in de description."""
    d = jira_mod.get_initiative(cfg(), client, S, "AI-4")
    assert d["confluence_page_ids"] == ["431293030", "431293031"]


def test_search_geeft_platte_rijen(client):
    rijen = jira_mod.search(cfg(), client, "project = AI AND issuetype = Epic", limit=5)
    assert rijen and all(set(r) == {"key", "summary", "status", "issuetype", "updated"} for r in rijen)
    assert all(r["issuetype"] == "Epic" for r in rijen)
    assert len(rijen) <= 5


# --- subtree -----------------------------------------------------------------------------------

def test_subtree_hierarchy_subtask_en_eag(client):
    """AI-25: epic AI-92 via Hierarchy, subtask AI-19, EAG-927 via Gerelateerd."""
    assert jira_mod.subtree(cfg(), client, "AI-25") == ["AI-19", "AI-25", "AI-92", "EAG-927"]


def test_subtree_volgt_epic_link(client):
    """AI-48 → epic AI-75 (Hierarchy) → story AI-46 (Epic Link customfield_10510)."""
    assert jira_mod.subtree(cfg(), client, "AI-48") == ["AI-46", "AI-48", "AI-75"]


def test_subtree_recursief_en_cross_project(client):
    """AI-4 → epics AI-62/63/64/67 → stories AI-50 en AI-68 onder AI-67; AI-5 → OB-1."""
    st = jira_mod.subtree(cfg(), client, "AI-4")
    assert st == ["AI-4", "AI-50", "AI-62", "AI-63", "AI-64", "AI-67", "AI-68"]
    assert jira_mod.subtree(cfg(), client, "AI-5") == ["AI-5", "EAG-918", "OB-1"]


def test_subtree_recurseert_niet_in_eag(client):
    """EAG-tickets tellen mee maar hun eigen kinderen niet: de fake kent EAG-927 niet als issue
    en zou op een fetch-poging niets teruggeven, dus de key blijft enkelvoudig."""
    st = jira_mod.subtree(cfg(), client, "AI-25")
    assert [k for k in st if k.startswith("EAG-")] == ["EAG-927"]


# --- uren ---------------------------------------------------------------------------------------

def _som(client, keys):
    total = 0.0
    for k in keys:
        for w in json.loads((FIX / f"jira-worklog-{k}.json").read_text())["worklogs"]:
            total += w["timeSpentSeconds"] / 3600
    return round(total, 2)


def test_hours_telt_de_hele_subtree(client):
    data = jira_mod.hours(cfg(), client, S, keys=["AI-25"])
    v = data["per_initiative"]["AI-25"]
    assert v["issues"] == ["AI-19", "AI-25", "AI-92", "EAG-927"]
    assert v["total_h"] == _som(client, ["AI-19", "AI-25", "AI-92"])
    assert v["total_h"] > 0


def test_hours_periode_en_per_month(client):
    since, until = dt.date(2026, 7, 1), dt.date(2026, 9, 30)
    data = jira_mod.hours(cfg(), client, S, keys=["AI-48"], since=since, until=until)
    v = data["per_initiative"]["AI-48"]
    assert data["since"] == "2026-07-01" and data["until"] == "2026-09-30"
    assert v["period_h"] <= v["total_h"]
    # per_month gaat over de periode en staat op de worklog-datum (started), niet op created
    assert v["per_month"] and all(m >= "2026-07" for m in v["per_month"])
    assert round(sum(v["per_month"].values()), 2) == pytest.approx(v["period_h"], abs=0.02)
    assert list(v["per_month"]) == sorted(v["per_month"])


def test_hours_periode_sluit_buiten_de_vensters_uit(client):
    ruim = jira_mod.hours(cfg(), client, S, keys=["AI-48"], since=dt.date(2000, 1, 1))
    eng = jira_mod.hours(cfg(), client, S, keys=["AI-48"], since=dt.date(2099, 1, 1))
    assert ruim["per_initiative"]["AI-48"]["period_h"] == ruim["per_initiative"]["AI-48"]["total_h"]
    assert eng["per_initiative"]["AI-48"]["period_h"] == 0.0
    assert eng["per_initiative"]["AI-48"]["total_h"] > 0.0


def test_hours_slaat_worklog_call_over_zonder_timespent(client):
    jira_mod.hours(cfg(), client, S, keys=["AI-4"])
    gevraagd = {p.split("/")[-2] for p, _ in client.calls if p.endswith("/worklog")}
    assert {"AI-50", "AI-64", "AI-67", "AI-68"} <= gevraagd      # hebben timespent
    assert "AI-4" not in gevraagd and "AI-62" not in gevraagd    # timespent None → geen call
    assert "AI-25" not in gevraagd                              # zit niet in deze subtree


def test_hours_zonder_keys_neemt_alle_initiatieven(client):
    data = jira_mod.hours(cfg(), client, S)
    assert sorted(data["per_initiative"], key=jira_mod.key_sort) == \
        ["AI-4", "AI-5", "AI-6", "AI-25", "AI-48"]           # ook Afgesloten (AI-6)


# --- wijzigingen ---------------------------------------------------------------------------------

def test_changes_transities_nieuwe_links_en_nieuwe_initiatieven(client):
    data = jira_mod.changes(cfg(), client, S, since=dt.date(2026, 1, 1), until=dt.date(2026, 12, 31))
    assert data["since"] == "2026-01-01" and data["until"] == "2026-12-31"

    t = data["transitions"]
    assert t and all(set(x) == {"key", "from", "to", "when"} for x in t)
    assert [x["when"] for x in t] == sorted(x["when"] for x in t)
    # nette namen waar het schema ze kent, ruwe naam waar niet
    assert any(x["to"] == "Implementatie" for x in t)        # Jira 'implementatie'
    assert any(x["from"] == "Backlog" for x in t)            # buiten het schema

    l = data["new_links"]
    assert l and all(set(x) == {"key", "linked", "type", "when"} for x in l)
    assert {"key": "AI-25", "linked": "EAG-927", "type": "is gerelateerd aan"} in \
        [{k: v for k, v in x.items() if k != "when"} for x in l]
    assert any(x["type"] == "includes" and x["linked"] == "AI-62" for x in l)

    assert [n["key"] for n in data["new_initiatives"]] == ["AI-4", "AI-5", "AI-6", "AI-25", "AI-48"]
    assert all(set(n) == {"key", "summary", "created"} for n in data["new_initiatives"])


def test_changes_nieuwe_initiatieven_volgen_het_venster(client):
    """Alleen wie in het venster is aangemaakt telt als nieuw (AI-25 op 2026-05-06,
    AI-48 op 2026-07-13; AI-4/5/6 dateren van maart)."""
    data = jira_mod.changes(cfg(), client, S, since=dt.date(2026, 5, 1), until=dt.date(2026, 6, 30))
    assert [n["key"] for n in data["new_initiatives"]] == ["AI-25"]


def test_changes_venster_snijdt_af(client):
    data = jira_mod.changes(cfg(), client, S, since=dt.date(2026, 8, 1), until=dt.date(2026, 8, 31))
    assert all("2026-08-01" <= x["when"][:10] <= "2026-08-31" for x in data["transitions"])
    assert all("2026-08-01" <= x["when"][:10] <= "2026-08-31" for x in data["new_links"])


# --- schrijven: zonder --apply enkel de payload, met --apply weigert de guard -------------------

def test_link_rendert_payload_zonder_apply(client):
    out = jira_mod.link(cfg(), client, "AI-25", "EAG-999")
    assert out["applied"] is False and out["exists"] is False
    assert out["payload"] == {"type": {"name": "Gerelateerd"},
                              "inwardIssue": {"key": "AI-25"},
                              "outwardIssue": {"key": "EAG-999"}}


def test_link_is_idempotent(client):
    out = jira_mod.link(cfg(), client, "AI-25", "EAG-927")
    assert out["exists"] is True and out["applied"] is False


def test_link_met_apply_weigert_in_dry_run(client):
    with pytest.raises(config.GuardRefused):
        jira_mod.link(cfg(), client, "AI-25", "EAG-999", apply=True)
    # ook als de link al bestaat: de guard komt vóór de idempotentiecheck
    with pytest.raises(config.GuardRefused):
        jira_mod.link(cfg(), client, "AI-25", "EAG-927", apply=True)


def test_create_initiative_payload_en_guard(client):
    out = jira_mod.create_initiative(cfg(), client, S, "Titel", "Omschrijving", eag="EAG-999",
                                     verantwoordelijke="vancrake")
    f = out["payload"]["fields"]
    assert out["applied"] is False and out["key"] is None
    assert f["project"] == {"key": "AI"} and f["issuetype"] == {"id": "13506"}
    assert f["summary"] == "Titel" and f["description"] == "Omschrijving"
    assert f["customfield_14415"] == dt.date.today().isoformat()      # Datum ontvangst
    assert f["customfield_10614"] == {"name": "vancrake"}             # Verantwoordelijke
    assert "customfield_19014" not in f                               # Trekker niet meegegeven
    assert out["link"]["outwardIssue"] == {"key": "EAG-999"}
    with pytest.raises(config.GuardRefused):
        jira_mod.create_initiative(cfg(), client, S, "Titel", "", apply=True)


def test_transition_zoekt_het_id_en_weigert_met_apply(client):
    out = jira_mod.transition(cfg(), client, S, "AI-25", "Afgesloten", resolution="stopgezet")
    assert out["applied"] is False and out["to"] == "Closed"
    assert out["payload"] == {"transition": {"id": "71"}}
    # deze instance zet resolution niet op het transitiescherm → aparte edit-payload
    assert out["resolution_payload"] == {"fields": {"resolution": {"name": "stopgezet"}}}
    with pytest.raises(config.GuardRefused):
        jira_mod.transition(cfg(), client, S, "AI-25", "Afgesloten", apply=True)


def test_transition_meldt_een_onbereikbare_status(client):
    out = jira_mod.transition(cfg(), client, S, "AI-25", "Planning")
    assert out["payload"] is None and "geen transitie" in out["problem"]


def test_onbekende_status_is_een_gebruiksfout(client):
    """§6: ongeldige invoer is exit 4, en aiec.py vertaalt daarvoor ValueError."""
    with pytest.raises(ValueError) as e:
        jira_mod.transition(cfg(), client, S, "AI-25", "Verzonnen")
    assert "Verzonnen" in str(e.value) and not isinstance(e.value, KeyError)


# --- markdown --------------------------------------------------------------------------------

def test_markdown_renderers(client):
    lst = jira_mod.list_markdown(jira_mod.list_initiatives(cfg(), client, S))
    assert lst.startswith("# Jira-initiatieven (4)") and "| AI-25 |" in lst and "EAG-927" in lst

    h = jira_mod.hours_markdown(jira_mod.hours(cfg(), client, S, keys=["AI-25", "AI-48"],
                                               since=dt.date(2026, 7, 1)))
    assert "# Uren per initiatief" in h and "| AI-25 |" in h and "Totaal in de periode" in h

    c = jira_mod.changes_markdown(jira_mod.changes(cfg(), client, S, since=dt.date(2026, 1, 1)))
    assert "## Statuswissels" in c and "## Nieuwe initiatieven" in c and "## Nieuwe links" in c
