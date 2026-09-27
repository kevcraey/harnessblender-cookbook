"""Fixed-reference milestone measurements. All inference is explicit and deterministic."""
from __future__ import annotations
from copy import deepcopy
from datetime import date
from decimal import Decimal
import re
from .report_inputs import blank, number
from . import report_history

FIELDS = {'id', 'name', 'status', 'baseline', 'actual', 'remaining'}


def validate_spec(report):
    spec = report.get('tracking')
    if spec is None:
        return
    _keys(spec, {'kind', 'section', 'fields', 'delivered', 'backlog'}, 'Trackingdefinitie')
    if spec.get('kind') != 'milestone_effort' or report.get('scope') != 'project' or report.get('cadence') != 'monthly':
        raise ValueError('Milestonemeting vraagt een maandelijks projectrapport')
    section = next((s for s in report['sections'] if s['id'] == spec.get('section')), None)
    if not section or section['kind'] != 'input_table':
        raise ValueError('Milestonemeting vraagt een invoertabel')
    fields = spec.get('fields', {})
    if not isinstance(fields, dict) or set(fields) != FIELDS or len(set(fields.values())) != len(FIELDS):
        raise ValueError('Onvolledige of dubbele veldmapping voor milestonemeting')
    cols = {c['id']: c for c in section['columns']}
    types = {'id': 'integer', 'name': 'text', 'status': 'text', 'baseline': 'decimal', 'actual': 'decimal', 'remaining': 'decimal'}
    if any(fields[k] not in cols or cols[fields[k]]['type'] != typ for k, typ in types.items()):
        raise ValueError('Milestonevelden verwijzen naar ontbrekende of anders getypeerde kolommen')
    aliases = []
    for name in ('delivered', 'backlog'):
        values = spec.get(name)
        if not isinstance(values, list) or not values or any(not isinstance(v, str) or not v.strip() for v in values):
            raise ValueError('Statusmapping vraagt expliciete aliassen')
        aliases += [v.strip().casefold() for v in values]
    if len(aliases) != len(set(aliases)):
        raise ValueError('Overlappende milestone-statusaliassen')


def _keys(value, allowed, label):
    if not isinstance(value, dict):
        raise ValueError(label+': verwacht een object')
    extra = set(value)-allowed
    if extra:
        raise ValueError(label+': onbekende velden '+', '.join(sorted(extra)))


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label+': tekst vereist')
    return value


def amount(value, label='Inspanning', positive=False):
    if blank(value):
        return None
    out = number(value, {'title': label, 'type': 'decimal'})
    if positive and Decimal(out) <= 0:
        raise ValueError(label+': moet positief zijn')
    return out


def text(value):
    if value is None:
        return None
    out = format(value, 'f')
    return out.rstrip('0').rstrip('.') if '.' in out else out


def nr(value):
    return int(number(value, {'title': 'Milestonenummer', 'type': 'integer', 'minimum': 1}))


def month(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', value):
        raise ValueError('Maand moet JJJJ-MM zijn')
    date.fromisoformat(value+'-01')
    return value


def months(start, end):
    month(start); month(end)
    a = int(start[:4])*12+int(start[5:])-1
    b = int(end[:4])*12+int(end[5:])-1
    if b < a or b-a > 1200:
        raise ValueError('Ongeldig of te groot maandbereik')
    return [f'{i//12:04d}-{i%12+1:02d}' for i in range(a, b+1)]


def baseline(value):
    _keys(value, {'budget_md', 'milestones', 'plan', 'source'}, 'Baseline')
    budget = amount(value.get('budget_md'), 'Oorspronkelijk budget', positive=True)
    if budget is None:
        raise ValueError('Baseline: oorspronkelijk budget ontbreekt')
    source = _text(value.get('source'), 'Bron van oorspronkelijke planning')
    rows = value.get('milestones')
    if not isinstance(rows, list) or not rows:
        raise ValueError('Baseline: oorspronkelijke milestones ontbreken')
    out = []
    for row in rows:
        _keys(row, {'nr', 'milestone', 'planned_md'}, 'Baseline-milestone')
        planned = amount(row.get('planned_md'), 'Oorspronkelijk geplande mandagen')
        if planned is None:
            raise ValueError('Baseline: geplande mandagen ontbreken')
        out.append({'nr': nr(row.get('nr')), 'milestone': _text(row.get('milestone'), 'Milestone'), 'planned_md': planned})
    if len({r['nr'] for r in out}) != len(out):
        raise ValueError('Dubbele milestone in baseline')
    total = sum((Decimal(r['planned_md']) for r in out), Decimal(0))
    if total <= 0:
        raise ValueError('Oorspronkelijke scope moet positief zijn')
    plan = value.get('plan')
    if not isinstance(plan, list) or not plan:
        raise ValueError('Baseline: expliciete maandplanning ontbreekt; geen planning verzinnen')
    points = []
    for point in plan:
        _keys(point, {'period', 'scope_md', 'effort_md'}, 'Planpunt')
        scope = amount(point.get('scope_md'), 'Geplande scope')
        effort = amount(point.get('effort_md'), 'Geplande inzet')
        if scope is None or effort is None:
            raise ValueError('Planpunt vraagt scope en inzet')
        points.append({'period': month(point.get('period')), 'scope_md': scope, 'effort_md': effort})
    points.sort(key=lambda p: p['period'])
    if len({p['period'] for p in points}) != len(points):
        raise ValueError('Dubbele maand in oorspronkelijke planning')
    months(points[0]['period'], points[-1]['period'])
    for field, limit in [('scope_md', total), ('effort_md', Decimal(budget))]:
        values = [Decimal(p[field]) for p in points]
        if any(a > b for a, b in zip(values, values[1:])) or values[-1] != limit:
            raise ValueError('Oorspronkelijke planning moet oplopen tot het volledige scopegewicht en budget')
    return {'budget_md': budget, 'milestones': sorted(out, key=lambda r: r['nr']), 'plan': points, 'source': source}


def scope_change(value):
    _keys(value, {'id', 'month', 'decision', 'milestones'}, 'Scopebesluit')
    ident = _text(value.get('id'), 'Scopebesluit-id')
    when = month(value.get('month'))
    decision = value.get('decision')
    _keys(decision, {'by', 'date', 'source'}, 'Scopebeslissing')
    for key in ('by', 'date', 'source'):
        _text(decision.get(key), 'Scopebeslissing '+key)
    if date.fromisoformat(decision['date']).isoformat() != decision['date'] or decision['date'][:7] != when:
        raise ValueError('Scope wordt zichtbaar in de maand van de formele goedkeuring')
    rows = value.get('milestones')
    if not isinstance(rows, list) or not rows:
        raise ValueError('Scopebesluit vraagt toegevoegde milestones')
    result = []
    for row in rows:
        _keys(row, {'nr', 'milestone', 'weight_md'}, 'Toegevoegde milestone')
        weight = amount(row.get('weight_md'), 'Goedgekeurd scopegewicht', positive=True)
        if weight is None:
            raise ValueError('Toegevoegde milestone vraagt een vast positief scopegewicht')
        result.append({'nr': nr(row.get('nr')), 'milestone': _text(row.get('milestone'), 'Milestone'), 'weight_md': weight})
    return {'id': ident, 'month': when, 'decision': deepcopy(decision), 'milestones': sorted(result, key=lambda r: r['nr'])}


def prepare(report, snapshot, target, initiative, period, inputs, supplied=None):
    spec = report['tracking']; fields = spec['fields']; sid = spec['section']
    supplied = {} if supplied is None else supplied
    _keys(supplied, {'baseline', 'scope_changes', 'assume_on_plan', 'legacy_ack', 'corrections', 'planning', 'future_factor'}, 'Meetinvoer')
    history = report_history.load(report, snapshot, target, initiative)
    previous = history['records'][-1] if history['records'] else None
    if previous and period <= previous['period']:
        raise ValueError('Deze of een latere rapportmaand bestaat al; historische rapporten niet overschrijven')
    result = {'inputs': deepcopy(inputs), 'questions': [], 'notes': [], 'state': None,
              'history': history, 'guard': report_history.guard(report, snapshot, target, initiative)}
    def ask(message):
        result['questions'].append({'section': sid, 'question': message})
    if 'report_pages' not in snapshot:
        ask('Deze bronmomentopname mist rapporthistoriek; verzamel opnieuw met de huidige collector.')
        return result
    base = baseline(previous['baseline']) if previous else None
    if supplied.get('baseline') is not None:
        candidate = baseline(supplied['baseline'])
        if base is not None and candidate != base:
            raise ValueError('Oorspronkelijke baseline is onveranderlijk; eerst een afzonderlijke review')
        base = candidate
    if base is None:
        ask('Leg de oorspronkelijke scopegewichten, het startbudget en de maandplanning met bron vast als baseline.')
        return result
    if month(period) < base['plan'][0]['period']:
        raise ValueError('Rapportperiode ligt vóór de oorspronkelijke planning')
    changes = deepcopy(previous['scope_changes']) if previous else []
    proposed = supplied.get('scope_changes', [])
    if not isinstance(proposed, list):
        raise ValueError('Scopebesluiten moeten een lijst zijn')
    known = {c['id']: c for c in changes}
    for raw in proposed:
        change = scope_change(raw)
        if change['id'] in known:
            if change != known[change['id']]:
                raise ValueError('Een bestaand scopebesluit is onveranderlijk')
            continue
        if change['month'] > period or (previous and change['month'] <= previous['period']) or change['month'] < base['plan'][0]['period']:
            raise ValueError('Nieuw scopebesluit ligt in de toekomst of wijzigt reeds vastgelegde historiek')
        changes.append(change); known[change['id']] = change
    changes.sort(key=lambda c: (c['month'], c['id']))
    if previous and changes[:len(previous['scope_changes'])] != previous['scope_changes']:
        raise ValueError('Bestaande scopehistoriek mag niet worden herschikt')
    weights = {r['nr']: {'weight': Decimal(r['planned_md']), 'planned': Decimal(r['planned_md']), 'added': False} for r in base['milestones']}
    for change in changes:
        for row in change['milestones']:
            if row['nr'] in weights:
                raise ValueError('Milestonenummer wordt hergebruikt in een scopebesluit')
            weights[row['nr']] = {'weight': Decimal(row['weight_md']), 'planned': Decimal(0), 'added': True}
    ack = deepcopy(previous.get('legacy_ack')) if previous else None
    if 'legacy_ack' in supplied:
        ack = supplied['legacy_ack']
        _keys(ack, {'pages', 'reason'}, 'Erkenning oude rapporten')
        if not isinstance(ack.get('pages'), list) or any(not isinstance(x, str) or not x.isdigit() for x in ack['pages']):
            raise ValueError('Erkenning vraagt een lijst pagina-id’s')
        _text(ack.get('reason'), 'Reden voor nieuwe meetstart')
    if set(history['legacy'])-set((ack or {}).get('pages', [])):
        ask('Oude rapporten zonder meetstand: '+', '.join(history['legacy'])+'. Erken deze expliciet met legacy_ack en motiveer de nieuwe meetstart; geen historie verzinnen.')
    if ack:
        result['notes'].append('Oude rapporten worden niet omgerekend: '+', '.join(ack['pages'])+'. Afspraak meetstart: '+ack['reason'])
    corrections = supplied.get('corrections', [])
    if not isinstance(corrections, list):
        raise ValueError('Correctietoelichtingen moeten een lijst zijn')
    reasons = {}
    for item in corrections:
        _keys(item, {'nr', 'reason'}, 'Correctietoelichting')
        ident = nr(item.get('nr'))
        if ident in reasons or ident not in weights:
            raise ValueError('Dubbele of onbekende milestone in correctietoelichting')
        reasons[ident] = _text(item.get('reason'), 'Correctiereden')
        result['notes'].append(f'Expliciete correctietoelichting milestone {ident}: '+reasons[ident])
    assume = supplied.get('assume_on_plan', False)
    if type(assume) is not bool:
        raise ValueError('assume_on_plan moet true of false zijn')
    rows = result['inputs'].get(sid, [])
    if not isinstance(rows, list):
        raise ValueError('Milestones moeten een lijst rijen zijn')
    normalized, seen, remaining_questions = [], set(), []
    old_rows = {r['nr']: r for r in previous['milestones']} if previous else {}
    categories = {a.strip().casefold(): group for group in ('delivered', 'backlog') for a in spec[group]}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Milestone moet een object zijn')
        if blank(row.get(fields['id'])):
            continue  # Generic input validation asks for the missing identifier.
        ident = nr(row[fields['id']])
        if ident in seen:
            raise ValueError('Dubbele milestone in maandstand')
        seen.add(ident)
        if ident not in weights:
            ask(f'Milestone {ident} staat niet in de baseline of goedgekeurde scope; eerst een scopebesluit vastleggen.')
            continue
        status = row.get(fields['status'])
        if not isinstance(status, str) or not status.strip():
            ask(f'Milestone {ident}: de voortgangsstatus ontbreekt voor de meting.')
            continue
        category = categories.get(status.strip().casefold(), 'other')
        actual = amount(row.get(fields['actual']), f'Milestone {ident} Actual')
        remaining = amount(row.get(fields['remaining']), f'Milestone {ident} Remaining')
        supplied_baseline = amount(row.get(fields['baseline']), f'Milestone {ident} Baseline')
        weight = weights[ident]
        if category == 'delivered':
            if remaining is not None and Decimal(remaining) != 0:
                ask(f'Milestone {ident} is opgeleverd maar heeft Remaining > 0; verduidelijk de tegenspraak.')
            elif remaining is None:
                remaining = '0'; row[fields['remaining']] = 0
        elif remaining is None:
            if category == 'backlog' and not weight['added'] and weight['planned'] > 0:
                remaining = text(weight['planned']); row[fields['remaining']] = remaining
            else:
                remaining_questions.append((f'Milestone {ident}: Remaining ontbreekt; onbekend is niet nul. Geef ook bij nieuwe scope een expliciete schatting.', weight['added']))
        elif Decimal(remaining) == 0:
            ask(f'Milestone {ident}: Remaining is nul maar de milestone is niet opgeleverd; verduidelijk, niet automatisch afsluiten.')
        # Baseline is the fixed original estimate (baseline or approved scope weight); it never follows Actual/Remaining.
        initial = text(weight['weight'])
        if supplied_baseline is not None and Decimal(supplied_baseline) != weight['weight']:
            result['notes'].append(f'Milestone {ident}: ingevulde Baseline {supplied_baseline} genegeerd; Baseline is de oorspronkelijke inschatting ({initial}) en wijzigt niet.')
        row[fields['baseline']] = initial
        expected = text(Decimal(actual)+Decimal(remaining)) if actual is not None and remaining is not None else None
        old = old_rows.get(ident)
        if old and old['delivered'] and category != 'delivered':
            ask(f'Milestone {ident} was al opgeleverd; heropening vraagt afzonderlijke review.')
        if old and old['actual_md'] is not None and actual is not None and Decimal(actual) < Decimal(old['actual_md']) and ident not in reasons:
            ask(f'Milestone {ident}: cumulatieve Actual is gedaald; geef een expliciete correctietoelichting.')
        normalized.append({'nr': ident, 'milestone': row.get(fields['name']), 'status': status, 'delivered': category == 'delivered',
                           'weight_md': text(weight['weight']), 'actual_md': actual, 'remaining_md': remaining, 'baseline_md': initial,
                           'expected_md': expected, 'backlog': category == 'backlog'})
    missing = set(weights)-seen
    if missing:
        ask('Goedgekeurde milestones ontbreken in de maandstand: '+', '.join(map(str, sorted(missing)))+'. Niet stilzwijgend verwijderen.')
    if len(normalized) != len(weights):
        return result
    denominator = sum((Decimal(r['planned_md']) for r in base['milestones']), Decimal(0))
    delivered = sum((Decimal(r['weight_md']) for r in normalized if r['delivered']), Decimal(0))
    approved = sum((r['weight'] for r in weights.values()), Decimal(0))
    estimate = Decimal(0)
    for row in normalized:
        if row['delivered']:
            fraction = Decimal(1)
        elif row['actual_md'] is None or row['remaining_md'] is None or Decimal(row['actual_md'])+Decimal(row['remaining_md']) == 0:
            estimate = None
            break
        else:
            fraction = Decimal(row['actual_md'])/(Decimal(row['actual_md'])+Decimal(row['remaining_md']))
        estimate += Decimal(row['weight_md'])*fraction
    effort = None if any(r['actual_md'] is None for r in normalized) else sum((Decimal(r['actual_md']) for r in normalized), Decimal(0))
    assumed = None
    if assume:
        if delivered or any(Decimal(r['metrics']['delivered_md']) for r in history['records']):
            raise ValueError('Aanname volgens plan kan alleen vóór de eerste formele oplevering')
        if estimate is not None:
            raise ValueError('Er is al een Actual/Remaining-inschatting; die niet vervangen door een planaanname')
        point = next((p for p in base['plan'] if p['period'] == period), None)
        if point is None:
            raise ValueError('Geen oorspronkelijk planpunt voor deze maand; geen aanname interpoleren')
        assumed = point['scope_md']
        result['notes'].append('Expliciete vroege aanname: volgens plan. Actual/Remaining zijn nog niet betrouwbaar beschikbaar; dit is geen gemeten voortgang.')
    else:
        for question, _ in remaining_questions:
            ask(question)
    if assume:
        for question, added in remaining_questions:
            if added:ask(question)
    if effort is None:
        result['notes'].append('Actual is niet voor alle milestones bekend; totale inzet blijft onbekend, niet gedeeltelijk opgeteld of nul.')
    if estimate is None and not assume:
        result['notes'].append('Geen volledige Actual/Remaining-inschatting; de gestippelde voortgang blijft deze maand leeg.')
    metrics = {'delivered_md': text(delivered), 'estimated_md': text(estimate), 'approved_md': text(approved),
               'actual_md': text(effort), 'assumed_md': assumed, 'scope_denominator_md': text(denominator),
               'budget_md': base['budget_md'], 'done': all(r['delivered'] for r in normalized)}
    # Effort in the reported month: growth of cumulative Actual since the previous measurement.
    # First report or newly added milestone: the full Actual counts. Unknown stays unknown.
    period_effort = Decimal(0)
    for row in normalized:
        old = old_rows.get(row['nr'])
        if row['actual_md'] is None or (old and old['actual_md'] is None):
            period_effort = None
            break
        period_effort += Decimal(row['actual_md'])-(Decimal(old['actual_md']) if old else 0)
    if period_effort is None:
        result['notes'].append('Inzet in de rapportmaand onbekend: Actual van deze of de vorige stand ontbreekt.')
    elif period_effort < 0:
        result['notes'].append(f'Inzet in de rapportmaand is negatief ({text(period_effort)} md) door een correctie van Actual.')
    # Effort ratio: expected total / Baseline over delivered and running milestones (backlog excluded).
    # Floats on purpose: the browser computes the same IEEE values, so both sides project identically.
    measured = [r for r in normalized if not r['backlog']]
    ratio = None
    if measured and all(r['expected_md'] is not None for r in measured):
        baseline_sum = float(sum((Decimal(r['baseline_md']) for r in measured), Decimal(0)))
        if baseline_sum:
            ratio = float(sum((Decimal(r['expected_md']) for r in measured), Decimal(0)))/baseline_sum
    # Factor for backlog work in the projection only: absent = 1, 'ratio' = measured ratio, or an explicit number.
    choice = supplied.get('future_factor')
    if choice is None:
        factor = 1.0
    elif choice == 'ratio':
        factor = ratio if ratio is not None else 1.0
        if ratio is None:
            result['notes'].append('Gemeten ratio verwacht/Baseline is nog onbekend; backlog wordt met factor 1 geprojecteerd.')
    else:
        value = amount(choice, 'Factor voor toekomstig werk', positive=True)
        if value is None:
            raise ValueError('Factor voor toekomstig werk ontbreekt')
        factor = float(value)
    from . import monthly_planning
    planned, planning_questions = monthly_planning.normalize(supplied.get('planning'), period)
    for question in planning_questions:ask(question)
    planned = None if planning_questions else planned
    plan_summary = monthly_planning.summary(planned, text(effort), normalized)
    if plan_summary and plan_summary['difference_md'] not in (None, '0'):
        result['notes'].append('Resterende maandplanning: '+plan_summary['planned_remaining_md']+' md; Remaining volgens milestones: '+plan_summary['remaining_md']+' md. Verschil: '+plan_summary['difference_md']+' md. Controleer de verdeling of de inschatting; niets automatisch over milestones verdeeld.')
    result['state'] = {'version': 1, 'model': 'milestone_effort', 'report': report['id'], 'target': target, 'initiative': initiative,
                       'period': period, 'baseline': base, 'scope_changes': changes, 'milestones': normalized, 'metrics': metrics,
                       'planning': planned, 'planning_summary': plan_summary, 'period_actual_md': text(period_effort),
                       'effort_ratio': ratio, 'future_factor': factor,
                       'inputs': deepcopy(inputs), 'tracking_input': deepcopy(supplied), 'legacy_ack': ack,
                       'source_time': snapshot.get('collected_at'), 'previous_hash': previous['hash'] if previous else None}
    return result
