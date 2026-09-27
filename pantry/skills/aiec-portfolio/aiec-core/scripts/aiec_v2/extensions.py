"""Install declarative definitions through an approved, reversible local change.

New executable handlers are deliberately not loaded from YAML. They require an ordinary
code review and tests, coordinated by the maintainer skill.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import shutil
import tempfile
from uuid import uuid4
import yaml
from .catalog import Catalog, digest
from .backend import now
from .execution import Refused, write_json, locked, append

KINDS={'rule':'rules','report':'reports','capability':'capabilities'}


def propose(cat,kind,definition):
    if kind not in KINDS:raise ValueError('Onbekend definitietype')
    obj=yaml.safe_load(definition)
    ident=obj.get('id','') if isinstance(obj,dict) else ''
    if not re.fullmatch(r'[a-z][a-z0-9-]*',ident):raise ValueError('Definitie mist geldige id')
    rel=f'catalog/{KINDS[kind]}/{ident}.yaml';target=cat.root/rel
    if target.is_symlink():raise Refused('Geen definities via symlinks vervangen')
    with tempfile.TemporaryDirectory(prefix='aiec-check-') as tmp:
        root=Path(tmp)/'core';shutil.copytree(cat.root,root,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
        (root/rel).write_text(definition);Catalog(root)
    result={'version':1,'id':str(uuid4()),'kind':'definition','root':str(cat.root.resolve()),'path':rel,
            'catalog_hash':cat.fingerprint,'created_at':now(),'expires_at':(datetime.now(timezone.utc)+timedelta(hours=24)).isoformat(),
            'before':target.read_text() if target.exists() else None,'after':definition,
            'validation':'Catalogus inclusief nieuwe definitie gevalideerd; inhoudelijk akkoord en praktijkproef blijven nodig.'}
    result['hash']=digest(result);return result


def validate(plan,cat):
    if plan.get('kind')!='definition' or digest({k:v for k,v in plan.items() if k!='hash'})!=plan.get('hash'):raise Refused('Definitievoorstel gewijzigd')
    if plan.get('root')!=str(cat.root.resolve()) or plan['catalog_hash']!=cat.fingerprint:raise Refused('Bron of catalogus gewijzigd; nieuw voorstel nodig')
    if datetime.now(timezone.utc)>datetime.fromisoformat(plan['expires_at']):raise Refused('Voorstel verlopen')
    if not re.fullmatch(r'catalog/(rules|reports|capabilities)/[a-z][a-z0-9-]*\.yaml',plan['path']):raise Refused('Geen toegelaten definitiepad')


def approve(plan,cat,by,evidence,ack):
    validate(plan,cat)
    if ack!=plan['hash'] or not by.strip() or not evidence.strip():raise Refused('Expliciet akkoord op de hash vereist')
    return {'plan_id':plan['id'],'plan_hash':plan['hash'],'approved_by':by,'evidence':evidence,'approved_at':now()}


def apply(plan,receipt,cat,state_dir):
    validate(plan,cat)
    if receipt.get('plan_id')!=plan['id'] or receipt.get('plan_hash')!=plan['hash'] or not receipt.get('approved_by') or not receipt.get('evidence'):raise Refused('Geen passend akkoord')
    root=Path(state_dir)/'definitions'
    with locked(root):
        # Recompute while locked: an earlier definition change invalidates this approval.
        validate(plan,Catalog(cat.root))
        target=(cat.root/plan['path'])
        if target.is_symlink() or not target.resolve().is_relative_to(cat.root.resolve()):raise Refused('Pad verlaat de catalogus')
        before=target.read_text() if target.exists() else None
        if before!=plan['before']:raise Refused('Definitie intussen gewijzigd')
        journal=root/(plan['id']+'.jsonl')
        if journal.exists():raise Refused('Al gestart; eerst de uitkomst controleren')
        write_json(root/(plan['id']+'.backup.json'),{'plan':plan,'approval':receipt},exclusive=True)
        append(journal,{'event':'started','path':plan['path']})
        tmp=target.with_suffix('.yaml.tmp');tmp.write_text(plan['after']);tmp.replace(target)
        try:Catalog(cat.root)
        except Exception:
            if before is None:target.unlink()
            else:target.write_text(before)
            append(journal,{'event':'rolled-back'});raise
        append(journal,{'event':'completed'})
        return {'status':'completed','path':str(target),'backup':str(root/(plan['id']+'.backup.json')),
                'next':'Genereer de leesbare catalogus opnieuw en publiceer de plugin opnieuw; voer de afgesproken praktijkproef uit.'}
