"""Monthly effort input and per-report future plans; never rewrite original baselines."""
from copy import deepcopy
import math
from decimal import Decimal, localcontext, ROUND_HALF_EVEN


def shape(rows):
    if rows is None:return
    if not isinstance(rows,list) or len(rows)>1200:raise ValueError('Maandplanning moet een lijst zijn (maximaal 1200 maanden)')
    for row in rows:
        if not isinstance(row,dict) or set(row)!={'period','effort_md'} or not isinstance(row['period'],str):
            raise ValueError('Planmaand: verwacht uitsluitend period en effort_md')
        value=row['effort_md']
        if value is not None and (isinstance(value,bool) or not isinstance(value,(str,int,float))):
            raise ValueError('Ongeldige inzetwaarde in maandplanning')


def normalize(rows, after=None):
    from .tracking import month, amount
    shape(rows)
    if rows is None:return None,[]
    out=[];problems=[];seen=set()
    for row in rows:
        when=row['period'];value=None
        try:
            month(when)
            if after and when<=after:raise ValueError('Resterende planning moet na de rapportmaand liggen: '+when)
            if when in seen:raise ValueError('Dubbele planmaand: '+when)
            seen.add(when)
        except ValueError as exc:problems.append(str(exc))
        try:
            value=amount(row['effort_md'],'Inzet '+when)
            if value is None:problems.append('Vul de maandinzet in voor '+(when or 'de planmaand')+'; onbekend is niet nul.')
        except ValueError as exc:problems.append(str(exc))
        out.append({'period':when,'effort_md':value})
    return sorted(out,key=lambda r:r['period']),problems


def from_baseline(base, after):
    """Only unambiguous monthly differences; gaps stay unknown, not spread or zeroed."""
    from .tracking import month, text, amount
    previous=None;amount_before=Decimal(0);out=[]
    for point in sorted(base['plan'],key=lambda p:p['period']):
        when=month(point['period']);value=Decimal(amount(point['effort_md']))
        index=int(when[:4])*12+int(when[5:])
        known=previous is None or index==previous+1
        if when>after:out.append({'period':when,'effort_md':text(value-amount_before) if known else None})
        previous=index;amount_before=value
    return out


def future(base, after, previous=None):
    if previous is not None:return [deepcopy(r) for r in previous if r['period']>after]
    return from_baseline(base,after)


def baseline_from_months(budget, milestones, rows, source):
    from .tracking import baseline, amount, text
    rows,problems=normalize(rows)
    if problems:raise ValueError('; '.join(problems))
    if not rows:raise ValueError('Voer minstens één planmaand in')
    budget=amount(budget,'Startbudget',positive=True)
    if budget is None:raise ValueError('Startbudget ontbreekt')
    scope=sum((Decimal(amount(r['planned_md'],'Milestoneplan')) for r in milestones),Decimal(0))
    running=Decimal(0);plan=[]
    with localcontext() as context:
        context.prec=160
        for row in rows:
            running+=Decimal(row['effort_md'])
            planned_scope=(running*scope/Decimal(budget)).quantize(Decimal('1e-28'),rounding=ROUND_HALF_EVEN)
            if running==Decimal(budget):planned_scope=scope
            plan.append({'period':row['period'],'scope_md':text(planned_scope),'effort_md':text(running)})
    return baseline({'budget_md':budget,'source':source,'milestones':milestones,'plan':plan})


def summary(rows, actual, milestones):
    from .tracking import text
    if rows is None:return None
    planned=sum((Decimal(r['effort_md']) for r in rows),Decimal(0))
    remaining=None if any(r['remaining_md'] is None for r in milestones) else sum((Decimal(r['remaining_md']) for r in milestones),Decimal(0))
    return {'planned_remaining_md':text(planned),'remaining_md':text(remaining),
            'end_total_md':None if actual is None else text(Decimal(actual)+planned),
            'difference_md':None if remaining is None else text(planned-remaining)}


def projected_remaining(state):
    """Remaining for the projection: backlog Remaining times the chosen factor, other milestones as estimated.
    With factor 1 exact decimals; otherwise float arithmetic rounded to 0.1 md, identical in the browser."""
    rows=state['milestones']
    if any(r['remaining_md'] is None for r in rows):return None
    plain=sum((Decimal(r['remaining_md']) for r in rows if not r.get('backlog')),Decimal(0))
    backlog=sum((Decimal(r['remaining_md']) for r in rows if r.get('backlog')),Decimal(0))
    factor=state.get('future_factor',1.0)
    if factor==1 or backlog==0:return plain+backlog
    return Decimal(repr(math.floor((float(plain)+float(backlog)*factor)*10+0.5)/10))


def cumulative(rows, state):
    """Per future month: cumulative effort, remaining work still open, and the scope expected from the plan.

    Planned effort is assumed to be spread over the open work of all milestones in proportion to their
    Remaining. Each milestone then delivers weight*Remaining/(Actual+Remaining) of its fixed weight, so the
    expected scope is estimated + (approved-estimated) * min(1, planned/remaining). Too little effort leaves
    the line below the approved scope; more effort reaches it earlier."""
    from .tracking import text
    metrics=state['metrics']
    total=None if metrics['actual_md'] is None else Decimal(metrics['actual_md'])
    remaining=projected_remaining(state)
    estimated=None if metrics['estimated_md'] is None else Decimal(metrics['estimated_md'])
    approved=Decimal(metrics['approved_md'])
    planned=Decimal(0);result=[]
    for row in rows or []:
        effort=None if row['effort_md'] is None else Decimal(row['effort_md'])
        total=None if total is None or effort is None else total+effort
        planned=None if planned is None or effort is None else planned+effort
        still_open=None if planned is None or remaining is None else max(Decimal(0),remaining-planned)
        if planned is None or remaining is None or estimated is None:scope=None
        elif remaining==0:scope=approved
        else:scope=estimated+(approved-estimated)*min(Decimal(1),planned/remaining)
        result.append({'period':row['period'],'effort_md':row['effort_md'],'total_md':text(total),'open_md':text(still_open),
                       'scope_md':None if scope is None else float(scope)})
    return result
