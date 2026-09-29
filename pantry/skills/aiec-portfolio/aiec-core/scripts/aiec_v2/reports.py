"""Generic report definitions: code provides facts, people provide judgments."""
from __future__ import annotations
from copy import deepcopy
from datetime import date
from html import escape
import re
import unicodedata
from .catalog import get, matches, placeholders
from .review import datasets, review
from . import periods
from aiec_lib.confluence import _cell_text, _jira_macro, details_macro
from .report_inputs import INPUT_KINDS, render_input, choice_text
from .form_files import font_faces


def preview_html(title, period, body, fixture=False, fonts=''):
    style=fonts+''':root{--grey-100:#f7f9fc;--grey-300:#cfd5dd;--grey-1000:#333332;--text-subtle:rgba(0,20,46,.6);--accent:#447a6d;--primary:#ffed00;--warning-100:#fff9e8;--warning-400:#ffe49c;--warning-800:#9f5804}*{box-sizing:border-box}body{margin:0;background:#fff;color:var(--grey-1000);font:18px/1.5 "Flanders Art Sans",sans-serif;-webkit-font-smoothing:antialiased}header{border-bottom:6px solid var(--primary)}header>div,main{max-width:1200px;margin:auto;padding:20px 30px}main{padding-bottom:60px}h1{font-size:32px;line-height:1.24;font-weight:500;margin:5px 0 0}h2{font-size:26px;line-height:1.3;font-weight:500;margin:40px 0 15px}h3,h4{font-size:22px;font-weight:500;margin:30px 0 10px}p{margin:0 0 15px}table{display:block;width:100%;overflow-x:auto;border-collapse:collapse;margin:15px 0;font-size:16px}th,td{padding:10px 12px;border-bottom:1px solid var(--grey-300);text-align:left;vertical-align:top}thead th{background:var(--grey-100);font-weight:500}.properties{display:table;width:auto;min-width:min(100%,560px);border:1px solid var(--grey-300);border-radius:3px}.properties th{width:220px;background:var(--grey-100);font-weight:500}.properties td{font-size:18px}aside{padding:15px 20px;background:var(--warning-100);border:1px solid var(--warning-400);border-radius:3px;margin:20px 0}aside strong{color:var(--warning-800)}.report-charts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}figure{margin:10px 0;border:1px solid var(--grey-300);border-radius:3px;overflow:hidden}figure img{display:block;width:100%;height:auto}figcaption{padding:8px 15px;color:var(--text-subtle);font-size:16px}em{color:var(--text-subtle);font-size:16px;font-style:normal}details{margin:30px 0 0;border-top:1px solid var(--grey-300);padding-top:15px}summary{cursor:pointer;font-weight:500}p,li{overflow-wrap:anywhere}.eyebrow{color:var(--accent);font-size:16px;font-weight:500}@media(max-width:900px){.report-charts{grid-template-columns:1fr}}@media(max-width:600px){header>div,main{padding:15px 16px}h1{font-size:26px}body{font-size:16px}}'''
    label='AIEC · Fictieve voorbeelddata · Concept' if fixture else 'AIEC · Concept ter goedkeuring'
    return '<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+escape(title)+'</title><style>'+style+'</style></head><body><header><div><div class="eyebrow">'+label+' · '+escape(period)+'</div><h1>'+escape(title)+'</h1></div></header><main>'+body+'</main></body></html>'


def title_date(spec, period, today=None):
    """Default datum in de paginatitel: laatste dag van de periode bij periodieke rapporten,
    anders de dag van aanmaak. Een invoer 'datum' gaat altijd voor."""
    if spec.get('cadence'):return periods.last_day(period).isoformat()
    return (today or date.today()).isoformat()


def slugify(text):
    """'Advies - Gezond uit eigen grond' -> 'advies-gezond-uit-eigen-grond'."""
    plain=unicodedata.normalize('NFKD',text or '').encode('ascii','ignore').decode()
    return '-'.join(re.findall(r'[a-z0-9]+',plain.lower()))


def cell(value):
    if value is None: return 'onbekend'
    if isinstance(value,list): value=', '.join(str(v) for v in value)
    return str(value).replace('|','\\|').replace('\n','<br>')


def linked_page(cat, data, report_id, target, initiative):
    """Newest page of a project report for this project, found by label and title pattern; None without one."""
    linked=cat.reports[report_id]
    parts=re.split(r'\{(\w+)\}',linked['page_title'])
    # The title carries the project's title key: the POR key, or 'intern' for an internal project.
    title_key=next((p.get('title_key') or p['key'] for p in data['projects'] if p['key']==target),target)
    forms={'datum':r'\d{4}-\d{2}-\d{2}','project':re.escape(title_key),'slug':r'[a-z0-9]+(?:-[a-z0-9]+)*'}
    pattern=''.join(forms[p] if i%2 else re.escape(p) for i,p in enumerate(parts))
    # Under a project page only that project's pages count: several internal projects share the title key.
    hits=sorted(a['title'] for a in data['artifacts'] if a.get('initiative')==initiative and a.get('project') in (None,target) and linked.get('label') in a.get('labels',[]) and re.fullmatch(pattern,a.get('title','')))
    return hits[-1] if hits else None


def render(cat, snapshot, report_id, target=None, period=None, inputs=None, cfg=None, slug=None, tracking=None):
    spec=cat.reports[report_id]
    inputs={} if inputs is None else inputs
    if not isinstance(inputs,dict):raise ValueError('Rapportinvoer moet een object met secties zijn')
    allowed={s['id'] for s in spec['sections'] if s['kind'] in INPUT_KINDS}
    if set(inputs)-allowed:raise ValueError('Onbekende invoersectie: '+', '.join(set(inputs)-allowed))
    scope=spec['scope']
    if scope!='portfolio' and not target:raise ValueError('Rapport vraagt een initiatief- of projectkey')
    if not period:raise ValueError('Periode vereist: JJJJ-MM, JJJJ-Qn, JJJJ-Hn of JJJJ')
    periods.parse(period)
    if spec.get('cadence')=='monthly' and periods.parse(period)[2]!=1:raise ValueError('Maandrapport vraagt JJJJ-MM')
    # A usage report covers the initiative's reporting period: quarter, half year or year.
    if spec.get('cadence')=='periodic' and periods.parse(period)[2]==1:raise ValueError('Gebruiksrapport vraagt JJJJ-Qn, JJJJ-Hn of JJJJ')
    data=datasets(cat,snapshot);data['findings']=review(cat,snapshot)
    initiative=target if scope=='initiative' else None;intern=False
    if scope=='project':
        candidates=[p for p in data['projects'] if p['key']==target]
        if len(candidates)!=1:raise ValueError('Project ontbreekt of is dubbel')
        keys=candidates[0].get('initiatives',[]);project_summary=candidates[0].get('summary')
        title_key=candidates[0].get('title_key') or target;intern=candidates[0].get('type')=='intern'
        if len(keys)!=1:raise ValueError('Project heeft geen eenduidige initiatiefkoppeling; eerst reviewen')
        initiative=keys[0]
    if initiative and len([i for i in data['initiatives'] if i['key']==initiative])!=1:raise ValueError('Initiatief ontbreekt of is dubbel')
    title=f"{('['+initiative+'] ') if initiative else ''}{spec['title']}{(' — '+target) if scope=='project' else ''} — {period}"
    title_questions=[]
    if 'page_title' in spec:
        # Explicit title parts only: datum from the human input or derived, slug proposed by the agent and approved with the plan.
        parts={}
        if 'datum' in placeholders(spec['page_title']):
            datum=(inputs.get('datum') or '').strip()
            if datum and not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])',datum):raise ValueError('Datum voor de paginatitel moet JJJJ-MM-DD zijn')
            parts['datum']=datum or title_date(spec,period)
        if 'project' in placeholders(spec['page_title']):
            parts['project']=title_key
            # Default slug from the Jira summary: visible in the proposal, overridable with slug.
            slug=slug or slugify(project_summary)
        if 'slug' in placeholders(spec['page_title']):
            if slug and not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*',slug):raise ValueError('Slug: enkel kleine letters, cijfers en enkelvoudige koppeltekens')
            if not slug:title_questions.append({'section':'slug','question':'Slug voor de paginatitel (kleine letters, cijfers, koppeltekens).'})
            parts['slug']=slug or ''
        if all(parts.values()):title=spec['page_title'].format_map(parts)
    prepared=None; assets=[]; chart_data=None; measurement=None
    final=None; final_questions=[]; final_notes=[]; guard=None; maintained=None
    working=inputs
    if spec.get('tracking'):
        from .tracking import prepare
        from . import report_charts, report_history
        # Validate raw input before deriving defaults; unknown/manual fields are never discarded.
        for section in spec['sections']:
            if section['kind'] in INPUT_KINDS:render_input(spec,section,inputs.get(section['id']))
        prepared=prepare(spec,snapshot,target,initiative,period,inputs,tracking)
        working=prepared['inputs']
        if prepared['state']:
            prepared['state']['title']=title
            chart_data,assets=report_charts.build(prepared['state'],prepared['history']['records'])
    elif tracking is not None:raise ValueError('Dit rapport ondersteunt geen meetinvoer')
    elif spec.get('tracking_source'):
        # The final report reads the last published measurement; it adds none of its own.
        from . import report_charts, report_history
        source=cat.reports[spec['tracking_source']['report']];sid=spec['tracking_source']['section']
        if 'report_pages' not in snapshot or 'meetstanden' not in snapshot:
            final_questions.append({'section':sid,'question':'Deze bronmomentopname mist rapporthistoriek of meetstanden; verzamel opnieuw met de huidige collector.'})
        else:
            history=report_history.load(source,snapshot,target,initiative)
            guard=report_history.guard(source,snapshot,target,initiative)
            if not history['records']:
                final_questions.append({'section':sid,'question':f'Nog geen {source["title"].lower()}srapport met meetstand voor {target}; publiceer eerst het laatste {source["title"].lower()}srapport.'})
            else:
                last=history['records'][-1]
                if period<last['period']:raise ValueError('Periode ligt vóór het laatste '+source['title'].lower()+'srapport ('+last['period']+')')
                # No projection: the planning of the last month is not part of the closed project.
                state=deepcopy(last);state['planning']=None;state['report']=report_id;state['closed']=True
                if last.get('legacy_ack'):final_notes.append('Oude rapporten zijn niet omgerekend: '+', '.join(last['legacy_ack']['pages'])+'. Afspraak meetstart: '+last['legacy_ack']['reason'])
                chart_data,assets=report_charts.build(state,history['records'][:-1])
                final={'state':state,'records':history['records']}
    elif spec.get('maintenance'):
        from . import maintenance
        for section in spec['sections']:
            if section['kind'] in INPUT_KINDS:render_input(spec,section,inputs.get(section['id']))
        datum=(inputs.get('datum') or '').strip() or title_date(spec,period)
        maintained=maintenance.prepare(cat,spec,snapshot,data,target,initiative,period,inputs,datum)
        final_questions+=maintained['questions'];final_notes+=maintained['notes'];guard=maintained['guard']
    md=[f'# {title}','','Concept ter goedkeuring. Bronmoment: '+snapshot.get('collected_at','onbekend')+'.','']
    body=[];preview_body=[];questions=list(title_questions)
    if prepared:questions+=prepared['questions']
    questions+=final_questions
    # A decision is self-contained; it needs no live ticket view.
    if initiative and spec.get('jira',True):
        if cfg:
            macro=_jira_macro(cfg['atlassian'],f'key in ({initiative}{", "+target if scope=="project" and not intern else ""})')
            if not macro:raise ValueError('Jira serverId ontbreekt; geen statische kopie als vervanging')
            body.append(macro)
        else:body.append('<p>Live Jira-verwijzing wordt bij publicatie toegevoegd.</p>')
    # A report with its own decision date needs no separate period line.
    if 'datum' not in {s['id'] for s in spec['sections']} and not spec.get('tracking_source') and not maintained:body.append(f'<p>Periode: {escape(period)}</p>')
    in_properties=set((spec.get('properties') or {}).get('sections',[]))
    if maintained:
        from .maintenance import DETAILS_ID, HIDDEN
        in_properties|=HIDDEN
        # Properties block: the interface for a later portfolio sum over active plans.
        rows=''.join(f'<tr><th>{escape(name)}</th><td>{value}</td></tr>' for name,value in maintained['rows'])
        plain=lambda v:re.sub(r'<ac:link>.*?<ac:link-body>(.*?)</ac:link-body></ac:link>',r'<strong>\1</strong>',v)
        body.append(details_macro(cat.schema,rows,hidden=True,details_id=DETAILS_ID))
        preview_body.append('<table class="properties"><tbody>'+''.join(f'<tr><th>{escape(n)}</th><td>{plain(v)}</td></tr>' for n,v in maintained['rows'])+'</tbody></table>')
        md+=[x for n,v in maintained['rows'] for x in (f'**{n}:** '+_cell_text(v),'')]
    measured_state=(prepared or {}).get('state') or (final or {}).get('state')
    headline_md=[]
    if spec.get('properties'):
        # Page Properties block: machine-readable for review and the Beslissingen overview.
        sections={s['id']:s for s in spec['sections']};rows=''
        for sid in spec['properties']['sections']:
            value=working.get(sid) or ''
            text=choice_text(spec,sections[sid],value) if sections[sid]['kind']=='choice' and value else str(value).strip()
            rows+=f"<tr><th>{escape(sections[sid]['title'])}</th><td>{escape(text).replace(chr(10),'<br/>')}</td></tr>"
        if measured_state:
            extra=report_charts.looptijd(measured_state) if final else []
            for name,value in report_charts.headline(measured_state)+extra:
                rows+=f"<tr><th>{escape(name)}</th><td>{escape(value)}</td></tr>";headline_md+=[f'**{name}:** {value}','']
        body.append(details_macro(cat.schema,rows,details_id=spec['properties']['id']))
        preview_body.append('<table class="properties"><tbody>'+rows+'</tbody></table>')
    current_group=None
    for section in spec['sections']:
        group=section.get('group')
        if group and group!=current_group:
            md+=[f'## {group}',''];body.append('<h2>'+escape(group)+'</h2>');preview_body.append('<h2>'+escape(group)+'</h2>')
        current_group=group
        if maintained and section['id'] in HIDDEN:
            # Consumed by the calculation: only its questions and the derived text appear.
            questions+=render_input(spec,section,working.get(section['id']))[2]
            if section['id'] in maintained['after']:
                extra_md,extra_storage=maintained['after'][section['id']]
                md+=extra_md;body.append(extra_storage);preview_body.append(extra_storage)
            continue
        # A section named after its group needs no second heading.
        same=group==section['title']
        if not same:md += [f"{'###' if group else '##'} {section['title']}",'']
        if section['kind']=='link':
            # A reference to the linked report's page, by its title pattern; no link without the page.
            linked=cat.reports[section['report']];hit=linked_page(cat,data,section['report'],target,initiative)
            tag='h3' if group else 'h2';lead=section['lead'].rstrip()+' '
            if hit:
                heading=f'<{tag}>'+escape(section['title'])+f'</{tag}>'
                body.append(heading+'<p>'+escape(lead)+'<ac:link><ri:page ri:content-title="'+escape(hit,quote=True)+'"/></ac:link></p>')
                preview_body.append(heading+'<p>'+escape(lead)+'<strong>'+escape(hit)+'</strong></p>');md+=[lead+hit,'']
            else:
                questions.append({'section':section['id'],'question':f"Er is nog geen {linked['title'].lower()} voor {target}; publiceer dat eerst, dit rapport verwijst ernaar."})
                md+=[f"**Nog te koppelen:** {linked['title'].lower()} van {target}.",'']
            continue
        if spec.get('tracking_source') and section['id']==spec['tracking_source']['section']:
            if final:
                final_md,final_storage,final_html=report_charts.final_fragments(final['state'],chart_data,assets)
                md[-2:-2]=final_md;body.append(final_storage);preview_body.append(final_html)
            else:
                message='Grafieken en milestones wachten op het laatste vooruitgangsrapport met meetstand.'
                md[-2:-2]=[message,''];preview_body.append('<p>'+message+'</p>')
        if section['kind'] in INPUT_KINDS:
            section_md,section_body,section_questions=render_input(spec,section,working.get(section['id']))
            if same and section_body.startswith('<h2>'):section_body=section_body.split('</h2>',1)[1]
            elif group and section_body.startswith('<h2>'):section_body='<h3>'+section_body[4:].replace('</h2>','</h3>',1)
            if prepared and section['id']==spec['tracking']['section']:
                if prepared['state']:
                    chart_md,chart_storage,chart_html=report_charts.fragments(prepared['state'],chart_data,assets)
                    md[-2:-2]=chart_md;body.append(chart_storage);preview_body.append(chart_html)
                else:
                    message='Grafieken wachten op een volledige, bevestigde meetbasis en milestonestand.'
                    md[-2:-2]=[message,''];preview_body.append('<p>'+message+'</p>')
            md += section_md
            if final and section['id']==spec['tracking_source']['section']:
                # Source material for the agent's proposal; the local concept only, never the page.
                md+=['> Bronmateriaal uit de maandrapporten (niet gepubliceerd):']
                for record in final['records']:
                    for key,name in (('wijzigingen','Wijzigingen'),('beslissing','Beslissingen')):
                        value=str(record.get('inputs',{}).get(key) or '').strip()
                        if value:md+=[f"> - {record['period']} · {name}: "+value.replace('\n',' / ')]
                md+=['']
            if section['id']==(spec.get('properties') or {}).get('sections',[None])[-1]:md+=headline_md
            # Values shown in the properties block are not repeated as a section.
            if section_body and section['id'] not in in_properties:
                body.append(section_body);preview_body.append(section_body)
            if maintained and section['id'] in maintained['after']:
                extra_md,extra_storage=maintained['after'][section['id']]
                md+=extra_md;body.append(extra_storage);preview_body.append(extra_storage)
            questions += section_questions
            if prepared and section['id']==spec['tracking']['section']:
                for note in prepared['notes']:
                    md += ['Opmerking: '+note,''];body.append('<p>'+escape(note)+'</p>');preview_body.append('<p>'+escape(note)+'</p>')
        else:
            rows=data[section['source']]
            if scope=='project' and section['source']=='projects':rows=[r for r in rows if r.get('key')==target]
            elif initiative:
                rows=[r for r in rows if r.get('key')==initiative or r.get('initiative')==initiative or initiative in r.get('initiatives',[]) or (scope=='project' and r.get('key')==target)]
            rows=[r for r in rows if matches(section.get('where'),r)]
            if section['kind']=='count':md += [str(len(rows)),'']
            else:
                cols=section['columns'];md+=['| '+' | '.join(cols)+' |','| '+' | '.join('---' for _ in cols)+' |']
                md += ['| '+' | '.join(cell(get(r,c)) for c in cols)+' |' for r in rows]
                if not rows:md+=['Geen gegevens in de gelezen bronnen.']
                md+=['']
            # No snapshot of Jira-owned data in Confluence. The live macro above provides it.
    if measured_state:
        appendix_md,appendix_storage,appendix_html=report_charts.appendix(measured_state,chart_data,[r['title'] for r in final['records']] if final else ())
        md+=appendix_md;body.append(appendix_storage);preview_body.append(appendix_html)
    for gap in snapshot.get('gaps',[]):md+=['Bronbeperking: '+gap]
    parent_title=spec['parent_title'].format_map({'initiative':initiative}) if 'parent_title' in spec else None
    storage=''.join(body)
    if prepared and prepared['state'] and not questions:
        measurement=report_history.seal(storage,prepared['state'])
    warnings=''.join('<li>'+escape(q['question'])+'</li>' for q in questions)
    warning_html='<aside><strong>Nog te beantwoorden</strong><ul>'+warnings+'</ul></aside>' if warnings else ''
    rich=bool(prepared or spec.get('tracking_source') or maintained)
    fonts=font_faces(cat.root/'form') if rich else ''
    html=preview_html(title,period,warning_html+''.join(preview_body),snapshot.get('source',{}).get('mode')=='fixture',fonts) if rich else None
    return {'report':report_id,'scope':scope,'target':target,'initiative':initiative,'title':title,'label':spec.get('label'),'parent_title':parent_title,
            'period':period,'questions':questions,'complete':not questions,'markdown':'\n'.join(md)+'\n','storage':storage,
            'inputs':inputs,'resolved_inputs':working,'source_time':snapshot.get('collected_at'),
            'html':html,'assets':assets,'chart_data':chart_data,'measurement':measurement,
            'history_guard':prepared['guard'] if prepared else guard,'notes':prepared['notes'] if prepared else final_notes,
            'replaces':(maintained or {}).get('replaces')}
