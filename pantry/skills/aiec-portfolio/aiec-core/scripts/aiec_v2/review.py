"""Review is a pure calculation over a dated snapshot; it never repairs data."""
from __future__ import annotations
from collections import Counter
from datetime import date, timedelta
import re
from aiec_lib import confluence as conf, schema as sch
from .catalog import matches


def day(value):
    try: return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError): return None


def previous_period(today, quarterly=False):
    if quarterly:
        q = (today.month-1)//3
        return f'{today.year if q else today.year-1}-Q{q if q else 4}'
    return (today.replace(day=1)-timedelta(days=1)).strftime('%Y-%m')


def in_period(title, period, kind):
    """Hoort een rapporttitel bij deze periode? Oude titels dragen de periode letterlijk
    ('— 2026-08'), nieuwe beginnen met datum en type ('2026-08-31 - vooruitgang - por-1')."""
    if not re.match(r'\d{4}-\d{2}-\d{2} - ', title):
        return period in title
    m = re.match(r'(\d{4})-(\d{2})-\d{2} - '+re.escape(kind)+' - ', title)
    if not m:
        return False
    year, month = int(m.group(1)), int(m.group(2))
    return period == (f'{year}-Q{(month-1)//3+1}' if 'Q' in period else f'{year}-{month:02d}')


def decided(cat, row, target):
    """Is the decision for the transition to target recorded where the gate says it lives?"""
    where = cat.process.get('gates', {}).get(target, {}).get('decision_in')
    if not where:
        return True
    if where == 'decisions':
        return target in row.get('decision_transitions', [])
    return where in row.get('own_labels', [])


def decision_question(cat, target):
    where = cat.process['gates'][target]['decision_in']
    if where == 'decisions':
        return f"Beslissing voor overgang naar {target} ontbreekt: maak een beslissing met 'Overgang naar' {target}."
    return f'Beslissing voor overgang naar {target} ontbreekt: die hoort in de sectie Beslissing van het {where}.'


def datasets(cat, snapshot, today=None):
    today = today or date.today()
    pages = snapshot.get('pages', [])
    grouped = {}
    for p in pages: grouped.setdefault(p.get('ai_key'), []).append(p)
    artifacts = []
    for p in pages:
        for a in p.get('children', []):
            artifacts.append(dict(a, initiative=p.get('ai_key'), key=a.get('page_id')))
    projects = []
    for p in snapshot.get('projects', []):
        r = dict(p)
        # Project artefacts hang under the project page; older reports only carry the key in their title.
        mine = [a for a in artifacts if a.get('initiative') in p.get('initiatives', []) and (a.get('project') == p['key'] or
                (not a.get('project') and re.search(r'(?<![A-Z0-9-])'+re.escape(p['key'])+r'(?![0-9])', a.get('title',''), re.I)))]
        r['previous_report'] = any('vooruitgangsrapport' in a.get('labels', []) and
            in_period(a.get('title',''), previous_period(today), 'vooruitgang') for a in mine)
        r['artifact_labels'] = sorted({l for a in artifacts if a.get('project') == p['key'] for l in a.get('labels', [])})
        r['page_id'] = next((a['page_id'] for a in artifacts if a.get('project_page') == p['key']), None)
        projects.append(r)
    initiatives = []
    for issue in snapshot.get('issues', []):
        candidates = grouped.get(issue['key'], [])
        p = candidates[0] if len(candidates)==1 else {}
        values = p.get('details') or {}
        r = dict(values)
        r.update(issue)
        r.update({'phase': cat.state(issue.get('status_raw') or issue.get('status')),
                  'page_id':p.get('page_id'), 'page_count':len(candidates),
                  'project_keys':[x['key'] for x in projects if issue['key'] in x.get('initiatives', [])],
                  'artifact_labels':sorted({l for a in artifacts if a['initiative']==issue['key'] for l in a.get('labels',[])}),
                  'own_labels':sorted({l for a in artifacts if a['initiative']==issue['key'] and not a.get('project') for l in a.get('labels',[])}),
                  'decision_transitions':sorted({d['overgang'] for d in p.get('decisions',[]) if d.get('overgang')})})
        # DPIA and DPO judgements live in the analysis report's properties block.
        analysis=[conf.parse_properties(cat.schema,a.get('storage',''),'aiec-analyse') for a in artifacts
                  if a['initiative']==issue['key'] and not a.get('project') and 'analyserapport' in a.get('labels',[])]
        r['dpia_oordeel']=next((x['DPIA'] for x in analysis if x.get('DPIA')),None)
        r['dpo_oordeel']=next((x['DPO'] for x in analysis if x.get('DPO')),None)
        dates = [d for d in [day(issue.get('updated')),day(p.get('last_activity'))] if d]
        r['inactive_days'] = (today-max(dates)).days if dates else None
        r['previous_report'] = any(a['initiative']==issue['key'] and 'vooruitgangsrapport' in a.get('labels',[]) and in_period(a.get('title',''), previous_period(today,True), 'gebruik') for a in artifacts)
        h = snapshot.get('hours',{}).get('per_initiative',{}).get(issue['key'], {})
        total, direct = h.get('period_h'), h.get('direct_h')
        r['direct_hours_share'] = direct/total if isinstance(total,(float,int)) and total>0 and isinstance(direct,(float,int)) else None
        # A claim without its assumption must not propagate into a report.
        if not r.get('aanname'): r['batenclaim'] = ''
        initiatives.append(r)
    return {'initiatives':initiatives,'projects':projects,'products':snapshot.get('products',[]),'artifacts':artifacts}


def review(cat, snapshot, today=None):
    today = today or date.today()
    data = datasets(cat,snapshot,today)
    findings = []
    def add(rule,severity,key,message,action,page_id=None):
        findings.append({'rule':rule,'severity':severity,'key':key,'page_id':page_id,'message':message,'action':action})
    for r in cat.rules.values():
        for row in data.get(r['scope'],[]):
            if matches(r.get('when'),row): add(r['id'],r['severity'],row.get('key'),r['message'],r['action'],row.get('page_id'))
    issues = {i['key']:i for i in data['initiatives']}
    keys = Counter(i['key'] for i in snapshot.get('issues',[]))
    for key,n in keys.items():
        if n>1:add('dubbel-ticket','error',key,'Dubbele Jira-key in brondata.','Controleer de verzameling.')
    for i in data['initiatives']:
        if i['page_count']!=1:
            add('pagina-koppeling','error',i['key'],f"{i['page_count']} initiatiefpagina’s gevonden; verwacht één.",'Bespreek aanmaak of samenvoeging; verwijder niets automatisch.')
        if i['phase'] is None:add('onbekende-status','warning',i['key'],'Jira-status ontbreekt in de procesmapping.','Laat de mapping bevestigen; leid geen fase af.')
    for p in snapshot.get('pages',[]):
        key=p.get('ai_key');i=issues.get(key,{})
        def emit(rule,severity,message,action):add(rule,severity,key,message,action,p.get('page_id'))
        if not i:emit('weespagina','error','Geen bijbehorend Jira-initiatief gevonden.','Controleer de key en de brondekking.')
        if cat.schema['label'] not in p.get('labels',[]):emit('registerlabel','warning','Label ai-initiatief ontbreekt.','Stel het label voor; laat de koppeling bevestigen.')
        if not p.get('has_details'):emit('details-ontbreekt','error','Geen herkenbaar kenmerkenblok.','Bereid toevoeging van het blok voor; behoud bestaande inhoud.')
        vals=p.get('details') or {}
        phase=i.get('phase');rank=cat.rank(phase)
        # Unknown fields and parser problems remain visible. Never erase them during a render.
        for problem in p.get('details_problems',[]):emit('structuur','warning',problem,'Neem dit op in de review; schemawijziging is een apart voorstel.')
        for f in cat.schema['fields']:
            raw=vals.get(f['key'])
            _,problem=sch.normalize_value(cat.schema,f,raw)
            if problem:emit('waarde','error',problem,'Vraag de bedoelde waarde; kies niet zelf een alternatief.')
            if sch.is_filled(raw):continue
            if f['key']=='eag_key':continue  # dedicated linkage rule; exceptions belong in review
            ctx={'values':vals,'soort':vals.get('soort'),'fase':rank,'status':phase,'resolution':i.get('resolution')}
            # Captation fields are due at entry into Analyse, not on first registration.
            required = (matches(f['required_when_v2'],i) if 'required_when_v2' in f else
                        sch.required_now(cat.schema,f,ctx) and (rank>=1 or f['key'] in ('ai_key','soort')))
            if f['key']=='stopreden' and phase=='Afgesloten':
                required = not bool(vals.get('opgeleverd'))  # no guessed resolution mapping
            if required:emit('verplicht-veld','error',f"{f['label']} ontbreekt.",'Vraag de inhoudelijk verantwoordelijke om aanvulling.')
            elif f.get('notice_when_v2') and matches(f['notice_when_v2'],i):emit('aan-te-vullen','info',f"{f['label']} is nog onbekend.",'Aanvullen tijdens Analyse; Other is geen vervanging voor onbekend.')
        links=i.get('eag_keys',[])
        if vals.get('soort')=='afgebakend' and not vals.get('eag_key') and not links:
            emit('geen-demand','warning','Geen EAG-verwijzing gevonden.','Leg de uitzondering aan Kenzo voor.')
        if vals.get('eag_key') and vals['eag_key'] not in links:
            emit('demand-mismatch','warning','EAG-veld en Jira-link stemmen niet overeen.','Laat de juiste demand bevestigen.')
        if vals.get('batenclaim') and not vals.get('aanname'):emit('claim-zonder-aanname','error','Batenclaim zonder aanname.','Niet citeren; vraag Kenzo om de aanname.')
        if vals.get('soort')=='doorlopend' and (phase not in ('Uitvoering',None) or vals.get('stopreden') or 'captatierapport' in i.get('artifact_labels',[])):
            emit('doorlopend-in-funnel','info','Doorlopende werking lijkt als eindig initiatief behandeld.','Bespreek soort en plaats in de werking.')
        expected=f"[{key}] {i.get('summary','')}"
        if i and p.get('title')!=expected:emit('titel','info','Paginatitel wijkt af van Jira-key of summary.','Stel een titelcorrectie voor.')
        pages_per_project=Counter(c['project_page'] for c in p.get('children',[]) if c.get('project_page'))
        for project,n in pages_per_project.items():
            if n>1:emit('projectpagina','warning',f'{n} projectpagina’s voor {project}.','Bespreek samenvoegen; verwijder niets automatisch.')
            if project not in i.get('project_keys',[]):emit('projectpagina','warning',f'Projectpagina {project} hoort niet bij een gelinkt project van {key}.','Link het project in Jira of verplaats de pagina.')
        for child in p.get('children',[]):
            if child.get('project_page'):continue
            labels=set(child.get('labels',[]))&set(cat.schema['artefact_labels'])
            if len(labels)!=1:emit('artefactlabel','warning',f"{child.get('title')}: {len(labels)} artefactlabels.",'Stel classificatie voor en bespreek die; geen automatische herlabeling.')
            if 'vooruitgangsrapport' in labels:
                title=child.get('title','')
                if not re.search(r'\b\d{4}-(?:0[1-9]|1[0-2]|Q[1-4])\b',title):
                    emit('rapportperiode','warning',f'{title}: geen geldige periode in titel.','Bevestig periode vóór titelcorrectie.')
                if not child.get('project') and re.search(r'\b\d{4}-(?:0[1-9]|1[0-2])\b',title) and len(i.get('project_keys',[]))>1 and not any(k.lower() in title.lower() for k in i['project_keys']):
                    emit('rapport-project','warning',f'{title}: onduidelijk voor welk project.','Laat de projectkoppeling bevestigen. Dit rapport telt niet stilzwijgend voor alle projecten.')
        # Every passed transition needs its decision. An early-closed initiative only needs the closing decision.
        rank=cat.rank(phase)
        for gate,spec in cat.process.get('gates',{}).items():
            passed = gate=='Afgesloten' if phase=='Afgesloten' else 0<cat.rank(gate)<=rank
            if spec.get('decision_in') and passed and i and not decided(cat,i,gate):
                emit('beslissing-ontbreekt','warning',decision_question(cat,gate),'Leg de beslissing vast; leid ze niet af.')
        for d in p.get('decisions',[]):
            if not d.get('overgang'):emit('beslissing-zonder-overgang','info',f"{d['title']}: geen 'Overgang naar' in het eigenschappenblok.",'Vul de overgang aan of neem de beslissing op in het juiste rapport.')
    # Templates we mirror but do not own: flag drift instead of silently diverging.
    from .templates import fingerprint
    for rid,spec in sorted(cat.reports.items()):
        tpl=spec.get('sjabloon')
        if not tpl:continue
        live=snapshot.get('templates',{}).get(str(tpl['page_id']))
        if live is None:
            add('sjabloon-niet-gelezen','warning',None,f"{tpl.get('omschrijving',rid)} (pagina {tpl['page_id']}) niet gelezen.",'Controleer leesrechten; de synchronisatie met rapport '+rid+' is niet nagekeken.')
            continue
        now_fp=fingerprint(live['storage'],tpl['deel'])
        if now_fp!=tpl['vingerafdruk']:
            add('sjabloon-uit-sync','warning',None,f"{tpl.get('omschrijving',rid)} (versie {live.get('version')}) wijkt af van rapport {rid}: vingerafdruk {now_fp} i.p.v. {tpl['vingerafdruk']}.",
                f'Vergelijk het sjabloon met {rid}.yaml, werk de secties bij en neem daarna de nieuwe vingerafdruk over.')
    for warning in snapshot.get('gaps',[]):add('brondekking','warning',None,warning,'Vul de bron of koppeling aan; ontbrekende gegevens zijn geen nul.')
    return sorted(findings,key=lambda x:({'error':0,'warning':1,'info':2}[x['severity']],str(x['key']),x['rule']))


def markdown(findings):
    lines=['# Portfolioreview','', 'Dit is een voorstel voor bespreking. Er is niets gewijzigd.','']
    for f in findings:
        lines += [f"## {f['key'] or 'Bronnen'} · {f['severity']} · {f['rule']}",f['message'],f"Actie: {f['action']}",'']
    if not findings:lines.append('Geen afwijkingen gevonden binnen de gelezen bronnen en ingestelde regels.')
    return '\n'.join(lines)+'\n'
