"""Tests voor aiec_lib.report (WP-B). build() is zuiver: geen netwerk, enkel de JSON-vormen uit
DESIGN.md §6. Het register komt uit tests/fixtures/register-sample.json; de Jira-kant wordt met
de FakeClient uit test_jira gevoed zodat de join op ai_key op echte (ingekorte) data draait.

Draaien: cd scripts && uv run --with pytest --with pyyaml python -m pytest tests -q
"""
import datetime as dt
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiec_lib import schema as sch  # noqa: E402
from aiec_lib import jira as jira_mod  # noqa: E402
from aiec_lib import report as report_mod  # noqa: E402

from test_jira import FakeClient, cfg  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"
S = sch.load()
SINCE, UNTIL = dt.date(2026, 7, 1), dt.date(2026, 9, 16)


def register():
    return json.loads((FIX / "register-sample.json").read_text())


@pytest.fixture
def bouwstenen():
    """(register, initiatives, hours, changes) op de fixtures; enkel de vier initiatieven die in
    beide bronnen zitten blijven over na de join."""
    c = FakeClient()
    initiatives = jira_mod.list_initiatives(cfg(), c, S, include_closed=True)
    hours = jira_mod.hours(cfg(), c, S, since=SINCE, until=UNTIL)
    changes = jira_mod.changes(cfg(), c, S, since=SINCE, until=UNTIL)
    return register(), initiatives, hours, changes


def bouw(bouwstenen, violations=None, tarief=0):
    reg, init, hrs, chg = bouwstenen
    c = cfg()
    c["report"] = dict(c["report"], uurtarief_eur=tarief)
    return report_mod.build(S, c, reg, init, hrs, chg, violations or [], SINCE, UNTIL)


# --- vorm ---------------------------------------------------------------------------------------

def test_build_heeft_alle_blokken_uit_het_contract(bouwstenen):
    d = bouw(bouwstenen)
    assert {"per_pijler", "per_status", "funnel", "doorlopend", "frigo", "risico", "heatmap",
            "kost", "bewogen", "nieuw", "zonder_pagina"} <= set(d)
    assert d["since"] == "2026-07-01" and d["until"] == "2026-09-16"
    assert [r["key"] for r in d["initiatieven"]] == ["AI-4", "AI-5", "AI-6", "AI-25", "AI-48"]


def test_join_neemt_de_paginatitel_en_de_details(bouwstenen):
    d = bouw(bouwstenen)
    ai25 = next(r for r in d["initiatieven"] if r["key"] == "AI-25")
    assert ai25["titel"].startswith("[AI-25]")        # paginatitel wint van de Jira-summary
    assert ai25["soort"] == "afgebakend" and ai25["pijler"] == "P2"
    assert ai25["afdeling"] == "BELEID" and ai25["persoonsgegevens"] == "ja"
    assert ai25["status"] == "Analyse"                # uit Jira, nooit uit het register
    assert ai25["uren_totaal"] > 0


def test_initiatief_zonder_registerpagina(bouwstenen):
    """Het register kent AI-5 wel; een Jira-initiatief zonder pagina belandt in zonder_pagina."""
    reg, init, hrs, chg = bouwstenen
    reg = {**reg, "pages": [p for p in reg["pages"] if p["ai_key"] != "AI-5"]}
    d = bouw((reg, init, hrs, chg))
    assert [z["key"] for z in d["zonder_pagina"]] == ["AI-5"]
    ai5 = next(r for r in d["initiatieven"] if r["key"] == "AI-5")
    assert ai5["titel"] == "Obscuro"                 # valt terug op de Jira-summary
    assert ai5["soort"] == "" and ai5["pijler"] == ""


# --- groeperingen ---------------------------------------------------------------------------------

def test_per_pijler_groepeert_op_code(bouwstenen):
    d = bouw(bouwstenen)
    per = {p["code"]: [i["key"] for i in p["initiatieven"]] for p in d["per_pijler"]}
    assert per["P1"] == ["AI-4", "AI-5", "AI-6"]
    assert per["P2"] == ["AI-25"]
    assert per["OMK"] == ["AI-48"]
    assert per["P3"] == [] and per["P4"] == []       # lege pijlers blijven staan
    velden = {"key", "titel", "status", "soort", "opgeleverd", "gebruikers", "batenclaim",
              "aanname", "uren_periode", "uren_totaal"}
    assert all(set(i) == velden for p in d["per_pijler"] for i in p["initiatieven"])


def test_per_pijler_vangt_initiatieven_zonder_pijler_op(bouwstenen):
    reg, init, hrs, chg = bouwstenen
    reg = {**reg, "pages": [p for p in reg["pages"] if p["ai_key"] != "AI-5"]}
    d = bouw((reg, init, hrs, chg))
    rest = next(p for p in d["per_pijler"] if p["code"] is None)
    assert [i["key"] for i in rest["initiatieven"]] == ["AI-5"]


def test_per_status_telt_ook_statussen_buiten_het_schema(bouwstenen):
    d = bouw(bouwstenen)
    assert d["per_status"]["Analyse"] == 1           # AI-25
    assert d["per_status"]["Implementatie"] == 2     # AI-4, AI-5
    assert d["per_status"]["Uitvoering"] == 1        # AI-48 (Jira 'Run')
    assert d["per_status"]["Afgesloten"] == 1        # AI-6
    assert sum(d["per_status"].values()) == len(d["initiatieven"])


def test_funnel_laat_doorlopend_buiten_beschouwing(bouwstenen):
    d = bouw(bouwstenen)
    assert d["funnel"]["fase"]["Uitvoering"] == 0    # AI-48 is doorlopend
    assert d["funnel"]["fase"]["Implementatie"] == 2
    assert sum(d["funnel"]["fase"].values()) == 4
    # AI-6 is Closed zonder resolution 'uitgevoerd' → telt mee met zijn stopreden
    assert d["funnel"]["stopreden"] == {"geen capaciteit": 1}


def test_funnel_stopreden_valt_weg_bij_uitvoering(bouwstenen):
    reg, init, hrs, chg = bouwstenen
    issues = [dict(i, resolution="Gerealiseerd") if i["key"] == "AI-6" else i
              for i in init["issues"]]
    d = bouw((reg, {**init, "issues": issues}, hrs, chg))
    assert d["funnel"]["stopreden"] == {}


def test_doorlopend_krijgt_de_uren_van_de_eigen_werking(bouwstenen):
    d = bouw(bouwstenen)
    assert [x["key"] for x in d["doorlopend"]] == ["AI-48"]
    assert d["doorlopend"][0]["uren_totaal"] > 0


# --- risico, heatmap, frigo, kost -----------------------------------------------------------------

def test_risico_per_klasse_en_persoonsgegevens(bouwstenen):
    """Herverdeling van de register-details over de AI Act-klassen; elk gejoind initiatief komt
    in precies één emmer terecht."""
    reg, d = bouwstenen[0], bouw(bouwstenen)
    details = {p["ai_key"]: p["details"] for p in reg["pages"]}
    keys = [r["key"] for r in d["initiatieven"]]
    per = d["risico"]["per_klasse"]
    assert set(per) == set(sch.field(S, "ai_act_klasse")["values"]) | {report_mod.ONBEKEND}
    for klasse, gevonden in per.items():
        verwacht = [k for k in keys
                    if (details.get(k, {}).get("ai_act_klasse") or report_mod.ONBEKEND) == klasse]
        assert gevonden == verwacht
    assert sorted(x for v in per.values() for x in v) == sorted(keys)   # geen dubbels
    assert "AI-25" in per["beperkt"] and per["hoog"] == []
    assert d["risico"]["persoonsgegevens_ja"] == \
        [k for k in keys if details.get(k, {}).get("persoonsgegevens") == "ja"]
    assert "AI-25" in d["risico"]["persoonsgegevens_ja"]


def test_heatmap_telt_afdeling_tegen_toepassingstype(bouwstenen):
    d = bouw(bouwstenen)
    assert d["heatmap"]["BELEID"] == {"Documentverwerking": 1, "Beslissingsondersteuning": 1}
    assert d["heatmap"]["DIGITALISERING"]["Procesautomatisering"] == 1
    # zonder afdeling of zonder toepassingstype: één streepje-emmer
    assert report_mod.ONBEKEND in d["heatmap"]


def test_frigo_komt_uit_de_violations(bouwstenen):
    v = [{"rule": "frigo", "severity": "waarschuwing", "ai_key": "AI-25", "page_id": "431293025",
          "message": "121 dagen stil", "fix": None},
         {"rule": "geen-eag", "severity": "waarschuwing", "ai_key": "AI-4", "page_id": None,
          "message": "geen EAG", "fix": None}]
    d = bouw(bouwstenen, violations=v)
    assert [f["ai_key"] for f in d["frigo"]] == ["AI-25"]
    assert d["frigo"][0]["titel"].startswith("[AI-25]")
    assert d["violations_per_ernst"] == {"waarschuwing": 2}


def test_kost_zonder_tarief_geeft_geen_euro(bouwstenen):
    d = bouw(bouwstenen)
    assert d["kost"]["euro"] is None and d["kost"]["aanname_tarief"] is None
    assert d["kost"]["uren_periode"] == pytest.approx(
        round(sum(r["uren_periode"] for r in d["initiatieven"]), 2))
    assert d["kost"]["uren_totaal"] >= d["kost"]["uren_periode"]


def test_kost_met_tarief_markeert_de_aanname(bouwstenen):
    d = bouw(bouwstenen, tarief=95)
    assert d["kost"]["aanname_tarief"] == 95
    assert d["kost"]["euro"] == pytest.approx(round(d["kost"]["uren_periode"] * 95, 2))
    md = report_mod.to_markdown(d)
    assert "aanname" in md and "95.00 €/u" in md


# --- beweging ---------------------------------------------------------------------------------------

def test_bewogen_verzamelt_transities_links_en_pagina_activiteit(bouwstenen):
    d = bouw(bouwstenen)
    bewogen = {b["key"]: b for b in d["bewogen"]}
    assert "AI-4" in bewogen                          # transitie Captatie → implementatie in juli
    assert bewogen["AI-4"]["transities"]
    assert "AI-25" in bewogen                         # pagina-activiteit 2026-09-02
    assert bewogen["AI-25"]["pagina_activiteit"] == "2026-09-02T09:12:00"
    assert [b["key"] for b in d["bewogen"]] == sorted(bewogen, key=jira_mod.key_sort)


def test_bewogen_laat_stille_initiatieven_weg(bouwstenen):
    d = bouw(bouwstenen)
    assert "AI-6" not in {b["key"] for b in d["bewogen"]}   # afgesloten in juni, pagina juni


# --- markdown -----------------------------------------------------------------------------------------

def test_to_markdown_volgt_de_volgorde_van_build(bouwstenen):
    md = report_mod.to_markdown(bouw(bouwstenen))
    koppen = [r for r in md.splitlines() if r.startswith("## ")]
    assert koppen == ["## Per pijler", "## Per status", "## Funnel (afgebakend)",
                      "## Doorlopende werking", "## Frigo", "## Risico",
                      "## Heatmap (afdeling × toepassingstype)", "## Kost",
                      "## Bewogen sinds 2026-07-01", "## Nieuw", "## Zonder registerpagina"]
    assert "| AI-25 |" in md and "Geen." in md          # lege tabellen zeggen 'Geen.'
    assert "geen tarief in de config" in md


def test_lege_invoer_breekt_niet(bouwstenen):
    d = report_mod.build(S, cfg(), {"pages": []}, {"issues": []}, {}, {}, [], SINCE, UNTIL)
    assert d["initiatieven"] == [] and d["kost"]["uren_periode"] == 0
    assert report_mod.to_markdown(d).startswith("# AIEC-portfolio")
