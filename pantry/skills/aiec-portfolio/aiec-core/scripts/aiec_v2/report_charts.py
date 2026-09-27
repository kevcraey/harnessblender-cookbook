"""Deterministic, self-contained PNG report charts. No browser, network, or model."""
from __future__ import annotations
import base64
from decimal import Decimal
from hashlib import sha256
from html import escape
from io import BytesIO
import math
from .tracking import months
from . import monthly_planning

# Flux-tokens (release 2.19.0), gelijk aan de grafiekreeksen in form/style.css en form/app.js.
BLACK = '#333332'  # grey-1000
BLUE = '#0055cc'  # action
TEAL = '#278e93'  # primary-niveau2-800
GRAY = '#8695a8'  # grey-600
GREEN = '#ecf6ee'  # success-100
ORANGE = '#9f5804'  # warning-800


def series(state, history):
    base = state['baseline']
    records = {r['period']: r for r in [*history, state]}
    plan = {p['period']: p for p in base['plan']}
    forward_rows=state.get('planning') or []
    # The x-axis stops once everything is delivered: at the report month when done, else when the planned
    # effort reaches the approved scope. Otherwise the full original plan and planning stay visible.
    future=monthly_planning.cumulative(forward_rows,state)
    approved_md=float(state['metrics']['approved_md'])
    reached=next((r['period'] for r in future if r['scope_md'] is not None and r['scope_md']>=approved_md-1e-9),None)
    if state['metrics']['done']:end=state['period']
    elif reached:end=max(state['period'],reached)
    else:end=max([max(plan), state['period']]+[r['period'] for r in forward_rows])
    periods = months(min(plan), end)
    scope = Decimal(state['metrics']['scope_denominator_md'])
    budget = Decimal(base['budget_md'])
    def pct(value, denominator):
        return None if value is None else float(Decimal(value)*100/denominator)
    data = {'periods': periods, 'as_of': state['period'], 'reported': [m in records for m in periods]}
    for name, metric, denominator in [('delivered', 'delivered_md', scope), ('estimated', 'estimated_md', scope),
                                       ('assumed', 'assumed_md', scope), ('actual', 'actual_md', budget)]:
        data[name] = [pct(records[m]['metrics'][metric], denominator) if m in records else None for m in periods]
    data['plan_scope'] = [pct(plan[m]['scope_md'], scope) if m in plan else None for m in periods]
    data['plan_effort'] = [pct(plan[m]['effort_md'], budget) if m in plan else None for m in periods]
    data['approved'] = [float((scope+sum((Decimal(r['weight_md']) for c in state['scope_changes'] if c['month'] <= m for r in c['milestones']), Decimal(0)))*100/scope) for m in periods]
    projected={state['period']:state['metrics']['actual_md']} if forward_rows else {}
    projected.update({r['period']:r['total_md'] for r in future})
    data['forward']=[pct(projected.get(m),budget) for m in periods]
    expected={r['period']:r['scope_md'] for r in future if r['scope_md'] is not None}
    if expected:expected[state['period']]=state['metrics']['estimated_md']
    data['expected_scope']=[pct(expected.get(m),scope) for m in periods]
    # A month without planned effort is zero effort: from the report month on, the projection runs flat to the end of the axis.
    def fill(values, anchor):
        if anchor is None or state['period'] not in periods:return values
        i = periods.index(state['period']); out = list(values)
        if out[i] is None:out[i] = anchor
        for k in range(i+1, len(out)):
            if out[k] is None:out[k] = out[k-1]
        return out
    if state.get('planning') is not None:
        data['forward'] = fill(data['forward'], pct(state['metrics']['actual_md'], budget))
        data['expected_scope'] = fill(data['expected_scope'], pct(state['metrics']['estimated_md'], scope))
    # Show the plan-based lines only when they deviate from the original plan somewhere.
    def deviates(values, reference):
        return any(v is not None and (r is None or abs(v-r) >= 0.05) for v, r in zip(values, reference))
    for key, reference in (('forward', 'plan_effort'), ('expected_scope', 'plan_scope')):
        if not deviates(data[key], data[reference]):data[key]=[None]*len(periods)
    # Each chart gets its own scale: an effort overrun must not stretch the scope chart.
    def scale(keys):
        values = [v for key in keys for v in data[key] if v is not None]
        return max(140, math.ceil((max(values+[100])+10)/20)*20)
    data['y_max_scope'] = scale(('delivered', 'estimated', 'assumed', 'plan_scope', 'approved', 'expected_scope'))
    data['y_max_effort'] = scale(('actual', 'plan_effort', 'forward'))
    return data


def runs(values):
    result, current = [], []
    for index, value in enumerate(values):
        if value is None:
            if current:
                result.append(current)
            current = []
        else:
            current.append((index, value))
    if current:
        result.append(current)
    return result


def label_indices(count, maximum):
    stride = max(1, math.ceil(count/maximum))
    indices = list(range(0, count, stride))
    if count-1 not in indices:
        if indices and count-1-indices[-1] < stride:indices.pop()
        indices.append(count-1)
    return indices


def png(data, kind, width=1000):
    from PIL import Image, ImageDraw, ImageFont
    scale = 2
    if width not in (600, 1000):raise ValueError('Onbekend grafiekformaat')
    height = 675
    compact = width == 600
    image = Image.new('RGB', (width*scale, height*scale), '#ffffff')
    draw = ImageDraw.Draw(image)
    fonts = {}
    def font(size):
        if size not in fonts:
            fonts[size] = ImageFont.load_default(size=size*scale)
        return fonts[size]
    def label(x, y, value, size=19, color='#333332', anchor='lt'):
        draw.text((round(x*scale), round(y*scale)), str(value), fill=color, font=font(size), anchor=anchor)
    def line(points, color, thick=2, dotted=False):
        points = [(x*scale, y*scale) for x, y in points]
        if not dotted:
            draw.line(points, fill=color, width=round(thick*scale))
            return
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            distance = math.hypot(x2-x1, y2-y1)
            if distance == 0:
                continue
            for step in range(0, math.ceil(distance), 7*scale):
                f = min(step/distance, 1)
                x, y = x1+(x2-x1)*f, y1+(y2-y1)*f
                radius = thick*scale/2
                draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=color)
    def rect(box, fill):
        draw.rectangle(tuple(round(v*scale) for v in box), fill=fill)
    def point(x, y, color, hollow=False):
        r = 4*scale
        draw.ellipse((x*scale-r, y*scale-r, x*scale+r, y*scale+r), fill='#ffffff' if hollow else color, outline=color, width=2*scale)
    scope = kind == 'scope'
    y_max = data['y_max_scope' if scope else 'y_max_effort']
    label(34, 13, 'Scope' if scope else 'Inzet', 26)
    items = [(BLACK, 'Plan (oorspronkelijk)', False, False), (BLUE, 'Opgeleverd' if scope else 'Werkelijk besteed', False, False)]
    if scope:
        items += [(BLUE, 'Opgeleverd incl. lopend', True, False), (TEAL, 'Goedgekeurde scope', True, False)]
    if not scope and any(v is not None for v in data.get('forward',[])):
        items.append((ORANGE, 'Actuele inzetplanning', True, False))
    if scope and any(v is not None for v in data['assumed']):
        items.append((GRAY, 'Aanname: volgens plan', True, False))
    if scope and any(v is not None for v in data.get('expected_scope', [])):
        items.append((ORANGE, 'Verwacht volgens inzetplanning', True, False))
    # A small legend that wraps to the chart width instead of fixed slots.
    size = 17 if compact else 14
    lx, ly = 34, 58
    for color, name, dotted, box in items:
        w = 30+draw.textlength(name, font=font(size))/scale+22
        if lx+w > width-20 and lx > 34:
            lx, ly = 34, ly+size+10
        if box:
            rect((lx, ly+2, lx+22, ly+size-2), GREEN)
        else:
            line([(lx, ly+size*.55), (lx+22, ly+size*.55)], color, 2.5, dotted)
        label(lx+30, ly, name, size)
        lx += w
    left, right, top, bottom = 95, 65, ly+size+45, 628
    count = len(data['periods'])
    pw, ph = width-left-right, bottom-top
    def x(i):
        return left+(i/(count-1) if count > 1 else .5)*pw
    def y(v):
        return bottom-v/y_max*ph
    step = pw/max(1, count-1)
    # Future: one zone starting at the current report's point. Missing past reports: a bar per month.
    first_future = next((i for i, period in enumerate(data['periods']) if period > data['as_of']), None)
    if first_future is not None:
        rect((x(first_future-1) if first_future > 0 else left, top, width-right, bottom), '#f7f9fc')
    for i, period in enumerate(data['periods']):
        if period <= data['as_of'] and not data['reported'][i]:
            rect((max(left, x(i)-step*.24), top, min(width-right, x(i)+step*.24), bottom), '#f7f9fc')
    plan = data['plan_scope' if scope else 'plan_effort']
    for run in runs(plan):
        polygon = [(x(i), y(v+10)) for i, v in run]+[(x(i), y(max(0, v-10))) for i, v in reversed(run)]
        if len(run) > 1:
            draw.polygon([(a*scale, b*scale) for a, b in polygon], fill=GREEN)
    # A bounded number of ticks even with extreme overspend; the values themselves are not capped.
    tick_step = 20*max(1, math.ceil(y_max/140))
    ticks = list(range(0, y_max+1, tick_step))
    if ticks[-1] != y_max:ticks.append(y_max)
    for tick in ticks:
        line([(left, y(tick)), (width-right, y(tick))], '#eceff4', 1)
        label(left-12, y(tick), f'{tick:.3g}%', 17, '#687483', 'rm')
    for i in label_indices(count, max(3, int(pw/85))):
        label(x(i), bottom+18, data['periods'][i], 16, '#687483', 'mt')
    def plot(values, color, dotted=False, hollow=False):
        for run in runs(values):
            if len(run) > 1:
                line([(x(i), y(v)) for i, v in run], color, 3, dotted)
            for i, v in run:
                point(x(i), y(v), color, hollow)
    plot(plan, BLACK)
    if scope:
        limit = data['approved']
        steps = [(x(0), y(limit[0]))]
        for i in range(1, count):
            steps += [(x(i), y(limit[i-1])), (x(i), y(limit[i]))]
        if len(steps) > 1:
            line(steps, TEAL, 2, True)
        plot(data.get('expected_scope', [None]*count), ORANGE, True, True)
        plot(data['estimated'], BLUE, True, True)
        plot(data['assumed'], GRAY, True, True)
    # The planning starts at the current Actual: draw it first so the measured point stays visible on top.
    if not scope:plot(data.get('forward',[None]*count), ORANGE, True, True)
    plot(data['delivered' if scope else 'actual'], BLUE)
    stream = BytesIO()
    image.save(stream, format='PNG', optimize=False, compress_level=9)
    return stream.getvalue()


def build(state, history):
    data = series(state, history)
    assets = []
    for kind in ('scope', 'effort'):
        content = png(data, kind)
        assets.append({'filename': f"aiec-{state['report']}-{state['target'].lower()}-{state['period']}-{kind}.png",
                       'media_type': 'image/png', 'sha256': sha256(content).hexdigest(),
                       'content_base64': base64.b64encode(content).decode(), 'kind': kind})
    return data, assets


def pct(value, denominator):
    return 'onbekend' if value is None else f'{Decimal(value)*100/Decimal(denominator):.1f}%'.replace('.', ',')


def headline(state):
    """The two numbers next to the health flag: delivered scope and spent budget, against the meetbasis."""
    metrics = state['metrics']
    return [('Opgeleverde scope', pct(metrics['delivered_md'], metrics['scope_denominator_md'])+' van de oorspronkelijke scope'),
            ('Besteed budget', pct(metrics['actual_md'], metrics['budget_md'])+' van het oorspronkelijke budget')]


def fragments(state, data, assets):
    metrics = state['metrics']
    summary = ('Opgeleverd: '+pct(metrics['delivered_md'], metrics['scope_denominator_md'])+
               '; goedgekeurde scope: '+pct(metrics['approved_md'], metrics['scope_denominator_md'])+
               '; inclusief lopend werk: '+pct(metrics['estimated_md'], metrics['scope_denominator_md'])+
               '; werkelijk besteed: '+pct(metrics['actual_md'], metrics['budget_md'])+'.')
    detail = ('Inclusief lopend werk: '+pct(metrics['estimated_md'], metrics['scope_denominator_md'])+
              '; goedgekeurde scope: '+pct(metrics['approved_md'], metrics['scope_denominator_md'])+'.')
    done = 'Alle goedgekeurde milestones zijn opgeleverd.' if metrics['done'] else 'Nog niet alle goedgekeurde milestones zijn opgeleverd.'
    # The monthly planning itself is visible as the orange lines; only a scaled projection needs a word.
    factor = state.get('future_factor', 1.0)
    scaled = [] if state.get('planning') is None or factor == 1 else ['Backlog is in de projectie geschaald met factor '+f'{factor:.2f}'.replace('.', ',')+'.']
    md = ['## Scope en inzet', '', detail, done, *scaled, '', 'Elke grafiek: zwart Plan; blauw vol Opgeleverd / Werkelijk besteed; blauw gestippeld Opgeleverd incl. lopend. Oranje gestippeld: actuele inzetplanning en de scope die daarmee verwacht wordt. Groen: ±10 procentpunt.', '']
    text = '<p>'+escape(detail)+' '+done+'</p>'+''.join('<p>'+escape(line)+'</p>' for line in scaled)
    storage = '<h2>Scope en inzet</h2>'+text
    preview = storage+'<div class="report-charts">'
    for asset in assets:
        title = 'Scope' if asset['kind'] == 'scope' else 'Inzet'
        alt = title+' — '+summary+' Legende: zwart Plan; blauw vol Opgeleverd of Werkelijk besteed; blauw gestippeld Opgeleverd incl. lopend.'
        storage += '<p><ac:image ac:width="900" ac:alt="'+escape(alt, quote=True)+'"><ri:attachment ri:filename="'+escape(asset['filename'], quote=True)+'"/></ac:image></p>'
        mobile = base64.b64encode(png(data, asset['kind'], width=600)).decode()
        preview += '<figure><picture><source media="(max-width:600px)" srcset="data:image/png;base64,'+mobile+'"/><img alt="'+escape(alt, quote=True)+'" src="data:image/png;base64,'+asset['content_base64']+'"/></picture></figure>'
    preview += '</div>'
    return md, storage, preview


def appendix(state, data):
    """Confluence gets only the progress history; the preview also shows the meetbasis and scope decisions for the approver."""
    headers = ['Maand', 'Plan scope', 'Opgeleverd', 'Incl. lopend', 'Goedgekeurd', 'Aanname', 'Plan inzet', 'Besteed']
    rows = []
    for i, period in enumerate(data['periods']):
        values = [data[k][i] for k in ('plan_scope', 'delivered', 'estimated', 'approved', 'assumed', 'plan_effort', 'actual')]
        rows.append([period+(' · geen rapport' if not data['reported'][i] else '')]+['onbekend' if v is None else f'{v:.1f}%'.replace('.', ',') for v in values])
    table = '<table><thead><tr>'+''.join('<th>'+h+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+v+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table>'
    base = state['baseline']
    basis = ('<p>Oorspronkelijk budget: '+escape(base['budget_md'])+' md. Bron: '+escape(base['source'])+'</p><table><thead><tr><th>Nr</th><th>Oorspronkelijke milestone</th><th>Baseline (md)</th></tr></thead><tbody>'+
             ''.join('<tr><td>'+str(r['nr'])+'</td><td>'+escape(r['milestone'])+'</td><td>'+escape(r['planned_md'])+'</td></tr>' for r in base['milestones'])+'</tbody></table>')
    md = ['## Meetbasis en scopebesluiten (enkel ter goedkeuring)', '', 'Oorspronkelijk budget: '+base['budget_md']+' md. Bron: '+base['source'], '']
    for change in state['scope_changes']:
        description = 'Scopebesluit '+change['id']+' · '+change['month']+' · '+change['decision']['by']+' · '+change['decision']['source']+'. Toegevoegd: '+', '.join(str(r['nr'])+' '+r['milestone']+' ('+r['weight_md']+' md vast gewicht)' for r in change['milestones'])+'.'
        basis += '<p>'+escape(description)+'</p>'; md += [description, '']
    md += ['## Vooruitgangshistoriek', '', '| '+' | '.join(headers)+' |', '| '+' | '.join('---' for _ in headers)+' |']+['| '+' | '.join(row)+' |' for row in rows]+['']
    storage = ('<ac:structured-macro ac:name="expand"><ac:parameter ac:name="title">Vooruitgangshistoriek</ac:parameter>'
               '<ac:rich-text-body>'+table+'</ac:rich-text-body></ac:structured-macro>')
    preview = ''.join('<details class="appendix"><summary>'+title+'</summary>'+content+'</details>'
                      for title, content in (('Vooruitgangshistoriek', table), ('Meetbasis en scopebesluiten (enkel ter goedkeuring, niet in Confluence)', basis)))
    return md, storage, preview
