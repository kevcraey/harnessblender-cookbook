"""Portable project files for the offline form. Never trust browser calculations/history."""
from __future__ import annotations
import base64
from copy import deepcopy
import json
from pathlib import Path
import re
from . import tracking, report_history, monthly_planning
from .report_inputs import render_input
from .review import datasets
from .catalog import digest

FORMAT = 'aiec-project'
VERSION = 2
MAX_BYTES = 2_000_000


def _object(value, allowed, required, label):
    if not isinstance(value, dict) or set(value)-set(allowed) or set(required)-set(value):
        raise ValueError(label+': ongeldige, ontbrekende of onbekende velden; niets verwijderen')


def validate_tracking_shape(value):
    changes=value.get('scope_changes',[])
    if not isinstance(changes,list):raise ValueError('Scopebesluiten moeten een lijst zijn')
    for change in changes:
        _object(change, ['id','month','decision','milestones'], ['id','month','decision','milestones'], 'Scopebesluit')
        if not isinstance(change['id'],str) or not change['id'].strip() or not isinstance(change['month'],str):raise ValueError('Ongeldige scope-identiteit')
        _object(change['decision'], ['by','date','source'], ['by','date','source'], 'Beslissing')
        if any(not isinstance(v,str) for v in change['decision'].values()):raise ValueError('Beslissing vraagt tekstvelden')
        if not isinstance(change['milestones'],list) or not change['milestones']:raise ValueError('Scopebesluit vraagt milestones')
        for row in change['milestones']:
            _object(row, ['nr','milestone','weight_md'], ['nr','milestone','weight_md'], 'Scopemilestone')
            if type(row['nr']) is not int or row['nr'] < 1 or not isinstance(row['milestone'],str):raise ValueError('Ongeldige scopemilestone')
            if row['weight_md'] is not None and (isinstance(row['weight_md'],bool) or not isinstance(row['weight_md'],(str,int,float))):raise ValueError('Ongeldige scopewaarde')
    if not isinstance(value.get('corrections',[]),list):raise ValueError('Correcties moeten een lijst zijn')
    for item in value.get('corrections',[]):
        _object(item, ['nr','reason'], ['nr','reason'], 'Correctie')
        if type(item['nr']) is not int or not isinstance(item['reason'],str):raise ValueError('Ongeldige correctie')
    if 'legacy_ack' in value:
        ack=value['legacy_ack'];_object(ack,['pages','reason'],['pages','reason'],'Meetstart')
        if not isinstance(ack['pages'],list) or any(not isinstance(x,str) for x in ack['pages']) or not isinstance(ack['reason'],str):raise ValueError('Ongeldige meetstart')
    if 'assume_on_plan' in value and type(value['assume_on_plan']) is not bool:raise ValueError('Ongeldige aannamekeuze')
    if 'future_factor' in value and not (value['future_factor']=='ratio' or (type(value['future_factor']) in (int,float,str) and value['future_factor']!='')):raise ValueError('Ongeldige factor voor toekomstig werk')


def validate_document(doc):
    v2=isinstance(doc,dict) and doc.get('version')==2
    fields=['format','version','project','baseline','periods']+(['settings'] if v2 else [])
    _object(doc, fields, fields, 'Projectbestand')
    if doc['format'] != FORMAT or type(doc['version']) is not int or doc['version'] not in (1,VERSION):
        raise ValueError('Onbekende projectbestandsversie; gebruik een passende formulierupdate')
    if len(json.dumps(doc, ensure_ascii=False).encode()) > MAX_BYTES:
        raise ValueError('Projectbestand is te groot')
    if v2:
        _object(doc['settings'],['auto_remaining'],['auto_remaining'],'Instellingen')
        if type(doc['settings']['auto_remaining']) is not bool:raise ValueError('Auto-calc moet aan of uit zijn')
    _object(doc['project'], ['key','name'], ['key','name'], 'Project')
    if not re.fullmatch(r'[A-Z][A-Z0-9_]*-\d+', str(doc['project']['key'])) or not isinstance(doc['project']['name'], str) or not doc['project']['name'].strip():
        raise ValueError('Projectkey en naam zijn verplicht')
    tracking.baseline(doc['baseline'])
    periods = doc['periods']
    if not isinstance(periods, list) or not 1 <= len(periods) <= 1200:
        raise ValueError('Projectbestand vraagt 1–1200 maanden')
    last = ''
    for index, p in enumerate(periods):
        fields=['period','inputs','tracking','confirmed','stage']+(['planning'] if v2 else [])
        _object(p, fields+['published_hash'], fields, 'Maand')
        if v2:monthly_planning.shape(p['planning'])
        tracking.month(p['period'])
        if p['period'] <= last:raise ValueError('Maanden moeten uniek en chronologisch zijn')
        last = p['period']
        if p['stage'] not in ('draft','closed','published') or (index < len(periods)-1 and p['stage']=='draft'):
            raise ValueError('Alleen de laatste maand kan een concept zijn')
        if 'published_hash' in p and not re.fullmatch(r'[0-9a-f]{64}', str(p['published_hash'])):
            raise ValueError('Ongeldige referentie naar gepubliceerde maand')
        _object(p['inputs'], ['vlag','wijzigingen','milestones','beslissing','volgende'], ['milestones'], 'Maandinvoer')
        for key in ('vlag','wijzigingen','beslissing','volgende'):
            if key in p['inputs'] and not isinstance(p['inputs'][key], str):raise ValueError('Tekst verwacht: '+key)
        rows = p['inputs']['milestones']
        if not isinstance(rows, list) or not 1 <= len(rows) <= 1000:raise ValueError('Verwacht 1–1000 milestoneregels')
        ids = []
        for row in rows:
            _object(row, ['nr','milestone','status','baseline_md','forecast_md','actual_md','remaining_md','gezondheid','notities'], ['nr','milestone','status'], 'Milestone')
            if type(row['nr']) is not int:raise ValueError('Formuliernummer moet een JSON-geheel getal zijn')
            ident = tracking.nr(row['nr'])
            if ident > 9007199254740991:raise ValueError('Milestonenummer te groot voor het formulier')
            ids.append(ident)
            for key, value in row.items():
                if key == 'nr':continue
                if value is not None and (isinstance(value, bool) or not isinstance(value, (str,int,float))):
                    raise ValueError('Ongeldige veldstructuur: '+key)
        if len(set(ids)) != len(ids):raise ValueError('Dubbele milestonenummers')
        if not isinstance(p['confirmed'], list) or any(type(n) is not int or n not in ids for n in p['confirmed']) or len(set(p['confirmed'])) != len(p['confirmed']):
            raise ValueError('Ongeldige bevestigde rijen')
        _object(p['tracking'], ['scope_changes','assume_on_plan','corrections','legacy_ack','future_factor'], [], 'Meetinvoer')
        validate_tracking_shape(p['tracking'])
    return doc


def upgrade(doc):
    validate_document(doc)
    result=deepcopy(doc)
    for p in result['periods']:
        for row in p['inputs']['milestones']:row.pop('forecast_md',None)  # Old name of the ignored Baseline input.
    if result['version']==1:
        result['version']=VERSION;result['settings']={'auto_remaining':True}
        for p in result['periods']:p['planning']=None
        current=result['periods'][-1]
        if current['stage']=='draft':current['planning']=monthly_planning.from_baseline(tracking.baseline(result['baseline']),current['period'])
    return validate_document(result)


def read_document(path):
    raw = Path(path).read_bytes()
    if len(raw) > MAX_BYTES:raise ValueError('Projectbestand is te groot')
    # Duplicate JSON keys must not silently discard manual input.
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:raise ValueError('Dubbele JSON-sleutel: '+key)
            out[key] = value
        return out
    def constant(value):raise ValueError('Ongeldige JSON-constante: '+value)
    return upgrade(json.loads(raw, object_pairs_hook=pairs, parse_constant=constant))


def evaluate(cat, doc):
    """Recompute local periods using Python. Local closure is not publication."""
    doc=upgrade(doc)
    spec = cat.reports['vooruitgang']; section = next(s for s in spec['sections'] if s['id']=='milestones')
    snapshot = {'report_pages':[], 'collected_at':None}; results = []
    for p in doc['periods']:
        try:
            _, _, questions = render_input(spec, section, p['inputs']['milestones'])
            prepared = tracking.prepare(spec, snapshot, doc['project']['key'], None, p['period'], p['inputs'], dict(p['tracking'],baseline=doc['baseline'],planning=p['planning']))
            questions += prepared['questions']
            flag = p['inputs'].get('vlag')
            if flag not in {v['value'] for v in spec['enums']['projectgezondheid']}:
                questions.append({'section':'vlag','question':'Kies de projectgezondheid.'})
            results.append({'period':p['period'], 'state':prepared['state'], 'questions':questions, 'notes':prepared['notes']})
            if questions or not prepared['state']:break
            state = prepared['state']; state['title'] = 'Lokale maand '+p['period']
            storage, record = report_history.embed('', state)
            snapshot['report_pages'].append({'page_id':str(len(results)), 'title':state['title'], 'labels':[spec['label']], 'storage':storage, 'revision':digest(record)})
        except (ValueError, KeyError, TypeError) as exc:
            results.append({'period':p['period'], 'state':None, 'questions':[{'section':'milestones','question':str(exc)}], 'notes':[]})
            break
    return results


def _project(cat, snapshot, key):
    projects = [p for p in datasets(cat, snapshot)['projects'] if p['key']==key]
    if len(projects)!=1 or len(projects[0]['initiatives'])!=1:raise ValueError('Project of initiatiefkoppeling is niet eenduidig')
    return projects[0], projects[0]['initiatives'][0]


def new_rows(base):
    return [{'nr':r['nr'], 'milestone':r['milestone'], 'status':'Backlog', 'actual_md':None,
             'remaining_md':r['planned_md'], 'gezondheid':'', 'notities':''} for r in base['milestones']]


def export_project(cat, snapshot, key, period, supplied=None):
    project, initiative = _project(cat, snapshot, key)
    spec = cat.reports['vooruitgang']; history = report_history.load(spec, snapshot, key, initiative)
    if 'report_pages' not in snapshot:raise ValueError('Verzamel opnieuw: rapporthistoriek ontbreekt')
    tracking.month(period); supplied = supplied or {}
    _object(supplied, ['baseline','scope_changes','assume_on_plan','corrections','legacy_ack','planning','future_factor'], [], 'Meetinvoer')
    if history['records']:
        last = history['records'][-1]
        base = last['baseline']
        if supplied.get('baseline') and tracking.baseline(supplied['baseline']) != base:raise ValueError('Baseline mag niet veranderen')
        if period <= last['period']:raise ValueError('Nieuwe werkmaand moet na de gepubliceerde historie liggen')
    else:
        base = tracking.baseline(supplied.get('baseline'))
    periods = []
    for record in history['records']:
        inp = deepcopy(record['inputs'])
        # Missing computed fields are resolved from the authoritative stored measurement.
        for row in inp['milestones']:
            row['nr'] = tracking.nr(row['nr'])
            actual = next(r for r in record['milestones'] if r['nr']==tracking.nr(row['nr']))
            if row.get('remaining_md') is None:row['remaining_md'] = actual['remaining_md']
            row.pop('baseline_md',None)  # Derived from the meetbasis; never carried as input.
        tr = {k:deepcopy(v) for k,v in record.get('tracking_input',{}).items() if k not in ('baseline','planning')}
        periods.append({'period':record['period'], 'inputs':inp, 'tracking':tr, 'stage':'published',
                        'confirmed':[tracking.nr(r['nr']) for r in inp['milestones']], 'published_hash':record['hash'], 'planning':deepcopy(record.get('planning'))})
    rows = deepcopy(periods[-1]['inputs']['milestones']) if periods else new_rows(base)
    for row in rows:row.pop('baseline_md',None)
    current = {k:deepcopy(v) for k,v in supplied.items() if k not in ('baseline','planning')}
    if periods and 'future_factor' not in current and 'future_factor' in periods[-1]['tracking']:
        current['future_factor'] = deepcopy(periods[-1]['tracking']['future_factor'])  # The choice carries over.
    plan=deepcopy(supplied['planning']) if 'planning' in supplied else monthly_planning.future(base,period,periods[-1]['planning'] if periods else None)
    periods.append({'period':period, 'inputs':{'milestones':rows, 'vlag':periods[-1]['inputs'].get('vlag','') if periods else ''},
                    'tracking':current, 'confirmed':[], 'stage':'draft','planning':plan})
    return validate_document({'format':FORMAT,'version':VERSION,'settings':{'auto_remaining':True},'project':{'key':key,'name':project['summary']},'baseline':base,'periods':periods})


def _measurement(state):
    return {**{k:state[k] for k in ('baseline','scope_changes','milestones','metrics')},'planning':state.get('planning')}


def import_request(cat, snapshot, doc, period=None):
    doc=upgrade(doc)
    key = doc['project']['key']; _, initiative = _project(cat, snapshot, key)
    history = report_history.load(cat.reports['vooruitgang'], snapshot, key, initiative)
    if 'report_pages' not in snapshot:raise ValueError('Verzamel opnieuw: rapporthistoriek ontbreekt')
    period = period or doc['periods'][-1]['period']
    chosen = next((p for p in doc['periods'] if p['period']==period),None)
    if not chosen:raise ValueError('Gekozen maand ontbreekt in bestand')
    if chosen['stage']=='published':raise ValueError('Deze maand is al gepubliceerd; niet overschrijven')
    # Evaluate only the selected period and its predecessors, never discard bad current input.
    subset = deepcopy(doc); subset['periods'] = [p for p in doc['periods'] if p['period']<=period]
    results = evaluate(cat, subset)
    if len(results)!=len(subset['periods']) or any(r['questions'] for r in results):
        raise ValueError('Formulier bevat vragen: '+'; '.join(q['question'] for r in results for q in r['questions']))
    official = {r['period']:r for r in history['records']}
    local = {r['period']:r['state'] for r in results}
    for when, old in official.items():
        if when >= period:raise ValueError('Deze of een latere maand is al gepubliceerd; laad een actueel projectbestand')
        if when not in local:raise ValueError('Gepubliceerde historiek ontbreekt in projectbestand; exporteer een actuele versie')
        if _measurement(local[when]) != _measurement(old):raise ValueError('Eerdere meetstand wijkt af van gepubliceerde historie: '+when)
        prior = next(p for p in doc['periods'] if p['period']==when)['inputs']
        for field in ('vlag','wijzigingen','beslissing','volgende'):
            if field in prior and prior[field] != old['inputs'].get(field,''):
                raise ValueError('Eerdere handmatige rapportinhoud wijkt af: '+when+' '+field)
        for row in prior['milestones']:
            original = next(r for r in old['inputs']['milestones'] if tracking.nr(r['nr'])==row['nr'])
            if any(row.get(field,'') != original.get(field,'') for field in ('gezondheid','notities')):
                raise ValueError('Eerdere milestone-inhoud wijkt af: '+when)
        declared = next(p for p in doc['periods'] if p['period']==when).get('published_hash')
        if declared and declared!=old['hash']:raise ValueError('Gepubliceerde referentie is gewijzigd; eerst reviewen')
    for when in local:
        if when < period and when not in official:raise ValueError('Dien eerst de nog niet gepubliceerde maand '+when+' afzonderlijk in')
    state = results[-1]['state']
    tr = deepcopy(chosen['tracking']); tr['baseline'] = deepcopy(doc['baseline']); tr['scope_changes'] = state['scope_changes']; tr['planning']=deepcopy(chosen['planning'])
    request = {'kind':'report','report':'vooruitgang','target':key,'period':period,'inputs':deepcopy(chosen['inputs']),'tracking':tr}
    check = tracking.prepare(cat.reports['vooruitgang'],snapshot,key,initiative,period,request['inputs'],tr)
    if check['questions']:raise ValueError('; '.join(q['question'] for q in check['questions']))
    return request


def contract(cat):
    spec = cat.reports['vooruitgang']
    return {'version':VERSION,'legacyVersions':[1],'format':FORMAT,'tracking':spec['tracking'],'health':spec['enums']['projectgezondheid'],
            'columns':next(s['columns'] for s in spec['sections'] if s['id']=='milestones'), 'maxBytes':MAX_BYTES,
            'texts':[{k:s[k] for k in ('id','title','prompt','min_lines','max_lines') if k in s} for s in spec['sections'] if s['kind']=='input']}


FONTS = ((400, 'FlandersArtSans-Regular.woff2'), (500, 'FlandersArtSans-Medium.woff2'), (700, 'FlandersArtSans-Bold.woff2'))


def font_faces(folder):
    return ''.join('@font-face{font-family:"Flanders Art Sans";font-weight:%d;font-style:normal;font-display:swap;src:url(data:font/woff2;base64,%s) format("woff2")}'
                   % (weight, base64.b64encode((folder/'fonts'/name).read_bytes()).decode()) for weight, name in FONTS)


def build_html(cat):
    folder = cat.root/'form'
    text = (folder/'index.html').read_text().replace('/*__FONTS__*/', font_faces(folder))
    data = json.dumps(contract(cat), ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    return text.replace('/*__STYLE__*/',(folder/'style.css').read_text()).replace('/*__CONTRACT__*/',data).replace('/*__MODEL__*/',(folder/'model.js').read_text()).replace('/*__APP__*/',(folder/'app.js').read_text())
