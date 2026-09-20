#!/usr/bin/env python3
"""collect.py — deterministische verzamelaar voor de routine (ochtend/avond).

Haalt de activiteit van één tijdvenster op uit alle bronnen die zonder oordeel te
bereiken zijn en schrijft ze weg als markdown: één bundel plus één bestand per
bron, zodat elke pane enkel leest wat ze nodig heeft. De LLM doet alleen wat
oordeel vraagt: samenvatten, groeperen, overlap wegen, schrijven.

Bronnen en hun credential-weg:
  rocketchat  keychain  rocketchat-personal-access-token (acct = userId)
  jira        keychain  jira-personal-token        (-a $(whoami))
  confluence  keychain  confluence-personal-token  (-a $(whoami))
  graph       GRAPH_TOKEN_FILE / GRAPH_TOKEN / klembord (pbpaste); kortlevend
  chrome      lokale History-sqlite (kopie, want Chrome houdt een lock)
  git         repo's onder ~/Dropbox + gewijzigde bestanden
  claude      ~/.claude/projects/**/*.jsonl
  vault       git diff in de vault
  notes       bestaande daily notes in het venster (voor overlap-detectie)

Venster: --since en --until (ISO). De routine draait dit script per dag, zodat
een gemiste week dag per dag ingehaald wordt en elke pane een kleine bundel
krijgt. Zonder --until: tot nu. Zonder --since: 00:00 van gisteren.

Uitvoer: --out DIR schrijft DIR/bundle.md en DIR/<bron>.md; zonder --out gaat
de bundel naar stdout (handig om te testen).
"""

import argparse
import contextlib
import datetime as dt
import html
import io
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

HOME = os.path.expanduser("~")
VAULT = os.environ.get("VAULT", f"{HOME}/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain")
# realpath: ~/Dropbox is een symlink naar CloudStorage, en find volgt symlinks niet —
# zonder dit levert de git-bron stilzwijgend niets op.
CODE_ROOT = os.path.realpath(os.environ.get("DIGEST_CODE_ROOT", f"{HOME}/Dropbox"))
JIRA = os.environ.get("JIRA_URL", "https://jira.omgeving.vlaanderen.be/jira")
CONFLUENCE = os.environ.get("CONFLUENCE_URL", "https://confluence.omgeving.vlaanderen.be/confluence")
ROCKET = os.environ.get("ROCKETCHAT_URL", "https://rocketchat.omgeving.vlaanderen.be")

# Auth-redirects en andere doorvoerpagina's: nooit signaal, altijd ruis.
CHROME_SKIP = re.compile(
    r"(authenticatie\.vlaanderen\.be|login\.microsoftonline\.com|accounts\.google\.com"
    r"|idp\.iamfas\.belgium\.be|sts\.vlaanderen\.be|ssov2\.omgeving\.vlaanderen\.be"
    r"|partner-sso\.anthropic\.com|_oauth|/login|/signin)"
)
# Domeinen die Kenzo nooit in de bundel wil. Eén domein (of substring) per regel,
# '#' voor commentaar. Bewust een lijst die hij zelf beheert: raden of iets werk
# of privé is, is oordeel — dat hoort bij de LLM, niet bij een regex hier.
EXCLUDE_FILE = os.environ.get(
    "DIGEST_EXCLUDE_DOMAINS", f"{HOME}/.config/routine/exclude-domains.txt")

WARN = []


def warn(msg):
    WARN.append(msg)
    print(f"[waarschuwing] {msg}", file=sys.stderr)


# ── helpers ──────────────────────────────────────────────────────────────────

def sh(cmd, cwd=None, timeout=60):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.stdout
    except Exception:
        return ""


def keychain(service=None, label=None, account=None):
    """Haalt een wachtwoord op; None als hij er niet is (geen exceptie)."""
    cmd = ["security", "find-generic-password"]
    if label:
        cmd += ["-l", label]
    if service:
        cmd += ["-s", service]
    if account:
        cmd += ["-a", account]
    out = sh(cmd + ["-w"], timeout=15).strip()
    return out or None


def keychain_account(label):
    """Het acct-attribuut van een keychain-item (Rocket.Chat stopt daar de userId in)."""
    out = sh(["security", "find-generic-password", "-l", label], timeout=15)
    m = re.search(r'"acct"<blob>="([^"]+)"', out)
    return m.group(1) if m else None


def graph_token():
    """Token uit (in volgorde) GRAPH_TOKEN_FILE, GRAPH_TOKEN, klembord. Nooit printen."""
    f = os.environ.get("GRAPH_TOKEN_FILE")
    if f and os.path.exists(f):
        t = open(f, encoding="utf-8").read().strip()
    else:
        t = os.environ.get("GRAPH_TOKEN") or sh(["pbpaste"], timeout=10).strip()
    if not t or len(t) < 500 or t.count(".") != 2:
        return None
    return t


def loc(ts, fmt="%Y-%m-%d %H:%M"):
    """UTC-tijdstempel uit een API naar lokale tijd. Graph, Teams en Rocket.Chat
    geven allemaal UTC terug; ongeconverteerd staat je hele dag twee uur te vroeg."""
    if not ts:
        return "?"
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().strftime(fmt)
    except ValueError:
        return ts[:16].replace("T", " ")


def clean(s, limit=None):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = re.sub(r"\s+", " ", html.unescape(s)).strip()
    return s[:limit] if limit else s


def get_json(url, headers, timeout=45):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def get_text(url, headers, timeout=45):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def section(title):
    print(f"\n## {title}\n")


def utc(t):
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── venster ──────────────────────────────────────────────────────────────────

def window(args):
    now = dt.datetime.now()
    if args.since:
        start = dt.datetime.fromisoformat(args.since)
    else:
        start = (now - dt.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    end = dt.datetime.fromisoformat(args.until) if args.until else now
    if end > now:
        end = now
    return start, end


# ── bronnen ──────────────────────────────────────────────────────────────────

def src_rocketchat(start, end):
    token = keychain(label="rocketchat-personal-access-token")
    uid = keychain_account("rocketchat-personal-access-token")
    if not token or not uid:
        warn("Rocket.Chat overgeslagen: keychain-item 'rocketchat-personal-access-token' niet gevonden.")
        return
    hdr = {"X-Auth-Token": token, "X-User-Id": uid}
    lo = start.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    hi = end.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    try:
        subs = get_json(f"{ROCKET}/api/v1/subscriptions.get", hdr)
    except Exception as e:
        warn(f"Rocket.Chat subscriptions faalde: {e}")
        return
    ep = {"c": "channels.history", "p": "groups.history", "d": "im.history"}
    section("Rocket.Chat")
    for s in subs.get("update", []):
        if max(s.get("ls") or "", s.get("_updatedAt") or "") < lo:
            continue
        if s.get("t") not in ep:
            continue
        q = urllib.parse.urlencode(
            {"roomId": s["rid"], "oldest": lo, "latest": hi, "count": 100, "inclusive": "false"}
        )
        try:
            hist = get_json(f"{ROCKET}/api/v1/{ep[s['t']]}?{q}", hdr)
        except Exception as e:
            warn(f"Rocket.Chat history faalde voor {s.get('name')}: {e}")
            continue
        # m.get("t") gezet = systeembericht (join/leave/topic) -> ruis
        msgs = [m for m in hist.get("messages", []) if m.get("msg") and not m.get("t")]
        if not msgs:
            continue
        kind = {"c": "kanaal", "p": "groep", "d": "DM"}[s["t"]]
        print(f"### [{kind}] {s.get('fname') or s.get('name')}")
        for m in reversed(msgs):
            who = (m.get("u") or {}).get("username", "?")
            print(f"- {loc(m['ts'])} **{who}**: {clean(m['msg'], 400)}")
        print()


def src_graph(start, end):
    token = graph_token()
    if not token:
        warn("Graph overgeslagen: geen geldig token in GRAPH_TOKEN_FILE, GRAPH_TOKEN of op het "
             "klembord (Graph Explorer -> tab 'Access token' -> kopiëren).")
        return
    hdr = {"Authorization": "Bearer " + token}
    lo, hi = utc(start), utc(end)

    def g(path, extra=None):
        h = dict(hdr)
        if extra:
            h.update(extra)
        try:
            return get_json("https://graph.microsoft.com/v1.0" + path, h)
        except urllib.error.HTTPError as e:
            if e.code == 401:
                warn("Graph-token verlopen of ongeldig (401).")
            else:
                warn(f"Graph {path.split('?')[0]} gaf {e.code}.")
            return None

    def who(addr):
        return ((addr or {}).get("emailAddress") or {}).get("name") or "?"

    def mine(addr):
        return "@" in (((addr or {}).get("emailAddress") or {}).get("address") or "") and \
            (((addr or {}).get("emailAddress") or {}).get("address") or "").lower().startswith("kenzo.vancraeynest")

    section("Mail")
    folders = {}
    for folder in ("inbox", "sentitems"):
        q = urllib.parse.urlencode({
            "$filter": f"receivedDateTime ge {lo} and receivedDateTime lt {hi}",
            "$select": "id,subject,from,toRecipients,ccRecipients,receivedDateTime,categories,"
                       "bodyPreview,conversationId",
            "$orderby": "receivedDateTime desc", "$top": 100})
        d = g(f"/me/mailFolders/{folder}/messages?{q}")
        if d is None:
            return  # 401 op de eerste call: verdere Graph-calls hebben geen zin
        folders[folder] = d.get("value", [])
    # Onbeantwoord = inbox-mail waarvan de conversatie geen latere verzonden mail kent.
    # Hier binnen het venster; buiten het venster verzonden antwoorden mist dit dus —
    # de ochtend-lijst is een hint voor het oordeel, geen waarheid.
    replied = {}
    for m in folders.get("sentitems", []):
        cid = m.get("conversationId")
        if cid:
            replied[cid] = max(replied.get(cid, ""), m.get("receivedDateTime") or "")
    for folder, msgs in folders.items():
        print(f"### {folder}")
        for m in msgs:
            cats = m.get("categories") or []
            # ICR2 = EU-only, ICR3/4 = nooit. Fail-open op ongetagde mail is bewust.
            if any(c in cats for c in ("ICR2", "ICR3", "ICR4")):
                print(f"- [ICR-overgeslagen] {m.get('subject')}")
                continue
            flags = []
            if "synced" in cats:
                flags.append("synced")
            if folder == "inbox":
                to = m.get("toRecipients") or []
                flags.append("aan mij" if any(mine(t) for t in to) else "cc")
                cid = m.get("conversationId")
                if not (cid in replied and replied[cid] > (m.get("receivedDateTime") or "")):
                    flags.append("onbeantwoord")
            frm = who(m.get("from"))
            to_names = [who(t) for t in (m.get("toRecipients") or [])][:3]
            tag = f" [{', '.join(flags)}]" if flags else ""
            print(f"- {loc(m['receivedDateTime'])} **{frm}** -> {', '.join(to_names)}{tag}")
            print(f"  - *{m.get('subject')}* — {clean(m.get('bodyPreview'), 300)}")
            print(f"  - id: `{m['id']}`")
        print()

    section("Agenda")
    # De agenda loopt tot het einde van de laatste dag in het venster, niet tot 'nu':
    # 's ochtends is de rest van de dag precies het interessantste stuk. Expliciete
    # UTC-offsets, want Graph leest naakte tijdstempels in de query als UTC.
    cal_lo = urllib.parse.quote(start.astimezone().strftime("%Y-%m-%dT%H:%M:%S%z"))
    cal_hi = urllib.parse.quote(
        end.astimezone().replace(hour=23, minute=59, second=59).strftime("%Y-%m-%dT%H:%M:%S%z"))
    d = g(
        f"/me/calendarView?startDateTime={cal_lo}"
        f"&endDateTime={cal_hi}"
        "&$select=subject,start,end,organizer,attendees,isCancelled,responseStatus,isAllDay,type,showAs"
        "&$orderby=start/dateTime&$top=100",
        {"Prefer": 'outlook.timezone="Romance Standard Time"'},  # anders komt alles in UTC terug
    )
    for ev in (d or {}).get("value", []):
        att = [(a["emailAddress"].get("name"), a["emailAddress"].get("address"))
               for a in ev.get("attendees", []) if not mine(a)][:15]
        flags = []
        if ev.get("isCancelled"):
            flags.append("geannuleerd")
        if ev.get("isAllDay"):
            flags.append("dagvullend")
        if ev.get("type") in ("occurrence", "exception"):
            flags.append("terugkerend")
        if (ev.get("responseStatus") or {}).get("response") in ("declined",):
            flags.append("afgewezen")
        if not att:
            flags.append("zonder deelnemers")
        try:
            s = dt.datetime.fromisoformat(ev["start"]["dateTime"][:19])
            e = dt.datetime.fromisoformat(ev["end"]["dateTime"][:19])
            dur = int((e - s).total_seconds() // 60)
        except Exception:
            dur = "?"
        tag = f" [{', '.join(flags)}]" if flags else ""
        print(f"- {ev['start']['dateTime'][:16].replace('T', ' ')}–{ev['end']['dateTime'][11:16]} "
              f"({dur} min) **{ev.get('subject')}**{tag}")
        print(f"  - organisator: {who(ev.get('organizer'))} | deelnemers: "
              + ", ".join(f"{n} <{a}>" if a else (n or "?") for n, a in att))
    print()

    section("Teams-chats")
    d = g("/me/chats?$top=50&$expand=lastMessagePreview")
    for ch in (d or {}).get("value", []):
        lm = ch.get("lastMessagePreview") or {}
        if (lm.get("createdDateTime") or "") < lo:
            continue
        msgs = g(f"/me/chats/{ch['id']}/messages?$top=40")
        if not msgs:
            continue
        rel = [m for m in msgs.get("value", [])
               if lo <= (m.get("createdDateTime") or "") < hi
               and clean((m.get("body") or {}).get("content"))]
        if not rel:
            continue
        print(f"### {ch.get('topic') or ch.get('chatType')}")
        for m in reversed(rel):
            f = m.get("from") or {}
            name = next((v.get("displayName") for k in ("user", "application", "device")
                         for v in [f.get(k) or {}] if v.get("displayName")), "systeem")
            print(f"- {loc(m['createdDateTime'])} **{name}**: "
                  f"{clean((m.get('body') or {}).get('content'), 400)}")
        print()
    warn("Teams-kanaalberichten ontbreken: het Graph Explorer-token heeft geen ChannelMessage.Read.All.")


def src_atlassian(start, end):
    jt = keychain(service="jira-personal-token", account=os.environ.get("USER"))
    ct = keychain(service="confluence-personal-token", account=os.environ.get("USER"))
    lo_date = start.strftime("%Y-%m-%d %H:%M")
    hi_date = end.strftime("%Y-%m-%d %H:%M")

    if jt:
        hdr = {"Authorization": "Bearer " + jt}
        section("Jira")
        # 1. Activity stream = precies de eigen acties (goedkoper dan changelogs per issue)
        try:
            me = get_json(f"{JIRA}/rest/api/2/myself", hdr)
            # De stream wil de username ('name'), niet de user key — met de key krijg
            # je een feed die er plausibel uitziet maar de recentste acties mist.
            feed = get_text(
                f"{JIRA}/activity?maxResults=100&streams="
                f"{urllib.parse.quote('user IS ' + me.get('name', ''))}", hdr)
            ns = {"a": "http://www.w3.org/2005/Atom"}
            print("### Eigen acties")
            for e in ET.fromstring(feed).findall("a:entry", ns):
                raw = e.findtext("a:updated", "", ns) or ""
                try:  # de feed geeft UTC; het venster is lokale tijd
                    when = dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone()
                except ValueError:
                    continue
                w = when.replace(tzinfo=None)
                if w < start or w >= end:
                    continue
                print(f"- {when:%Y-%m-%d %H:%M} {clean(e.findtext('a:title', '', ns), 220)}")
            print()
        except Exception as e:
            warn(f"Jira activity stream faalde: {e}")
        # 2. Issues die bewogen (ook door anderen) waar jij bij betrokken bent
        try:
            jql = (f'updated >= "{lo_date}" AND updated < "{hi_date}" AND (assignee = currentUser() '
                   f'OR reporter = currentUser() OR creator = currentUser()) ORDER BY updated DESC')
            d = get_json(f"{JIRA}/rest/api/2/search?"
                         + urllib.parse.urlencode({"jql": jql, "maxResults": 50,
                                                   "fields": "summary,status,updated,assignee"}), hdr)
            print("### Bewogen issues (jij als reporter/assignee/creator)")
            for i in d.get("issues", []):
                f = i["fields"]
                a = (f.get("assignee") or {}).get("displayName", "niemand")
                print(f"- **{i['key']}** {f['summary']} — {f['status']['name']} | {a} | "
                      f"{f['updated'][:16].replace('T', ' ')}")
            print()
        except Exception as e:
            warn(f"Jira JQL faalde: {e}")
    else:
        warn("Jira overgeslagen: keychain-item 'jira-personal-token' niet gevonden.")

    if ct:
        hdr = {"Authorization": "Bearer " + ct}
        section("Confluence")
        try:
            cql = (f'contributor = currentUser() AND lastModified >= "{lo_date}" '
                   f'AND lastModified < "{hi_date}"')
            d = get_json(f"{CONFLUENCE}/rest/api/content/search?"
                         + urllib.parse.urlencode({"cql": cql, "limit": 25,
                                                   "expand": "version,space"}), hdr)
            for r in d.get("results", []):
                v = r.get("version", {})
                print(f"- **{r.get('title')}** ({r.get('space', {}).get('key')}) — v{v.get('number')} "
                      f"op {(v.get('when') or '')[:16].replace('T', ' ')}")
            print()
        except Exception as e:
            warn(f"Confluence-zoekopdracht faalde: {e}")
    else:
        warn("Confluence overgeslagen: keychain-item 'confluence-personal-token' niet gevonden.")


def src_chrome(start, end):
    src = f"{HOME}/Library/Application Support/Google/Chrome/Default/History"
    if not os.path.exists(src):
        warn("Chrome-history niet gevonden.")
        return
    tmp = os.path.join(tempfile.mkdtemp(), "History")
    shutil.copy2(src, tmp)  # kopie: Chrome houdt het origineel gelockt
    epoch = dt.datetime(1601, 1, 1)
    lo = int((start - epoch).total_seconds() * 1e6)
    hi = int((end - epoch).total_seconds() * 1e6)
    try:
        rows = sqlite3.connect(tmp).execute(
            "select v.visit_time, u.url, u.title from visits v join urls u on u.id = v.url "
            "where v.visit_time between ? and ? order by v.visit_time", (lo, hi)).fetchall()
    except Exception as e:
        warn(f"Chrome-history lezen faalde: {e}")
        return
    finally:
        shutil.rmtree(os.path.dirname(tmp), ignore_errors=True)
    section("Chrome")
    excl = []
    if os.path.exists(EXCLUDE_FILE):
        excl = [l.strip() for l in open(EXCLUDE_FILE, encoding="utf-8")
                if l.strip() and not l.startswith("#")]
        print(f"*{len(excl)} domeinpatronen uitgesloten via `{EXCLUDE_FILE}`.*\n")
    seen, weg = set(), 0
    for vt, url, title in rows:
        if not title or CHROME_SKIP.search(url):
            continue
        if any(e in url for e in excl):
            weg += 1
            continue
        key = title[:80]
        if key in seen:
            continue
        seen.add(key)
        when = (epoch + dt.timedelta(microseconds=vt)).strftime("%m-%d %H:%M")
        print(f"- {when} `{urllib.parse.urlparse(url).netloc}` {title[:110]}")
    if weg:
        print(f"\n*{weg} bezoeken weggelaten door de exclude-lijst.*")
    print()


def src_git(start, end):
    """Alleen git-repo's. Losse bestanden elders in de Dropbox-boom zeggen niets:
    Dropbox raakt zelf bestanden aan, en 'mtime veranderd' is geen werk."""
    section("Code")
    since = start.strftime("%Y-%m-%d %H:%M")
    until = end.strftime("%Y-%m-%d %H:%M")
    repos = sorted({os.path.dirname(d) for d in sh(
        ["find", "-L", CODE_ROOT, "-maxdepth", "6", "-name", ".git",
         "-not", "-path", "*/node_modules/*"], timeout=180).splitlines() if d})
    print(f"*{len(repos)} repo's onder `{CODE_ROOT}` bekeken.*\n")
    stil = []
    for r in repos:
        if os.path.realpath(r) == os.path.realpath(VAULT):
            continue  # de vault heeft een eigen, rijkere sectie
        rel = os.path.relpath(r, CODE_ROOT)
        commits = sh(["git", "-C", r, "log", "--all", f"--since={since}", f"--until={until}",
                      "--pretty=  - %h %ad %an | %s", "--date=format:%m-%d %H:%M"], timeout=30).strip()
        # Niet-gecommit werk is vaak juist het lopende werk. Wel op mtime filteren:
        # een repo kan al maanden een vuile working tree hebben, en dat is geen nieuws.
        dirty = []
        for l in sh(["git", "-C", r, "status", "--porcelain", "-uall"], timeout=30).splitlines():
            if not l.strip():
                continue
            path = l[3:].strip().strip('"').split(" -> ")[-1]
            full = os.path.join(r, path)
            try:
                m = dt.datetime.fromtimestamp(os.path.getmtime(full))
            except OSError:
                continue  # verwijderd bestand: geen mtime, en de commit-lijst dekt dat al
            if start <= m <= end:
                dirty.append(f"{l.strip()}  ({m:%m-%d %H:%M})")
        if not commits and not dirty:
            stil.append(rel)
            continue
        print(f"### {rel}")
        if commits:
            print("Commits:")
            print(commits)
        if dirty:
            print(f"Niet-gecommit ({len(dirty)} bestanden):")
            for l in dirty[:25]:
                print(f"  - {l.strip()}")
            if len(dirty) > 25:
                print(f"  - … en {len(dirty) - 25} andere")
        print()
    if stil:
        print(f"*{len(stil)} repo's zonder activiteit in dit venster (niet opgesomd).*\n")


def src_vault(start, end):
    section("Vault")
    if not os.path.isdir(os.path.join(VAULT, ".git")):
        warn("Vault is geen git-repo; vault-diff overgeslagen.")
        return
    # Commits in het venster + de vuile working tree: samen is dat wat er in de vault
    # gebeurde. Het venster op commits filtert; de working tree is per definitie 'nu'.
    since = start.strftime("%Y-%m-%d %H:%M")
    until = end.strftime("%Y-%m-%d %H:%M")
    print("### Commits in dit venster")
    log = sh(["git", "-C", VAULT, "log", f"--since={since}", f"--until={until}",
              "--pretty=- %h %ad | %s", "--date=format:%m-%d %H:%M"], timeout=60).strip()
    print(log or "- (geen)")
    print("\n### Diff sinds laatste commit")
    stat = sh(["git", "-C", VAULT, "diff", "--stat"], timeout=60).strip()
    print(stat or "- (geen wijzigingen)")
    print("\n### Toegevoegde regels (proza)")
    # .obsidian = UI-state (open tabs, graph-posities): verandert constant, zegt niets
    diff = sh(["git", "-C", VAULT, "diff", "-U0", "--", ".", ":(exclude).obsidian",
               ":(exclude)*.json", ":(exclude).idea"], timeout=60)
    cur = None
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            cur = line[6:]
        elif line.startswith("+") and not line.startswith("+++"):
            t = line[1:].strip()
            # frontmatter-achtige regels en kale scaffolding dragen geen kennis
            if len(t.split()) < 4 or t.startswith(("---", "#", "|", "kanban_plugin")):
                continue
            # afgevinkte/gearchiveerde taken zijn boekhouding, geen nieuwe kennis
            if re.match(r"^- \[[xX-]\]", t) and "#archived" in t:
                continue
            print(f"- `{cur}` {t[:220]}")
    print("\n### Nieuwe, nog niet-getrackte bestanden")
    for line in sh(["git", "-C", VAULT, "status", "--porcelain"], timeout=60).splitlines():
        if line.startswith("??"):
            print(f"- {line[3:].strip()}")
    print()


def src_claude(start, end):
    section("Claude Code-sessies")
    root = f"{HOME}/.claude/projects"
    if not os.path.isdir(root):
        warn("Geen ~/.claude/projects gevonden.")
        return
    files = sh(["find", root, "-name", "*.jsonl",
                "-newermt", start.strftime("%Y-%m-%d %H:%M"),
                "!", "-newermt", end.strftime("%Y-%m-%d %H:%M")], timeout=60).splitlines()
    if not files:
        print("- (geen sessies in dit venster)")
        return
    for f in files:
        prompts = []
        try:
            for line in open(f, encoding="utf-8", errors="replace"):
                r = json.loads(line)
                if r.get("type") != "user":
                    continue
                c = r.get("message", {}).get("content")
                if isinstance(c, list):
                    c = " ".join(x.get("text", "") for x in c if isinstance(x, dict))
                if not isinstance(c, str) or not c.strip():
                    continue
                # slash-commands, hook-output en systeemruis zijn geen intentie van de gebruiker
                if any(t in c for t in ("<system-reminder>", "<command-name>", "<local-command",
                                        "Caveat: The messages below")):
                    continue
                prompts.append(clean(c, 200))
        except Exception as e:
            warn(f"Sessie {os.path.basename(f)} onleesbaar: {e}")
            continue
        if not prompts:
            continue
        print(f"### {os.path.basename(os.path.dirname(f))} / {os.path.basename(f)[:8]}")
        for p in prompts[:25]:
            print(f"- {p}")
        print()


def src_notes(start, end):
    """Bestaande daily notes in het venster: input voor overlap-detectie."""
    section("AL VASTGELEGD — daily notes in dit venster")
    print("*Alles hieronder staat al in de vault. Niet opnieuw voorstellen; enkel echt nieuwe "
          "informatie of een wezenlijke voortzetting van een van deze punten is nog interessant.*\n")
    d = start.date()
    leeg = True
    while d <= end.date():
        p = os.path.join(VAULT, "04 - Journal", f"{d:%Y}", f"{d:%m}", f"{d:%d}", f"{d:%Y-%m-%d}.md")
        if os.path.exists(p):
            leeg = False
            body = open(p, encoding="utf-8", errors="replace").read()
            body = body.split("## 📋 Logs")[0]  # dataview-blokken dragen geen inhoud
            print(f"### {d:%Y-%m-%d}\n```markdown\n{body.strip()}\n```\n")
        d += dt.timedelta(days=1)
    if leeg:
        print("- (geen bestaande daily notes in dit venster)")
    print()


SOURCES = {
    "notes": src_notes,
    "rocketchat": src_rocketchat,
    "graph": src_graph,
    "atlassian": src_atlassian,
    "chrome": src_chrome,
    "git": src_git,
    "vault": src_vault,
    "claude": src_claude,
}


def mail_body(msg_id):
    """Volledige tekst van één mail. De bundel geeft previews (300 tekens); precies
    de beslissende mail staat daar vaak voorbij. Welke mail dat is, is oordeel — dus
    haalt de LLM ze gericht op in plaats van dat het script alles meesleept."""
    token = graph_token()
    if not token:
        print("Geen geldig Graph-token (GRAPH_TOKEN_FILE, GRAPH_TOKEN of klembord).", file=sys.stderr)
        return 1
    try:
        m = get_json(
            f"https://graph.microsoft.com/v1.0/me/messages/{urllib.parse.quote(msg_id)}"
            "?$select=subject,from,toRecipients,receivedDateTime,body",
            {"Authorization": "Bearer " + token})
    except urllib.error.HTTPError as e:
        print(f"Graph gaf {e.code} voor bericht {msg_id}.", file=sys.stderr)
        return 1
    print(f"# {m.get('subject')}")
    print(f"{loc(m['receivedDateTime'])} | van {(m.get('from', {}).get('emailAddress', {}) or {}).get('name')} "
          f"| aan {', '.join(t['emailAddress'].get('name', '') for t in m.get('toRecipients', []))}\n")
    print(clean(m["body"]["content"]))
    return 0


def check_graph():
    """Is er een bruikbaar Graph-token? Exit 0 = bruikbaar, 1 = ontbreekt of verlopen."""
    token = graph_token()
    if not token:
        print("GEEN TOKEN — vraag een vers token uit Graph Explorer (tab 'Access token').")
        return 1
    try:
        get_json("https://graph.microsoft.com/v1.0/me?$select=id",
                 {"Authorization": "Bearer " + token})
    except urllib.error.HTTPError as e:
        print(f"TOKEN ONGELDIG ({e.code}) — vraag een vers token uit Graph Explorer.")
        return 1
    print("Graph-token OK.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Verzamel activiteit voor de routine.")
    ap.add_argument("--since", help="starttijd, ISO (default: gisteren 00:00)")
    ap.add_argument("--until", help="eindtijd, ISO (default: nu)")
    ap.add_argument("--out", metavar="DIR", help="schrijf bundle.md + <bron>.md in DIR i.p.v. stdout")
    ap.add_argument("--only", help="komma-gescheiden bronnen: " + ",".join(SOURCES))
    ap.add_argument("--skip", help="komma-gescheiden bronnen om over te slaan")
    ap.add_argument("--mail-body", metavar="ID",
                    help="print de volledige tekst van één mail (id staat in de bundel)")
    ap.add_argument("--check-graph", action="store_true",
                    help="controleer enkel of er een geldig Graph-token is (exit 1 als niet)")
    args = ap.parse_args()

    if args.check_graph:
        sys.exit(check_graph())
    if args.mail_body:
        sys.exit(mail_body(args.mail_body))

    start, end = window(args)
    want = list(SOURCES)
    if args.only:
        want = [s.strip() for s in args.only.split(",") if s.strip() in SOURCES]
    if args.skip:
        skip = {s.strip() for s in args.skip.split(",")}
        want = [s for s in want if s not in skip]

    head = f"# Bundel {start:%Y-%m-%d %H:%M} → {end:%Y-%m-%d %H:%M}\n\nBronnen: {', '.join(want)}\n"
    parts = {}
    for name in want:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            try:
                SOURCES[name](start, end)
            except Exception as e:
                warn(f"Bron '{name}' faalde: {type(e).__name__}: {e}")
        parts[name] = buf.getvalue()
    tail = "\n## Bronnen die ontbraken of faalden\n\n" + ("\n".join(f"- {w}" for w in WARN) or "- (geen)") + "\n"

    if not args.out:
        print(head + "".join(parts.values()) + tail)
        return
    os.makedirs(args.out, exist_ok=True)
    for name, txt in parts.items():
        with open(os.path.join(args.out, f"{name}.md"), "w", encoding="utf-8") as f:
            f.write(f"# {name} {start:%Y-%m-%d %H:%M} → {end:%Y-%m-%d %H:%M}\n" + txt)
    with open(os.path.join(args.out, "bundle.md"), "w", encoding="utf-8") as f:
        f.write(head + "".join(parts.values()) + tail)
    with open(os.path.join(args.out, "meta.json"), "w", encoding="utf-8") as f:
        json.dump({"since": start.isoformat(timespec="minutes"), "until": end.isoformat(timespec="minutes"),
                   "sources": want, "warnings": WARN}, f, ensure_ascii=False, indent=1)
    print(f"{args.out}: {', '.join(f'{k}={len(v)}' for k, v in parts.items())}; "
          f"{len(WARN)} waarschuwing(en)")


if __name__ == "__main__":
    main()
