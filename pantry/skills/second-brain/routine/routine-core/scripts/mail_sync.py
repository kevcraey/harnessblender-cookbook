#!/usr/bin/env python3
"""mail_sync.py — zet de categorie `synced` op verwerkte mail. Enige Graph-mutatie
in de hele routine: nooit verwijderen, verplaatsen of beantwoorden.

  mail_sync.py <ids.txt>     één Graph message-id per regel (uit mail.md: `id: ...`)
  mail_sync.py --from-md <mail.md>   alle ids uit een mail.md die nog niet [synced] zijn

Token via GRAPH_TOKEN_FILE (voorkeur), GRAPH_TOKEN of klembord. Bestaande
categorieën blijven staan; een mail die al `synced` draagt wordt overgeslagen.
"""

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

GRAPH = "https://graph.microsoft.com/v1.0"


def token():
    f = os.environ.get("GRAPH_TOKEN_FILE")
    if f and os.path.exists(f):
        t = open(f, encoding="utf-8").read().strip()
    else:
        t = os.environ.get("GRAPH_TOKEN") or subprocess.run(
            ["pbpaste"], capture_output=True, text=True).stdout.strip()
    if not t or len(t) < 500 or t.count(".") != 2:
        sys.exit("geen geldig Graph-token")
    return t


def ids_from_md(path):
    """Ids van mails zonder [synced]-vlag. De vlag staat op de regel vóór de id-regel,
    dus lees per mailblok: kopregel -> onderwerp -> id."""
    out, flagged = [], False
    for line in open(path, encoding="utf-8"):
        s = line.strip()
        if s.startswith("- ") and not s.startswith("- id:") and not s.startswith("- *"):
            flagged = any("synced" in f for f in re.findall(r"\[([^\]]+)\]", s))
        m = re.match(r"-\s*id:\s*`([^`]+)`", s)
        if m and not flagged:
            out.append(m.group(1))
    return out


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "--from-md":
        ids = ids_from_md(argv[1])
    else:
        ids = [l.strip() for l in open(argv[0], encoding="utf-8") if l.strip() and not l.startswith("#")]
    if not ids:
        print("niets te markeren")
        return 0
    hdr = {"Authorization": "Bearer " + token(), "Content-Type": "application/json"}
    ok = skip = fail = 0
    for mid in ids:
        url = f"{GRAPH}/me/messages/{urllib.parse.quote(mid)}"
        try:
            with urllib.request.urlopen(urllib.request.Request(url + "?$select=categories", headers=hdr)) as r:
                cats = json.load(r).get("categories") or []
            if "synced" in cats:
                skip += 1
                continue
            body = json.dumps({"categories": cats + ["synced"]}).encode()
            with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=hdr, method="PATCH")) as r:
                r.read()
            ok += 1
        except urllib.error.HTTPError as e:
            fail += 1
            print(f"FAIL {mid[:24]}…: {e.code}", file=sys.stderr)
            if e.code == 401:
                print("token verlopen — stop", file=sys.stderr)
                break
    print(f"synced gezet: {ok}, al gemarkeerd: {skip}, mislukt: {fail}")
    return 1 if fail else 0


if __name__ == "__main__":
    import urllib.parse
    sys.exit(main(sys.argv[1:]))
