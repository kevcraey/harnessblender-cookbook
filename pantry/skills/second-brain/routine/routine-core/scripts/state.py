#!/usr/bin/env python3
"""state.py — waar staat de routine? Eén JSON-bestand, geen oordeel.

  state.py show                       hele state
  state.py get <key>                  één waarde (leeg als onbekend)
  state.py set <key> <value>          waarde zetten
  state.py days [--today]             dagen die nog een digest nodig hebben, één per regel
  state.py run-dir <ochtend|avond>    pad van de run-map van vandaag (maakt hem aan)
  state.py sweep [--keep-days N]      oude run-mappen opruimen (default 30 dagen)

Sleutels:
  digest_done_through   laatste dag (YYYY-MM-DD) waarvan de daily note volledig is
  last_ochtend / last_avond   ISO-tijdstip van de laatste geslaagde run

`days` geeft de dagen van (digest_done_through + 1) tot en met gisteren; met
--today ook vandaag. Cap op 14 dagen: daarboven print het script een waarschuwing
op stderr en enkel de 14 recentste — ouder inhalen vraagt een expliciete --since
aan de digest, dat is een bewuste keuze en geen stilzwijgende sprong.
"""

import datetime as dt
import json
import os
import shutil
import sys

ROOT = os.path.expanduser(os.environ.get("ROUTINE_HOME", "~/.config/routine"))
STATE = os.path.join(ROOT, "state.json")
RUNS = os.path.join(ROOT, "runs")
CAP = 14


def load():
    if not os.path.exists(STATE):
        return {}
    with open(STATE, encoding="utf-8") as f:
        return json.load(f)


def save(s):
    os.makedirs(ROOT, exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=1, ensure_ascii=False)
    os.replace(tmp, STATE)


def days(include_today):
    s = load()
    today = dt.date.today()
    done = s.get("digest_done_through")
    if done:
        start = dt.date.fromisoformat(done) + dt.timedelta(days=1)
    else:
        start = today - dt.timedelta(days=2)  # bootstrap: twee dagen terug, zoals de oude digest
    end = today if include_today else today - dt.timedelta(days=1)
    out = []
    d = start
    while d <= end:
        out.append(d)
        d += dt.timedelta(days=1)
    if len(out) > CAP:
        print(f"[waarschuwing] {len(out)} dagen open sinds {start}; enkel de {CAP} recentste. "
              f"Ouder inhalen: digest met expliciete --since.", file=sys.stderr)
        out = out[-CAP:]
    return out


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "show":
        print(json.dumps(load(), indent=1, ensure_ascii=False))
    elif cmd == "get":
        print(load().get(rest[0], "") if rest else "")
    elif cmd == "set":
        s = load()
        s[rest[0]] = rest[1]
        save(s)
    elif cmd == "days":
        for d in days("--today" in rest):
            print(d.isoformat())
    elif cmd == "run-dir":
        kind = rest[0] if rest else "run"
        p = os.path.join(RUNS, f"{dt.date.today():%Y-%m-%d}-{kind}")
        os.makedirs(os.path.join(p, "days"), exist_ok=True)
        print(p)
    elif cmd == "sweep":
        keep = 30
        if "--keep-days" in rest:
            keep = int(rest[rest.index("--keep-days") + 1])
        cutoff = dt.date.today() - dt.timedelta(days=keep)
        n = 0
        if os.path.isdir(RUNS):
            for name in os.listdir(RUNS):
                try:
                    d = dt.date.fromisoformat(name[:10])
                except ValueError:
                    continue
                if d < cutoff:
                    shutil.rmtree(os.path.join(RUNS, name), ignore_errors=True)
                    n += 1
        print(f"{n} run-map(pen) ouder dan {keep} dagen verwijderd")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
