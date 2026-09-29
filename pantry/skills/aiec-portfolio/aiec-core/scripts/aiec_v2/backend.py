"""Read adapters and narrowly scoped writes. Live mode is off by default."""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import re
from aiec_lib import confluence as conf, jira, http
from .catalog import digest
from . import report_history


def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
# Writes to the git archive, not to Atlassian: no Atlassian write guard or writer.
ARCHIVE_KINDS = {'meetstand.archive', 'rapportering.archive'}


# Jira plugin fields (Development) serialize as Java toString with per-request identity
# hashes (pkg.SummaryBean@2052e645). Masking them keeps real content changes detectable.
_IDENTITY=re.compile(r'(\.[A-Z][\w$]*)@[0-9a-f]{1,8}\b')
# ScriptRunner fields computed at read time (Cycle time, Flow efficiency); they change with the clock.
_VOLATILE={'customfield_16210','customfield_16211'}


def _stable(v):
    # Confluence search results omit some _links that a direct GET returns; links are not content.
    if isinstance(v,dict):return {k:_stable(x) for k,x in v.items() if k!='_links' and k not in _VOLATILE}
    if isinstance(v,list):return [_stable(x) for x in v]
    return _IDENTITY.sub(r'\1',v) if isinstance(v,str) else v


def revision(obj): return digest(_stable(obj))


class FixtureBackend:
    """Persistent offline sandbox; never loads credentials or opens a socket."""
    def __init__(self,path,cat,cfg):
        self.path=Path(path).resolve();self.cat=cat;self.cfg=cfg
        self.data=json.loads(self.path.read_text())
        self.identity={'mode':'fixture','path':str(self.path)}
    def get(self,kind,key):
        return deepcopy(self.data.get('objects',{}).get(kind,{}).get(str(key)))
    def collect(self,**kwargs):
        snap=normalize(self.cat,self.cfg,self.data['objects'],self.identity)
        snap['meetstanden']=deepcopy(self.data.get('meetstanden',[]))
        snap['rapportering']=deepcopy(self.data.get('rapportering',[]))
        return snap
    def transitions(self,key):return deepcopy(self.data.get('transitions',{}).get(key,[]))
    def title_exists(self,space,title):
        return any(p['space']['key']==space and p['title']==title for p in self.data['objects'].get('page',{}).values())
    def search_duplicate(self,title):
        return any(i['fields']['summary']==title for i in self.data['objects'].get('issue',{}).values())
    def user_active(self,name):return bool(self.data.get('users',{}).get(name,{}).get('active'))
    def mutate(self,action):
        kind=action['kind']; key=action.get('key');payload=deepcopy(action['payload'])
        objects=self.data['objects'];result={}
        if kind=='page.update':
            p=objects['page'][key];p.update(payload);p['body']={'storage':payload['body']['storage']};result={'id':key}
        elif kind=='page.label':
            p=objects['page'][key];ls=p.setdefault('metadata',{}).setdefault('labels',{}).setdefault('results',[])
            ls.extend(x for x in payload if x['name'] not in {l['name'] for l in ls});result={'id':key}
        elif kind=='issue.transition':
            p=objects['issue'][key];transition=next(t for t in self.transitions(key) if t['id']==payload['transition']['id'])
            p['fields']['status']=transition['to'];p['fields']['updated']=now();result={'key':key}
        elif kind=='issue.link':
            a,b=payload['inwardIssue']['key'],payload['outwardIssue']['key']
            objects['issue'][a]['fields'].setdefault('issuelinks',[]).append({'type':payload['type'],'outwardIssue':{'key':b}})
            result={'linked':[a,b]}
        elif kind=='issue.update':
            objects['issue'][key]['fields'].update(payload['fields']);objects['issue'][key]['fields']['updated']=now();result={'key':key}
        elif kind=='page.create':
            key=str(max([int(x) for x in objects['page']]+[100])+1)
            objects['page'][key]=dict(payload,id=key,version={'number':1,'when':now()})
            labels=objects['page'][key].get('metadata',{}).get('labels',[])
            objects['page'][key]['metadata']={'labels':{'results':labels}}
            # REST expands ancestors with titles; fixture emulates that response.
            for ancestor in objects['page'][key].get('ancestors',[]):
                ancestor['title']=objects['page'].get(str(ancestor['id']),{}).get('title','')
            result={'id':key}
        elif kind=='page.attachment':
            from .report_assets import attachment_bytes
            attachment_bytes(payload)
            if key not in objects['page']:raise ValueError('Bijlagepagina ontbreekt')
            files=objects.setdefault('attachments',{}).setdefault(key,{})
            if payload['filename'] in files:raise ValueError('Bijlage bestaat al; niet overschrijven')
            files[payload['filename']]=payload
            result={'page_id':key,'filename':payload['filename'],'sha256':payload['sha256']}
        elif kind=='meetstand.archive':
            from .report_history import archive_name
            if key not in objects['page']:raise ValueError('Rapportpagina bij meetstand ontbreekt')
            entries=self.data.setdefault('meetstanden',[]);name=archive_name(payload['record'])
            if any(archive_name(e['record'])==name for e in entries):raise ValueError('Meetstand bestaat al; niet overschrijven')
            entries.append({'page_id':key,'record':payload['record']});result={'page_id':key,'archive':name}
        elif kind=='rapportering.archive':
            from .report_history import rapportering_name
            from .periods import check_frequency
            entries=self.data.setdefault('rapportering',[]);name=rapportering_name(check_frequency(payload))
            if any(rapportering_name(e)==name for e in entries):raise ValueError('Rapporteringsfrequentie bestaat al; niet overschrijven')
            entries.append(deepcopy(payload));result={'archive':name}
        elif kind=='issue.create':
            project=payload['fields']['project']['key'];keys=[int(x.split('-')[1]) for x in objects['issue'] if x.startswith(project+'-')]
            key=f'{project}-{max(keys+[0])+1}';payload['fields'].update(status={'name':'Captatie'},updated=now(),created=now())
            objects['issue'][key]=dict(payload,key=key);result={'key':key}
        else:raise ValueError('Onbekende actie '+kind)
        # Atomic replace, action journal is maintained separately by execution engine.
        tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps(self.data,ensure_ascii=False,indent=2)+'\n');tmp.replace(self.path)
        return result


class LiveBackend:
    def __init__(self,cat,cfg):
        self.cat,self.cfg=cat,cfg
        self.cc=http.confluence(cfg);self.jc=http.jira(cfg)
        self.identity={'mode':'live','jira':cfg['atlassian']['jira_url'],'confluence':cfg['atlassian']['confluence_url'],'space':cfg['atlassian']['space']}
    def get(self,kind,key):
        if kind=='issue':return self.jc.get(f'/rest/api/2/issue/{key}')
        return self.cc.get(f'/rest/api/content/{key}',{'expand':conf.PAGE_EXPAND})
    def transitions(self,key):return self.jc.get(f'/rest/api/2/issue/{key}/transitions',{'expand':'transitions.fields'}).get('transitions',[])
    def title_exists(self,space,title):
        hits=conf._paged(self.cc,'/rest/api/content',{'spaceKey':space,'title':title,'type':'page'})
        return bool(hits)
    def user_active(self,name):
        try:return bool(self.jc.get('/rest/api/2/user',{'username':name}).get('active'))
        except http.HttpError as error:
            if error.status==404:return False
            raise
    def search_duplicate(self,title):
        # Exact comparison in code; never interpolate free text into JQL.
        rows=jira._search(self.jc,f'project = {self.cfg["atlassian"]["jira_project"]} AND issuetype = Initiative',fields='summary')
        return any(x['fields']['summary']==title for x in rows)
    def collect(self,include_hours=False,since=None,until=None):
        a=self.cfg['atlassian'];objects={'issue':{},'page':{}}
        roots=jira._search(self.jc,f'project = {a["jira_project"]} AND issuetype = Initiative',fields='*all')
        for i in roots:objects['issue'][i['key']]=i
        # Follow explicit links only. Billingkey coincidence is not a verified relationship.
        pending=[l['key'] for i in roots for l in jira._links(i) if l['key'].split('-')[0] in ('EAG','POR','PROD')]
        while pending:
            key=pending.pop()
            if key in objects['issue']:continue
            obj=self.get('issue',key);objects['issue'][key]=obj
            pending += [l['key'] for l in jira._links(obj) if l['key'].split('-')[0] in ('EAG','POR','PROD') and l['key'] not in objects['issue']]
            if len(objects['issue'])>5000:raise ValueError('Meer dan 5000 gekoppelde tickets; scope nakijken')
        # Maintenance of a product: POR tasks pointing to it via Bedrijfstoepassing, with their Tempo account.
        prods=sorted(k for k in objects['issue'] if k.startswith('PROD-'))
        objects['maintenance']=jira._search(self.jc,f'cf[{jira.BEDRIJFSTOEPASSING.split("_")[1]}] in ({", ".join(prods)})',
                                            fields=f'summary,status,{jira.BEDRIJFSTOEPASSING},{jira.BILLINGKEY}') if prods else []
        # Every product, linked or not: a maintenance plan names the products it depends on by key.
        objects['product_catalog']=jira._search(self.jc,'project = PROD',fields='summary')
        objects['tempo_account']={}
        for bk in {(m['fields'].get(jira.BILLINGKEY) or {}).get('key') for m in objects['maintenance']}-{None}:
            try:objects['tempo_account'][bk]=self.jc.get(f'/rest/tempo-accounts/1/account/key/{bk}')
            except http.HttpError:pass   # unknown account is not onderhoud
        cql=f'space = "{a["space"]}" and type = page'
        # Full space scan: catches missing labels and duplicate candidate roots.
        for p in conf._paged(self.cc,'/rest/api/content/search',{'cql':cql,'expand':conf.PAGE_EXPAND}):objects['page'][p['id']]=p
        # External templates we mirror (other space, read only): review checks they did not drift.
        objects['template']={}
        for tid in {str(r['sjabloon']['page_id']) for r in self.cat.reports.values() if r.get('sjabloon')}:
            try:objects['template'][tid]=self.cc.get(f'/rest/api/content/{tid}',{'expand':'body.storage,version'})
            except http.HttpError:pass   # missing template is reported by review
        snap=normalize(self.cat,self.cfg,objects,self.identity)
        if include_hours:
            cache=dict(objects['issue']);per={};worklogs={}
            for issue in snap['issues']:
                key=issue['key'];tree=set(jira._subtree(self.cfg,self.jc,key,cache))
                for proj in snap['projects']:
                    # An internal project has no Jira subtree; its hours are on the initiative.
                    if key in proj['initiatives'] and proj.get('type')!=INTERN:tree.update(jira._subtree(self.cfg,self.jc,proj['key'],cache))
                total=direct=0.0
                for ticket in sorted(tree):
                    if ticket not in worklogs:
                        out=[];start=0
                        while True:
                            d=self.jc.get(f'/rest/api/2/issue/{ticket}/worklog',{'startAt':start,'maxResults':100});batch=d.get('worklogs',[])
                            out+=batch;start+=len(batch)
                            if start>=d.get('total',len(out)):break
                            if not batch:raise ValueError('Onvolledige worklogpaginering')
                        worklogs[ticket]=out
                    for w in worklogs[ticket]:
                        date=str(w.get('started',''))[:10]
                        if (since and date<since) or (until and date>until):continue
                        hrs=(w.get('timeSpentSeconds') or 0)/3600;total+=hrs
                        if ticket==key:direct+=hrs
                per[key]={'period_h':round(total,4),'direct_h':round(direct,4),'issues':sorted(tree)}
            snap['hours']={'since':since,'until':until,'per_initiative':per}
            snap['gaps']=[g for g in snap['gaps'] if not g.startswith('Uren zijn niet')]
        snap['meetstanden']=report_history.read_archive(self.cfg['meetstanden']['path'])
        snap['rapportering']=report_history.read_rapportering(self.cfg['meetstanden']['path'])
        return snap
    def mutate(self,action):
        kind=action['kind'];key=action.get('key');scope=action['scope']
        if kind=='meetstand.archive':return archive(self.cfg,key,action['payload']['record'])
        if kind=='rapportering.archive':return archive_frequency(self.cfg,action['payload'])
        client=http.writer(self.cfg,'confluence' if kind.startswith('page.') else 'jira',scope,True)
        if kind=='page.attachment':
            from .report_assets import attachment_bytes
            content=attachment_bytes(action['payload'])
            existing=self.cc.get(f'/rest/api/content/{key}/child/attachment',{'filename':action['payload']['filename']})
            if existing.get('results'):raise ValueError('Bijlage bestaat al; niet overschrijven')
            result=client.upload_attachment(key,action['payload']['filename'],content)
            if not result or not result.get('results'):raise ValueError('Uploadresultaat ontbreekt; eerst reconciliëren')
            return {'page_id':key,'filename':action['payload']['filename'],'sha256':action['payload']['sha256'],'attachment_id':result['results'][0]['id']}
        routes={'page.update':('PUT',f'/rest/api/content/{key}'),'page.label':('POST',f'/rest/api/content/{key}/label'),
                'page.create':('POST','/rest/api/content'),'issue.transition':('POST',f'/rest/api/2/issue/{key}/transitions'),
                'issue.create':('POST','/rest/api/2/issue'),'issue.link':('POST','/rest/api/2/issueLink'),
                'issue.update':('PUT',f'/rest/api/2/issue/{key}')}
        method,path=routes[kind]
        result=client.request(method,path,body=action['payload']) or {'ok':True}
        # Confluence Server ignores metadata.labels on create; set them explicitly afterwards.
        labels=action['payload'].get('metadata',{}).get('labels') if kind=='page.create' else None
        if labels:result['labels']=client.request('POST',f"/rest/api/content/{result['id']}/label",body=labels)
        return result


def _commit(cfg,root,name,message):
    import subprocess
    git=lambda *args:subprocess.run(['git','-C',str(root),*args],check=True,capture_output=True,text=True)
    git('add','--',name);git('commit','-m',message)
    if cfg['meetstanden'].get('push',True):git('push','origin','HEAD')
    return git('rev-parse','HEAD').stdout.strip()


def archive_frequency(cfg,record):
    """Write one reporting-frequency record to the git archive, commit it and push it. Never overwrites."""
    from .periods import check_frequency
    root=Path(cfg['meetstanden']['path']).expanduser()
    report_history.read_rapportering(root)  # Refuses a missing or inconsistent archive before writing.
    name=report_history.rapportering_name(check_frequency(record));path=root/name
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:f.write(json.dumps(record,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    return {'archive':name,'commit':_commit(cfg,root,name,f"rapportering {record['key']}: {record['frequentie']}"+(f" vanaf {record['vanaf']}" if record['vanaf'] else ''))}


def archive(cfg,page_id,record):
    """Write one measurement to the git archive, commit it and push it. Never overwrites."""
    root=Path(cfg['meetstanden']['path']).expanduser()
    report_history.read_archive(root)  # Refuses a missing or inconsistent archive before writing.
    name=report_history.archive_name(record);path=root/name
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:f.write(json.dumps({'page_id':str(page_id),'record':record},ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    return {'page_id':str(page_id),'archive':name,'commit':_commit(cfg,root,name,f"meetstand {record['target']} {record['period']} (pagina {page_id})")}


# A project page is a folder under the initiative: 'POR-123 - <summary>'. Its children are that project's artefacts.
# An internal project has no POR ticket: 'intern - <naam>'. Type, status, start date, decision and its technical key
# (AI-49-intern-1, numbered per initiative; archive, form and tracking only) live in the page's properties block.
PROJECT_TITLE_RE=re.compile(r'(POR-\d+|intern) - ')
INTERN='intern'
INTERN_KEY_RE=re.compile(r'[A-Z][A-Z0-9_]*-\d+-intern-\d+')
PROJECT_DETAILS='aiec-project'


def intern_key(ai,n):return f'{ai}-{INTERN}-{n}'


def project_properties_of(schema,storage):
    """Properties of an internal project page. Beslissing is the linked page's title, which Confluence keeps current on rename."""
    out={}
    for s,e in conf.find_details_blocks(schema,storage or '',PROJECT_DETAILS):
        for label,cell in conf._rows(storage[s:e]):
            m=re.search(r'ri:content-title="([^"]*)"',cell) if label=='Beslissing' else None
            out[label]=html.unescape(m.group(1)) if m else conf._cell_text(cell)
    return out


def normalize(cat,cfg,objects,identity):
    a=cfg['atlassian'];issues=[];projects={};products={};pages=[];gaps=[];report_pages=[]
    rawissues=objects.get('issue',{});rawpages=objects.get('page',{})
    # Parent chain via the direct parent: live REST lists all ancestors, the fixture only the parent.
    parent_of={str(x['id']):str(x['ancestors'][-1]['id']) for x in rawpages.values() if x.get('ancestors')}
    def descends(page_id,root):
        seen=set()
        while page_id in parent_of and page_id not in seen:
            seen.add(page_id);page_id=parent_of[page_id]
            if page_id==root:return True
        return False
    for raw in rawissues.values():
        if raw['key'].startswith(a['jira_project']+'-') and (raw['fields'].get('issuetype') or {}).get('name')=='Initiative':
            i=jira._to_initiative(cfg,cat.schema,raw);issues.append(i)
            pending=[l['key'] for l in jira._links(raw)];seen=set()
            while pending:
                key=pending.pop()
                if key in seen:continue
                seen.add(key)
                if key not in rawissues:continue
                obj=rawissues[key];f=obj['fields'];prefix=key.split('-')[0]
                if prefix not in ('EAG','POR','PROD'):continue
                if prefix in ('POR','PROD'):
                    target=projects if prefix=='POR' else products
                    rec=target.setdefault(key,{'key':key,'type':'por','title_key':key,'summary':f.get('summary'),'status':(f.get('status') or {}).get('name'),'assignee':jira._user(f.get('assignee')),'updated':f.get('updated'),'initiatives':[],'url':a['jira_url'].rstrip('/')+'/browse/'+key})
                    if i['key'] not in rec['initiatives']:rec['initiatives'].append(i['key'])
                    if prefix=='PROD':rec.update(applicatiefiche=f.get(jira.APPLICATIEFICHE) or '',verantwoordelijk_team=(f.get(jira.VERANTWOORDELIJK_TEAM) or {}).get('value') or '')
                # No traversal back through other AI initiatives.
                pending += [l['key'] for l in jira._links(obj) if l['key'].split('-')[0] in ('EAG','POR','PROD')]
    for raw in rawpages.values():
        storage=raw.get('body',{}).get('storage',{}).get('value','')
        from .report_history import MARKER
        tracked_labels={r.get('label') for r in cat.reports.values() if r.get('tracking')}
        if MARKER in storage or tracked_labels.intersection(conf._labels(raw)):
            report_pages.append({'page_id':str(raw['id']),'title':raw['title'],'space':raw['space']['key'],
                                 'labels':conf._labels(raw),'storage':storage,'revision':revision(raw)})
        label=cat.schema['label'] in conf._labels(raw)
        key=conf._key_of(raw['title'])
        anc=raw.get('ancestors',[])
        ancestor_ai=any(conf._key_of(x.get('title','')) for x in anc)
        if not label and not (key and not ancestor_ai):continue
        def under(parent_id):
            return [{'page_id':child['id'],'title':child['title'],'labels':conf._labels(child),'last_modified':child.get('version',{}).get('when',''),'storage':child.get('body',{}).get('storage',{}).get('value','')}
                    for child in rawpages.values() if child.get('ancestors') and str(child['ancestors'][-1]['id'])==str(parent_id)]
        children=under(raw['id'])
        for c in list(children):
            m=PROJECT_TITLE_RE.match(c['title'])
            if not m:continue
            pk=m.group(1)
            if pk==INTERN:
                if not key:continue
                props=project_properties_of(cat.schema,c['storage']);pk=props.get('Projectkey','')
                # Without its own key under this initiative the page is no project; review shows it as unknown.
                if not INTERN_KEY_RE.fullmatch(pk) or not pk.startswith(key+'-'):continue
                projects.setdefault(pk,{'key':pk,'type':INTERN,'title_key':INTERN,'summary':c['title'][m.end():],'status':props.get('Status') or None,
                                        'assignee':None,'updated':c['last_modified'],'initiatives':[key],'url':conf._url(cfg,c['page_id']),'beslissing':props.get('Beslissing') or '',
                                        'startdatum':props.get('Startdatum') or None})
            c['project_page']=pk
            children+=[dict(g,project=pk,parent_id=str(c['page_id'])) for g in under(c['page_id'])]
        rec=conf._page_record(cfg,cat.schema,raw,children);rec.update(storage=storage,space=raw['space']['key'])
        # Decision pages anywhere under the initiative; 'Overgang naar' comes from their properties block.
        # A report with a Beslissing block (initiatie, verkenning) counts too once it names a later transition.
        reports={g['decision_in'] for g in cat.process.get('gates',{}).values() if g.get('decision_in') not in (None,'decisions')}
        props=lambda x:conf.parse_properties(cat.schema,x.get('body',{}).get('storage',{}).get('value',''),'aiec-beslissing')
        rec['decisions']=[{'page_id':str(x['id']),'title':x['title'],'overgang':cat.state(props(x).get('Overgang naar'))}
                          for x in rawpages.values() if descends(str(x['id']),str(raw['id'])) and
                          ('decisions' in conf._labels(x) or (reports&set(conf._labels(x)) and props(x).get('Overgang naar')))]
        pages.append(rec)
    accounts=objects.get('tempo_account',{})
    for m in objects.get('maintenance',[]):
        f=m['fields'];prod=(f.get(jira.BEDRIJFSTOEPASSING) or {}).get('key');bk=(f.get(jira.BILLINGKEY) or {}).get('key')
        if prod not in products:continue
        # Only the Tempo account category decides whether a task is maintenance.
        if ((accounts.get(bk) or {}).get('category') or {}).get('key')=='OND':
            products[prod].setdefault('onderhoud_keys',[]).append(m['key']);products[prod].setdefault('onderhoud_billingkeys',[]).append(bk)
    for p in products.values():
        p.setdefault('onderhoud_keys',[]);p.setdefault('onderhoud_billingkeys',[])
    gaps.append('Uren zijn niet opgehaald; gebruik collect --hours met een expliciete periode voor boekingscontrole.')
    gaps.append('Project- en productkoppelingen volgen expliciete Jira-links. Niet-gelinkte of uitsluitend via billingkey verbonden tickets zijn niet volledig afgedekt.')
    for p in projects.values():
        if len(p['initiatives'])>1:gaps.append(f"{p['key']} hangt aan meerdere initiatieven; uren niet zonder verdeelsleutel optellen.")
    templates={str(k):{'version':(t.get('version') or {}).get('number'),'storage':t.get('body',{}).get('storage',{}).get('value','')} for k,t in objects.get('template',{}).items()}
    catalog={x['key']:x['fields'].get('summary') or '' for x in list(rawissues.values())+objects.get('product_catalog',[]) if x['key'].startswith('PROD-')}
    return {'version':2,'collected_at':now(),'source':identity,'issues':issues,'pages':pages,'projects':list(projects.values()),'products':list(products.values()),'product_catalog':catalog,'report_pages':report_pages,'templates':templates,'gaps':gaps}
