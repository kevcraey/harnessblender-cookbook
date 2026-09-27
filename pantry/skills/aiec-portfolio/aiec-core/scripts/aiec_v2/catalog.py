"""Data-driven definitions. No eval, templates cannot execute code or access files."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import re
import string
import yaml
from aiec_lib import schema as legacy_schema
from .report_inputs import INPUT_KINDS, validate_definitions

CORE = Path(__file__).resolve().parents[2]
OPERATORS = {'eq', 'ne', 'in', 'not_in', 'empty', 'filled', 'contains', 'gt', 'gte'}
SOURCES = {'initiatives', 'projects', 'products', 'artifacts', 'findings'}


def placeholders(template):
    """Named {veld}-placeholders; attribute, index and format specs are refused."""
    names=set()
    for _,name,spec,conv in string.Formatter().parse(template):
        if name is None:continue
        if not re.fullmatch(r'[a-z_]+',name) or spec or conv:raise ValueError('Ongeldige placeholder in titelsjabloon')
        names.add(name)
    return names


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def get(obj, path, default=None):
    for bit in path.split('.'):
        if not isinstance(obj, dict) or bit not in obj:
            return default
        obj = obj[bit]
    return obj


def matches(expr, row):
    if not expr:
        return True
    if 'all' in expr:
        return all(matches(x, row) for x in expr['all'])
    if 'any' in expr:
        return any(matches(x, row) for x in expr['any'])
    if 'not' in expr:
        return not matches(expr['not'], row)
    value, op, want = get(row, expr['field']), expr['op'], expr.get('value')
    if op == 'empty': return value is None or value == '' or value == []
    if op == 'filled': return value is not None and value != '' and value != []
    if op == 'eq': return value == want
    if op == 'ne': return value != want
    if op == 'in': return value in want
    if op == 'not_in': return value not in want
    if op == 'contains': return want in (value or [])
    if op == 'gt': return isinstance(value, (float, int)) and value > want
    if op == 'gte': return isinstance(value, (float, int)) and value >= want
    raise ValueError(f'Onbekende operator: {op}')


def check_expr(expr):
    if expr is None or expr == {}: return
    if not isinstance(expr, dict): raise ValueError('Voorwaarde moet een object zijn')
    for group in ('all', 'any', 'not'):
        if group in expr:
            if set(expr) != {group}: raise ValueError('Gemengde voorwaarden')
            if group == 'not': check_expr(expr[group])
            else:
                if not isinstance(expr[group], list) or not expr[group]: raise ValueError('Lege voorwaardenlijst')
                for e in expr[group]: check_expr(e)
            return
    if set(expr) - {'field','op','value'} or not isinstance(expr.get('field'), str) or expr.get('op') not in OPERATORS:
        raise ValueError(f'Ongeldige voorwaarde: {expr}')
    if expr['op'] not in ('empty','filled') and 'value' not in expr: raise ValueError('value ontbreekt')
    if expr['op'] in ('in','not_in') and not isinstance(expr['value'], list): raise ValueError('in verwacht lijst')


class Catalog:
    def __init__(self, root=CORE):
        self.root = Path(root)
        self.schema = legacy_schema.load(self.root / 'schema.yaml')
        self.process = yaml.safe_load((self.root / 'catalog/process.yaml').read_text())
        self.rules = self._load('rules')
        self.reports = self._load('reports')
        self.capabilities = self._load('capabilities')
        self.validate()
        # Bind approvals to both definitions AND executing source code.
        files = [self.root/'schema.yaml', *sorted((self.root/'catalog').rglob('*.yaml')),
                 *sorted((self.root/'scripts').rglob('*.py')),
                 *sorted(p for p in (self.root/'form').rglob('*') if p.is_file())]
        self.fingerprint = digest({str(p.relative_to(self.root)):hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in files if 'tests' not in p.parts})

    def _load(self, kind):
        out = {}
        for p in sorted((self.root/'catalog'/kind).glob('*.yaml')):
            item = yaml.safe_load(p.read_text())
            if not isinstance(item, dict) or not re.fullmatch(r'[a-z][a-z0-9-]*', str(item.get('id',''))):
                raise ValueError(f'Ongeldige definitie: {p.name}')
            if item['id'] in out: raise ValueError(f'Dubbele {kind}: {item["id"]}')
            out[item['id']] = item
        return out

    def validate(self):
        errors = legacy_schema.check(self.schema)
        if errors: raise ValueError('; '.join(errors))
        states = self.process['states']
        aliases = [a.casefold() for s in states.values() for a in s['aliases']]
        if len(aliases) != len(set(aliases)): raise ValueError('Dubbele statusalias')
        for name, spec in self.process.get('gates', {}).items():
            if name not in states: raise ValueError('Onbekende gate-status')
            if any(x not in self.schema['artefact_labels'] for x in spec.get('artifacts', [])):
                raise ValueError('Onbekend gate-artefact')
            if set(spec.get('project_artifacts', []))-set(spec.get('artifacts', [])):
                raise ValueError('Projectartefact van een gate moet ook gate-artefact zijn')
            # Where the decision for this transition lives: a report with its own decision section, or a separate decision page.
            where = spec.get('decision_in')
            if where and (where not in self.schema['artefact_labels'] or (where != 'decisions' and where not in spec.get('artifacts', []))):
                raise ValueError('decision_in moet een artefactlabel zijn en, buiten decisions, ook gate-artefact')
        for f in self.schema['fields']:
            for k in ('required_when_v2', 'notice_when_v2'): check_expr(f.get(k))
        columns = {
            'initiatives': {f['key'] for f in self.schema['fields']} | {'key','summary','phase','status','status_raw','fase','resolution','created','updated','last_transition','eag_keys','links','children','billingkey','labels','assignee','trekker','verantwoordelijke','confluence_page_ids','url','page_id','page_count','project_keys','artifact_labels','own_labels','decision_transitions','dpia_oordeel','dpo_oordeel','inactive_days','previous_report','direct_hours_share'},
            'projects': {'key','summary','status','assignee','updated','initiatives','url','previous_report','artifact_labels','page_id'},
            'products': {'key','summary','status','assignee','updated','initiatives','url'},
            'artifacts': {'key','page_id','title','labels','last_modified','storage','initiative','project','project_page','parent_id'},
            'findings': {'rule','severity','key','page_id','message','action'},
        }
        def paths(expr, scope):
            if not expr: return
            if 'field' in expr and expr['field'] not in columns[scope]:
                raise ValueError(f"Onbekend bronveld {scope}.{expr['field']}")
            for group in ('all','any'):
                for e in expr.get(group,[]): paths(e,scope)
            if 'not' in expr: paths(expr['not'],scope)
        for rule in self.rules.values():
            if rule.get('scope') not in SOURCES - {'findings'}: raise ValueError('Onbekende regelscope')
            if rule.get('severity') not in ('error','warning','info'): raise ValueError('Onbekende ernst')
            if not rule.get('message') or not rule.get('action'): raise ValueError('Regel mist tekst/actie')
            check_expr(rule.get('when'))
            paths(rule.get('when'),rule['scope'])
        for report in self.reports.values():
            if report.get('scope') not in ('initiative','project','portfolio'): raise ValueError('Onbekende rapportscope')
            if not isinstance(report.get('sections'), list) or not report['sections']: raise ValueError('Rapport mist secties')
            if report.get('label') and report['label'] not in self.schema['artefact_labels']: raise ValueError('Onbekend rapportlabel')
            if 'page_title' in report and placeholders(report['page_title'])-{'datum','slug','project'}: raise ValueError('Paginatitel kent enkel {datum}, {project} en {slug}')
            if 'project' in placeholders(report.get('page_title','')) and report.get('scope')!='project': raise ValueError('Paginatitel met {project} vraagt een projectrapport')
            if 'parent_title' in report and (report.get('scope')!='initiative' or placeholders(report['parent_title'])-{'initiative'}): raise ValueError('Ouderpaginatitel kent enkel {initiative} bij initiatiefrapporten')
            seen = set()
            for s in report['sections']:
                if s.get('id') in seen or not s.get('id'): raise ValueError('Dubbele/ontbrekende sectie-id')
                seen.add(s['id'])
                if s.get('kind') not in INPUT_KINDS | {'table','count'}: raise ValueError('Onbekend sectietype')
                if s['kind'] not in INPUT_KINDS and s.get('source') not in SOURCES: raise ValueError('Onbekende databron')
                if s['kind'] == 'table' and not s.get('columns'): raise ValueError('Tabel zonder kolommen')
                check_expr(s.get('where'))
                if s['kind'] not in INPUT_KINDS:
                    paths(s.get('where'),s['source'])
                    if any(c not in columns[s['source']] for c in s.get('columns',[])):
                        raise ValueError('Onbekende rapportkolom')
            if not isinstance(report.get('jira', True), bool): raise ValueError('jira is true of false')
            tpl = report.get('sjabloon')
            if tpl is not None and (not str(tpl.get('page_id','')).isdigit() or not tpl.get('deel') or not tpl.get('vingerafdruk')):
                raise ValueError('Sjabloon vraagt page_id, deel en vingerafdruk')
            props = report.get('properties')
            if props is not None:
                kinds = {s['id']: s['kind'] for s in report['sections']}
                if not props.get('id') or not props.get('sections') or any(kinds.get(x) not in ('input', 'choice') for x in props['sections']):
                    raise ValueError('Eigenschappen vragen een id en bestaande invoer- of keuzesecties')
            validate_definitions(report)
            from .tracking import validate_spec
            validate_spec(report)
            # A group is one heading over consecutive sections; it may not come back later in the report.
            groups = [s.get('group') for s in report['sections']]
            if any(g is not None and (not isinstance(g, str) or not g.strip()) for g in groups): raise ValueError('Groep moet tekst zijn')
            runs = [g for i, g in enumerate(groups) if g and (i == 0 or groups[i-1] != g)]
            if len(runs) != len(set(runs)): raise ValueError('Secties van één groep moeten aansluiten')
            source = report.get('tracking_source')
            if source is not None:
                if report.get('tracking') or report.get('scope') != 'project' or not isinstance(source, dict) or set(source) != {'report', 'section'}:
                    raise ValueError('tracking_source vraagt een projectrapport zonder eigen meting, met report en section')
                if not (self.reports.get(source['report']) or {}).get('tracking') or source['section'] not in seen:
                    raise ValueError('tracking_source verwijst naar een rapport zonder meting of een onbekende sectie')
            link = report.get('link_report')
            if link is not None and (report.get('scope') != 'project' or (self.reports.get(link) or {}).get('scope') != 'project'):
                raise ValueError('link_report verwijst naar een projectrapport, vanuit een projectrapport')
        for cap in self.capabilities.values():
            if cap.get('handler') not in ('review','report','change','extend'): raise ValueError('Onbekende capability-handler')

    def state(self, raw):
        for name, spec in self.process['states'].items():
            if str(raw).casefold() in [x.casefold() for x in spec['aliases']]: return name
        return None

    def rank(self, state):
        return self.process['states'].get(state, {}).get('rank', -1)

    def overview(self):
        return {'version':2,'fingerprint':self.fingerprint,'capabilities':list(self.capabilities.values()),
                'reports':[{k:v for k,v in r.items() if k!='sections'} for r in self.reports.values()],
                'rules':list(self.rules.values()), 'process':self.process, 'schema':self.schema}
