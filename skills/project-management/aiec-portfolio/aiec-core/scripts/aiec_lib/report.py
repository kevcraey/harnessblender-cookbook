"""Dataset voor aiec-rapport (DESIGN.md §6, data.json / data.md). WP-B bouwt dit. Geen proza:
tabellen en tellingen die de LLM letterlijk overneemt.

build() voegt samen: register (pages), initiatives, hours, changes, violations, en berekent:
per_pijler [{code, naam, initiatieven: [{key, titel, status, soort, opgeleverd, gebruikers,
batenclaim, aanname, uren_periode, uren_totaal}]}], per_status {naam: aantal}, funnel
({fase: aantal} + stopreden-verdeling bij Afgesloten), doorlopend (uren per doorlopend initiatief),
frigo (uit violations rule=frigo), risico ({ai_act_klasse: [keys]}, persoonsgegevens_ja: [keys]),
heatmap {afdeling: {toepassingstype: aantal}}, kost {uren_periode, uren_totaal, euro | None,
aanname_tarief}, bewogen (initiatieven met transitie/nieuwe link/nieuwe pagina-activiteit sinds
since), nieuw (new_initiatives), zonder_pagina (Jira-initiatieven zonder registerpagina).

Deze module is zuiver: ze rekent enkel op de JSON-vormen van §6 en praat niet met het netwerk.
"""
from __future__ import annotations

import datetime as dt
import re

from aiec_lib import schema as sch

ONBEKEND = "—"          # celwaarde als het register niets zegt
KEY_RE = re.compile(r"^([A-Z][A-Z0-9_]*)-(\d+)$")


def _key_sort(key: str):
    """AI-9 vóór AI-10."""
    m = KEY_RE.match(key or "")
    return (m.group(1), int(m.group(2))) if m else (key or "", 0)


def _pages_by_key(register: dict) -> dict[str, dict]:
    return {p["ai_key"]: p for p in (register or {}).get("pages") or [] if p.get("ai_key")}


def _details(page: dict | None) -> dict:
    return (page or {}).get("details") or {}


def _uren(hours: dict, key: str) -> tuple[float, float]:
    v = ((hours or {}).get("per_initiative") or {}).get(key) or {}
    return float(v.get("period_h") or 0.0), float(v.get("total_h") or 0.0)


def build(schema: dict, cfg: dict, register: dict, initiatives: dict, hours: dict, changes: dict,
          violations: list[dict], since: dt.date, until: dt.date) -> dict:
    pages = _pages_by_key(register)
    issues = (initiatives or {}).get("issues") or []
    changes = changes or {}
    violations = violations or []
    lo, hi = since.isoformat(), until.isoformat()

    # --- per initiatief één rij, gejoind op ai_key -------------------------------------------
    rijen = []
    for issue in issues:
        key = issue["key"]
        page = pages.get(key)
        d = _details(page)
        periode_h, totaal_h = _uren(hours, key)
        rijen.append({
            "key": key,
            "titel": (page or {}).get("title") or issue.get("summary") or "",
            "status": issue.get("status") or issue.get("status_raw") or ONBEKEND,
            "fase": issue.get("fase"),
            "resolution": issue.get("resolution"),
            # Ruwe Jira-resolution → categorie (uitgevoerd | stopgezet | geannuleerd) uit het schema
            "resolution_categorie": sch.resolution_category(schema, issue.get("resolution")),
            "soort": d.get("soort") or "",
            "pijler": d.get("pijler") or "",
            "afdeling": d.get("afdeling") or "",
            "toepassingstype": d.get("toepassingstype") or [],
            "ai_act_klasse": d.get("ai_act_klasse") or "",
            "persoonsgegevens": d.get("persoonsgegevens") or "",
            "opgeleverd": d.get("opgeleverd") or "",
            "gebruikers": d.get("gebruikers") or "",
            "batenclaim": d.get("batenclaim") or "",
            "aanname": d.get("aanname") or "",
            "stopreden": d.get("stopreden") or "",
            "uren_periode": periode_h,
            "uren_totaal": totaal_h,
            "page_id": (page or {}).get("page_id"),
            "last_activity": (page or {}).get("last_activity"),
            "url": issue.get("url"),
        })
    per_key = {r["key"]: r for r in rijen}

    # --- per pijler ---------------------------------------------------------------------------
    velden = ["key", "titel", "status", "soort", "opgeleverd", "gebruikers", "batenclaim",
              "aanname", "uren_periode", "uren_totaal"]
    per_pijler = []
    for p in schema["pijlers"]:
        groep = [{k: r[k] for k in velden} for r in rijen if r["pijler"] == p["code"]]
        per_pijler.append({"code": p["code"], "naam": p["naam"], "initiatieven": groep})
    zonder = [{k: r[k] for k in velden} for r in rijen
              if not sch.pijler(schema, r["pijler"]) ]
    if zonder:
        per_pijler.append({"code": None, "naam": "zonder pijler", "initiatieven": zonder})

    # --- status en funnel ---------------------------------------------------------------------
    per_status = {}
    for s in sch.statuses(schema):
        per_status[s["naam"]] = sum(1 for r in rijen if r["status"] == s["naam"])
    for r in rijen:
        if r["status"] not in per_status:
            per_status[r["status"]] = per_status.get(r["status"], 0) + 1

    # De funnel gaat enkel over afgebakende initiatieven; doorlopende werking valt erbuiten.
    funnel_rijen = [r for r in rijen if r["soort"] != "doorlopend"]
    funnel = {"fase": {s["naam"]: sum(1 for r in funnel_rijen if r["status"] == s["naam"])
                       for s in sch.statuses(schema)},
              "stopreden": {}}
    for r in funnel_rijen:
        if r["status"] == _eindstatus(schema) and r["resolution_categorie"] != "uitgevoerd":
            reden = r["stopreden"] or "(geen stopreden)"
            funnel["stopreden"][reden] = funnel["stopreden"].get(reden, 0) + 1

    # --- doorlopende werking ------------------------------------------------------------------
    doorlopend = [{"key": r["key"], "titel": r["titel"], "uren_periode": r["uren_periode"],
                   "uren_totaal": r["uren_totaal"]}
                  for r in rijen if r["soort"] == "doorlopend"]

    # --- frigo, risico, heatmap ----------------------------------------------------------------
    frigo = [{"ai_key": v.get("ai_key"), "message": v.get("message"),
              "titel": (per_key.get(v.get("ai_key")) or {}).get("titel", "")}
             for v in violations if v.get("rule") == "frigo"]

    risico = {"per_klasse": {}, "persoonsgegevens_ja": []}
    for f in sch.field(schema, "ai_act_klasse")["values"]:
        risico["per_klasse"][f] = [r["key"] for r in rijen if r["ai_act_klasse"] == f]
    risico["per_klasse"][ONBEKEND] = [r["key"] for r in rijen if not r["ai_act_klasse"]]
    risico["persoonsgegevens_ja"] = [r["key"] for r in rijen if r["persoonsgegevens"] == "ja"]

    heatmap: dict[str, dict[str, int]] = {}
    for r in rijen:
        afdeling = r["afdeling"] or ONBEKEND
        rij = heatmap.setdefault(afdeling, {})
        for t in (r["toepassingstype"] or [ONBEKEND]):
            rij[t] = rij.get(t, 0) + 1

    # --- kost -----------------------------------------------------------------------------------
    tarief = float((cfg.get("report") or {}).get("uurtarief_eur") or 0)
    uren_periode = round(sum(r["uren_periode"] for r in rijen), 2)
    uren_totaal = round(sum(r["uren_totaal"] for r in rijen), 2)
    kost = {"uren_periode": uren_periode, "uren_totaal": uren_totaal,
            "euro": round(uren_periode * tarief, 2) if tarief > 0 else None,
            "euro_totaal": round(uren_totaal * tarief, 2) if tarief > 0 else None,
            "aanname_tarief": tarief if tarief > 0 else None}

    # --- beweging -------------------------------------------------------------------------------
    bewogen_keys = {t["key"] for t in changes.get("transitions") or []}
    bewogen_keys |= {l["key"] for l in changes.get("new_links") or []}
    bewogen_keys |= {r["key"] for r in rijen
                     if (r["last_activity"] or "")[:10] >= lo and r["last_activity"]}
    bewogen = []
    for key in sorted(bewogen_keys, key=_key_sort):
        r = per_key.get(key)
        if r is None:
            continue
        bewogen.append({
            "key": key, "titel": r["titel"], "status": r["status"],
            "uren_periode": r["uren_periode"],
            "transities": [{"from": t["from"], "to": t["to"], "when": t["when"]}
                           for t in changes.get("transitions") or [] if t["key"] == key],
            "nieuwe_links": [{"linked": l["linked"], "type": l["type"], "when": l["when"]}
                             for l in changes.get("new_links") or [] if l["key"] == key],
            "pagina_activiteit": r["last_activity"]})

    zonder_pagina = [{"key": r["key"], "titel": r["titel"], "status": r["status"]}
                     for r in rijen if not r["page_id"]]

    return {"generated": dt.datetime.now().isoformat(timespec="seconds"),
            "since": lo, "until": hi,
            "initiatieven": rijen,
            "per_pijler": per_pijler,
            "per_status": per_status,
            "funnel": funnel,
            "doorlopend": doorlopend,
            "frigo": frigo,
            "risico": risico,
            "heatmap": heatmap,
            "kost": kost,
            "bewogen": bewogen,
            "nieuw": changes.get("new_initiatives") or [],
            "zonder_pagina": zonder_pagina,
            "violations_per_ernst": _tel_ernst(violations)}


def _eindstatus(schema: dict) -> str:
    for s in sch.statuses(schema):
        if s.get("eind"):
            return s["naam"]
    return "Afgesloten"


def _tel_ernst(violations: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for v in violations or []:
        ernst = v.get("severity") or "info"
        out[ernst] = out.get(ernst, 0) + 1
    return out


# --- markdown -----------------------------------------------------------------------------------

def _tabel(kop: list[str], rijen: list[list[str]]) -> list[str]:
    if not rijen:
        return ["Geen."]
    return ["| " + " | ".join(kop) + " |", "|" + "---|" * len(kop)] + \
           ["| " + " | ".join(str(c) for c in rij) + " |" for rij in rijen]


def to_markdown(data: dict) -> str:
    """data.md: dezelfde tabellen in markdown, in de volgorde van build()."""
    out = [f"# AIEC-portfolio — data {data['since']} … {data['until']}", "",
           f"{len(data['initiatieven'])} initiatieven · "
           f"{data['kost']['uren_periode']:.2f} u in de periode · "
           f"{data['kost']['uren_totaal']:.2f} u totaal.", ""]

    out += ["## Per pijler", ""]
    for p in data["per_pijler"]:
        out += [f"### {p['code'] or '—'} {p['naam']}", ""]
        out += _tabel(["key", "titel", "status", "soort", "opgeleverd", "gebruikers",
                       "batenclaim", "aanname", "u periode", "u totaal"],
                      [[i["key"], i["titel"], i["status"], i["soort"] or "—", i["opgeleverd"] or "—",
                        i["gebruikers"] or "—", i["batenclaim"] or "—", i["aanname"] or "—",
                        f"{i['uren_periode']:.2f}", f"{i['uren_totaal']:.2f}"]
                       for i in p["initiatieven"]])
        out.append("")

    out += ["## Per status", ""]
    out += _tabel(["status", "aantal"], [[k, v] for k, v in data["per_status"].items()])

    out += ["", "## Funnel (afgebakend)", ""]
    out += _tabel(["fase", "aantal"], [[k, v] for k, v in data["funnel"]["fase"].items()])
    out += ["", "Stopredenen bij afsluiting zonder uitvoering:", ""]
    out += _tabel(["stopreden", "aantal"], [[k, v] for k, v in data["funnel"]["stopreden"].items()])

    out += ["", "## Doorlopende werking", ""]
    out += _tabel(["key", "titel", "u periode", "u totaal"],
                  [[d["key"], d["titel"], f"{d['uren_periode']:.2f}", f"{d['uren_totaal']:.2f}"]
                   for d in data["doorlopend"]])

    out += ["", "## Frigo", ""]
    out += _tabel(["key", "titel", "melding"],
                  [[f["ai_key"], f["titel"], f["message"]] for f in data["frigo"]])

    out += ["", "## Risico", ""]
    out += _tabel(["AI Act-klasse", "initiatieven"],
                  [[k, ", ".join(v) or "—"] for k, v in data["risico"]["per_klasse"].items()])
    out += ["", f"Persoonsgegevens = ja: {', '.join(data['risico']['persoonsgegevens_ja']) or '—'}."]

    out += ["", "## Heatmap (afdeling × toepassingstype)", ""]
    kolommen = sorted({t for rij in data["heatmap"].values() for t in rij})
    out += _tabel(["afdeling"] + kolommen,
                  [[afd] + [rij.get(t, 0) for t in kolommen]
                   for afd, rij in sorted(data["heatmap"].items())])

    k = data["kost"]
    out += ["", "## Kost", "",
            f"- uren in de periode: {k['uren_periode']:.2f}",
            f"- uren totaal: {k['uren_totaal']:.2f}"]
    if k["euro"] is None:
        out.append("- euro: geen tarief in de config, dus geen bedrag")
    else:
        out.append(f"- euro (aanname {k['aanname_tarief']:.2f} €/u): "
                   f"{k['euro']:.2f} in de periode, {k['euro_totaal']:.2f} totaal")

    out += ["", "## Bewogen sinds " + data["since"], ""]
    out += _tabel(["key", "titel", "status", "u periode", "transities", "nieuwe links"],
                  [[b["key"], b["titel"], b["status"], f"{b['uren_periode']:.2f}",
                    "; ".join(f"{t['from']} → {t['to']} ({t['when'][:10]})" for t in b["transities"]) or "—",
                    "; ".join(f"{l['type']} {l['linked']}" for l in b["nieuwe_links"]) or "—"]
                   for b in data["bewogen"]])

    out += ["", "## Nieuw", ""]
    out += _tabel(["key", "summary", "aangemaakt"],
                  [[n["key"], n["summary"], (n["created"] or "")[:10]] for n in data["nieuw"]])

    out += ["", "## Zonder registerpagina", ""]
    out += _tabel(["key", "titel", "status"],
                  [[z["key"], z["titel"], z["status"]] for z in data["zonder_pagina"]])
    return "\n".join(out) + "\n"
