"""Jira-kant: initiatieven, uren, wijzigingen, en de drie guarded writes. WP-B bouwt dit.
Contract: DESIGN.md §4 en §6 (initiatives.json, hours.json, changes.json).

Vaste feiten (uit tempo.py van de routine-plugin, geverifieerd op deze instance):
- Issue type heet `Initiative` (id 13506). Statussen: zie schema['statussen'][*]['jira'].
- Links: AI↔EAG via linktype `Gerelateerd`; kinderen via `Hierarchy` (zie de inward-noot hieronder).
- Epic Link = customfield_10510; Tempo Account/billingkey = customfield_12012 (staat niet op het
  create/edit-scherm van Initiative; enkel lezen).
- Create-scherm Initiative: summary, description, priority, assignee, Datum ontvangst
  (customfield_14415), Verantwoordelijke (customfield_10614), Trekker (customfield_19014),
  Stakeholder(s) (customfield_20213). Werkorganisatie (customfield_14113, single select: Project,
  Doorlopende werking) staat op create- en editscherm.
- JQL op `issuelinks` wordt geweigerd; links lees je per issue uit het veld `issuelinks`.
- /rest/api/2/search met maxResults ≤ 100 en startAt-paginering; changelog via expand=changelog.
- Worklogs: /rest/api/2/issue/{key}/worklog (Tempo-worklogs zijn Jira-worklogs op Server).
- Schrijven kan enkel met een client uit http.writer(cfg, "jira", <projectsleutel>, apply); de
  meegegeven client is alleen-lezen.

Live geverifieerd tijdens WP-B (read-only, 2026-09-16):
- Een Hierarchy-link staat op het kind als `outwardIssue` ("is part of") en op de ouder als
  `inwardIssue` ("includes"). Kinderen zijn dus de inward-kant.
- `"Epic Link"` en `cf[10510]` zijn hetzelfde veld; kinderen mogen in een ander project zitten
  (OB-1, ROS-31, DECIBEL-1682), dus subtree-zoekopdrachten filteren nooit op project.
- Subtasks hangen rechtstreeks in het veld `subtasks`; geen extra call nodig.
- Changelog: veld `status` (fromString/toString = Jira-statusnaam) en veld `Link` met toString
  "This issue includes AI-30" / "This issue is gerelateerd aan EAG-927"; toString = None betekent
  dat de link net verwijderd is.
- Onderhoud van een product: POR-taak met Bedrijfstoepassing (customfield_20131) = PROD-key en een
  billingkey waarvan het Tempo-account (/rest/tempo-accounts/1/account/key/{key}) categorie `OND`
  (onderhoud) heeft. Bv. PROD-98 ↔ POR-2157 (ZENDAN_OND), PROD-100 ↔ POR-2212 (QGISZEND_OND).
- createmeta voor Initiative staat op /rest/api/2/issue/createmeta/AI/issuetypes/13506 (de oude
  /issue/createmeta geeft 404).
"""
from __future__ import annotations

import datetime as dt
import re

from aiec_lib import config  # noqa: F401
from aiec_lib import http
from aiec_lib import schema as sch

INITIATIVE_TYPE = "Initiative"
INITIATIVE_TYPE_ID = "13506"
HIERARCHY = "Hierarchy"
GERELATEERD = "Gerelateerd"

EPIC_LINK = "customfield_10510"
BILLINGKEY = "customfield_12012"
BEDRIJFSTOEPASSING = "customfield_20131"
# Op PROD-tickets (geverifieerd op PROD-100): applicatiefiche is een URL, het team een keuzeveld.
APPLICATIEFICHE = "customfield_20118"
VERANTWOORDELIJK_TEAM = "customfield_12615"
DATUM_ONTVANGST = "customfield_14415"
VERANTWOORDELIJKE = "customfield_10614"
TREKKER = "customfield_19014"
# Werkorganisatie (single select) spiegelt de Confluence-soort, voor wie enkel Jira leest (beslist 2026-10-01).
WERKORGANISATIE = "customfield_14113"
WERKORGANISATIE_SOORT = {"afgebakend": "Project", "doorlopend": "Doorlopende werking"}

# Velden die we altijd opvragen; alles wat hieronder geparsed wordt staat hierin.
FIELDS = ",".join(["summary", "status", "resolution", "created", "updated", "issuetype",
                   "issuelinks", "labels", "subtasks", "timespent", "description",
                   EPIC_LINK, BILLINGKEY, DATUM_ONTVANGST, VERANTWOORDELIJKE, TREKKER, WERKORGANISATIE])

# Confluence-verwijzing in de description: /pages/431293025 én ?pageId=431293025 komen beide voor.
PAGE_RE = re.compile(r"(?:pages/|pageId=)(\d+)")
# Changelog-item van een link: "This issue includes AI-30".
LINK_RE = re.compile(r"^This issue (.+?) ([A-Z][A-Z0-9_]*-\d+)$")
KEY_RE = re.compile(r"^([A-Z][A-Z0-9_]*)-(\d+)$")

PAGE_SIZE = 100          # /search: maxResults ≤ 100
BATCH = 50               # keys per `key in (...)`-zoekopdracht


# --- laag-bij-de-grond ------------------------------------------------------------------------

def _search(client, jql: str, fields: str = FIELDS, expand: str | None = None) -> list[dict]:
    """Alle pagina's van /rest/api/2/search ophalen."""
    params = {"jql": jql, "fields": fields, "maxResults": PAGE_SIZE, "startAt": 0}
    if expand:
        params["expand"] = expand
    out: list[dict] = []
    while True:
        d = client.get("/rest/api/2/search", dict(params, startAt=len(out)))
        out += d.get("issues") or []
        if len(out) >= d.get("total", 0) or not d.get("issues"):
            return out


def _fetch(client, keys: list[str], expand: str | None = None) -> dict[str, dict]:
    """key → issue, in batches. Nooit op project filteren: kinderen zitten in andere projecten."""
    found: dict[str, dict] = {}
    for i in range(0, len(keys), BATCH):
        chunk = keys[i:i + BATCH]
        for issue in _search(client, f"key in ({', '.join(chunk)}) ORDER BY key", expand=expand):
            found[issue["key"]] = issue
    return found


def key_sort(key: str):
    """AI-9 vóór AI-10; onbekende vormen achteraan."""
    m = KEY_RE.match(key)
    return (m.group(1), int(m.group(2))) if m else (key, 0)


def _user(v) -> str | None:
    return (v or {}).get("displayName") or (v or {}).get("name") if isinstance(v, dict) else v


def _closed_jira_status(schema: dict) -> str:
    for s in sch.statuses(schema):
        if s.get("eind"):
            return s["jira"]
    return "Closed"


def _links(issue: dict) -> list[dict]:
    """[{type, key, direction}] — direction 'outward' = het gelinkte issue staat aan de
    outward-kant (op een Hierarchy-link is dat de ouder)."""
    out = []
    for l in issue["fields"].get("issuelinks") or []:
        other, direction = (l.get("outwardIssue"), "outward") if l.get("outwardIssue") \
            else (l.get("inwardIssue"), "inward")
        if other:
            out.append({"type": l["type"]["name"], "key": other["key"], "direction": direction})
    return out


def _children(issue: dict) -> list[str]:
    """Hierarchy-kinderen: de inward-kant ("includes")."""
    return [l["key"] for l in _links(issue) if l["type"] == HIERARCHY and l["direction"] == "inward"]


def _subtask_keys(issue: dict) -> list[str]:
    return [s["key"] for s in issue["fields"].get("subtasks") or []]


def _eag_keys(cfg: dict, issue: dict) -> list[str]:
    prefix = cfg["atlassian"]["eag_project"] + "-"
    return [l["key"] for l in _links(issue)
            if l["type"] == GERELATEERD and l["key"].startswith(prefix)]


def _to_initiative(cfg: dict, schema: dict, issue: dict) -> dict:
    f = issue["fields"]
    status_raw = (f.get("status") or {}).get("name")
    naam, fase = sch.status_from_jira(schema, status_raw)
    bk = f.get(BILLINGKEY)
    return {
        "key": issue["key"],
        "summary": f.get("summary") or "",
        "status_raw": status_raw,
        "status": naam,
        "fase": fase,
        "resolution": (f.get("resolution") or {}).get("name"),
        "created": f.get("created"),
        "updated": f.get("updated"),
        "last_transition": _last_transition(issue),
        "eag_keys": _eag_keys(cfg, issue),
        "links": _links(issue),
        "children": _children(issue),
        "billingkey": (bk.get("key") if isinstance(bk, dict) else bk),
        "labels": f.get("labels") or [],
        "assignee": _user(f.get("assignee")),
        "trekker": _user(f.get(TREKKER)),
        "verantwoordelijke": _user(f.get(VERANTWOORDELIJKE)),
        "werkorganisatie": (f.get(WERKORGANISATIE) or {}).get("value"),
        "confluence_page_ids": sorted(set(PAGE_RE.findall(f.get("description") or ""))),
        "url": f"{cfg['atlassian']['jira_url'].rstrip('/')}/browse/{issue['key']}",
    }


def _last_transition(issue: dict) -> str | None:
    """Laatste statuswissel uit de changelog; None als de changelog niet meegevraagd is."""
    best = None
    for h in (issue.get("changelog") or {}).get("histories") or []:
        if any(it["field"] == "status" for it in h["items"]) and (best is None or h["created"] > best):
            best = h["created"]
    return best


# --- lezen ------------------------------------------------------------------------------------

def list_initiatives(cfg: dict, client, schema: dict, include_closed: bool = False) -> dict:
    """initiatives.json. Per issue: key, summary, status_raw, status (nette naam), fase (index of
    None), resolution, created, updated, last_transition (laatste statuswissel uit changelog),
    eag_keys (Gerelateerd naar cfg eag_project), links [{type, key, direction}], children
    (Hierarchy includes), billingkey, labels, assignee, trekker, verantwoordelijke,
    confluence_page_ids (uit description, pattern pages/(\\d+)), url."""
    jql = f'project = {cfg["atlassian"]["jira_project"]} AND issuetype = {INITIATIVE_TYPE}'
    if not include_closed:
        jql += f' AND status != "{_closed_jira_status(schema)}"'
    issues = _search(client, jql + " ORDER BY key", expand="changelog")
    return {"generated": dt.datetime.now().isoformat(timespec="seconds"),
            "issues": [_to_initiative(cfg, schema, i) for i in issues]}


def get_initiative(cfg: dict, client, schema: dict, key: str) -> dict:
    """Zelfde velden + description (ruwe tekst)."""
    issue = client.get(f"/rest/api/2/issue/{key}", {"fields": FIELDS, "expand": "changelog"})
    out = _to_initiative(cfg, schema, issue)
    out["description"] = issue["fields"].get("description") or ""
    return out


def search(cfg: dict, client, jql: str, limit: int = 50) -> list[dict]:
    """Ruwe JQL, alleen-lezen: [{key, summary, status, issuetype, updated}]. Bedoeld om
    kandidaat-issues te zoeken (bv. een EAG-ticket op titel) zonder de volle initiatief-vorm."""
    d = client.get("/rest/api/2/search",
                   {"jql": jql, "fields": "summary,status,issuetype,updated",
                    "maxResults": max(1, min(int(limit), PAGE_SIZE)), "startAt": 0})
    return [{"key": i["key"],
             "summary": i["fields"].get("summary") or "",
             "status": (i["fields"].get("status") or {}).get("name"),
             "issuetype": (i["fields"].get("issuetype") or {}).get("name"),
             "updated": i["fields"].get("updated")}
            for i in d.get("issues") or []]


def _subtree(cfg: dict, client, key: str, cache: dict[str, dict]) -> list[str]:
    """Interne subtree die de issue-cache deelt tussen initiatieven."""
    inside: set[str] = set()          # issues waarvan we de kinderen verder volgen
    eag: set[str] = set()             # gelinkte EAG-tickets: wél meegeteld, niet verder gevolgd
    frontier = [key]
    while frontier:
        todo = [k for k in frontier if k not in cache]
        if todo:
            cache.update(_fetch(client, todo))
        nieuw = [k for k in frontier if k in cache and k not in inside]
        inside.update(nieuw)
        volgende: set[str] = set()
        for k in nieuw:
            issue = cache[k]
            volgende.update(_children(issue))
            volgende.update(_subtask_keys(issue))
            eag.update(_eag_keys(cfg, issue))
        if nieuw:
            # Stories hangen met Epic Link (customfield_10510) aan hun epic.
            for issue in _search(client, f'cf[10510] in ({", ".join(nieuw)})'):
                cache[issue["key"]] = issue
                volgende.add(issue["key"])
        frontier = sorted(volgende - inside, key=key_sort)
    return sorted(inside | eag, key=key_sort)


def subtree(cfg: dict, client, key: str) -> list[str]:
    """Alle issue-keys onder een initiatief: Hierarchy-kinderen (recursief), stories via Epic Link
    op elke epic, subtasks via parent, plus de gelinkte EAG-tickets. Bevat key zelf."""
    return _subtree(cfg, client, key, {})


def _worklogs(client, key: str) -> list[dict]:
    d = client.get(f"/rest/api/2/issue/{key}/worklog")
    return d.get("worklogs") or []


def hours(cfg: dict, client, schema: dict, keys: list[str] | None = None,
          since: dt.date | None = None, until: dt.date | None = None) -> dict:
    """hours.json: per initiatief total_h (alle worklogs), period_h (since..until), per_month,
    issues (de subtree). Zonder keys: alle initiatieven incl. Afgesloten."""
    cache: dict[str, dict] = {}
    if keys:
        wanted = list(keys)
    else:
        wanted = [i["key"] for i in
                  _search(client, f'project = {cfg["atlassian"]["jira_project"]} AND '
                                  f"issuetype = {INITIATIVE_TYPE} ORDER BY key")]
    subtrees = {k: _subtree(cfg, client, k, cache) for k in wanted}

    alle = sorted({i for st in subtrees.values() for i in st}, key=key_sort)
    # De gelinkte EAG-tickets zitten nog niet in de cache (we volgen hun kinderen niet); toch
    # ophalen, want zonder timespent hoeft de worklog-call niet.
    ontbreekt = [k for k in alle if k not in cache]
    if ontbreekt:
        cache.update(_fetch(client, ontbreekt))
    wl_cache: dict[str, list[dict]] = {}
    for k in alle:
        issue = cache.get(k)
        if issue is not None and not issue["fields"].get("timespent"):
            wl_cache[k] = []
        else:
            wl_cache[k] = _worklogs(client, k)

    lo = since.isoformat() if since else None
    hi = until.isoformat() if until else None
    per: dict[str, dict] = {}
    for k in wanted:
        total = period = 0.0
        per_month: dict[str, float] = {}
        for issue_key in subtrees[k]:
            for w in wl_cache.get(issue_key) or []:
                uren = (w.get("timeSpentSeconds") or 0) / 3600
                total += uren
                dag = (w.get("started") or "")[:10]
                if (lo and dag < lo) or (hi and dag > hi):
                    continue
                period += uren
                maand = dag[:7]
                per_month[maand] = round(per_month.get(maand, 0.0) + uren, 2)
        per[k] = {"total_h": round(total, 2), "period_h": round(period, 2),
                  "per_month": dict(sorted(per_month.items())), "issues": subtrees[k]}
    return {"since": lo, "until": hi, "per_initiative": per}


def changes(cfg: dict, client, schema: dict, since: dt.date, until: dt.date | None = None) -> dict:
    """changes.json: transitions [{key, from, to, when}] (nette namen), new_initiatives
    [{key, summary, created}], new_links [{key, linked, type, when}] — uit changelog."""
    lo = since.isoformat()
    hi = (until or dt.date.today()).isoformat()
    jql = (f'project = {cfg["atlassian"]["jira_project"]} AND issuetype = {INITIATIVE_TYPE} '
           f'AND updated >= "{lo}" ORDER BY key')
    issues = _search(client, jql, expand="changelog")

    transitions, new_links, new_initiatives = [], [], []
    for issue in issues:
        key = issue["key"]
        if lo <= (issue["fields"].get("created") or "")[:10] <= hi:
            new_initiatives.append({"key": key, "summary": issue["fields"].get("summary") or "",
                                    "created": issue["fields"].get("created")})
        for h in (issue.get("changelog") or {}).get("histories") or []:
            when = h["created"]
            if not (lo <= when[:10] <= hi):
                continue
            for it in h["items"]:
                if it["field"] == "status":
                    transitions.append({
                        "key": key,
                        "from": sch.status_from_jira(schema, it.get("fromString"))[0],
                        "to": sch.status_from_jira(schema, it.get("toString"))[0],
                        "when": when})
                elif it["field"] == "Link" and it.get("toString"):
                    m = LINK_RE.match(it["toString"].strip())
                    if m:
                        new_links.append({"key": key, "linked": m.group(2), "type": m.group(1),
                                          "when": when})
    return {"since": lo, "until": hi,
            "transitions": sorted(transitions, key=lambda t: (t["when"], t["key"])),
            "new_initiatives": sorted(new_initiatives, key=lambda n: key_sort(n["key"])),
            "new_links": sorted(new_links, key=lambda n: (n["when"], n["key"]))}


# --- schrijven (altijd via http.writer; zonder --apply enkel de payload) -----------------------

def create_initiative(cfg: dict, client, schema: dict, title: str, description: str, eag: str | None = None,
                      verantwoordelijke: str | None = None, trekker: str | None = None, apply: bool = False) -> dict:
    """Initiative aanmaken (Datum ontvangst = vandaag) en Gerelateerd-link naar eag. Geeft
    {applied, key | None, payload}."""
    project = cfg["atlassian"]["jira_project"]
    w = http.writer(cfg, "jira", project, apply)          # guard eerst: --apply in dry-run = exit 3
    fields = {"project": {"key": project},
              "issuetype": {"id": INITIATIVE_TYPE_ID},
              "summary": title,
              "description": description,
              DATUM_ONTVANGST: dt.date.today().isoformat()}
    if verantwoordelijke:
        fields[VERANTWOORDELIJKE] = {"name": verantwoordelijke}
    if trekker:
        fields[TREKKER] = {"name": trekker}
    payload = {"fields": fields}
    out = {"applied": False, "key": None, "payload": payload,
           "link": _link_payload(eag, None) if eag else None}
    if not apply:
        return out
    # ONGEVERIFIEERD: nooit uitgevoerd (write-mode staat op dry-run). Het veldenlijstje komt uit
    # /rest/api/2/issue/createmeta/AI/issuetypes/13506, die wél live gelezen is.
    created = w.post("/rest/api/2/issue", payload)
    out["applied"], out["key"] = True, created["key"]
    if eag:
        out["link"] = _link_payload(eag, created["key"])
        w.post("/rest/api/2/issueLink", out["link"])      # ONGEVERIFIEERD: nooit uitgevoerd
    return out


def _link_payload(eag_key: str, ai_key: str | None) -> dict:
    return {"type": {"name": GERELATEERD},
            "inwardIssue": {"key": ai_key},
            "outwardIssue": {"key": eag_key}}


def link(cfg: dict, client, key: str, other: str, apply: bool = False) -> dict:
    """Link Gerelateerd tussen key en other (idempotent: bestaat hij al, dan niets)."""
    project = key.split("-")[0]
    w = http.writer(cfg, "jira", project, apply)          # guard eerst, ook als de link al bestaat
    issue = client.get(f"/rest/api/2/issue/{key}", {"fields": "issuelinks"})
    bestaat = any(l["type"] == GERELATEERD and l["key"] == other for l in _links(issue))
    payload = _link_payload(other, key)
    out = {"applied": False, "exists": bestaat, "key": key, "other": other, "payload": payload}
    if bestaat or not apply:
        return out
    w.post("/rest/api/2/issueLink", payload)             # ONGEVERIFIEERD: nooit uitgevoerd
    out["applied"] = True
    return out


def transition(cfg: dict, client, schema: dict, key: str, to_naam: str, resolution: str | None = None,
               apply: bool = False) -> dict:
    """Nette naam → Jira-status via schema.jira_from_status; transitie-id opzoeken via
    /transitions; resolution meegeven als het scherm dat vraagt."""
    project = key.split("-")[0]
    w = http.writer(cfg, "jira", project, apply)
    try:
        doel = sch.jira_from_status(schema, to_naam)
    except KeyError as e:
        raise ValueError(str(e).strip("'")) from None     # aiec.py vertaalt ValueError naar exit 4
    beschikbaar = client.get(f"/rest/api/2/issue/{key}/transitions",
                             {"expand": "transitions.fields"}).get("transitions") or []
    gekozen = next((t for t in beschikbaar if sch.fold(t["to"]["name"]) == sch.fold(doel)), None)
    out = {"applied": False, "key": key, "to": doel,
           "available": [{"id": t["id"], "name": t["name"], "to": t["to"]["name"]} for t in beschikbaar]}
    if gekozen is None:
        out["problem"] = (f"geen transitie naar '{doel}' beschikbaar vanuit de huidige status; "
                          f"wel: {', '.join(t['to']['name'] for t in beschikbaar)}")
        out["payload"] = None
        return out
    payload = {"transition": {"id": gekozen["id"]}}
    # Op deze instance geeft /transitions?expand=transitions.fields geen velden terug voor
    # Initiative, dus resolution rijdt niet mee op de transitie maar gaat als aparte edit.
    # ONGEVERIFIEERD: nooit uitgevoerd (write-mode staat op dry-run).
    resolution_payload = None
    if resolution:
        if "resolution" in (gekozen.get("fields") or {}):
            payload["fields"] = {"resolution": {"name": resolution}}
        else:
            resolution_payload = {"fields": {"resolution": {"name": resolution}}}
    out["payload"], out["resolution_payload"] = payload, resolution_payload
    if not apply:
        return out
    w.post(f"/rest/api/2/issue/{key}/transitions", payload)   # ONGEVERIFIEERD: nooit uitgevoerd
    if resolution_payload:
        w.put(f"/rest/api/2/issue/{key}", resolution_payload)
    out["applied"] = True
    return out


# --- markdown ---------------------------------------------------------------------------------

def _tabel(kop: list[str], rijen: list[list[str]]) -> list[str]:
    return ["| " + " | ".join(kop) + " |", "|" + "---|" * len(kop)] + \
           ["| " + " | ".join(rijen_cel) + " |" for rijen_cel in rijen]


def list_markdown(data: dict) -> str:
    """Tabel: key | status | soort? (n.v.t. hier) | summary | EAG | laatste transitie | updated."""
    rijen = [[i["key"], i["status"] or "—", i["summary"],
              ", ".join(i["eag_keys"]) or "—",
              (i["last_transition"] or "")[:10] or "—", (i["updated"] or "")[:10]]
             for i in data["issues"]]
    out = [f"# Jira-initiatieven ({len(data['issues'])})", ""]
    out += _tabel(["key", "status", "summary", "EAG", "laatste transitie", "updated"], rijen)
    return "\n".join(out) + "\n"


def hours_markdown(data: dict) -> str:
    per = data["per_initiative"]
    maanden = sorted({m for v in per.values() for m in v["per_month"]})
    kop = ["initiatief", "periode (u)", "totaal (u)"] + maanden + ["issues"]
    rijen = []
    for k in sorted(per, key=key_sort):
        v = per[k]
        rijen.append([k, f"{v['period_h']:.2f}", f"{v['total_h']:.2f}"]
                     + [f"{v['per_month'].get(m, 0):.2f}" for m in maanden]
                     + [str(len(v["issues"]))])
    periode = f"{data.get('since') or '—'} … {data.get('until') or '—'}"
    out = [f"# Uren per initiatief ({periode})", ""]
    out += _tabel(kop, rijen)
    out += ["", f"Totaal in de periode: {sum(v['period_h'] for v in per.values()):.2f} u."]
    return "\n".join(out) + "\n"


def changes_markdown(data: dict) -> str:
    out = [f"# Wijzigingen {data['since']} … {data['until']}", "", "## Statuswissels", ""]
    if data["transitions"]:
        out += _tabel(["wanneer", "key", "van", "naar"],
                      [[t["when"][:10], t["key"], t["from"] or "—", t["to"] or "—"]
                       for t in data["transitions"]])
    else:
        out.append("Geen.")
    out += ["", "## Nieuwe initiatieven", ""]
    if data["new_initiatives"]:
        out += _tabel(["key", "summary", "aangemaakt"],
                      [[n["key"], n["summary"], (n["created"] or "")[:10]] for n in data["new_initiatives"]])
    else:
        out.append("Geen.")
    out += ["", "## Nieuwe links", ""]
    if data["new_links"]:
        out += _tabel(["wanneer", "key", "relatie", "gelinkt"],
                      [[l["when"][:10], l["key"], l["type"], l["linked"]] for l in data["new_links"]])
    else:
        out.append("Geen.")
    return "\n".join(out) + "\n"
