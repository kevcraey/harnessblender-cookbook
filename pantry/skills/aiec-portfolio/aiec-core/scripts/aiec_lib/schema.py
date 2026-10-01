"""Het schema (schema.yaml) laden, waarden normaliseren en verplicht-wanneer evalueren.
Alles wat over velden, enums, pijlers of statussen gaat, gaat via deze module."""
from __future__ import annotations

import re
from pathlib import Path

import yaml

SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "schema.yaml"
PIJLER_RE = re.compile(r"^\s*(P\d+|OMK)\b")


def load(path: str | Path | None = None) -> dict:
    p = Path(path) if path else SCHEMA_PATH
    s = yaml.safe_load(p.read_text())
    s["_path"] = str(p)
    return s


# --- velden ----------------------------------------------------------------------------------

def fields(schema: dict) -> list[dict]:
    return schema["fields"]


def field(schema: dict, key: str) -> dict:
    for f in schema["fields"]:
        if f["key"] == key:
            return f
    raise KeyError(f"veld '{key}' bestaat niet in het schema")


def field_by_label(schema: dict, label: str) -> dict | None:
    want = _fold(label)
    for f in schema["fields"]:
        if _fold(f["label"]) == want:
            return f
    return None


def keys(schema: dict) -> list[str]:
    return [f["key"] for f in schema["fields"]]


def empty_values(schema: dict) -> dict:
    return {f["key"]: ([] if f["type"] == "multi" else "") for f in schema["fields"]}


# --- statussen en pijlers --------------------------------------------------------------------

def statuses(schema: dict) -> list[dict]:
    return schema["statussen"]


def status_from_jira(schema: dict, raw: str | None) -> tuple[str | None, int | None]:
    """Jira-statusnaam → (nette naam, fase-index). Onbekend → (raw, None)."""
    for i, s in enumerate(schema["statussen"]):
        if _fold(s["jira"]) == _fold(raw or "") or _fold(s["naam"]) == _fold(raw or ""):
            return s["naam"], i
    return raw, None


def jira_from_status(schema: dict, naam: str) -> str:
    for s in schema["statussen"]:
        if _fold(s["naam"]) == _fold(naam) or _fold(s["jira"]) == _fold(naam):
            return s["jira"]
    raise KeyError(f"status '{naam}' onbekend; kies uit {', '.join(s['naam'] for s in schema['statussen'])}")


def fase_index(schema: dict, naam: str) -> int:
    for i, s in enumerate(schema["statussen"]):
        if _fold(s["naam"]) == _fold(naam):
            return i
    raise KeyError(f"fase '{naam}' onbekend")


def pijler(schema: dict, code: str) -> dict | None:
    for p in schema["pijlers"]:
        if p["code"].upper() == (code or "").strip().upper():
            return p
    return None


def pijler_text(schema: dict, code: str) -> str:
    p = pijler(schema, code)
    return f"{p['code']} — {p['naam']}" if p else code


def parse_pijler(schema: dict, text: str) -> str | None:
    """'P2 — Slimme oplossingen bouwen' | 'P2' | volledige naam → code."""
    if not text:
        return None
    m = PIJLER_RE.match(text.upper())
    if m and pijler(schema, m.group(1)):
        return m.group(1)
    for p in schema["pijlers"]:
        if _fold(p["naam"]) == _fold(text):
            return p["code"]
    return None


# --- normalisatie -----------------------------------------------------------------------------

def _fold(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).casefold().rstrip(".")


fold = _fold  # publieke naam voor de zustermodules


def resolution_category(schema: dict, raw: str | None) -> str | None:
    """Ruwe Jira-resolution → categorie uit schema['resoluties'] (uitgevoerd | stopgezet |
    geannuleerd). De categorienaam zelf telt ook als treffer. Onbekend of leeg → None."""
    if not raw:
        return None
    want = _fold(raw)
    for cat, spec in (schema.get("resoluties") or {}).items():
        names = [cat] + list((spec or {}).get("jira", []) if isinstance(spec, dict) else [])
        if any(_fold(n) == want for n in names):
            return cat
    return None


def _match_enum(values: list[str], raw: str) -> str | None:
    want = _fold(raw)
    for v in values:
        if _fold(v) == want:
            return v
    return None


def _split_multi(raw) -> list[str]:
    if isinstance(raw, list):
        items = raw
    else:
        items = re.split(r"[,;\n•]|<br\s*/?>", str(raw or ""))
    return [i.strip() for i in items if i and i.strip()]


def normalize_value(schema: dict, f: dict, raw) -> tuple[object, str | None]:
    """Eén veld normaliseren. Geeft (waarde, probleem). Leeg is nooit een probleem hier;
    verplichtheid is werk voor rules."""
    t = f["type"]
    if t == "multi":
        out, bad = [], []
        for item in _split_multi(raw):
            m = _match_enum(f["values"], item)
            (out if m else bad).append(m or item)
        return out, (f"{f['key']}: onbekende waarde(n) {', '.join(bad)}" if bad else None)
    raw = "" if raw is None else str(raw).strip()
    if raw == "":
        return "", None
    if t == "enum":
        m = _match_enum(f["values"], raw)
        return (m, None) if m else (raw, f"{f['key']}: '{raw}' niet in {', '.join(f['values'])}")
    if t == "pijler":
        c = parse_pijler(schema, raw)
        return (c, None) if c else (raw, f"{f['key']}: '{raw}' is geen pijler")
    if t == "text":
        pat = f.get("pattern")
        if pat and not re.match(pat, raw):
            return raw, f"{f['key']}: '{raw}' voldoet niet aan {pat}"
        return raw, None
    raise ValueError(f"veldtype '{t}' onbekend")


def normalize_values(schema: dict, values: dict) -> tuple[dict, list[str]]:
    """Alle velden normaliseren; onbekende sleutels zijn een probleem. Ontbrekende sleutels
    worden leeg gezet."""
    out, problems = {}, []
    known = keys(schema)
    for k in values:
        if k not in known:
            problems.append(f"onbekend veld '{k}'")
    for f in fields(schema):
        v, p = normalize_value(schema, f, values.get(f["key"]))
        out[f["key"]] = v
        if p:
            problems.append(p)
    return out, problems


def display_value(schema: dict, f: dict, value) -> str:
    """Celtekst in het details-blok."""
    if f["type"] == "multi":
        return ", ".join(value or [])
    if f["type"] == "pijler":
        return pijler_text(schema, value) if value else ""
    return "" if value is None else str(value)


def is_filled(value) -> bool:
    return bool(value) if isinstance(value, list) else bool(str(value or "").strip())


# --- verplicht-wanneer ------------------------------------------------------------------------

def required_now(schema: dict, f: dict, ctx: dict) -> bool:
    """ctx: values (dict), soort, fase (int|None), status (nette naam|None), resolution (str|None).
    `required_when` is een lijst voorwaarden die allemaal moeten gelden."""
    if f.get("required"):
        return True
    conds = f.get("required_when") or []
    if not conds:
        return False
    values = ctx.get("values", {})
    for c in conds:
        (k, v), = c.items()
        if k == "soort":
            if _fold(str(ctx.get("soort") or values.get("soort") or "")) != _fold(v):
                return False
        elif k == "fase_min":
            # Closed without realisation: phase-bound fields are no longer demanded (beslist 2026-10-01).
            if _fold(str(ctx.get("status") or "")) == _fold("Afgesloten") and \
                    resolution_category(schema, ctx.get("resolution")) != "uitgevoerd":
                return False
            fase = ctx.get("fase")
            if fase is None or fase < fase_index(schema, v):
                return False
        elif k == "status":
            if _fold(str(ctx.get("status") or "")) != _fold(v):
                return False
        elif k == "resolution_not":
            raw = ctx.get("resolution")
            cat = resolution_category(schema, raw) or _fold(str(raw or ""))
            if cat == _fold(v):
                return False
        elif k == "filled":
            if not is_filled(values.get(v)):
                return False
        else:
            raise ValueError(f"voorwaarde '{k}' onbekend in required_when van {f['key']}")
    return True


# --- consistentie en weergave ---------------------------------------------------------------

def check(schema: dict) -> list[str]:
    problems = []
    seen = set()
    for f in schema["fields"]:
        if f["key"] in seen:
            problems.append(f"dubbele key {f['key']}")
        seen.add(f["key"])
        if f["type"] in ("enum", "multi"):
            vals = [_fold(v) for v in f.get("values", [])]
            if len(vals) != len(set(vals)):
                problems.append(f"{f['key']}: dubbele enum-waarden")
            if not vals:
                problems.append(f"{f['key']}: geen values")
        for v in (f.get("value_hints") or {}):
            if _fold(v) not in [_fold(x) for x in f.get("values", [])]:
                problems.append(f"{f['key']}: value_hints verwijst naar onbekende waarde {v}")
        for c in f.get("required_when") or []:
            if len(c) != 1:
                problems.append(f"{f['key']}: voorwaarde met meer dan één sleutel")
            (k, v), = c.items()
            if k == "fase_min":
                try:
                    fase_index(schema, v)
                except KeyError as e:
                    problems.append(str(e))
            if k == "filled" and v not in seen and v not in keys(schema):
                problems.append(f"{f['key']}: filled verwijst naar onbekend veld {v}")
    codes = [p["code"] for p in schema["pijlers"]]
    if len(codes) != len(set(codes)):
        problems.append("dubbele pijlercodes")
    if not any(s.get("eind") for s in schema["statussen"]):
        problems.append("geen eindstatus gemarkeerd")
    seen_res: dict[str, str] = {}
    for cat, spec in (schema.get("resoluties") or {}).items():
        if not isinstance(spec, dict) or "jira" not in spec:
            problems.append(f"resoluties.{cat}: verwacht een mapping met 'tekst' en 'jira' (lijst instance-namen)")
            continue
        for n in spec["jira"]:
            if _fold(n) in seen_res:
                problems.append(f"resolution '{n}' staat bij {seen_res[_fold(n)]} én {cat}")
            seen_res[_fold(n)] = cat
    labels = [_fold(f["label"]) for f in schema["fields"]]
    if len(labels) != len(set(labels)):
        problems.append("dubbele veldlabels")
    for k in schema["overzicht"]["kolommen"]:
        if k not in keys(schema):
            problems.append(f"overzicht.kolommen: onbekend veld {k}")
    return problems


_REQ_TEKST = {
    "soort": lambda v: f"enkel bij soort {v}",
    "fase_min": lambda v: f"vanaf fase {v}",
    "status": lambda v: f"bij status {v}",
    "resolution_not": lambda v: f"als de resolutie niet {v} is",
    "filled": lambda v: f"zodra {v} gevuld is",
}


def _verplicht_tekst(f: dict) -> str:
    if f.get("required"):
        return "altijd"
    conds = f.get("required_when") or []
    if not conds:
        return "nee"
    delen = []
    for c in conds:
        (k, v), = c.items()
        delen.append(_REQ_TEKST[k](v) if k in _REQ_TEKST else f"{k}={v}")
    return ", ".join(delen)


def to_markdown(schema: dict) -> str:
    out = [
        "---",
        "tags:",
        "  - type/note",
        "  - expertisecentrum-ai",
        "generated: true",
        "source: aiec-core/schema.yaml",
        "---",
        f"# AIEC-schema v{schema['version']}",
        "",
        "> [!danger] Gegenereerd document, niet met de hand bewerken",
        "> Dit bestand komt uit `aiec-core/schema.yaml` in de AIEC-portfolio-plugin. Elke wijziging die je",
        "> hier typt is weg bij de volgende generatie. Wijzig `schema.yaml` en genereer opnieuw, vanuit",
        "> `aiec-core/scripts` in de plugin:",
        ">",
        "> ```",
        "> python3.13 aiec.py schema --out \"$VAULT/02 - Areas/aiec-schema.md\"",
        "> ```",
        "",
        f"details-id `{schema['details_id']}` · label `{schema['label']}` · titel `{schema['page_title']}`",
        "",
        "## Pijlers",
        "",
    ]
    for p in schema["pijlers"]:
        out.append(f"- **{p['code']} {p['naam']}** — {p.get('toelichting', '')}")
        if p.get("grens"):
            out.append(f"  - grens: {p['grens']}")
    out += ["", "## Statussen", "", "| fase | in Jira | naam |", "|---|---|---|"]
    for i, st in enumerate(schema["statussen"]):
        out.append(f"| {i} | `{st['jira']}` | {st['naam']}{' (eind)' if st.get('eind') else ''} |")
    out += ["", "## Velden", "", "| veld | groep | type | waarden | verplicht | toelichting |",
            "|---|---|---|---|---|---|"]
    for f in schema["fields"]:
        vals = ", ".join(f.get("values", [])) if f["type"] in ("enum", "multi") else \
            ("pijlercode" if f["type"] == "pijler" else f.get("pattern", "vrije tekst"))
        extra = " · **niet afleidbaar (KENZO)**" if f.get("not_inferable") else ""
        extra += " · verborgen blok" if f.get("verborgen") else ""
        out.append(f"| {f['label']} (`{f['key']}`) | {f.get('groep', '')} | {f['type']} | {vals} | "
                   f"{_verplicht_tekst(f)} | {f.get('hint', '')}{extra} |")
    met_hints = [f for f in schema["fields"] if f.get("value_hints")]
    if met_hints:
        out += ["", "## Wat de waarden betekenen", ""]
        for f in met_hints:
            out += [f"### {f['label']}", "", "| waarde | betekenis |", "|---|---|"]
            for v in f["values"]:
                h = f["value_hints"].get(v, "")
                out.append(f"| {v} | {h} |")
            out.append("")
        out = out[:-1]
    if schema.get("resoluties"):
        out += ["", "## Resolutie bij afsluiten", "", "| categorie | betekenis | namen op de instance |",
                "|---|---|---|"]
        for cat, spec in schema["resoluties"].items():
            out.append(f"| {cat} | {spec.get('tekst', '')} | {', '.join(spec.get('jira', []))} |")
    out += ["", "## Artefactlabels", ""]
    for k, v in schema["artefact_labels"].items():
        out.append(f"- `{k}` — {v}")
    return "\n".join(out) + "\n"
