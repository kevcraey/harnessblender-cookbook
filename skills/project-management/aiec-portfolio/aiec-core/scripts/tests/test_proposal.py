"""Voorstel-bestanden (DESIGN.md §8) — parser, skelet en apply (WP-D). Geen netwerk: de calls naar
confluence/jira worden gemonkeypatcht, en het dry-run-pad mag er helemaal geen doen."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiec_lib import config, confluence, jira, proposal, schema as sch  # noqa: E402

S = sch.load()

# Het voorbeeld uit DESIGN.md §8, letterlijk.
VOORBEELD = """# aiec voorstel — retrofit — 2026-09-16
<!-- aiec:proposal v1 -->

## AI-25 — AI-ondersteuning Milieu-Investerings-Aftrek
- pagina: 431293025
- actie: upsert-details

| veld | waarde | bron | zekerheid |
|---|---|---|---|
| soort | afgebakend | jira | hoog |
| pijler | P2 | briefing 2026-09-06 | midden |
| batenclaim |  | — | KENZO |

### Acties
- [x] label ai-initiatief
- [ ] jira link AI-25 EAG-927
"""

# Zelfde vorm, maar met alles wat de parser verder moet aankunnen: een doorstreepte rij, een label
# in plaats van een key in de eerste kolom, create-page, skip en een transitie met resolutie.
UITGEBREID = """# aiec voorstel — groom — 2026-09-16
<!-- aiec:proposal v1 -->

## AI-16 — Detectie van illegale dierenverkoop
- pagina: 431293016
- actie: upsert-details

| veld | waarde | bron | zekerheid |
|---|---|---|---|
| Soort | afgebakend | jira | hoog |
| AI Act-klasse | hoog | captatierapport | hoog |
| Toepassingstype | Beeld- & sensoranalyse, Voorspellen & detecteren | intake | midden |
| ~~vrager~~ | ~~teamhoofd handhaving~~ | ~~intake~~ | ~~laag~~ |
| batenclaim |  | — | KENZO |

### Acties
- [x] jira link AI-16 EAG-921
- [ ] label verkenningsrapport

## AI-82 — Digitale Assistent Departement Omgeving
- actie: create-page

| veld | waarde | bron | zekerheid |
|---|---|---|---|
| ai_key | AI-82 | jira | hoog |
| soort | afgebakend | jira | hoog |

## AI-6 — Grup arresten migreren naar tech stack dOMG
- pagina: 431293006
- actie: skip

### Acties
- [x] jira transition AI-6 Afgesloten stopgezet
"""


def cfg(mode="dry-run"):
    c = config._merge(config.DEFAULTS, {"writes": {"mode": mode}})
    c["_path"] = "<test>"
    return c


def geen_clients():
    raise AssertionError("dry-run mag geen client vragen")


# --- parser ------------------------------------------------------------------------------------

def test_voorbeeld_uit_het_ontwerp():
    p = proposal.parse(VOORBEELD, S)
    assert p["soort"] == "retrofit" and p["datum"] == "2026-09-16" and p["versie"] is True
    assert p["problems"] == []
    item, = p["items"]
    assert item["ai_key"] == "AI-25"
    assert item["titel"] == "AI-ondersteuning Milieu-Investerings-Aftrek"
    assert item["pagina"] == "431293025" and item["actie"] == "upsert-details"
    assert item["values"] == {"soort": "afgebakend", "pijler": "P2"}    # lege waarde = niet zetten
    assert item["acties"] == [{"checked": True, "kind": "label", "args": ["ai-initiatief"]},
                              {"checked": False, "kind": "jira-link", "args": ["AI-25", "EAG-927"]}]
    assert item["problems"] == []


def test_parser_zonder_schema_laadt_zelf():
    assert proposal.parse(VOORBEELD)["items"][0]["values"]["pijler"] == "P2"


def test_bestand_van_schijf(tmp_path):
    f = tmp_path / "retrofit.md"
    f.write_text(VOORBEELD)
    assert proposal.parse(f.read_text(), S)["items"][0]["pagina"] == "431293025"


def test_label_in_de_eerste_kolom_en_doorstreepte_rij():
    item = proposal.parse(UITGEBREID, S)["items"][0]
    assert item["values"] == {"soort": "afgebakend", "ai_act_klasse": "hoog",
                              "toepassingstype": ["Beeld- & sensoranalyse", "Voorspellen & detecteren"]}
    assert "vrager" not in item["values"]        # ~~-rij wordt overgeslagen
    assert item["problems"] == []


def test_create_page_en_skip_en_transitie():
    p = proposal.parse(UITGEBREID, S)
    assert p["soort"] == "groom"
    create, skip = p["items"][1], p["items"][2]
    assert create["actie"] == "create-page" and create["pagina"] is None and create["problems"] == []
    assert create["values"] == {"ai_key": "AI-82", "soort": "afgebakend"}
    assert skip["actie"] == "skip" and skip["values"] == {}
    assert skip["acties"] == [{"checked": True, "kind": "jira-transition",
                               "args": ["AI-6", "Afgesloten", "stopgezet"]}]


def test_transitie_zonder_resolutie():
    tekst = "## AI-7 — x\n- actie: skip\n\n### Acties\n- [x] jira transition AI-7 Planning\n"
    actie, = proposal.parse(tekst, S)["items"][0]["acties"]
    assert actie["args"] == ["AI-7", "Planning"]


def test_pipe_in_een_waarde():
    tekst = "## AI-9 — x\n- actie: skip\n\n| veld | waarde |\n|---|---|\n| opgeleverd | a \\| b | \n"
    assert proposal.parse(tekst, S)["items"][0]["values"]["opgeleverd"] == "a | b"


@pytest.mark.parametrize("regel, fragment", [
    ("| onzin | x | — | — |", "geen veld uit het schema"),
    ("| soort | onbekend | — | — |", "niet in afgebakend, doorlopend"),
])
def test_tabelfouten_worden_gemeld(regel, fragment):
    tekst = f"## AI-9 — x\n- pagina: 1\n- actie: upsert-details\n\n| veld | waarde |\n|---|---|\n{regel}\n"
    item = proposal.parse(tekst, S)["items"][0]
    assert any(fragment in p for p in item["problems"])
    assert item["values"] == {}


def test_onbekende_actie_en_ontbrekende_pagina():
    tekst = ("## AI-9 — x\n- actie: upsert-details\n\n### Acties\n- [x] confluence verwijder alles\n")
    item = proposal.parse(tekst, S)["items"][0]
    assert any("niet herkend" in p for p in item["problems"])
    assert any("zonder 'pagina:'" in p for p in item["problems"])
    assert item["acties"] == []


def test_onbekende_status_in_een_transitie():
    tekst = "## AI-7 — x\n- actie: skip\n\n### Acties\n- [x] jira transition AI-7 Bezig\n"
    item = proposal.parse(tekst, S)["items"][0]
    assert any("status 'Bezig' onbekend" in p for p in item["problems"])
    assert item["acties"] == []


def test_create_page_zonder_titel():
    item = proposal.parse("## AI-9\n- actie: create-page\n", S)["items"][0]
    assert any("create-page zonder titel" in p for p in item["problems"])


def test_label_zonder_pagina():
    tekst = "## AI-9 — x\n- actie: skip\n\n### Acties\n- [x] label ai-initiatief\n"
    item = proposal.parse(tekst, S)["items"][0]
    assert any("'label' zonder 'pagina:'" in p for p in item["problems"])


def test_onbekende_soort_en_actie_in_de_kop():
    p = proposal.parse("# aiec voorstel — onzin — 2026-09-16\n\n## AI-9 — x\n- actie: verwijder\n", S)
    assert any("geen retrofit" in x for x in p["problems"])
    assert any("geen upsert-details" in x for x in p["items"][0]["problems"])


def test_zonder_marker_en_zonder_items():
    p = proposal.parse("# aiec voorstel — groom — 2026-09-16\n", S)
    assert p["versie"] is False and p["items"] == []


# --- skelet ------------------------------------------------------------------------------------

def test_skeleton_round_trip():
    values = {"ai_key": "AI-25", "soort": "afgebakend", "pijler": "P2",
              "toepassingstype": ["Documentverwerking", "Kennisontsluiting & zoeken"]}
    sectie = proposal.skeleton(S, "retrofit", "AI-25", "AI-ondersteuning MIA", "431293025",
                               "upsert-details", values, bronnen={"soort": "jira"},
                               zekerheid={"soort": "hoog"},
                               acties=[{"checked": True, "kind": "label", "args": ["ai-initiatief"]},
                                       {"checked": False, "kind": "jira-link",
                                        "args": ["AI-25", "EAG-927"]}])
    assert "| batenclaim |  | — | KENZO |" in sectie       # not_inferable blijft leeg voor Kenzo
    p = proposal.parse(proposal.document("retrofit", [sectie], "2026-09-16"), S)
    item, = p["items"]
    assert p["soort"] == "retrofit" and p["versie"] is True and item["problems"] == []
    assert item["values"] == values
    assert item["pagina"] == "431293025" and item["actie"] == "upsert-details"
    assert item["acties"][0] == {"checked": True, "kind": "label", "args": ["ai-initiatief"]}
    assert item["acties"][1]["checked"] is False


def test_skeleton_pijlertekst_wordt_weer_de_code():
    sectie = proposal.skeleton(S, "retrofit", "AI-9", "x", None, "create-page", {"pijler": "OMK"})
    assert "| pijler | OMK — Omkadering |" in sectie
    assert proposal.parse(proposal.document("retrofit", [sectie]), S)["items"][0]["values"] == {"pijler": "OMK"}


# --- apply: dry-run ------------------------------------------------------------------------------

def test_dry_run_raakt_geen_client_aan():
    r = proposal.apply(cfg(), S, proposal.parse(VOORBEELD, S), apply=False, clients=geen_clients)
    assert r["applied"] is False and r["mode"] == "dry-run"
    item, = r["items"]
    assert item["status"] == "ok" and item["fout"] is None
    assert item["gedaan"] == ["upsert-details op pagina 431293025 (2 veld(en))",
                              "label ai-initiatief op pagina 431293025"]
    assert item["overgeslagen"] == ["niet aangevinkt: jira link AI-25 EAG-927"]


def test_dry_run_verslag_over_alle_soorten_items():
    r = proposal.apply(cfg(), S, proposal.parse(UITGEBREID, S), apply=False, clients=geen_clients)
    statussen = {i["ai_key"]: i["status"] for i in r["items"]}
    assert statussen == {"AI-16": "ok", "AI-82": "ok", "AI-6": "ok"}
    assert r["items"][1]["gedaan"] == ["create-page 'Digitale Assistent Departement Omgeving' (2 veld(en))"]
    assert r["items"][2]["overgeslagen"] == ["actie: skip"]
    assert r["items"][2]["gedaan"] == ["jira transition AI-6 → Afgesloten (stopgezet)"]
    md = proposal.result_markdown(r)
    assert "dry-run" in md and "zou gebeuren" in md and "## AI-82 — ok" in md


def test_item_zonder_werk_is_overgeslagen():
    tekst = "## AI-6 — x\n- actie: skip\n"
    r = proposal.apply(cfg(), S, proposal.parse(tekst, S), apply=False, clients=geen_clients)
    assert r["items"][0]["status"] == "overgeslagen"


def test_parserfout_maakt_het_item_fout_maar_stopt_de_rest_niet():
    tekst = UITGEBREID.replace("| Soort | afgebakend | jira | hoog |", "| onzin | x | — | — |")
    r = proposal.apply(cfg(), S, proposal.parse(tekst, S), apply=False, clients=geen_clients)
    assert [i["status"] for i in r["items"]] == ["fout", "ok", "ok"]
    assert "geen veld uit het schema" in r["items"][0]["fout"]


# --- apply: de guard ------------------------------------------------------------------------------

def test_apply_in_dry_run_mode_wordt_geweigerd():
    with pytest.raises(config.GuardRefused):
        proposal.apply(cfg("dry-run"), S, proposal.parse(VOORBEELD, S), apply=True,
                       clients=geen_clients)


def test_apply_zonder_clients_is_een_programmeerfout():
    with pytest.raises(ValueError):
        proposal.apply(cfg("production"), S, proposal.parse(VOORBEELD, S), apply=True)


# --- apply: uitvoeren (calls gemonkeypatcht) -------------------------------------------------------

@pytest.fixture
def recorder(monkeypatch):
    calls = []

    def conf_upsert(cfg_, client, schema, page_id, values, apply=False):
        calls.append(("upsert", page_id, values, apply))
        return {"page_id": page_id, "applied": apply, "version_after": 8}

    def conf_create(cfg_, client, schema, values, titel, parent_id=None, samenvatting="", apply=False):
        calls.append(("create", titel, values, apply))
        return {"page_id": "999", "applied": apply}

    def conf_labels(cfg_, client, page_id, labels, apply=False):
        calls.append(("labels", page_id, labels, apply))
        return {"page_id": page_id, "toegevoegd": labels, "applied": apply}

    def jira_link(cfg_, client, key, other, apply=False):
        calls.append(("link", key, other, apply))
        return {"applied": apply}

    def jira_transition(cfg_, client, schema, key, to_naam, resolution=None, apply=False):
        calls.append(("transition", key, to_naam, resolution, apply))
        return {"applied": apply}

    monkeypatch.setattr(confluence, "upsert_details", conf_upsert)
    monkeypatch.setattr(confluence, "create_initiative", conf_create)
    monkeypatch.setattr(confluence, "set_labels", conf_labels)
    monkeypatch.setattr(jira, "link", jira_link)
    monkeypatch.setattr(jira, "transition", jira_transition)
    return calls


def test_apply_in_production_voert_uit(recorder):
    r = proposal.apply(cfg("production"), S, proposal.parse(VOORBEELD, S), apply=True,
                       clients=lambda: ("cc", "jc"))
    assert r["applied"] is True and r["items"][0]["status"] == "ok"
    assert recorder == [("upsert", "431293025", {"soort": "afgebakend", "pijler": "P2"}, True),
                        ("labels", "431293025", ["ai-initiatief"], True)]
    assert "versie 8" in r["items"][0]["gedaan"][0]
    assert "gedaan" in proposal.result_markdown(r)


def test_apply_voert_alle_items_uit_en_slaat_niet_aangevinkte_over(recorder):
    r = proposal.apply(cfg("production"), S, proposal.parse(UITGEBREID, S), apply=True,
                       clients=lambda: ("cc", "jc"))
    assert [i["status"] for i in r["items"]] == ["ok", "ok", "ok"]
    assert [c[0] for c in recorder] == ["upsert", "link", "create", "transition"]
    assert recorder[-1] == ("transition", "AI-6", "Afgesloten", "stopgezet", True)


def test_create_page_geeft_de_nieuwe_pagina_door_aan_het_label(recorder):
    tekst = ("## AI-82 — Digitale Assistent Departement Omgeving\n- actie: create-page\n\n"
             "| veld | waarde |\n|---|---|\n| ai_key | AI-82 |\n\n### Acties\n- [x] label ai-initiatief\n")
    r = proposal.apply(cfg("production"), S, proposal.parse(tekst, S), apply=True,
                       clients=lambda: ("cc", "jc"))
    assert r["items"][0]["status"] == "ok"
    assert recorder == [("create", "Digitale Assistent Departement Omgeving", {"ai_key": "AI-82"}, True),
                        ("labels", "999", ["ai-initiatief"], True)]


def test_een_falend_item_stopt_de_rest_niet(monkeypatch, recorder):
    def stuk(*a, **kw):
        raise RuntimeError("409 versieconflict")

    monkeypatch.setattr(confluence, "upsert_details", stuk)
    r = proposal.apply(cfg("production"), S, proposal.parse(UITGEBREID, S), apply=True,
                       clients=lambda: ("cc", "jc"))
    assert [i["status"] for i in r["items"]] == ["fout", "ok", "ok"]
    assert "409 versieconflict" in r["items"][0]["fout"]
    assert [c[0] for c in recorder] == ["create", "transition"]


def test_jira_in_test_mode_wordt_per_item_geweigerd(monkeypatch):
    # Confluence mag in test-mode (test_space), Jira nooit. jira.link en jira.transition blijven
    # hier echt: de guard in http.writer moet weigeren vóór er een client of token in het spel is.
    calls = []
    monkeypatch.setattr(confluence, "upsert_details",
                        lambda *a, **kw: calls.append("upsert") or {"version_after": 3})
    monkeypatch.setattr(confluence, "create_initiative",
                        lambda *a, **kw: calls.append("create") or {"page_id": "999"})
    c = cfg("test")
    c["atlassian"] = dict(c["atlassian"], space=c["writes"]["test_space"])
    r = proposal.apply(c, S, proposal.parse(UITGEBREID, S), apply=True, clients=lambda: ("cc", "jc"))
    assert [i["status"] for i in r["items"]] == ["geweigerd", "ok", "geweigerd"]
    assert "enkel toegestaan in production" in r["items"][0]["fout"]
    assert r["items"][0]["gedaan"] == ["upsert-details op pagina 431293016 (versie 3)"]
    assert calls == ["upsert", "create"]


def test_result_markdown_meldt_documentproblemen():
    p = proposal.parse("# aiec voorstel — onzin — 2026-09-16\n", S)
    md = proposal.result_markdown(proposal.apply(cfg(), S, p, apply=False))
    assert "**document**" in md and "onzin" in md
