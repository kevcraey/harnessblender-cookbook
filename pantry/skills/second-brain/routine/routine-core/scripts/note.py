#!/usr/bin/env python3
"""note.py — daily note vinden of aanmaken volgens het vault-template. Geen oordeel.

  note.py path <YYYY-MM-DD>      pad van de daily note (bestaat niet noodzakelijk)
  note.py ensure <YYYY-MM-DD>    maak de note aan vanuit het template als ze ontbreekt; print pad
  note.py body <YYYY-MM-DD>      inhoud boven `## 📋 Logs` (leeg als de note ontbreekt)

Template = tag, lege regel, H1, blockquote, dan de Logs-blokken. Inhoud komt altijd
tussen de blockquote en `## 📋 Logs`.
"""

import datetime as dt
import os
import sys

VAULT = os.environ.get("VAULT", os.path.expanduser("~/Library/CloudStorage/Dropbox/1-Kenzo/1-Second-Brain"))
LOGS = "## 📋 Logs"

TEMPLATE = """#daily [[{ym}]]

# 📥 Daily Note
> When in doubt, just throw it here. Use timestamps! If you add a task here, it's due (due::today)


## 📋 Logs
### Notes created today
```dataviewjs
const query = `
List
FROM ""
WHERE file.cday = date(substring("${{dv.current().file.name}}",0,10))
SORT file.ctime asc
`;
dv.span('```dataview' + query + '```');
```
### Notes last touched today
```dataviewjs
const query = `
List
FROM ""
WHERE file.mday = date(substring("${{dv.current().file.name}}",0,10))
SORT file.mtime asc
`;
dv.span('```dataview' + query + '```');
```
### Tasks completed today
```dataviewjs
var date = dv.current().file.name.split('-')

var year = date[0]
var month = date[1]
var day = date[2]

var formattedDate = year+"-"+month+"-"+day

if (year != "template"){{
\tconst query = `
TASK
WHERE completion = date(${{formattedDate}})
SORT file.ctime asc
`;
\tdv.span('```dataview' + query + '```');
}}
```
"""


def path(d):
    return os.path.join(VAULT, "04 - Journal", f"{d:%Y}", f"{d:%m}", f"{d:%d}", f"{d:%Y-%m-%d}.md")


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    cmd, d = argv[0], dt.date.fromisoformat(argv[1])
    p = path(d)
    if cmd == "path":
        print(p)
    elif cmd == "ensure":
        if not os.path.exists(p):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(TEMPLATE.format(ym=f"{d:%Y-%m}"))
        print(p)
    elif cmd == "body":
        if os.path.exists(p):
            print(open(p, encoding="utf-8").read().split(LOGS)[0].rstrip())
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
