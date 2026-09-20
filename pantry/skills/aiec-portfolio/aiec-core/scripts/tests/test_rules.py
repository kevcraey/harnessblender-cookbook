"""Regels van DESIGN.md §7 (WP-D). Elke regel krijgt één positieve en één negatieve case uit
tests/fixtures/register-sample.json + initiatives-sample.json. Vandaag staat vast op 2026-09-16,
zodat frigo (grens 90 dagen) reproduceerbaar is. Geen netwerk."""
import copy
import datetime as dt
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiec_lib import config, rules, schema as sch  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VANDAAG = dt.date(2026, 9, 16)
S = sch.load()


def cfg(frigo_dagen=90):
    c = config._merge(config.DEFAULTS, {"report": {"frigo_dagen": frigo_dagen}})
    c["_path"] = "<test>"
    return c


@pytest.fixture
def register():
    return json.loads((FIXTURES / "register-sample.json").read_text())


@pytest.fixture
def initiatives():
    return json.loads((FIXTURES / "initiatives-sample.json").read_text())


@pytest.fixture
def gemeld(register, initiatives):
    """{ai_key: {regel, ...}} over de hele fixture-set."""
    out = {}
    for v in rules.validate(S, cfg(), register, initiatives, today=VANDAAG):
        out.setdefault(v["ai_key"], set()).add(v["rule"])
    return out


def pagina(register, key):
    return next(p for p in register["pages"] if p["ai_key"] == key)


def issue(initiatives, key):
    return next(i for i in initiatives["issues"] if i["key"] == key)


def run(register, initiatives, **kw):
    return rules.validate(S, cfg(kw.pop("frigo_dagen", 90)), register, initiatives,
                          today=kw.pop("today", VANDAAG))


def regels(violations, key):
    return {v["rule"] for v in violations if v["ai_key"] == key}


# --- de zestien regels: positief en negatief ---------------------------------------------------

@pytest.mark.parametrize("regel, positief, negatief", [
    ("ontbrekend-veld", "AI-14", "AI-3"),           # vrager leeg bij afgebakend
    ("enum-buiten-bereik", "AI-21", "AI-3"),        # herkomst 'topdown'
    ("pijler-tekst-verouderd", "AI-27", "AI-3"),    # celtekst 'P2 — Slimme oplossingen'
    ("geen-eag", "AI-21", "AI-3"),
    ("eag-link-ontbreekt", "AI-16", "AI-3"),
    ("eag-mismatch", "AI-17", "AI-3"),
    ("geen-captatierapport", "AI-16", "AI-3"),
    ("geen-verkenningsrapport", "AI-7", "AI-3"),
    ("frigo", "AI-21", "AI-14"),                    # beide Captatie, AI-14 bewoog recent
    ("geen-stopreden", "AI-5", "AI-47"),            # AI-47 is afgesloten als uitgevoerd
    ("geen-pagina", "AI-82", "AI-3"),
    ("wees-pagina", "AI-99", "AI-3"),
    ("titel-drift", "AI-16", "AI-3"),
    ("doorlopend-in-funnel", "AI-52", "AI-3"),
    ("artefact-zonder-label", "AI-27", "AI-3"),
    ("baten-zonder-aanname", "AI-49", "AI-3"),
])
def test_regel_positief_en_negatief(gemeld, regel, positief, negatief):
    assert regel in gemeld.get(positief, set())
    assert regel not in gemeld.get(negatief, set())


def test_schone_initiatieven_geven_niets(gemeld):
    assert "AI-3" not in gemeld and "AI-47" not in gemeld


def test_elke_regel_uit_het_ontwerp_komt_voor(gemeld):
    gezien = {r for regels_ in gemeld.values() for r in regels_}
    verwacht = {"ontbrekend-veld", "enum-buiten-bereik", "pijler-tekst-verouderd", "geen-eag",
                "eag-link-ontbreekt", "eag-mismatch", "geen-captatierapport",
                "geen-verkenningsrapport", "frigo", "geen-stopreden", "geen-pagina", "wees-pagina",
                "titel-drift", "doorlopend-in-funnel", "artefact-zonder-label",
                "baten-zonder-aanname"}
    assert gezien == verwacht


# --- vorm van een violation ---------------------------------------------------------------------

def test_violation_vorm_en_ernst(register, initiatives):
    ernsten = {"fout", "waarschuwing", "info"}
    for v in run(register, initiatives):
        assert set(v) == {"rule", "severity", "ai_key", "page_id", "message", "fix"}
        assert v["severity"] in ernsten and v["message"]
        if v["fix"]:
            assert v["fix"]["action"] in {"label", "jira-link", "rerender", "transition"}
            assert isinstance(v["fix"]["args"], dict)


def test_volgorde_is_stabiel_en_per_initiatief(register, initiatives):
    vs = run(register, initiatives)
    assert [v["ai_key"] for v in vs] == sorted(
        (v["ai_key"] for v in vs), key=lambda k: int(k.split("-")[1]))
    for eerder, later in zip(vs, vs[1:]):
        if eerder["ai_key"] == later["ai_key"]:
            assert rules.SEVERITY_ORDER[eerder["severity"]] <= rules.SEVERITY_ORDER[later["severity"]]


def test_fixes_wijzen_naar_de_juiste_actie(register, initiatives):
    fixes = {(v["rule"], v["fix"]["action"]) for v in run(register, initiatives) if v["fix"]}
    assert ("eag-link-ontbreekt", "jira-link") in fixes
    assert ("pijler-tekst-verouderd", "rerender") in fixes
    assert ("artefact-zonder-label", "label") in fixes
    fix = next(v["fix"] for v in run(register, initiatives) if v["rule"] == "eag-link-ontbreekt")
    assert fix["args"] == {"key": "AI-16", "eag": "EAG-921"}


# --- randgevallen per regel ---------------------------------------------------------------------

def test_frigo_volgt_de_config(register, initiatives):
    assert "frigo" in regels(run(register, initiatives, frigo_dagen=90), "AI-21")
    assert "frigo" not in regels(run(register, initiatives, frigo_dagen=200), "AI-21")
    # precies op de grens (167 dagen stil) telt niet als frigo: "stil > frigo_dagen"
    assert "frigo" not in regels(run(register, initiatives, frigo_dagen=167), "AI-21")
    assert "frigo" in regels(run(register, initiatives, frigo_dagen=166), "AI-21")


def test_frigo_kijkt_naar_beide_bronnen(register, initiatives):
    pagina(register, "AI-21")["last_activity"] = "2026-09-01T10:00:00"
    assert "frigo" not in regels(run(register, initiatives), "AI-21")


def test_frigo_niet_voor_doorlopend_of_late_fase(register, initiatives):
    # AI-48 is doorlopend en staat in Uitvoering; stilte mag daar.
    issue(initiatives, "AI-48")["updated"] = "2025-11-04T08:00:00.000+0100"
    pagina(register, "AI-48")["last_activity"] = "2025-11-04T08:00:00"
    assert "frigo" not in regels(run(register, initiatives), "AI-48")


def test_ontbrekend_veld_volgt_de_fase(register, initiatives):
    # delivery_mode is pas verplicht vanaf Planning; AI-27 staat in Analyse.
    assert "ontbrekend-veld" not in regels(run(register, initiatives), "AI-27")
    i = issue(initiatives, "AI-27")
    i["status"], i["status_raw"], i["fase"] = "Planning", "Prioritering en planning", 2
    boodschappen = [v["message"] for v in run(register, initiatives)
                    if v["ai_key"] == "AI-27" and v["rule"] == "ontbrekend-veld"]
    assert any("Delivery-mode" in m for m in boodschappen)
    assert any("Batenclaim" in m for m in boodschappen)


def test_pagina_zonder_details_blok_geeft_een_melding(register, initiatives):
    # De toestand vóór de retro-fit: liever één melding met de lijst dan vijf losse.
    p = pagina(register, "AI-3")
    p["has_details"], p["details"], p["details_raw"] = False, {}, {}
    vs = [v for v in run(register, initiatives) if v["ai_key"] == "AI-3" and v["rule"] == "ontbrekend-veld"]
    assert len(vs) == 1
    for label in ("AI-key", "Soort", "Pijler", "AI Act-klasse", "Persoonsgegevens"):
        assert label in vs[0]["message"]


def test_doorlopend_ontsnapt_aan_de_afgebakende_verplichtingen(gemeld):
    # AI-52 heeft geen EAG-key, geen vrager, geen afdeling: dat mag bij doorlopende werking.
    assert gemeld.get("AI-52") == {"doorlopend-in-funnel"}


def test_lege_eag_key_met_jira_link_is_een_ontbrekend_veld(register, initiatives):
    pagina(register, "AI-16")["details"]["eag_key"] = ""
    issue(initiatives, "AI-16")["eag_keys"] = ["EAG-921"]
    vs = [v for v in run(register, initiatives) if v["ai_key"] == "AI-16"]
    ontbreekt = [v for v in vs if v["rule"] == "ontbrekend-veld"]
    assert len(ontbreekt) == 1 and "EAG-921" in ontbreekt[0]["message"]
    assert not [v for v in vs if v["rule"] in ("geen-eag", "eag-link-ontbreekt", "eag-mismatch")]


def test_geen_stopreden_en_ontbrekend_veld_dubbelen_niet(register, initiatives):
    vs = [v for v in run(register, initiatives) if v["ai_key"] == "AI-5"]
    assert [v["rule"] for v in vs] == ["geen-stopreden"]


def test_baten_zonder_aanname_dubbelt_niet_met_ontbrekend_veld(register, initiatives):
    vs = [v for v in run(register, initiatives) if v["ai_key"] == "AI-49"]
    assert [v["rule"] for v in vs] == ["baten-zonder-aanname"]
    pagina(register, "AI-49")["details"]["aanname"] = "1500 dossiers x 5 minuten"
    assert "AI-49" not in {v["ai_key"] for v in run(register, initiatives)}


def test_titel_zonder_key_en_titel_met_drift(register, initiatives):
    boodschap = {v["ai_key"]: v["message"] for v in run(register, initiatives)
                 if v["rule"] == "titel-drift"}
    assert "bevat de key niet" in boodschap["AI-17"]
    assert "Jira-summary" in boodschap["AI-16"]


def test_pagina_zonder_ai_key_is_een_wees(register, initiatives):
    p = copy.deepcopy(pagina(register, "AI-99"))
    p.update(page_id="999", title="Losse notitie", ai_key=None)
    register["pages"].append(p)
    wees = [v for v in run(register, initiatives) if v["rule"] == "wees-pagina" and v["ai_key"] is None]
    assert len(wees) == 1 and wees[0]["page_id"] == "999"


def test_lege_datasets(register):
    assert rules.validate(S, cfg(), {"pages": []}, {"issues": []}, today=VANDAAG) == []
    vs = rules.validate(S, cfg(), register, {"issues": []}, today=VANDAAG)
    assert {v["rule"] for v in vs if v["rule"].endswith("pagina")} == {"wees-pagina"}


# --- markdown -----------------------------------------------------------------------------------

def test_markdown_groepeert_en_telt(register, initiatives):
    md = rules.to_markdown(run(register, initiatives))
    assert md.startswith("# Regelcheck AIEC-portfolio")
    assert "## AI-21" in md and "## Telling per regel" in md
    assert md.index("## AI-14") < md.index("## AI-21")         # oplopend op nummer
    assert "`geen-stopreden`" in md and "→ fix `jira-link`" in md
    assert "# ONGEVERIFIEERD" not in md


def test_markdown_zonder_meldingen():
    assert "Geen meldingen." in rules.to_markdown([])
