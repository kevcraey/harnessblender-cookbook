#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml>=6,<7", "pillow>=11,<13"]
# ///
"""AIEC v2: code-first portfolio work. No live writes outside approved proposals."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import yaml
from aiec_lib import config
from aiec_v2.catalog import Catalog, CORE
from aiec_v2.backend import FixtureBackend, LiveBackend
from aiec_v2 import review as reviews, reports, changes, execution, extensions


def read_json(path):return json.loads(Path(path).expanduser().read_text())


def emit(data,out=None,markdown=None):
    if out:
        html=(data.get('html') or data.get('preview_html')) if isinstance(data,dict) else None
        paths=[Path(out)]+([Path(out).with_suffix('.md')] if markdown else [])+([Path(out).with_suffix('.html')] if html else [])
        if len(set(paths))!=len(paths) or any(p.exists() for p in paths):raise ValueError('Uitvoerbestand bestaat al of uitvoerpaden vallen samen; niets overschreven')
        execution.write_json(out,data,exclusive=True)
        if markdown:
            p=Path(out).with_suffix('.md')
            with p.open('x',encoding='utf-8') as f:f.write(markdown)
        if html:
            with Path(out).with_suffix('.html').open('x',encoding='utf-8') as f:f.write(html)
        print(str(Path(out).resolve()))
    else:print(markdown if markdown else json.dumps(data,ensure_ascii=False,indent=2))


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--core',default=str(CORE),help='Bronmap met schema, catalog en scripts')
    p.add_argument('--config',default=str(Path.home()/'.config/aiec-v2/config.toml'))
    p.add_argument('--fixture',help='Offline sandbox JSON; nooit netwerk')
    p.add_argument('--state-dir',default=str(Path.home()/'.local/state/aiec-v2'))
    s=p.add_subparsers(dest='cmd',required=True)
    q=s.add_parser('catalog');q.add_argument('--out')
    s.add_parser('check')
    s.add_parser('doctor')
    s.add_parser('config-init')
    q=s.add_parser('collect');q.add_argument('--out',required=True);q.add_argument('--hours',action='store_true');q.add_argument('--since');q.add_argument('--until')
    q=s.add_parser('review');q.add_argument('--snapshot',required=True);q.add_argument('--out');q.add_argument('--today')
    q=s.add_parser('report');q.add_argument('report');q.add_argument('--snapshot',required=True);q.add_argument('--target');q.add_argument('--period',required=True);q.add_argument('--inputs');q.add_argument('--tracking',help='JSON met baseline/scopebesluiten/expliciete aannames');q.add_argument('--slug');q.add_argument('--out')
    q=s.add_parser('propose');q.add_argument('--request',required=True);q.add_argument('--out',required=True)
    q=s.add_parser('form');fs=q.add_subparsers(dest='form_action',required=True)
    x=fs.add_parser('build');x.add_argument('--out',required=True)
    x=fs.add_parser('export');x.add_argument('--snapshot',required=True);x.add_argument('--target',required=True);x.add_argument('--period',required=True);x.add_argument('--tracking');x.add_argument('--out',required=True)
    x=fs.add_parser('open',help='Formulier met het project erin, geopend in de browser');x.add_argument('--snapshot',required=True);x.add_argument('--target',required=True);x.add_argument('--period',help='Standaard: maand na de laatste meetstand');x.add_argument('--tracking');x.add_argument('--dir',help='Standaard [form].dir');x.add_argument('--fresh',action='store_true',help='Bewaard concept negeren');x.add_argument('--no-open',action='store_true')
    x=fs.add_parser('import');x.add_argument('--snapshot',required=True);x.add_argument('--file',help='Standaard: laatst bewaarde <target>_<period>.aiec.json in [form].dir');x.add_argument('--target');x.add_argument('--period');x.add_argument('--out',required=True)
    q=s.add_parser('show');q.add_argument('--plan',required=True)
    q=s.add_parser('approve');q.add_argument('--plan',required=True);q.add_argument('--by',required=True);q.add_argument('--evidence',required=True);q.add_argument('--ack',required=True);q.add_argument('--out',required=True)
    q=s.add_parser('apply');q.add_argument('--plan',required=True);q.add_argument('--approval',required=True)
    q=s.add_parser('scaffold');q.add_argument('kind',choices=['rule','report','capability']);q.add_argument('id');q.add_argument('--out',required=True)
    q=s.add_parser('schema-doc');q.add_argument('--out')
    q=s.add_parser('extend');es=q.add_subparsers(dest='action',required=True)
    x=es.add_parser('propose');x.add_argument('kind',choices=['rule','report','capability']);x.add_argument('--file',required=True);x.add_argument('--out',required=True)
    x=es.add_parser('approve');x.add_argument('--plan',required=True);x.add_argument('--by',required=True);x.add_argument('--evidence',required=True);x.add_argument('--ack',required=True);x.add_argument('--out',required=True)
    x=es.add_parser('apply');x.add_argument('--plan',required=True);x.add_argument('--approval',required=True)
    return p


def main(argv=None):
    args=parser().parse_args(argv)
    try:
        cat=Catalog(args.core);cfg=config.load(args.config)
        if args.cmd=='check':
            emit({'ok':True,'reports':len(cat.reports),'rules':len(cat.rules),'capabilities':len(cat.capabilities),'fingerprint':cat.fingerprint});return 0
        if args.cmd=='catalog':emit(cat.overview(),args.out);return 0
        if args.cmd=='doctor':
            emit({'catalog':'ok','write_mode':cfg['writes']['mode'],'config':args.config,'fixture':bool(args.fixture),'live_tested':False,'open_process_decisions':cat.process['open_decisions'],'note':'Geen netwerkcontrole uitgevoerd. Gebruik collect voor een expliciete leesproef.'});return 0
        if args.cmd=='config-init':print(config.init(args.config));return 0
        if args.cmd=='schema-doc':
            from export_docs import documents
            text=documents(cat)['aiec-schema.md']
            if args.out:
                with Path(args.out).open('x',encoding='utf-8') as f:f.write(text)
            else:print(text)
            return 0
        if args.cmd=='review':
            from datetime import date
            data=reviews.review(cat,read_json(args.snapshot),date.fromisoformat(args.today) if args.today else None)
            emit(data,args.out,reviews.markdown(data));return 0
        if args.cmd=='report':
            result=reports.render(cat,read_json(args.snapshot),args.report,args.target,args.period,read_json(args.inputs) if args.inputs else {},cfg,args.slug,read_json(args.tracking) if args.tracking else None)
            emit(result,args.out,result['markdown']);return 0
        if args.cmd=='form':
            from aiec_v2 import form_files
            if args.form_action=='build':
                output=Path(args.out);output.parent.mkdir(parents=True,exist_ok=True)
                with output.open('x',encoding='utf-8') as f:f.write(form_files.build_html(cat))
                print(str(output.resolve()))
            elif args.form_action=='export':
                emit(form_files.export_project(cat,read_json(args.snapshot),args.target,args.period,read_json(args.tracking) if args.tracking else None),args.out)
            elif args.form_action=='open':
                snapshot=read_json(args.snapshot);folder=Path(args.dir or cfg['form']['dir']).expanduser()
                doc,draft=form_files.prepare(cat,snapshot,args.target,folder,args.period,read_json(args.tracking) if args.tracking else None,args.fresh)
                period=doc['periods'][-1]['period'];output=folder/f'{args.target}_{period}.html'  # Regenerated each time; the saved .aiec.json is the work.
                output.parent.mkdir(parents=True,exist_ok=True);output.write_text(form_files.build_html(cat,doc),encoding='utf-8')
                if not args.no_open:subprocess.run(['open',str(output)],check=True)
                emit({'form':str(output),'period':period,'project':f'bewaard concept {draft}' if draft else 'verse export'})
            else:
                file=args.file
                if not file:
                    if not args.target:raise ValueError('Geef --file of --target')
                    period=args.period or form_files.next_period(cat,read_json(args.snapshot),args.target)
                    file=form_files.saved_draft(cfg['form']['dir'],args.target,period)
                    if not file:raise ValueError(f'Geen bewaard projectbestand {args.target}_{period}*.aiec.json in {cfg["form"]["dir"]}')
                emit(form_files.import_request(cat,read_json(args.snapshot),form_files.read_document(file),args.period),args.out)
            return 0
        if args.cmd=='extend':
            if args.action=='propose':emit(extensions.propose(cat,args.kind,Path(args.file).read_text()),args.out)
            elif args.action=='approve':emit(extensions.approve(read_json(args.plan),cat,args.by,args.evidence,args.ack),args.out)
            else:emit(extensions.apply(read_json(args.plan),read_json(args.approval),cat,args.state_dir))
            return 0
        if args.cmd=='show':print(changes.plan_markdown(read_json(args.plan)));return 0
        if args.cmd=='scaffold':
            if not re.fullmatch(r'[a-z][a-z0-9-]*',args.id):raise ValueError('Gebruik een slug als id')
            if args.kind=='rule':obj={'id':args.id,'scope':'initiatives','severity':'warning','when':{'field':'afdeling','op':'empty'},'message':'Afdeling ontbreekt.','action':'Vraag de afdeling aan de vrager.'}
            elif args.kind=='report':obj={'id':args.id,'title':args.id,'scope':'project','label':'verslag','sections':[{'id':'bron','title':'Project','kind':'table','source':'projects','columns':['key','summary','url']},{'id':'duiding','title':'Duiding','kind':'input','required':True,'prompt':'Wat wil je hier vastleggen?'}]}
            else:obj={'id':args.id,'handler':'report','description':'Beschrijf wanneer deze handeling nodig is.'}
            with Path(args.out).open('x',encoding='utf-8') as f:f.write(yaml.safe_dump(obj,allow_unicode=True,sort_keys=False))
            print('Conceptdefinitie gemaakt; nog niet actief. Valideer in een kopie van de bron, test en vraag akkoord.');return 0
        backend=FixtureBackend(args.fixture,cat,cfg) if args.fixture else LiveBackend(cat,cfg)
        if args.cmd=='collect':
            if args.hours and (not args.since or not args.until):raise ValueError('--hours vraagt --since en --until')
            if args.since or args.until:
                from datetime import date
                if args.since:date.fromisoformat(args.since)
                if args.until:date.fromisoformat(args.until)
                if args.since and args.until and args.since>args.until:raise ValueError('Omgekeerde periode')
            emit(backend.collect(include_hours=args.hours,since=args.since,until=args.until),args.out)
        elif args.cmd=='propose':
            plan=changes.make_plan(cat,backend,cfg,read_json(args.request));emit(plan,args.out,changes.plan_markdown(plan))
        elif args.cmd=='approve':
            receipt=execution.approve(read_json(args.plan),cat,cfg,backend,args.by,args.evidence,args.ack);emit(receipt,args.out)
        elif args.cmd=='apply':emit(execution.execute(read_json(args.plan),read_json(args.approval),cat,cfg,backend,args.state_dir))
        return 0
    except (ValueError,KeyError,OSError) as e:
        print(f'Geweigerd: {e}',file=sys.stderr);return 3
    except Exception as e:
        # Never echo HTTP response bodies, headers, tokens or a raw traceback.
        print(f'Niet uitgevoerd ({type(e).__name__}). Controleer bronbereikbaarheid, rechten en configuratie.',file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
