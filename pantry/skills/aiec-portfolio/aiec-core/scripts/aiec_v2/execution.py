"""Approval-bound execution, optimistic concurrency, backups, and an append-only journal.

Receipts record approval; they do not authenticate a human. A local operator with filesystem
access can forge them. The agent must only create one after explicit conversational approval.
"""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
from .catalog import digest
from .backend import now, revision
from aiec_lib.config import guard


class Refused(ValueError): pass


def write_json(path,data,exclusive=False):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if exclusive:
        with path.open('x',encoding='utf-8') as f:
            os.chmod(path,0o600);json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    else:
        temp=path.with_suffix(path.suffix+'.tmp')
        with temp.open('w',encoding='utf-8') as f:
            os.chmod(temp,0o600);json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        temp.replace(path)


def validate_plan(plan,cat,cfg,backend):
    unsigned={k:v for k,v in plan.items() if k!='hash'}
    if plan.get('version')!=2 or digest(unsigned)!=plan.get('hash'):raise Refused('Voorstel gewijzigd of ongeldig; opnieuw voorstellen')
    if plan['catalog_hash']!=cat.fingerprint:raise Refused('Code of definities gewijzigd; nieuw voorstel vereist')
    if plan['config_hash']!=digest(cfg):raise Refused('Configuratie gewijzigd; nieuw voorstel vereist')
    if plan['source']!=backend.identity:raise Refused('Andere omgeving dan in het voorstel')
    if datetime.now(timezone.utc)>datetime.fromisoformat(plan['expires_at']):raise Refused('Voorstel verlopen; opnieuw verzamelen')
    if plan['questions']:raise Refused('Voorstel bevat onbeantwoorde vragen')
    if not plan['actions']:raise Refused('Voorstel bevat geen wijzigingen')
    from .report_assets import attachment_bytes
    creates={};filenames=set()
    for action in plan['actions']:
        if action['kind']=='page.create':creates[action['id']]=action
        if action['kind']=='page.attachment':
            attachment_bytes(action['payload'])
            ref=action['payload']['page_action'];filename=action['payload']['filename']
            if action.get('key') is not None or ref not in creates or creates[ref]['scope']!=action['scope']:
                raise Refused('Bijlage moet verwijzen naar een eerdere nieuwe pagina in dezelfde scope')
            if (ref,filename) in filenames:raise Refused('Dubbele rapportbijlage')
            filenames.add((ref,filename))
        if action['kind']=='meetstand.archive':
            ref=action['payload'].get('page_action')
            if action.get('key') is not None or ref not in creates or not isinstance(action['payload'].get('record'),dict):
                raise Refused('Meetstand moet verwijzen naar een eerdere nieuwe rapportpagina')


def approve(plan,cat,cfg,backend,by,evidence,ack):
    validate_plan(plan,cat,cfg,backend)
    if ack!=plan['hash']:raise Refused('Bevestig de volledige hash van het beoordeelde voorstel')
    if not by.strip() or not evidence.strip():raise Refused('Naam en verwijzing naar expliciet akkoord vereist')
    return {'version':1,'plan_id':plan['id'],'plan_hash':plan['hash'],'approved_by':by,'evidence':evidence,'approved_at':now()}


@contextmanager
def locked(directory):
    directory.mkdir(parents=True,exist_ok=True)
    with (directory/'execution.lock').open('a') as f:
        try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise Refused('Er loopt al een uitvoering in deze omgeving') from None
        try:yield
        finally:fcntl.flock(f,fcntl.LOCK_UN)


def append(path,event):
    with path.open('a',encoding='utf-8') as f:
        os.chmod(path,0o600);f.write(json.dumps(dict(event,time=now()),ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())


def execute(plan,receipt,cat,cfg,backend,state_dir):
    validate_plan(plan,cat,cfg,backend)
    if receipt.get('plan_id')!=plan['id'] or receipt.get('plan_hash')!=plan['hash'] or not receipt.get('approved_by') or not receipt.get('evidence'):
        raise Refused('Geen passend expliciet akkoord')
    root=Path(state_dir).expanduser()/('fixture' if backend.identity['mode']=='fixture' else 'live')
    with locked(root):
        journal=root/(plan['id']+'.jsonl')
        if journal.exists():raise Refused('Voorstel is al uitgevoerd of gedeeltelijk gestart. Eerst reconciliëren; geen automatische herhaling')
        # Check the history set, not just existing pages: another month may have appeared.
        if plan.get('history_guard'):
            from .report_history import guard as history_guard
            expected=plan['history_guard']
            actual=history_guard(cat.reports[expected['report']],backend.collect(),expected['target'],expected['initiative'])
            if actual!=expected:raise Refused('Rapporthistoriek is gewijzigd; nieuw voorstel en akkoord vereist')
        # Preflight every read before the first write.
        for p in plan['preconditions']:
            current=backend.get(p['kind'],p['key'])
            if revision(current)!=p['revision']:raise Refused(f"{p['kind']} {p['key']} is gewijzigd; vraag nieuw akkoord op een nieuw voorstel")
        for a in plan['actions']:
            if backend.identity['mode']=='live':guard(cfg,'confluence' if a['kind'].startswith('page.') else 'jira',a['scope'],True)
            if a['kind']=='page.create' and backend.title_exists(a['scope'],a['payload']['title']):raise Refused('Paginatitel bestaat intussen')
            if a['kind']=='issue.create' and backend.search_duplicate(a['payload']['fields']['summary']):raise Refused('Initiatief bestaat mogelijk al')
        # Durable backup of original objects and exact payloads before any mutation.
        write_json(root/(plan['id']+'.backup.json'),{'plan':plan,'approval':receipt},exclusive=True)
        append(journal,{'event':'approved','plan_hash':plan['hash'],'by':receipt['approved_by']})
        results=[];updated=set();new_pages={}
        try:
            for a in plan['actions']:
                # Re-read untouched targets immediately before each write. Jira lacks an atomic
                # if-match operation: the remaining server-side race is documented explicitly.
                if a.get('key'):
                    typ='page' if a['kind'].startswith('page.') else 'issue';tag=(typ,a['key'])
                    p=next((p for p in plan['preconditions'] if (p['kind'],p['key'])==tag),None)
                    if p and tag not in updated and revision(backend.get(*tag))!=p['revision']:raise Refused('Bron gewijzigd tijdens uitvoering')
                    updated.add(tag)
                append(journal,{'event':'started','action':a['id'],'kind':a['kind']})
                effective=a
                if a['kind'] in ('page.attachment','meetstand.archive'):
                    from copy import deepcopy
                    created=new_pages[a['payload']['page_action']]
                    if revision(backend.get('page',created['key']))!=created['revision']:
                        raise Refused('Nieuwe rapportpagina is gewijzigd vóór de bijlage-upload')
                    effective=deepcopy(a);effective['key']=created['key']
                result=backend.mutate(effective)
                results.append({'action':a['id'],'result':result})
                append(journal,{'event':'succeeded','action':a['id'],'result':result})
                if a['kind']=='page.create' and any(x['kind'] in ('page.attachment','meetstand.archive') and x['payload']['page_action']==a['id'] for x in plan['actions']):
                    from .report_history import content_hash
                    import re
                    key=str(result.get('id',''))
                    if not re.fullmatch(r'\d+',key):raise Refused('Nieuwe pagina-id ontbreekt; eerst reconciliëren')
                    page=backend.get('page',key)
                    before=a['payload']['body']['storage']['value'];after=page['body']['storage']['value']
                    if page['space']['key']!=a['scope'] or page['title']!=a['payload']['title'] or content_hash(before)!=content_hash(after):
                        raise Refused('Nieuwe pagina wijkt af van het goedgekeurde rapport')
                    new_pages[a['id']]={'key':key,'revision':revision(page)}
        except Exception as error:
            append(journal,{'event':'stopped','error_type':type(error).__name__,'message':'Controleer de bron: een gestarte mutatie kan wel uitgevoerd zijn.'})
            raise Refused(f'Uitvoering gestopt; niet opnieuw uitvoeren. Controleer journaal {journal} en verzamel opnieuw. Oorzaak: {type(error).__name__}') from error
        append(journal,{'event':'completed','actions':len(results)})
        return {'status':'completed','results':results,'journal':str(journal),'backup':str(root/(plan['id']+'.backup.json'))}
