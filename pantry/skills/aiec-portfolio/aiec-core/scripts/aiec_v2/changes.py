"""Build explicit payloads. Every backend mutation is a separate journalled action."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from html import escape
import difflib
import re
from uuid import uuid4
from aiec_lib import confluence as conf, jira, schema as sch
from .catalog import digest
from .backend import now, revision
from .review import datasets, review, decided, decision_question
from .reports import render


def patch_details(cat, storage, values):
    known={f['key']:f for f in cat.schema['fields']}
    if set(values)-set(known):raise ValueError('Onbekende kenmerken: '+', '.join(set(values)-set(known)))
    cleaned={}
    for key,value in values.items():
        val,problem=sch.normalize_value(cat.schema,known[key],value)
        if problem:raise ValueError(problem)
        cleaned[key]=val
    spans=conf.find_details_blocks(cat.schema,storage)
    if not spans:
        if 'ac:name="details"' in storage:raise ValueError('Onbekend details-blok: eerst de structuur reviewen')
        pos=conf.insert_position(storage)
        return storage[:pos]+conf.render_details(cat.schema,cleaned)+storage[pos:]
    # One visible block plus at most one hidden block (hidden=true, same id).
    blocks=[storage[s:e] for s,e in spans];hidden=[conf.details_hidden(b) for b in blocks]
    if hidden.count(False)!=1 or hidden.count(True)>1:raise ValueError('Meerdere kenmerkenblokken; eerst reviewen')
    extra=''
    # Preserve all rows, unknown properties, markup, macros and prose outside changed cells.
    for key,value in cleaned.items():
        f=known[key];replacement=escape(sch.display_value(cat.schema,f,value));found=[]
        for i,block in enumerate(blocks):
            for row in conf.ROW_RE.finditer(block):
                cells=list(conf.CELL_RE.finditer(row.group(1)))
                rowfield=sch.field_by_label(cat.schema,conf._cell_text(cells[0].group(2) or '')) if cells else None
                if len(cells)>=2 and rowfield and rowfield['key']==key:
                    c=cells[1]
                    if not c.group(1):raise ValueError('Zelfsluitende waardecel: eerst structureren')
                    found.append((i,row.start(1)+c.start(2),row.start(1)+c.end(2)))
        if len(found)>1:raise ValueError(f'Dubbele rij voor {key}; eerst reviewen')
        if found:
            i,a,b=found[0];blocks[i]=blocks[i][:a]+replacement+blocks[i][b:]
            continue
        row=f"<tr><th>{escape(f['label'])}</th><td>{replacement}</td></tr>"
        want=bool(f.get('verborgen'))
        if want not in hidden:extra+=row;continue
        i=hidden.index(want);block=blocks[i]
        pos=block.rfind('</tbody>')
        if pos<0:pos=block.rfind('</table>')
        if pos<0:raise ValueError('Geen tabel gevonden in kenmerkenblok')
        blocks[i]=block[:pos]+row+block[pos:]
    # A hidden field without a hidden block gets one directly after the last block.
    if extra:blocks[-1]+=conf.details_macro(cat.schema,extra,hidden=True)
    for (s,e),block in reversed(list(zip(spans,blocks))):storage=storage[:s]+block+storage[e:]
    return storage


def make_plan(cat,backend,cfg,request):
    if not isinstance(request,dict):raise ValueError('Verzoek moet een object zijn')
    kind=request.get('kind');snapshot=backend.collect();data=datasets(cat,snapshot)
    issues={i['key']:i for i in data['initiatives']};key=request.get('key')
    observed={};actions=[];questions=[];notes=[]
    def observe(typ,ident):
        if not re.fullmatch(r'[A-Z][A-Z0-9_]*-\d+' if typ=='issue' else r'\d+',str(ident)):raise ValueError('Ongeldige objectkey')
        obj=backend.get(typ,str(ident))
        if obj is None:raise ValueError(f'{typ} {ident} niet gevonden')
        observed[typ+':'+str(ident)]={'kind':typ,'key':str(ident),'revision':revision(obj),'before':obj}
        return obj
    def action(typ,scope,payload,key=None):
        actions.append({'id':str(len(actions)+1),'kind':typ,'scope':scope,'key':key,'payload':payload})
        return actions[-1]['id']
    def page_for(ai):
        pages=[p for p in snapshot['pages'] if p.get('ai_key')==ai]
        if len(pages)!=1:raise ValueError(f'{ai}: verwacht één pagina, vond {len(pages)}')
        return observe('page',pages[0]['page_id'])
    def project_page_for(ai,project):
        home=[p for p in snapshot['pages'] if p.get('ai_key')==ai]
        if len(home)!=1:raise ValueError(f'{ai}: verwacht één pagina, vond {len(home)}')
        hits=[c for c in home[0].get('children',[]) if c.get('project_page')==project]
        if len(hits)!=1:raise ValueError(f'Projectpagina {project} niet eenduidig gevonden ({len(hits)}); maak ze eerst met project-page of geef parent_id op')
        return observe('page',hits[0]['page_id'])
    def update_page(p,body):
        if body==p['body']['storage']['value']:notes.append('Geen inhoudelijke wijziging aan de pagina.');return
        action('page.update',p['space']['key'],{'type':'page','title':p['title'],'version':{'number':p['version']['number']+1},'body':{'storage':{'value':body,'representation':'storage'}}},str(p['id']))
    def create_page(parent,title,body,labels):
        p=observe('page',str(parent));space=p['space']['key']
        if backend.title_exists(space,title):raise ValueError('Een pagina met deze titel bestaat al; geen duplicaat aangemaakt')
        return action('page.create',space,{'type':'page','title':title,'space':{'key':space},'ancestors':[{'id':str(parent)}],
               'body':{'storage':{'value':body,'representation':'storage'}},'metadata':{'labels':[{'prefix':'global','name':l} for l in labels]}})
    if kind in ('details','transition','initiative-page','people'):
        if key not in issues:raise ValueError('Onbekend AI-initiatief')
        observe('issue',key)
    if kind=='details':
        values=request.get('values',{})
        if not values:raise ValueError('Geen wijzigingen opgegeven')
        if 'ai_key' in values and values['ai_key']!=key:raise ValueError('Identiteit niet wijzigen via kenmerken')
        p=page_for(key);update_page(p,patch_details(cat,p['body']['storage']['value'],values))
    elif kind=='label':
        p=observe('page',str(request.get('page_id','')));label=request.get('label')
        if label not in set(cat.schema['artefact_labels'])|{cat.schema['label']}:raise ValueError('Onbekend label; eerst catalogusuitbreiding voorstellen')
        existing=set(conf._labels(p))&set(cat.schema['artefact_labels'])
        if label in cat.schema['artefact_labels'] and existing-{label}:raise ValueError('Een ander artefactlabel bestaat al; niet een tweede toevoegen')
        if label not in conf._labels(p):action('page.label',p['space']['key'],[{'prefix':'global','name':label}],str(p['id']))
    elif kind=='new-initiative':
        title=request.get('title','').strip();description=request.get('description','').strip()
        if not title or not description:raise ValueError('Titel en beschrijving vereist')
        if backend.search_duplicate(title):raise ValueError('Mogelijk dubbel initiatief: dezelfde titel bestaat')
        fields={'project':{'key':cfg['atlassian']['jira_project']},'issuetype':{'name':'Initiative'},'summary':title,'description':description}
        if request.get('received'):fields['customfield_14415']=request['received']
        action('issue.create',cfg['atlassian']['jira_project'],{'fields':fields})
        notes.append('Na aanmaak: met de verkregen AI-key een afzonderlijk voorstel voor initiatiefpagina en eventuele EAG-link. Geen lege artefactpagina’s.')
    elif kind=='initiative-page':
        if any(p.get('ai_key')==key for p in snapshot['pages']):raise ValueError('Initiatief heeft al een kandidaatpagina; eerst reviewen')
        values=dict(request.get('values',{}),ai_key=key)
        vals,problems=sch.normalize_values(cat.schema,values)
        if problems:raise ValueError('; '.join(problems))
        if not request.get('summary'):raise ValueError('Korte probleemomschrijving vereist')
        body=conf.render_page(cat.schema,vals,request['summary'],cfg)
        if not cfg['atlassian'].get('jira_server_id'):raise ValueError('Jira serverId vereist')
        create_page(request['parent_id'],f"[{key}] {issues[key]['summary']}",body,[cat.schema['label']])
    elif kind=='people':
        # Jira-rollen: assignee = werkverdeling, Verantwoordelijke = inhoudelijk verantwoordelijke.
        raw=observe('issue',key)['fields']
        roles={'assignee':'assignee','verantwoordelijke':jira.VERANTWOORDELIJKE,'trekker':jira.TREKKER}
        wanted={roles[r]:u for r,u in request.items() if r in roles and u}
        if not wanted:raise ValueError('Geen persoon opgegeven (assignee, verantwoordelijke of trekker)')
        for u in wanted.values():
            if not backend.user_active(u):raise ValueError(f'Onbekende of inactieve Jira-gebruiker: {u}')
        fields={f:{'name':u} for f,u in wanted.items() if (raw.get(f) or {}).get('name')!=u}
        if fields:action('issue.update',key.split('-')[0],{'fields':fields},key)
        else:notes.append('Personen staan al zo in Jira.')
    elif kind=='project-page':
        project=next((p for p in data['projects'] if p['key']==key),None)
        if not project:raise ValueError('Onbekend project; link het POR-ticket eerst aan een initiatief')
        if len(project['initiatives'])!=1:raise ValueError('Project hangt niet aan precies één initiatief; eerst reviewen')
        if project.get('page_id'):raise ValueError('Projectpagina bestaat al')
        if not cfg['atlassian'].get('jira_server_id'):raise ValueError('Jira serverId vereist')
        home=page_for(project['initiatives'][0]);observe('issue',key)
        body=('<h2>Stand van zaken</h2><p>'+conf._jira_macro(cfg['atlassian'],f'key = {key} OR issue in linkedIssues({key})')+'</p>'
              '<h2>Artefacten</h2><p>'+conf._artefacts_macro(cat.schema,['decisions'])+'</p>')
        create_page(home['id'],f"{key} - {project['summary']}",body,[])
    elif kind=='link':
        key=request['key'];other=request['other'];a=observe('issue',key);observe('issue',other)
        if not key.startswith(cfg['atlassian']['jira_project']+'-') or not other.startswith(cfg['atlassian']['eag_project']+'-'):raise ValueError('Deze actie ondersteunt alleen AI → EAG Gerelateerd')
        if not any(l['key']==other and l['type']=='Gerelateerd' for l in __import__('aiec_lib.jira',fromlist=['_links'])._links(a)):
            action('issue.link',key.split('-')[0],{'type':{'name':'Gerelateerd'},'inwardIssue':{'key':key},'outwardIssue':{'key':other}},key)
    elif kind=='transition':
        target=cat.state(request.get('to'));gate=cat.process.get('gates',{}).get(target,{})
        if not target:raise ValueError('Doelfase is onbekend')
        if issues[key]['phase']==target:raise ValueError('Initiatief staat al in die fase')
        p=page_for(key)
        # Pin every deliverable used in checking a gate, including its human-edited body.
        for root in snapshot['pages']:
            if root['ai_key']==key:
                for child in root['children']:observe('page',child['page_id'])
        # The decision is an artefact (report section or decision page), not free text in the request.
        if not decided(cat,issues[key],target):questions.append(decision_question(cat,target))
        if not gate.get('defined'):questions.append(gate.get('question','Deze faseovergang is nog niet beschreven.'))
        # Initiative artefacts hang directly under the initiative; project artefacts under their project page.
        own={l for a in data['artifacts'] if a['initiative']==key and not a.get('project') for l in a.get('labels',[])}
        per_project={p['key']:set(p['artifact_labels']) for p in data['projects'] if key in p['initiatives']}
        for x in gate.get('project_artifacts',[]):
            questions += [f'Gate-artefact ontbreekt voor project {pk}: {x}' for pk,labels in sorted(per_project.items()) if x not in labels]
        # With exactly one project, its artefact also counts for the initiative.
        single=next(iter(per_project.values())) if len(per_project)==1 else set()
        needed=[x for x in gate.get('artifacts',[]) if x not in own and not (x in gate.get('project_artifacts',[]) and x in single)]
        questions += ['Gate-artefact ontbreekt: '+x for x in needed]
        future=__import__('copy').deepcopy(snapshot)
        for i in future['issues']:
            if i['key']==key:i['status_raw']=target
        questions += [x['message'] for x in review(cat,future) if x['key']==key and x['severity']=='error']
        if target=='Afgesloten':questions.append('Bevestig de Jira-resolution en afsluitcategorie; deze mapping is nog open. Afsluiten wordt nog niet uitgevoerd.')
        options=[t for t in backend.transitions(key) if cat.state(t.get('to',{}).get('name'))==target]
        if len(options)!=1:questions.append('Geen eenduidige beschikbare Jira-transitie naar deze fase.')
        if questions:notes.append('Geen statuswijziging uitvoerbaar zolang deze vragen openstaan.')
        else:
            required=[k for k,v in options[0].get('fields',{}).items() if v.get('required')]
            if required:questions.append('Jira-transitiescherm vraagt extra velden: '+', '.join(required))
            else:action('issue.transition',key.split('-')[0],{'transition':{'id':options[0]['id']}},key)
        notes.append('EAG/POR/PROD worden niet stilzwijgend mee gewijzigd. Afwijkingen en benodigde vervolgacties blijven reviewpunten.')
    elif kind=='report':
        result=render(cat,snapshot,request['report'],request.get('target'),request.get('period'),request.get('inputs'),cfg,request.get('slug'),request.get('tracking'))
        if result['scope']=='portfolio':raise ValueError('Portfoliorapport is een lokaal concept; geen publicatie naar Confluence in deze release')
        questions += [x['question'] for x in result['questions']]
        notes += result.get('notes',[])
        for page in (result.get('history_guard') or {}).get('pages',[]):
            current=observe('page',page['page_id'])
            if revision(current)!=page['revision']:raise ValueError('Rapporthistoriek is tijdens het voorstellen gewijzigd; opnieuw verzamelen')
        if not questions:
            if request.get('parent_id'):parent=observe('page',str(request['parent_id']))
            elif result['scope']=='project':parent=project_page_for(result['initiative'],result['target'])
            elif result['parent_title']:
                home=[p for p in snapshot['pages'] if p.get('ai_key')==result['initiative']]
                if len(home)!=1:raise ValueError(f"{result['initiative']}: verwacht één pagina, vond {len(home)}")
                hits=[c for c in home[0].get('children',[]) if c['title']==result['parent_title']]
                if len(hits)!=1:raise ValueError(f"Ouderpagina '{result['parent_title']}' niet eenduidig gevonden ({len(hits)}); maak ze eerst of geef parent_id op")
                parent=observe('page',hits[0]['page_id'])
            else:parent=page_for(result['initiative'])
            created=create_page(parent['id'],result['title'],result['storage'],[result['label']])
            for asset in result.get('assets',[]):
                payload={k:v for k,v in asset.items() if k!='kind'}
                payload['page_action']=created
                action('page.attachment',parent['space']['key'],payload)
            observe('issue',result['initiative'])
            if result['scope']=='project':observe('issue',result['target'])
        notes.append('Rapport wordt als nieuwe momentopname gemaakt, niet over een bestaand rapport heen geschreven.')
    else:raise ValueError('Onbekende verzoeksoort: '+str(kind))
    # Scope guard checks actual objects, not just the caller's claimed scope.
    allowed={cfg['atlassian']['space'],cfg['writes']['test_space']}
    for op in actions:
        if op['kind'].startswith('page.') and op['scope'] not in allowed:raise ValueError('Pagina buiten toegestane space')
        if op['kind'].startswith('issue.') and op['scope'] not in {cfg['atlassian']['jira_project'],cfg['atlassian']['eag_project']}:raise ValueError('Ticket buiten toegestane projecten')
    plan={'version':2,'id':str(uuid4()),'created_at':now(),'expires_at':(datetime.now(timezone.utc)+timedelta(hours=24)).isoformat(),
          'catalog_hash':cat.fingerprint,'config_hash':digest(cfg),'source':backend.identity,'request':request,
          'preconditions':list(observed.values()),'actions':actions,'questions':list(dict.fromkeys(questions)),'notes':notes}
    if kind=='report':
        plan['preview_html']=result.get('html')
        plan['report_markdown']=result['markdown']
        plan['history_guard']=result.get('history_guard')
    plan['hash']=digest(plan)
    return plan


def plan_markdown(plan):
    lines=['# Wijzigingsvoorstel',f"ID: `{plan['id']}`",f"SHA-256: `{plan['hash']}`",'', 'Er is nog niets uitgevoerd.','']
    if plan['questions']:lines+=['## Eerst beantwoorden']+['- '+q for q in plan['questions']]+['']
    if plan.get('report_markdown'):lines+=['## Rapport ter beoordeling','',plan['report_markdown'],'']
    for a in plan['actions']:
        payload=dict(a['payload']) if isinstance(a['payload'],dict) else a['payload']
        if a['kind']=='page.attachment':payload['content_base64']='[Exacte PNG-bytes in het JSON-voorstel; beoordeel de bijbehorende HTML-preview. SHA-256 hierboven.]'
        lines += [f"## {a['id']}. {a['kind']} · {a.get('key') or 'nieuw'}",f"Scope: {a['scope']}",'```json',__import__('json').dumps(payload,ensure_ascii=False,indent=2),'```','']
        if a['kind']=='page.update':
            before=next(p['before']['body']['storage']['value'] for p in plan['preconditions'] if p['kind']=='page' and p['key']==a['key'])
            after=a['payload']['body']['storage']['value']
            lines+=['```diff',*list(difflib.unified_diff(before.replace('><','>\n<').splitlines(),after.replace('><','>\n<').splitlines(),fromfile='voor',tofile='na',lineterm='')),'```']
    lines+=['## Opmerkingen']+['- '+n for n in plan['notes']]
    return '\n'.join(lines)+'\n'
