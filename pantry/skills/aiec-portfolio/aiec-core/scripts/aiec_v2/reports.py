"""Generic report definitions: code provides facts, people provide judgments."""
from __future__ import annotations
import calendar
from datetime import date
from html import escape
import re
import unicodedata
from .catalog import get, matches, placeholders
from .review import datasets, review
from aiec_lib.confluence import _jira_macro, details_macro
from .report_inputs import INPUT_KINDS, render_input, choice_text
from .form_files import font_faces


def preview_html(title, period, body, fixture=False, fonts=''):
    style=fonts+''':root{--grey-100:#f7f9fc;--grey-300:#cfd5dd;--grey-1000:#333332;--text-subtle:rgba(0,20,46,.6);--accent:#447a6d;--primary:#ffed00;--warning-100:#fff9e8;--warning-400:#ffe49c;--warning-800:#9f5804}*{box-sizing:border-box}body{margin:0;background:#fff;color:var(--grey-1000);font:18px/1.5 "Flanders Art Sans",sans-serif;-webkit-font-smoothing:antialiased}header{border-bottom:6px solid var(--primary)}header>div,main{max-width:1200px;margin:auto;padding:20px 30px}main{padding-bottom:60px}h1{font-size:32px;line-height:1.24;font-weight:500;margin:5px 0 0}h2{font-size:26px;line-height:1.3;font-weight:500;margin:40px 0 15px}h3,h4{font-size:22px;font-weight:500;margin:30px 0 10px}p{margin:0 0 15px}table{display:block;width:100%;overflow-x:auto;border-collapse:collapse;margin:15px 0;font-size:16px}th,td{padding:10px 12px;border-bottom:1px solid var(--grey-300);text-align:left;vertical-align:top}thead th{background:var(--grey-100);font-weight:500}.properties{display:table;width:auto;min-width:min(100%,560px);border:1px solid var(--grey-300);border-radius:3px}.properties th{width:220px;background:var(--grey-100);font-weight:500}.properties td{font-size:18px}aside{padding:15px 20px;background:var(--warning-100);border:1px solid var(--warning-400);border-radius:3px;margin:20px 0}aside strong{color:var(--warning-800)}.report-charts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}figure{margin:10px 0;border:1px solid var(--grey-300);border-radius:3px;overflow:hidden}figure img{display:block;width:100%;height:auto}figcaption{padding:8px 15px;color:var(--text-subtle);font-size:16px}em{color:var(--text-subtle);font-size:16px;font-style:normal}details{margin:30px 0 0;border-top:1px solid var(--grey-300);padding-top:15px}summary{cursor:pointer;font-weight:500}p,li{overflow-wrap:anywhere}.eyebrow{color:var(--accent);font-size:16px;font-weight:500}@media(max-width:900px){.report-charts{grid-template-columns:1fr}}@media(max-width:600px){header>div,main{padding:15px 16px}h1{font-size:26px}body{font-size:16px}}'''
    label='AIEC · Fictieve voorbeelddata · Concept' if fixture else 'AIEC · Concept ter goedkeuring'
    return '<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+escape(title)+'</title><style>'+style+'</style></head><body><header><div><div class="eyebrow">'+label+' · '+escape(period)+'</div><h1>'+escape(title)+'</h1></div></header><main>'+body+'</main></body></html>'


def title_date(spec, period, today=None):
    """Default datum in de paginatitel: laatste dag van de periode bij periodieke rapporten,
    anders de dag van aanmaak. Een invoer 'datum' gaat altijd voor."""
    if spec.get('cadence'):
        year=int(period[:4]);month=int(period[6])*3 if 'Q' in period else int(period[5:7])
        return date(year,month,calendar.monthrange(year,month)[1]).isoformat()
    return (today or date.today()).isoformat()


def slugify(text):
    """'Advies - Gezond uit eigen grond' -> 'advies-gezond-uit-eigen-grond'."""
    plain=unicodedata.normalize('NFKD',text or '').encode('ascii','ignore').decode()
    return '-'.join(re.findall(r'[a-z0-9]+',plain.lower()))


def cell(value):
    if value is None: return 'onbekend'
    if isinstance(value,list): value=', '.join(str(v) for v in value)
    return str(value).replace('|','\\|').replace('\n','<br>')


def render(cat, snapshot, report_id, target=None, period=None, inputs=None, cfg=None, slug=None, tracking=None):
    spec=cat.reports[report_id]
    inputs={} if inputs is None else inputs
    if not isinstance(inputs,dict):raise ValueError('Rapportinvoer moet een object met secties zijn')
    allowed={s['id'] for s in spec['sections'] if s['kind'] in INPUT_KINDS}
    if set(inputs)-allowed:raise ValueError('Onbekende invoersectie: '+', '.join(set(inputs)-allowed))
    scope=spec['scope']
    if scope!='portfolio' and not target:raise ValueError('Rapport vraagt een initiatief- of projectkey')
    if not period or not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2]|Q[1-4])',period):raise ValueError('Periode vereist: JJJJ-MM of JJJJ-Qn')
    if spec.get('cadence')=='monthly' and 'Q' in period:raise ValueError('Maandrapport vraagt JJJJ-MM')
    if spec.get('cadence')=='quarterly' and 'Q' not in period:raise ValueError('Kwartaalrapport vraagt JJJJ-Qn')
    data=datasets(cat,snapshot);data['findings']=review(cat,snapshot)
    initiative=target if scope=='initiative' else None
    if scope=='project':
        candidates=[p for p in data['projects'] if p['key']==target]
        if len(candidates)!=1:raise ValueError('Project ontbreekt of is dubbel')
        keys=candidates[0].get('initiatives',[]);project_summary=candidates[0].get('summary')
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
            parts['project']=target
            # Default slug from the Jira summary: visible in the proposal, overridable with slug.
            slug=slug or slugify(project_summary)
        if 'slug' in placeholders(spec['page_title']):
            if slug and not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*',slug):raise ValueError('Slug: enkel kleine letters, cijfers en enkelvoudige koppeltekens')
            if not slug:title_questions.append({'section':'slug','question':'Slug voor de paginatitel (kleine letters, cijfers, koppeltekens).'})
            parts['slug']=slug or ''
        if all(parts.values()):title=spec['page_title'].format_map(parts)
    prepared=None; assets=[]; chart_data=None; measurement=None
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
    md=[f'# {title}','','Concept ter goedkeuring. Bronmoment: '+snapshot.get('collected_at','onbekend')+'.','']
    body=[];preview_body=[];questions=list(title_questions)
    if prepared:questions+=prepared['questions']
    # A decision is self-contained; it needs no live ticket view.
    if initiative and spec.get('jira',True):
        if cfg:
            macro=_jira_macro(cfg['atlassian'],f'key in ({initiative}{", "+target if scope=="project" else ""})')
            if not macro:raise ValueError('Jira serverId ontbreekt; geen statische kopie als vervanging')
            body.append(macro)
        else:body.append('<p>Live Jira-verwijzing wordt bij publicatie toegevoegd.</p>')
    # A report with its own decision date needs no separate period line.
    if 'datum' not in {s['id'] for s in spec['sections']}:body.append(f'<p>Periode: {escape(period)}</p>')
    in_properties=set((spec.get('properties') or {}).get('sections',[]))
    headline_md=[]
    if spec.get('properties'):
        # Page Properties block: machine-readable for review and the Beslissingen overview.
        sections={s['id']:s for s in spec['sections']};rows=''
        for sid in spec['properties']['sections']:
            value=working.get(sid) or ''
            text=choice_text(spec,sections[sid],value) if sections[sid]['kind']=='choice' and value else str(value).strip()
            rows+=f"<tr><th>{escape(sections[sid]['title'])}</th><td>{escape(text).replace(chr(10),'<br/>')}</td></tr>"
        if prepared and prepared['state']:
            for name,value in report_charts.headline(prepared['state']):
                rows+=f"<tr><th>{escape(name)}</th><td>{escape(value)}</td></tr>";headline_md+=[f'**{name}:** {value}','']
        body.append(details_macro(cat.schema,rows,details_id=spec['properties']['id']))
        preview_body.append('<table class="properties"><tbody>'+rows+'</tbody></table>')
    for section in spec['sections']:
        md += [f"## {section['title']}",'']
        if section['kind'] in INPUT_KINDS:
            section_md,section_body,section_questions=render_input(spec,section,working.get(section['id']))
            if prepared and section['id']==spec['tracking']['section']:
                if prepared['state']:
                    chart_md,chart_storage,chart_html=report_charts.fragments(prepared['state'],chart_data,assets)
                    md[-2:-2]=chart_md;body.append(chart_storage);preview_body.append(chart_html)
                else:
                    message='Grafieken wachten op een volledige, bevestigde meetbasis en milestonestand.'
                    md[-2:-2]=[message,''];preview_body.append('<p>'+message+'</p>')
            md += section_md
            if section['id']==(spec.get('properties') or {}).get('sections',[None])[-1]:md+=headline_md
            # Values shown in the properties block are not repeated as a section.
            if section_body and section['id'] not in in_properties:
                body.append(section_body);preview_body.append(section_body)
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
    if prepared and prepared['state']:
        appendix_md,appendix_storage,appendix_html=report_charts.appendix(prepared['state'],chart_data)
        md+=appendix_md;body.append(appendix_storage);preview_body.append(appendix_html)
    for gap in snapshot.get('gaps',[]):md+=['Bronbeperking: '+gap]
    parent_title=spec['parent_title'].format_map({'initiative':initiative}) if 'parent_title' in spec else None
    storage=''.join(body)
    if prepared and prepared['state'] and not questions:
        storage,measurement=report_history.embed(storage,prepared['state'])
    warnings=''.join('<li>'+escape(q['question'])+'</li>' for q in questions)
    warning_html='<aside><strong>Nog te beantwoorden</strong><ul>'+warnings+'</ul></aside>' if warnings else ''
    fonts=font_faces(cat.root/'form') if prepared else ''
    html=preview_html(title,period,warning_html+''.join(preview_body),snapshot.get('source',{}).get('mode')=='fixture',fonts) if prepared else None
    return {'report':report_id,'scope':scope,'target':target,'initiative':initiative,'title':title,'label':spec.get('label'),'parent_title':parent_title,
            'period':period,'questions':questions,'complete':not questions,'markdown':'\n'.join(md)+'\n','storage':storage,
            'inputs':inputs,'resolved_inputs':working,'source_time':snapshot.get('collected_at'),
            'html':html,'assets':assets,'chart_data':chart_data,'measurement':measurement,
            'history_guard':prepared['guard'] if prepared else None,'notes':prepared['notes'] if prepared else []}
