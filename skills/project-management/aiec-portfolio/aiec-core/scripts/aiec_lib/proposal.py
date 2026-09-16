"""Voorstel-bestanden (DESIGN.md §8): parsen, skelet renderen, uitvoeren. WP-D bouwt dit.

parse(text) → {"soort": "retrofit|initiatief|groom", "datum": "...", "items": [{"ai_key", "titel",
"pagina", "actie": "upsert-details|create-page|skip", "values": {key: waarde}, "acties":
[{"checked": bool, "kind": "label|jira-link|jira-transition", "args": [...]}]}]}.
Tabelrijen: eerste kolom = veldkey (of label; beide toegestaan via schema.field_by_label), tweede =
waarde; lege waarde = niet zetten; rij met `~~` = overslaan; overige kolommen negeren.
apply(): per item eerst de pagina (upsert/create via confluence.*), dan de aangevinkte acties
(confluence.set_labels, jira.link, jira.transition). Zonder apply=True: geen enkele call, enkel een
verslag van wat er zou gebeuren. Eén item dat faalt stopt het geheel niet; het verslag zegt per item
ok/geweigerd/fout.
skeleton(): rendert een voorstel voor één initiatief uit values + bronnen (voor de skills).

Wat Kenzo in het bestand fout kan typen (onbekend veld, onbekende actie, upsert zonder pagina)
wordt niet stil genegeerd: het komt als `problems` op het item terecht en maakt dat item `fout`.
"""
from __future__ import annotations

import datetime as dt
import re
from typing import Callable

from aiec_lib import config
from aiec_lib import confluence
from aiec_lib import jira
from aiec_lib import schema as sch

MARKER = "<!-- aiec:proposal v1 -->"
SOORTEN = ("retrofit", "initiatief", "groom")
ACTIES = ("upsert-details", "create-page", "skip")

KOP_RE = re.compile(r"^#\s+aiec voorstel\s*[—-]\s*(.+?)\s*[—-]\s*(\S+)\s*$", re.I)
SECTIE_RE = re.compile(r"^##\s+(.+?)(?:\s+[—-]\s+(.*))?$")   # de key mag zelf een - bevatten
ACTIES_KOP_RE = re.compile(r"^###\s+acties\s*$", re.I)
VELD_RE = re.compile(r"^-\s*(pagina|actie)\s*:\s*(.*)$", re.I)
BULLET_RE = re.compile(r"^-\s*\[([ xX])\]\s*(.+?)\s*$")
CEL_SPLIT_RE = re.compile(r"(?<!\\)\|")
STREEP_RE = re.compile(r"^:?-{3,}:?$")


def _cellen(regel: str) -> list[str]:
    delen = CEL_SPLIT_RE.split(regel.strip())
    if delen and not delen[0].strip():
        delen = delen[1:]
    if delen and not delen[-1].strip():
        delen = delen[:-1]
    return [d.replace("\\|", "|").strip() for d in delen]


def _actie_tekst(actie: dict) -> str:
    vink = "x" if actie.get("checked") else " "
    woorden = {"label": ["label"], "jira-link": ["jira", "link"],
               "jira-transition": ["jira", "transition"]}[actie["kind"]]
    return f"- [{vink}] " + " ".join(woorden + [str(a) for a in actie["args"]])


def _parse_actie(tekst: str) -> tuple[str, list[str]] | None:
    """'label ai-initiatief' | 'jira link AI-25 EAG-927' | 'jira transition AI-6 Afgesloten
    stopgezet' → (kind, args). Nette statusnamen zijn één woord, dus splitsen op spaties volstaat."""
    delen = tekst.split()
    if not delen:
        return None
    if delen[0].lower() == "label" and len(delen) >= 2:
        return "label", delen[1:]
    if delen[0].lower() == "jira" and len(delen) >= 2:
        if delen[1].lower() == "link" and len(delen) == 4:
            return "jira-link", delen[2:]
        if delen[1].lower() == "transition" and len(delen) in (4, 5):
            return "jira-transition", delen[2:]
    return None


# --- parser ---------------------------------------------------------------------------------

def parse(text: str, schema: dict | None = None) -> dict:
    """Voorstel-bestand → structuur. `schema` enkel om labels in de eerste kolom te herkennen;
    zonder meegegeven schema wordt schema.yaml geladen."""
    schema = sch.load() if schema is None else schema
    veldkeys = set(sch.keys(schema))
    voorstel = {"soort": None, "datum": None, "versie": MARKER in text, "problems": [], "items": []}
    item = None
    in_acties = False

    for nr, regel in enumerate(text.splitlines(), 1):
        kaal = regel.strip()
        if not kaal:
            continue
        if kaal.startswith("<!--"):
            continue

        kop = KOP_RE.match(kaal)
        if kop:
            voorstel["soort"] = kop.group(1).strip().lower()
            voorstel["datum"] = kop.group(2).strip()
            if voorstel["soort"] not in SOORTEN:
                voorstel["problems"].append(
                    f"regel {nr}: soort '{voorstel['soort']}' is geen {' | '.join(SOORTEN)}")
            continue
        if kaal.startswith("# "):
            continue

        if kaal.startswith("## "):
            sectie = SECTIE_RE.match(kaal)
            item = {"ai_key": sectie.group(1), "titel": (sectie.group(2) or "").strip(),
                    "pagina": None, "actie": None, "values": {}, "acties": [], "problems": []}
            voorstel["items"].append(item)
            in_acties = False
            continue

        if item is None:
            continue

        if ACTIES_KOP_RE.match(kaal):
            in_acties = True
            continue
        if kaal.startswith("### "):
            in_acties = False
            continue

        bullet = BULLET_RE.match(kaal)
        if bullet:
            ontleed = _parse_actie(bullet.group(2))
            if ontleed is None:
                item["problems"].append(f"regel {nr}: actie '{bullet.group(2)}' niet herkend")
                continue
            if ontleed[0] == "jira-transition":
                try:                       # de resolutie niet: die namen verschillen op de instance
                    sch.jira_from_status(schema, ontleed[1][1])
                except KeyError as e:
                    item["problems"].append(f"regel {nr}: {e.args[0]}")
                    continue
            item["acties"].append({"checked": bullet.group(1).lower() == "x",
                                   "kind": ontleed[0], "args": ontleed[1]})
            continue

        veld = VELD_RE.match(kaal)
        if veld and not in_acties:
            naam, waarde = veld.group(1).lower(), veld.group(2).strip()
            if naam == "pagina":
                item["pagina"] = waarde or None
            else:
                item["actie"] = waarde.lower()
                if item["actie"] not in ACTIES:
                    item["problems"].append(
                        f"regel {nr}: actie '{waarde}' is geen {' | '.join(ACTIES)}")
            continue

        if kaal.startswith("|"):
            cellen = _cellen(kaal)
            if len(cellen) < 2 or all(STREEP_RE.match(c) for c in cellen if c):
                continue
            if sch._fold(cellen[0]) in ("veld", "field"):
                continue
            if "~~" in kaal:                      # doorstreepte rij: bewust overgeslagen
                continue
            eerste, waarde = cellen[0], cellen[1]
            if eerste in veldkeys:
                key = eerste
            else:
                f = sch.field_by_label(schema, eerste)
                if f is None:
                    item["problems"].append(f"regel {nr}: '{eerste}' is geen veld uit het schema")
                    continue
                key = f["key"]
            if not waarde:                        # lege waarde = niet zetten
                continue
            genormaliseerd, probleem = sch.normalize_value(schema, sch.field(schema, key), waarde)
            if probleem:
                item["problems"].append(f"regel {nr}: {probleem}")
                continue
            item["values"][key] = genormaliseerd

    for item in voorstel["items"]:
        if item["actie"] is None:
            item["problems"].append(f"{item['ai_key']}: geen 'actie:' opgegeven")
        elif item["actie"] == "upsert-details" and not item["pagina"]:
            item["problems"].append(f"{item['ai_key']}: actie upsert-details zonder 'pagina:'")
        elif item["actie"] == "create-page" and not item["titel"]:
            item["problems"].append(f"{item['ai_key']}: actie create-page zonder titel achter de key")
        # Een label hoort op een pagina; bij create-page is dat de pagina die net gemaakt wordt.
        if item["actie"] != "create-page" and not item["pagina"] \
                and any(a["checked"] and a["kind"] == "label" for a in item["acties"]):
            item["problems"].append(f"{item['ai_key']}: actie 'label' zonder 'pagina:'")
    return voorstel


# --- skelet ---------------------------------------------------------------------------------

def skeleton(schema: dict, soort: str, ai_key: str, titel: str, pagina: str | None, actie: str,
             values: dict, bronnen: dict | None = None, zekerheid: dict | None = None,
             acties: list[dict] | None = None) -> str:
    """Markdown-sectie voor één initiatief; velden in schema-volgorde; not_inferable-velden krijgen
    zekerheid KENZO."""
    bronnen, zekerheid = bronnen or {}, zekerheid or {}
    uit = [f"## {ai_key} — {titel}".rstrip(" —")]
    if pagina:
        uit.append(f"- pagina: {pagina}")
    uit += [f"- actie: {actie}", "", "| veld | waarde | bron | zekerheid |", "|---|---|---|---|"]
    for f in sch.fields(schema):
        key = f["key"]
        waarde = sch.display_value(schema, f, values.get(key, "")).replace("|", "\\|")
        zeker = zekerheid.get(key) or ("KENZO" if f.get("not_inferable") else "")
        uit.append(f"| {key} | {waarde} | {bronnen.get(key, '—')} | {zeker} |")
    if acties:
        uit += ["", "### Acties"] + [_actie_tekst(a) for a in acties]
    return "\n".join(uit) + "\n"


def document(soort: str, secties: list[str], datum: dt.date | str | None = None) -> str:
    """Volledig voorstel-bestand: kop, marker, secties. Inverse van parse()."""
    datum = datum or dt.date.today()
    datum = datum.isoformat() if isinstance(datum, dt.date) else str(datum)
    return "\n".join([f"# aiec voorstel — {soort} — {datum}", MARKER, ""] + list(secties))


# --- uitvoeren -------------------------------------------------------------------------------

def _pagina_stap(cfg, schema, item, cc, doen: bool) -> str:
    """De pagina-mutatie van één item. `doen=False` schrijft niets en raakt geen client aan.
    Een nieuwe pagina zet `item['pagina']`, zodat een label-actie erna weet waar ze moet landen."""
    aantal = len(item["values"])
    if item["actie"] == "upsert-details":
        if not doen:
            return f"upsert-details op pagina {item['pagina']} ({aantal} veld(en))"
        r = confluence.upsert_details(cfg, cc, schema, item["pagina"], item["values"], apply=True)
        return f"upsert-details op pagina {item['pagina']} (versie {r.get('version_after')})"
    if not doen:
        return f"create-page '{item['titel']}' ({aantal} veld(en))"
    r = confluence.create_initiative(cfg, cc, schema, item["values"], item["titel"], apply=True)
    item["pagina"] = r.get("page_id")
    return f"create-page '{item['titel']}' → pagina {item['pagina']}"


def _actie_stap(cfg, schema, item, actie, cc, jc, doen: bool) -> str:
    """Eén aangevinkte actie-bullet."""
    args = actie["args"]
    if actie["kind"] == "label":
        if not doen:
            return f"label {' '.join(args)} op pagina {item['pagina']}"
        r = confluence.set_labels(cfg, cc, item["pagina"], args, apply=True)
        return f"label {' '.join(args)} op pagina {item['pagina']} ({len(r.get('toegevoegd', args))} toegevoegd)"
    if actie["kind"] == "jira-link":
        if not doen:
            return f"jira link {args[0]} {args[1]}"
        jira.link(cfg, jc, args[0], args[1], apply=True)
        return f"jira link {args[0]} {args[1]}"
    resolutie = args[2] if len(args) > 2 else None
    if not doen:
        return f"jira transition {args[0]} → {args[1]}" + (f" ({resolutie})" if resolutie else "")
    jira.transition(cfg, jc, schema, args[0], args[1], resolution=resolutie, apply=True)
    return f"jira transition {args[0]} → {args[1]}" + (f" ({resolutie})" if resolutie else "")


def apply(cfg: dict, schema: dict, proposal: dict, apply: bool = False, clients: Callable | None = None) -> dict:
    """clients() → (confluence_client, jira_client), lazy zodat dry-run zonder netwerk kan als er
    niets te lezen valt. Geeft {"items": [{"ai_key", "status": "ok|geweigerd|fout|overgeslagen",
    "gedaan": [...], "fout": str | None}], "applied": bool}."""
    # De guard eerst, vóór er een client (en dus een token) gevraagd wordt: in dry-run-mode stopt
    # elke --apply hier met exit 3. Per item kan er later nog een GuardRefused komen (mode test
    # weigert Jira); die maakt enkel dat ene item "geweigerd".
    if apply:
        if config.mode(cfg) == "dry-run":
            config.guard(cfg, "confluence", cfg["atlassian"]["space"], True)   # weigert altijd
        if clients is None:
            raise ValueError("apply=True vereist clients()")
    resultaat = {"applied": bool(apply), "mode": config.mode(cfg),
                 "soort": proposal.get("soort"), "datum": proposal.get("datum"),
                 "problems": list(proposal.get("problems") or []), "items": []}
    paar: list = []

    def _clients():
        if not paar:
            paar.extend(clients())
        return paar[0], paar[1]

    for item in proposal.get("items") or []:
        r = {"ai_key": item["ai_key"], "actie": item["actie"], "status": "ok",
             "gedaan": [], "overgeslagen": [], "fout": None}
        resultaat["items"].append(r)
        try:
            if item["problems"]:
                raise ValueError("; ".join(item["problems"]))
            cc, jc = _clients() if apply else (None, None)
            if item["actie"] == "skip":
                r["overgeslagen"].append("actie: skip")
            else:
                r["gedaan"].append(_pagina_stap(cfg, schema, item, cc, apply))
            for actie in item["acties"]:
                if actie["checked"]:
                    r["gedaan"].append(_actie_stap(cfg, schema, item, actie, cc, jc, apply))
                else:
                    r["overgeslagen"].append("niet aangevinkt: " + _actie_tekst(actie)[6:])
            if not r["gedaan"]:
                r["status"] = "overgeslagen"
        except config.GuardRefused as e:
            r["status"], r["fout"] = "geweigerd", str(e)
        except Exception as e:  # één falend item stopt de rest niet
            r["status"], r["fout"] = "fout", f"{type(e).__name__}: {e}"
    return resultaat


def result_markdown(result: dict) -> str:
    werkwoord = "gedaan" if result["applied"] else "zou gebeuren"
    tellers: dict[str, int] = {}
    for i in result["items"]:
        tellers[i["status"]] = tellers.get(i["status"], 0) + 1
    uit = [f"# Voorstel {result.get('soort') or ''} {result.get('datum') or ''}".rstrip(), "",
           f"mode `{result['mode']}` · {'uitgevoerd' if result['applied'] else 'niets geschreven'} · "
           + ", ".join(f"{n}× {s}" for s, n in sorted(tellers.items())), ""]
    for p in result.get("problems") or []:
        uit.append(f"- **document**: {p}")
    for i in result["items"]:
        uit += ["", f"## {i['ai_key']} — {i['status']}", ""]
        if i["fout"]:
            uit.append(f"- **fout**: {i['fout']}")
        for g in i["gedaan"]:
            uit.append(f"- {werkwoord}: {g}")
        for o in i["overgeslagen"]:
            uit.append(f"- overgeslagen: {o}")
    return "\n".join(uit) + "\n"
