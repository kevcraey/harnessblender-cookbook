#!/usr/bin/env python3
"""tempo.py — tijdschrijven via Jira Server + Tempo Timesheets 4. Geen oordeel:
wat er geboekt wordt beslist de LLM (en Kenzo), dit script boekt en telt.

  tempo.py gaps [--days 30]         werkdagen (ma-vr) met <7,6h of >8h, plus wat er al staat
  tempo.py day <YYYY-MM-DD>         alle worklogs van één dag
  tempo.py issue <KEY>              id, samenvatting, status, billingkey van een issue
  tempo.py search "<jql>"           issues zoeken (key | status | samenvatting)
  tempo.py book <tabel.md> [--dry]  boek de regels uit een markdown-tabel
  tempo.py issue-create --project P --summary S [--epic KEY] [--account ID] [--description D] [--close]

Tabelformaat voor `book` (kop en scheidingsregel verplicht; regels die met `~~`
beginnen of in de laatste kolom `skip` dragen worden overgeslagen):

  | datum      | ticket   | uren | commentaar                       |
  |------------|----------|------|----------------------------------|
  | 2026-09-04 | AI-48    | 7.6  | Assessment                        |

Vaste feiten die eerder één per één ontdekt zijn:
- Tempo wil als `worker` de Jira user **key** (opaque, uit /rest/api/2/myself),
  niet de username — met de username vindt de search niets.
- Billingkey = Tempo Account = customfield_12012; bij aanmaken als **string-id**
  meegeven ("1047"); {"id": "1047"} faalt met "Account id 'null' is invalid".
- /rest/api/2/issue/createmeta?projectKeys= bestaat niet meer op deze Jira;
  velden opvragen kan via createmeta/<project>/issuetypes/<id> of de Atlassian-MCP.
- Volle werkdag = 7,6h (27360 s).
"""

import argparse
import collections
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

JIRA = os.environ.get("JIRA_URL", "https://jira.omgeving.vlaanderen.be/jira")
TEMPO = f"{JIRA}/rest/tempo-timesheets/4"
FULL_DAY = 7.6
ACCOUNT_FIELD = "customfield_12012"
EPIC_FIELD = "customfield_10510"


def token():
    out = subprocess.run(["security", "find-generic-password", "-s", "jira-personal-token",
                          "-a", os.environ.get("USER", ""), "-w"], capture_output=True, text=True)
    t = out.stdout.strip()
    if not t:
        out = subprocess.run(["security", "find-generic-password", "-s", "jira-personal-token", "-w"],
                             capture_output=True, text=True)
        t = out.stdout.strip()
    if not t:
        sys.exit("keychain-item 'jira-personal-token' niet gevonden")
    return t


HDR = None


def hdr():
    global HDR
    if HDR is None:
        HDR = {"Authorization": "Bearer " + token(), "Content-Type": "application/json"}
    return HDR


def call(method, url, body=None):
    req = urllib.request.Request(url, method=method, headers=hdr(),
                                 data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:400]
        raise RuntimeError(f"{method} {url.split('?')[0]} -> {e.code}: {detail}") from None


def me():
    return call("GET", f"{JIRA}/rest/api/2/myself")


def worklogs(frm, to):
    return call("POST", f"{TEMPO}/worklogs/search",
                {"from": frm.isoformat(), "to": to.isoformat(), "worker": [me()["key"]]}) or []


def per_day(logs):
    d = collections.defaultdict(list)
    for w in logs:
        d[w["started"][:10]].append(w)
    return d


def fmt_log(w):
    # altijd key én titel: Kenzo kent de nummers niet van buiten
    i = w.get("issue") or {}
    return (f"{i.get('key', '?')} *{i.get('summary', '')}* {w['timeSpentSeconds'] / 3600:.1f}h "
            f"— {w.get('comment') or ''}")


def cmd_gaps(args):
    today = dt.date.today()
    frm = today - dt.timedelta(days=args.days)
    # vandaag telt enkel mee met --today ('s avonds); 's ochtends is vandaag nog geen gat
    last = today if args.today else today - dt.timedelta(days=1)
    logs = per_day(worklogs(frm, last))
    d = frm
    rows = []
    while d <= last:
        if d.weekday() < 5:  # nooit weekend: daar wordt niet geschreven, ook al werd er gewerkt
            hrs = sum(w["timeSpentSeconds"] for w in logs.get(d.isoformat(), [])) / 3600
            if hrs < FULL_DAY - 0.01 or hrs > 8.0:
                rows.append((d, hrs, logs.get(d.isoformat(), [])))
        d += dt.timedelta(days=1)
    if not rows:
        print(f"Geen onvolledige werkdagen in de laatste {args.days} dagen.")
        return
    print(f"Onvolledige werkdagen (laatste {args.days} dagen, norm {FULL_DAY}h):\n")
    for d, hrs, ws in rows:
        print(f"## {d.isoformat()} ({d.strftime('%a')}) — {hrs:.1f}h geboekt, {FULL_DAY - hrs:.1f}h open")
        for w in ws:
            print(f"- {fmt_log(w)}")
        print()


def cmd_day(args):
    d = dt.date.fromisoformat(args.date)
    ws = worklogs(d, d)
    tot = sum(w["timeSpentSeconds"] for w in ws) / 3600
    print(f"{d.isoformat()} ({d.strftime('%a')}): {tot:.1f}h")
    for w in ws:
        print(f"- {fmt_log(w)}")


def issue(key):
    i = call("GET", f"{JIRA}/rest/api/2/issue/{key}?fields=summary,status,{ACCOUNT_FIELD},issuetype")
    f = i["fields"]
    acc = f.get(ACCOUNT_FIELD) or {}
    return {"id": int(i["id"]), "key": i["key"], "summary": f["summary"], "status": f["status"]["name"],
            "type": f["issuetype"]["name"], "account": acc.get("key"), "account_name": acc.get("name")}


def cmd_issue(args):
    print(json.dumps(issue(args.key), ensure_ascii=False, indent=1))


def cmd_search(args):
    d = call("GET", f"{JIRA}/rest/api/2/search?" + urllib.parse.urlencode(
        {"jql": args.jql, "maxResults": args.max, "fields": f"summary,status,{ACCOUNT_FIELD}"}))
    for i in d.get("issues", []):
        f = i["fields"]
        acc = (f.get(ACCOUNT_FIELD) or {}).get("key") or "-"
        print(f"{i['key']} | {f['status']['name']} | {acc} | {f['summary']}")


def parse_table(path):
    """Kolommen op naam uit de kopregel: datum, ticket, uren, commentaar verplicht;
    titel optioneel (leesbaarheid voor Kenzo, wordt niet geboekt); een laatste kolom
    met `skip` slaat de regel over."""
    rows, col = [], None
    for line in open(path, encoding="utf-8"):
        s = line.strip()
        if not s.startswith("|") or re.match(r"^[\s:|-]+$", s):  # scheidingsregel |---|---|
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if col is None:
            names = [c.lower() for c in cells]
            if "datum" in names and "ticket" in names and "uren" in names:
                col = {n: i for i, n in enumerate(names)}
                if "commentaar" not in col:
                    sys.exit("tabel mist kolom 'commentaar'")
            continue
        if cells[0].startswith("~~") or cells[-1].lower() == "skip":
            continue
        try:
            day = dt.date.fromisoformat(cells[col["datum"]])
            hrs = float(cells[col["uren"]].replace(",", "."))
        except (ValueError, IndexError):
            print(f"regel overgeslagen (datum/uren onleesbaar): {s}", file=sys.stderr)
            continue
        key = cells[col["ticket"]].upper()
        if key in ("?", ""):
            print(f"regel overgeslagen (geen ticket): {s}", file=sys.stderr)
            continue
        rows.append((day, key, hrs, cells[col["commentaar"]]))
    if col is None:
        sys.exit("geen tabelkop met datum/ticket/uren gevonden in " + path)
    return rows


def cmd_book(args):
    rows = parse_table(args.table)
    if not rows:
        sys.exit("geen boekbare regels gevonden in " + args.table)
    weekend = [r for r in rows if r[0].weekday() >= 5]
    if weekend:
        sys.exit("weekenddagen in de tabel — daar wordt niet geschreven: "
                 + ", ".join(r[0].isoformat() for r in weekend))
    worker = me()["key"]
    info = {}
    ok = 0
    for day, key, hrs, comment in rows:
        if key not in info:
            try:
                info[key] = issue(key)
            except RuntimeError as e:
                print(f"FAIL {day} {key}: {e}")
                continue
        label = f"{key} *{info[key]['summary']}*"
        secs = int(round(hrs * 3600))
        body = {"attributes": {}, "billableSeconds": secs, "originTaskId": info[key]["id"],
                "started": f"{day.isoformat()} 00:00:00.000", "timeSpentSeconds": secs,
                "worker": worker, "comment": comment}
        if args.dry:
            print(f"DRY  {day} {label} {hrs}h — {comment}")
            ok += 1
            continue
        try:
            call("POST", f"{TEMPO}/worklogs/", body)
            print(f"OK   {day} {label} {hrs}h")
            ok += 1
        except RuntimeError as e:
            print(f"FAIL {day} {key} {hrs}h: {e}")
    print(f"\n{'gepland' if args.dry else 'geboekt'}: {ok}/{len(rows)}")
    if not args.dry:
        days = sorted({r[0] for r in rows})
        logs = per_day(worklogs(days[0], days[-1]))
        print("\nTotalen na boeking:")
        for d in days:
            tot = sum(w["timeSpentSeconds"] for w in logs.get(d.isoformat(), [])) / 3600
            flag = "" if abs(tot - FULL_DAY) < 0.01 else "  <-- niet 7.6"
            print(f"- {d.isoformat()} ({d.strftime('%a')}) {tot:.1f}h{flag}")


def cmd_issue_create(args):
    m = me()
    fields = {"project": {"key": args.project}, "issuetype": {"name": args.type},
              "summary": args.summary, "reporter": {"name": m["name"]}, "assignee": {"name": m["name"]}}
    if args.description:
        fields["description"] = args.description
    if args.epic:
        fields[EPIC_FIELD] = args.epic
    if args.account:
        fields[ACCOUNT_FIELD] = str(args.account)  # string-id, zie docstring
    created = call("POST", f"{JIRA}/rest/api/2/issue", {"fields": fields})
    key = created["key"]
    info = issue(key)
    print(f"aangemaakt: {key} — {info['summary']} | billingkey {info['account'] or 'GEEN'} | {info['status']}")
    if args.account and not info["account"]:
        sys.exit("billingkey is niet blijven staan — controleer vóór je erop boekt")
    if args.close:
        tr = call("GET", f"{JIRA}/rest/api/2/issue/{key}/transitions")["transitions"]
        close = next((t for t in tr if t["name"].lower() in ("close", "closed", "sluiten", "done")), None)
        if not close:
            sys.exit("geen Close-transitie gevonden: " + ", ".join(t["name"] for t in tr))
        call("POST", f"{JIRA}/rest/api/2/issue/{key}/transitions", {"transition": {"id": close["id"]}})
        print(f"gesloten via '{close['name']}'")
    print(f"{JIRA}/browse/{key}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("gaps"); p.add_argument("--days", type=int, default=30)
    p.add_argument("--today", action="store_true", help="vandaag ook als gat tellen (avond)")
    p.set_defaults(fn=cmd_gaps)
    p = sub.add_parser("day"); p.add_argument("date"); p.set_defaults(fn=cmd_day)
    p = sub.add_parser("issue"); p.add_argument("key"); p.set_defaults(fn=cmd_issue)
    p = sub.add_parser("search"); p.add_argument("jql"); p.add_argument("--max", type=int, default=30)
    p.set_defaults(fn=cmd_search)
    p = sub.add_parser("book"); p.add_argument("table"); p.add_argument("--dry", action="store_true")
    p.set_defaults(fn=cmd_book)
    p = sub.add_parser("issue-create")
    p.add_argument("--project", required=True); p.add_argument("--summary", required=True)
    p.add_argument("--type", default="Story"); p.add_argument("--epic"); p.add_argument("--account")
    p.add_argument("--description"); p.add_argument("--close", action="store_true")
    p.set_defaults(fn=cmd_issue_create)
    args = ap.parse_args()
    try:
        args.fn(args)
    except RuntimeError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
