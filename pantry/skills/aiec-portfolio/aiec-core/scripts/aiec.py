#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml"]
# ///
"""aiec.py — deterministische kern van de AIEC-portfolio-plugin. Beslist niets; leest Confluence
en Jira, rendert storage-XML uit schema.yaml, valideert, en schrijft enkel met --apply én een
toelatende write-mode (config.toml › writes.mode). Contract: ../../DESIGN.md §6.

Exitcodes: 0 ok · 1 fout · 2 gebruiksfout · 3 write geweigerd door guard · 4 validatiefout.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from aiec_lib import config, http, schema as sch
from aiec_lib import confluence as conf_mod
from aiec_lib import jira as jira_mod
from aiec_lib import proposal as prop_mod
from aiec_lib import report as report_mod
from aiec_lib import rules as rules_mod


class UsageError(Exception):
    pass


# --- output -----------------------------------------------------------------------------------

def emit(args, data, markdown=None, default_name=None):
    """--out: naar bestand (json, of md als de naam op .md eindigt / --out een map is: beide);
    --json: json op stdout; anders markdown (of json als er geen markdown-renderer is)."""
    md = markdown(data) if markdown else None
    if args.out:
        out = Path(args.out).expanduser()
        if out.is_dir() or (default_name and not out.suffix):
            out.mkdir(parents=True, exist_ok=True)
            base = default_name or "output"
            (out / f"{base}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))
            if md:
                (out / f"{base}.md").write_text(md)
            print(f"geschreven: {out / (base + '.json')}" + (f" en {base}.md" if md else ""))
        elif out.suffix == ".md" and md:
            out.write_text(md)
            print(f"geschreven: {out}")
        else:
            out.write_text(json.dumps(data, indent=1, ensure_ascii=False) if not isinstance(data, str) else data)
            print(f"geschreven: {out}")
        return
    if args.json or md is None:
        print(json.dumps(data, indent=1, ensure_ascii=False) if not isinstance(data, str) else data)
    else:
        print(md)


def load_values(spec: str) -> dict:
    """--values: pad naar json-bestand of inline json."""
    s = spec.strip()
    if s.startswith("{"):
        return json.loads(s)
    return json.loads(Path(s).expanduser().read_text())


def load_json(path: str | None):
    return json.loads(Path(path).expanduser().read_text()) if path else None


def parse_date(s: str | None) -> dt.date | None:
    return dt.date.fromisoformat(s) if s else None


# --- commando's -------------------------------------------------------------------------------

def cmd_schema(args, cfg, schema):
    if args.action == "check":
        problems = sch.check(schema)
        for p in problems:
            print(f"- {p}")
        print("schema ok" if not problems else f"{len(problems)} probleem/problemen")
        return 4 if problems else 0
    emit(args, {k: v for k, v in schema.items() if not k.startswith("_")}, lambda _: sch.to_markdown(schema))
    return 0


def cmd_config(args, cfg, schema):
    if args.action == "init":
        print(f"config: {config.init(args.config)}")
    elif args.action == "mode":
        print(config.mode(cfg))
    else:
        emit(args, cfg, lambda c: "```toml\n" + Path(c["_path"]).read_text() + "```\n" if Path(c["_path"]).exists()
             else f"geen configbestand ({c['_path']}); defaults gelden, mode {config.mode(c)}\n")
    return 0


def cmd_state(args, cfg, schema):
    if args.action == "get":
        v = config.state_get(args.key) if args.key else config.state_load()
        print(json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v)
    elif args.action == "set":
        if not args.key or args.value is None:
            raise UsageError("state set <key> <value>")
        config.state_set(args.key, args.value)
        print(f"{args.key} = {args.value}")
    elif args.action == "run-dir":
        if not args.key:
            raise UsageError("state run-dir <skill>")
        print(config.run_dir(args.key))
    return 0


def cmd_jira(args, cfg, schema):
    client = http.jira(cfg)
    a = args.action
    if a == "list":
        data = jira_mod.list_initiatives(cfg, client, schema, include_closed=args.all)
        emit(args, data, jira_mod.list_markdown, "initiatives")
    elif a == "get":
        emit(args, jira_mod.get_initiative(cfg, client, schema, args.key))
    elif a == "search":
        if not args.key:
            raise UsageError('jira search "<jql>"')
        emit(args, jira_mod.search(cfg, client, args.key, limit=args.limit))
    elif a == "hours":
        sel = args.keys or [k for k in (args.key, args.other) if k] or None   # --keys of positioneel
        data = jira_mod.hours(cfg, client, schema, keys=sel,
                              since=parse_date(args.since), until=parse_date(args.until))
        emit(args, data, jira_mod.hours_markdown, "hours")
    elif a == "changes":
        if not args.since:
            raise UsageError("jira changes --since YYYY-MM-DD")
        data = jira_mod.changes(cfg, client, schema, since=parse_date(args.since), until=parse_date(args.until))
        emit(args, data, jira_mod.changes_markdown, "changes")
    elif a == "create":
        if not args.title:
            raise UsageError("jira create --title T --description D")
        emit(args, jira_mod.create_initiative(cfg, client, schema, args.title, args.description or "",
                                              eag=args.eag, verantwoordelijke=args.verantwoordelijke,
                                              trekker=args.trekker, apply=args.apply))
    elif a == "link":
        if not (args.key and args.other):
            raise UsageError("jira link <AI-key> <EAG-key>")
        emit(args, jira_mod.link(cfg, client, args.key, args.other, apply=args.apply))
    elif a == "transition":
        if not (args.key and args.to):
            raise UsageError("jira transition <AI-key> --to <naam>")
        emit(args, jira_mod.transition(cfg, client, schema, args.key, args.to, resolution=args.resolution,
                                       apply=args.apply))
    return 0


def cmd_conf(args, cfg, schema):
    a = args.action
    if a in ("render", "render-template", "render-overview"):
        # offline: geen client nodig
        if a == "render":
            values, problems = sch.normalize_values(schema, load_values(args.values))
            if problems:
                print("\n".join(f"- {p}" for p in problems), file=sys.stderr)
                return 4
            xml = conf_mod.render_page(schema, values, samenvatting=args.samenvatting or "", cfg=cfg) if args.page \
                else conf_mod.render_details(schema, values)
        elif a == "render-template":
            xml = conf_mod.render_template(schema)
        else:
            xml = conf_mod.render_overview(schema, cfg)
        emit(args, xml)
        return 0
    client = http.confluence(cfg)
    if a == "pages":
        emit(args, conf_mod.list_pages(cfg, client, schema, discover=args.discover), conf_mod.pages_markdown, "register")
    elif a == "get":
        emit(args, conf_mod.get_page(cfg, client, schema, args.ident))
    elif a == "search":
        emit(args, conf_mod.search(cfg, client, args.cql, limit=args.limit))
    elif a == "upsert-details":
        values, problems = sch.normalize_values(schema, load_values(args.values))
        if problems:
            print("\n".join(f"- {p}" for p in problems), file=sys.stderr)
            return 4
        emit(args, conf_mod.upsert_details(cfg, client, schema, args.page, values, apply=args.apply),
             conf_mod.change_markdown)
    elif a == "create-initiative":
        values, problems = sch.normalize_values(schema, load_values(args.values))
        if problems:
            print("\n".join(f"- {p}" for p in problems), file=sys.stderr)
            return 4
        if not args.title:
            raise UsageError("conf create-initiative --values <json> --title <titel>")
        emit(args, conf_mod.create_initiative(cfg, client, schema, values, args.title, parent_id=args.parent,
                                              samenvatting=args.samenvatting or "", apply=args.apply),
             conf_mod.change_markdown)
    elif a == "create-child":
        if not (args.parent and args.title):
            raise UsageError("conf create-child --parent <id> --title <titel> [--label L] [--from-title T]")
        emit(args, conf_mod.create_child(cfg, client, schema, args.parent, args.title, labels=args.label or [],
                                         body_from_title=args.from_title, apply=args.apply), conf_mod.change_markdown)
    elif a == "publish-template":
        emit(args, conf_mod.publish_template(cfg, client, schema, apply=args.apply), conf_mod.change_markdown)
    elif a == "publish-overview":
        emit(args, conf_mod.publish_overview(cfg, client, schema, apply=args.apply), conf_mod.change_markdown)
    elif a == "set-labels":
        if not (args.page and args.labels):
            raise UsageError("conf set-labels <page-id> <label>...")
        emit(args, conf_mod.set_labels(cfg, client, args.page, args.labels, apply=args.apply), conf_mod.change_markdown)
    return 0


def cmd_validate(args, cfg, schema):
    register = load_json(args.register) or conf_mod.list_pages(cfg, http.confluence(cfg), schema, discover=args.discover)
    initiatives = load_json(args.jira) or jira_mod.list_initiatives(cfg, http.jira(cfg), schema, include_closed=True)
    hours = load_json(args.hours)
    violations = rules_mod.validate(schema, cfg, register, initiatives, hours=hours)
    emit(args, violations, rules_mod.to_markdown, "violations")
    return 0


def cmd_report(args, cfg, schema):
    if args.action != "data":
        raise UsageError("report data --since YYYY-MM-DD [--until YYYY-MM-DD]")
    if not args.since:
        raise UsageError("report data --since YYYY-MM-DD")
    since, until = parse_date(args.since), parse_date(args.until) or dt.date.today()
    cc, jc = http.confluence(cfg), http.jira(cfg)
    register = conf_mod.list_pages(cfg, cc, schema)
    initiatives = jira_mod.list_initiatives(cfg, jc, schema, include_closed=True)
    hours = jira_mod.hours(cfg, jc, schema, since=since, until=until)
    changes = jira_mod.changes(cfg, jc, schema, since=since, until=until)
    violations = rules_mod.validate(schema, cfg, register, initiatives, hours=hours)
    data = report_mod.build(schema, cfg, register, initiatives, hours, changes, violations, since, until)
    emit(args, data, report_mod.to_markdown, "data")
    return 0


def cmd_apply(args, cfg, schema):
    text = Path(args.proposal).expanduser().read_text()
    proposal = prop_mod.parse(text)
    result = prop_mod.apply(cfg, schema, proposal, apply=args.apply,
                            clients=lambda: (http.confluence(cfg), http.jira(cfg)))
    emit(args, result, prop_mod.result_markdown)
    return 0


# --- argparse ---------------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="aiec.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config", help="pad naar config.toml (default ~/.config/aiec/config.toml)")
    p.add_argument("--schema", help="pad naar schema.yaml (default: naast aiec-core/SKILL.md)")
    p.add_argument("--json", action="store_true", help="machine-output (json) op stdout")
    p.add_argument("--out", help="bestand of map om naar te schrijven")
    # dezelfde vlaggen mogen ook ná het subcommando staan; zonder waarde laten ze het globale default staan
    common = argparse.ArgumentParser(add_help=False)
    for flag, kw in (("--config", {}), ("--schema", {}), ("--json", {"action": "store_true"}), ("--out", {})):
        common.add_argument(flag, default=argparse.SUPPRESS, **kw)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("schema", parents=[common], help="model tonen; 'check' = consistentie")
    s.add_argument("action", nargs="?", choices=["show", "check"], default="show")

    c = sub.add_parser("config", parents=[common], help="init | show | mode")
    c.add_argument("action", choices=["init", "show", "mode"])

    st = sub.add_parser("state", parents=[common], help="get [key] | set <key> <value> | run-dir <skill>")
    st.add_argument("action", choices=["get", "set", "run-dir"])
    st.add_argument("key", nargs="?")
    st.add_argument("value", nargs="?")

    j = sub.add_parser("jira", parents=[common], help="list | get | search | hours | changes | create | link | transition")
    j.add_argument("action", choices=["list", "get", "search", "hours", "changes", "create", "link", "transition"])
    j.add_argument("key", nargs="?", help="AI-key (get, link, transition); jql (search)")
    j.add_argument("--limit", type=int, default=50, help="search: max resultaten")
    j.add_argument("other", nargs="?", help="EAG-key (link)")
    j.add_argument("--all", action="store_true", help="list: ook Afgesloten")
    j.add_argument("--keys", nargs="*", help="hours: beperk tot deze initiatieven")
    j.add_argument("--since"), j.add_argument("--until")
    j.add_argument("--title"), j.add_argument("--description"), j.add_argument("--eag")
    j.add_argument("--verantwoordelijke"), j.add_argument("--trekker")
    j.add_argument("--to", help="transition: nette statusnaam"), j.add_argument("--resolution")
    j.add_argument("--apply", action="store_true")

    cf = sub.add_parser("conf", parents=[common], help="pages | get | search | render | render-template | render-overview | "
                                     "upsert-details | create-initiative | create-child | publish-template | publish-overview | set-labels")
    cf.add_argument("action", choices=["pages", "get", "search", "render", "render-template", "render-overview",
                                       "upsert-details", "create-initiative", "create-child", "publish-template",
                                       "publish-overview", "set-labels"])
    cf.add_argument("ident", nargs="?", help="get: page-id of AI-key; search: cql")
    cf.add_argument("labels", nargs="*", help="set-labels: labels")
    cf.add_argument("--cql"), cf.add_argument("--limit", type=int, default=100)
    cf.add_argument("--discover", action="store_true", help="pages: ook pagina's zonder label, op titel")
    cf.add_argument("--values", help="json-bestand of inline json met veldwaarden")
    cf.add_argument("--page", help="page-id (upsert-details, set-labels); bij render: hele pagina renderen",
                    nargs="?", const="__page__")
    cf.add_argument("--title", help="create-initiative: titel (zonder key)")
    cf.add_argument("--samenvatting", help="tekst onder 'Waarover gaat het'")
    cf.add_argument("--parent", help="create-initiative / create-child: parent page-id")
    cf.add_argument("--label", action="append", help="create-child: label (herhaalbaar)")
    cf.add_argument("--from-title", help="create-child: body kopiëren van de pagina met deze titel (sjabloon)")
    cf.add_argument("--apply", action="store_true")

    v = sub.add_parser("validate", parents=[common], help="regels over live data of aangeleverde bestanden")
    v.add_argument("--register"), v.add_argument("--jira"), v.add_argument("--hours")
    v.add_argument("--discover", action="store_true", help="live: ook pagina's zonder label (vóór de retro-fit)")

    r = sub.add_parser("report", parents=[common], help="data --since D [--until D]")
    r.add_argument("action", choices=["data"])
    r.add_argument("--since"), r.add_argument("--until")

    ap = sub.add_parser("apply", parents=[common], help="voorstel-bestand uitvoeren")
    ap.add_argument("--proposal", required=True)
    ap.add_argument("--apply", action="store_true")
    return p


COMMANDS = {"schema": cmd_schema, "config": cmd_config, "state": cmd_state, "jira": cmd_jira,
            "conf": cmd_conf, "validate": cmd_validate, "report": cmd_report, "apply": cmd_apply}


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    # `--page` bij conf: zonder waarde = vlag (render hele pagina); met waarde = page-id
    if args.cmd == "conf":
        args.page_flag = args.page == "__page__"
        if args.page_flag:
            args.page = None
        if args.action == "render":
            args.page = args.page_flag
        if args.action == "set-labels" and args.ident and not args.page:
            args.page = args.ident
        if args.action == "search" and args.ident and not args.cql:
            args.cql = args.ident
    try:
        cfg = config.load(args.config)
        schema = sch.load(args.schema)
        return COMMANDS[args.cmd](args, cfg, schema)
    except UsageError as e:
        print(f"gebruik: {e}", file=sys.stderr)
        return 2
    except config.GuardRefused as e:
        print(f"geweigerd: {e}", file=sys.stderr)
        return 3
    except ValueError as e:
        print(f"ongeldig: {e}", file=sys.stderr)
        return 4
    except http.AuthError as e:
        print(f"auth: {e}", file=sys.stderr)
        return 1
    except http.HttpError as e:
        print(f"http: {e}", file=sys.stderr)
        return 1
    except NotImplementedError as e:
        print(f"nog niet gebouwd: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
