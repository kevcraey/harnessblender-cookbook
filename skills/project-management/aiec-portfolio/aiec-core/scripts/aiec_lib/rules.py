"""Validatieregels (DESIGN.md §7) over register.json + initiatives.json (+ hours.json).
WP-D bouwt dit. Geen netwerk; puur functies over de JSON-vormen uit §6.

Elke violation: {rule, severity: fout|waarschuwing|info, ai_key, page_id, message,
fix: {action: label|jira-link|rerender|transition, args: {...}} | None}.
Verplichtheid via schema.required_now met ctx {values, soort, fase, status, resolution}.
Frigo: cfg report.frigo_dagen, laatste activiteit = max(jira updated, register last_activity).
"""
from __future__ import annotations

import datetime as dt
import re

from aiec_lib import schema as sch  # noqa: F401

SEVERITY_ORDER = {"fout": 0, "waarschuwing": 1, "info": 2}
KEY_RE = re.compile(r"\bAI-\d+\b")

# Velden met een eigen regel in §7; die mogen niet óók als ontbrekend-veld gemeld worden.
EIGEN_REGEL = {"eag_key", "aanname", "stopreden"}

# Fases waarin een afgebakend initiatief in de frigo kan belanden (§4).
FRIGO_STATUSSEN = ("Captatie", "Analyse", "Planning")


def _v(rule: str, severity: str, ai_key, page_id, message: str, fix: dict | None = None) -> dict:
    return {"rule": rule, "severity": severity, "ai_key": ai_key, "page_id": page_id,
            "message": message, "fix": fix}


def _dag(ts) -> dt.date | None:
    """Datum uit een tijdstempel. Jira geeft '2026-09-15T07:35:43.000+0200', Confluence
    '2026-09-02T09:12:00'; frigo rekent per dag, dus de eerste tien tekens volstaan."""
    try:
        return dt.date.fromisoformat(str(ts)[:10])
    except (TypeError, ValueError):
        return None


def _key_uit_titel(titel: str) -> str | None:
    m = KEY_RE.search(titel or "")
    return m.group(0) if m else None


def _sorteersleutel(v: dict) -> tuple:
    key = v.get("ai_key") or ""
    m = re.search(r"-(\d+)$", key)
    return (0 if key else 1, int(m.group(1)) if m else 0, SEVERITY_ORDER.get(v["severity"], 9), v["rule"])


def _kind_labels(page: dict) -> set[str]:
    return {lbl for kind in (page.get("children") or []) for lbl in (kind.get("labels") or [])}


def validate(schema: dict, cfg: dict, register: dict, initiatives: dict, hours: dict | None = None,
             today: dt.date | None = None) -> list[dict]:
    """Alle regels van §7 over de aangeleverde datasets. `hours` wordt nog door geen enkele regel
    gebruikt; het staat in de signatuur omdat aiec.py het doorgeeft."""
    today = today or dt.date.today()
    frigo_dagen = int(cfg["report"]["frigo_dagen"])
    artefact_labels = set(schema["artefact_labels"])
    fase_analyse = sch.fase_index(schema, "Analyse")
    fase_planning = sch.fase_index(schema, "Planning")
    pijler_label = sch.field(schema, "pijler")["label"]

    violations: list[dict] = []
    pages: dict[str, dict] = {}
    for p in register.get("pages") or []:
        key = p.get("ai_key") or _key_uit_titel(p.get("title", ""))
        if not key:
            violations.append(_v("wees-pagina", "fout", None, p.get("page_id"),
                                 f"pagina '{p.get('title')}' heeft geen AI-key"))
            continue
        pages[key] = p
    issues = {i["key"]: i for i in initiatives.get("issues") or []}

    for key in set(pages) | set(issues):
        page, issue = pages.get(key), issues.get(key)
        page_id = page.get("page_id") if page else None
        values = (page.get("details") or {}) if page else {}
        soort = str(values.get("soort") or "")
        afgebakend = soort == "afgebakend"
        fase = issue.get("fase") if issue else None
        ctx = {"values": values, "soort": soort, "fase": fase,
               "status": issue.get("status") if issue else None,
               "resolution": issue.get("resolution") if issue else None}
        add = lambda *a, **kw: violations.append(_v(*a, **kw))  # noqa: E731

        # geen-pagina / wees-pagina: het koppelvlak tussen beide bronnen.
        if issue and not page:
            add("geen-pagina", "fout", key, None,
                f"Jira-initiatief '{issue.get('summary', '')}' heeft geen registerpagina")
        if page and not issue:
            add("wees-pagina", "fout", key, page_id,
                f"registerpagina '{page.get('title')}' verwijst naar een key die niet in Jira bestaat")

        if page:
            # ontbrekend-veld — verplichtheid komt volledig uit het schema. Een pagina zonder
            # details-blok (de retro-fit-toestand) geeft één melding in plaats van er vijf.
            ontbreken = [f for f in sch.fields(schema) if f["key"] not in EIGEN_REGEL
                         and sch.required_now(schema, f, ctx) and not sch.is_filled(values.get(f["key"]))]
            if page.get("has_details") is False:
                add("ontbrekend-veld", "fout", key, page_id,
                    "geen details-blok op de pagina; verplicht zijn nu: "
                    + ", ".join(f["label"] for f in ontbreken))
            else:
                for f in ontbreken:
                    add("ontbrekend-veld", "fout", key, page_id,
                        f"{f['label']} is leeg maar verplicht" + (f" ({f['hint']})" if f.get("hint") else ""))

            # enum-buiten-bereik — dezelfde normalisatie als bij het schrijven; ook
            # pattern-velden (AI-key, EAG-key) komen hier terecht, die hebben geen eigen regel.
            for f in sch.fields(schema):
                v = values.get(f["key"])
                if not sch.is_filled(v):
                    continue
                _, probleem = sch.normalize_value(schema, f, v)
                if probleem:
                    add("enum-buiten-bereik", "fout", key, page_id, probleem)

            # pijler-tekst-verouderd — code klopt, de tekst in de cel niet meer.
            code = values.get("pijler")
            raw = (page.get("details_raw") or {}).get(pijler_label)
            if code and sch.pijler(schema, code) and raw and sch._fold(raw) != sch._fold(sch.pijler_text(schema, code)):
                add("pijler-tekst-verouderd", "info", key, page_id,
                    f"pijlertekst '{raw}' wijkt af van '{sch.pijler_text(schema, code)}'",
                    fix={"action": "rerender", "args": {"page_id": page_id, "veld": "pijler"}})

            # EAG-regels. Een lege EAG-key is ofwel geen-eag (ook de Jira-link ontbreekt, Kenzo
            # beslist per stuk) ofwel een echt ontbrekend veld (de link bestaat wel).
            eag = str(values.get("eag_key") or "").strip()
            gelinkt = list(issue.get("eag_keys") or []) if issue else []
            if not eag and sch.required_now(schema, sch.field(schema, "eag_key"), ctx):
                if gelinkt:
                    add("ontbrekend-veld", "fout", key, page_id,
                        f"EAG-key is leeg terwijl Jira {', '.join(gelinkt)} gelinkt heeft")
                else:
                    add("geen-eag", "waarschuwing", key, page_id,
                        "afgebakend initiatief zonder EAG-key en zonder Jira-link Gerelateerd")
            elif eag and issue:
                if not gelinkt:
                    add("eag-link-ontbreekt", "waarschuwing", key, page_id,
                        f"EAG-key {eag} staat op de pagina, maar de Jira-link Gerelateerd ontbreekt",
                        fix={"action": "jira-link", "args": {"key": key, "eag": eag}})
                elif eag not in gelinkt:
                    add("eag-mismatch", "waarschuwing", key, page_id,
                        f"EAG-key {eag} op de pagina, {', '.join(gelinkt)} gelinkt in Jira")

            # Artefacten per fase.
            kind_labels = _kind_labels(page)
            if afgebakend and fase is not None:
                if fase >= fase_analyse and "captatierapport" not in kind_labels:
                    add("geen-captatierapport", "waarschuwing", key, page_id,
                        f"fase {ctx['status']} zonder kindpagina met label captatierapport")
                if fase >= fase_planning and "verkenningsrapport" not in kind_labels:
                    add("geen-verkenningsrapport", "waarschuwing", key, page_id,
                        f"fase {ctx['status']} zonder kindpagina met label verkenningsrapport")

            # geen-stopreden en baten-zonder-aanname: eigen ernst, zelfde voorwaarden als het schema.
            # De ruwe Jira-resolution wordt via schema.resolution_category (schema.yaml › resoluties)
            # naar uitgevoerd/stopgezet/geannuleerd vertaald; een naam buiten die mapping telt als
            # niet-uitgevoerd en meldt dus. De mapping zelf is een voorstel (DESIGN.md §11.3).
            if sch.required_now(schema, sch.field(schema, "stopreden"), ctx) \
                    and not sch.is_filled(values.get("stopreden")):
                add("geen-stopreden", "fout", key, page_id,
                    f"afgesloten met resolution {ctx['resolution'] or 'geen'}, maar stopreden is leeg")
            if sch.required_now(schema, sch.field(schema, "aanname"), ctx) \
                    and not sch.is_filled(values.get("aanname")):
                add("baten-zonder-aanname", "fout", key, page_id,
                    "batenclaim ingevuld zonder aanname eronder")

            # titel-drift.
            if issue:
                titel = page.get("title") or ""
                if key not in titel:
                    add("titel-drift", "info", key, page_id, f"titel '{titel}' bevat de key niet")
                else:
                    # Live komt '[AI-8]: Copilot M365' voor; de dubbelpunt hoort niet bij de titel.
                    rest = titel.split("]", 1)[1].lstrip(" :") if "]" in titel else titel.replace(key, "")
                    if sch._fold(rest) != sch._fold(issue.get("summary") or ""):
                        add("titel-drift", "info", key, page_id,
                            f"titel '{rest.strip()}' wijkt af van de Jira-summary '{issue.get('summary')}'")

            # doorlopend-in-funnel.
            if soort == "doorlopend" and ("captatierapport" in kind_labels or sch.is_filled(values.get("stopreden"))):
                reden = "een captatierapport" if "captatierapport" in kind_labels else "een stopreden"
                add("doorlopend-in-funnel", "info", key, page_id,
                    f"doorlopende werking met {reden}; die hoort bij de funnel van afgebakende initiatieven")

            # artefact-zonder-label — het label kiezen is werk voor de LLM.
            for kind in page.get("children") or []:
                if not (set(kind.get("labels") or []) & artefact_labels):
                    add("artefact-zonder-label", "info", key, kind.get("page_id"),
                        f"kindpagina '{kind.get('title')}' heeft geen artefactlabel",
                        fix={"action": "label", "args": {"page_id": kind.get("page_id"),
                                                         "titel": kind.get("title"),
                                                         "keuze": sorted(artefact_labels)}})

        # frigo — stilte over beide bronnen heen.
        if afgebakend and issue and ctx["status"] in FRIGO_STATUSSEN:
            dagen = [d for d in (_dag(issue.get("updated")),
                                 _dag(page.get("last_activity")) if page else None) if d]
            if dagen:
                stil = (today - max(dagen)).days
                if stil > frigo_dagen:
                    add("frigo", "waarschuwing", key, page_id,
                        f"{stil} dagen stil in fase {ctx['status']} (grens {frigo_dagen}); "
                        f"verkennen, parkeren met herbekijkdatum, of afsluiten met stopreden")

    violations.sort(key=_sorteersleutel)
    return violations


def to_markdown(violations: list[dict]) -> str:
    """Gegroepeerd per initiatief (fout → waarschuwing → info), daarna een telling per regel."""
    tellers = {"fout": 0, "waarschuwing": 0, "info": 0}
    for v in violations:
        tellers[v["severity"]] = tellers.get(v["severity"], 0) + 1
    out = ["# Regelcheck AIEC-portfolio", "",
           f"{len(violations)} melding(en): {tellers['fout']} fout, "
           f"{tellers['waarschuwing']} waarschuwing, {tellers['info']} info", ""]
    if not violations:
        return "\n".join(out[:2] + ["Geen meldingen."]) + "\n"

    huidig = object()
    for v in violations:
        if v["ai_key"] != huidig:
            huidig = v["ai_key"]
            out += ["", f"## {huidig or 'zonder key'}", ""]
        fix = v.get("fix")
        staart = f" → fix `{fix['action']}`" if fix else ""
        out.append(f"- **{v['severity']}** `{v['rule']}` — {v['message']}{staart}")

    per_regel: dict[str, int] = {}
    for v in violations:
        per_regel[v["rule"]] = per_regel.get(v["rule"], 0) + 1
    out += ["", "## Telling per regel", "", "| regel | aantal |", "|---|---|"]
    out += [f"| `{r}` | {n} |" for r, n in sorted(per_regel.items(), key=lambda kv: (-kv[1], kv[0]))]
    return "\n".join(out) + "\n"
