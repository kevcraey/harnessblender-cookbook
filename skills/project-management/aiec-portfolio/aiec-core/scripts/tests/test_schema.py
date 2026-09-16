"""Tests voor aiec_lib.schema (Fable, ontwerpfase). Draaien: cd scripts && uv run --with pytest --with pyyaml python -m pytest tests"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiec_lib import schema as sch  # noqa: E402

S = sch.load()


def test_schema_consistent():
    assert sch.check(S) == []


def test_status_mapping():
    assert sch.status_from_jira(S, "In Analyse") == ("Analyse", 1)
    assert sch.status_from_jira(S, "implementatie") == ("Implementatie", 3)
    assert sch.status_from_jira(S, "Closed") == ("Afgesloten", 6)
    assert sch.status_from_jira(S, "Onbekend") == ("Onbekend", None)
    assert sch.jira_from_status(S, "Uitvoering") == "Run"


def test_pijler_round_trip():
    assert sch.parse_pijler(S, "P2 — Mens & Adoptie") == "P2"
    assert sch.parse_pijler(S, "p2") == "P2"
    assert sch.parse_pijler(S, "Omkadering") == "OMK"
    assert sch.parse_pijler(S, "P9") is None
    assert sch.pijler_text(S, "P3") == "P3 — Interne Operaties & Productiviteit"


def test_normalize_values():
    vals, problems = sch.normalize_values(S, {
        "ai_key": "AI-25", "soort": "Afgebakend", "pijler": "P2 — Mens & Adoptie",
        "toepassingstype": "documentverwerking, Beslissingsondersteuning", "ai_act_klasse": "Beperkt",
        "persoonsgegevens": "JA", "herkomst": "Management", "onzin": 1, "eag_key": "EAG927"})
    assert vals["soort"] == "afgebakend"
    assert vals["pijler"] == "P2"
    assert vals["toepassingstype"] == ["Documentverwerking", "Beslissingsondersteuning"]
    assert vals["ai_act_klasse"] == "beperkt" and vals["persoonsgegevens"] == "ja"
    assert vals["batenclaim"] == "" and vals["ai_techniek"] == []
    assert any("onzin" in p for p in problems)
    assert any("EAG927" in p for p in problems)
    assert sch.display_value(S, sch.field(S, "toepassingstype"), vals["toepassingstype"]) == \
        "Documentverwerking, Beslissingsondersteuning"


def test_required_when():
    f = sch.field
    base = {"values": {"soort": "afgebakend", "batenclaim": ""}, "soort": "afgebakend", "fase": 1,
            "status": "Analyse", "resolution": None}
    assert sch.required_now(S, f(S, "ai_key"), base)
    assert sch.required_now(S, f(S, "eag_key"), base)
    assert not sch.required_now(S, f(S, "eag_key"), {**base, "soort": "doorlopend", "values": {"soort": "doorlopend"}})
    assert sch.required_now(S, f(S, "toepassingstype"), base)            # fase_min Analyse
    assert not sch.required_now(S, f(S, "delivery_mode"), base)          # fase_min Planning
    assert sch.required_now(S, f(S, "delivery_mode"), {**base, "fase": 2})
    assert not sch.required_now(S, f(S, "aanname"), base)
    assert sch.required_now(S, f(S, "aanname"), {**base, "values": {"soort": "afgebakend", "batenclaim": "400 manuren"}})
    closed = {**base, "fase": 6, "status": "Afgesloten", "resolution": "stopgezet"}
    assert sch.required_now(S, f(S, "stopreden"), closed)
    assert sch.required_now(S, f(S, "stopreden"), {**closed, "resolution": None})
    assert not sch.required_now(S, f(S, "stopreden"), {**closed, "resolution": "uitgevoerd"})
    assert not sch.required_now(S, f(S, "stopreden"), base)
