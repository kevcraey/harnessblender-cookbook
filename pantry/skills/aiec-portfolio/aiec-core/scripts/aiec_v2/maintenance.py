"""Maintenance plan: criticality from the outage matrix, yearly cost from the investment, one active plan per product.

The properties block (aiec-onderhoud) is the interface for a later portfolio sum: fixed labels,
Status exactly 'Actief' or 'Vervangen', numbers with a decimal comma or 'onvolledig'.
"""
from __future__ import annotations
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from html import escape
import re
from aiec_lib import confluence as conf
from .report_inputs import number

DETAILS_ID = 'aiec-onderhoud'
DURATIONS = ['15m', '30m', '1u', '4u', '1d', '1w']
# Named classes: P1–P3 are already the pillar codes.
FIXED_MD = Decimal('10')
SHARE = {'kritisch': Decimal('0.15'), 'belangrijk': Decimal('0.125'), 'standaard': Decimal('0.10')}
# A yearly upgrade per model; cheaper when a reference dataset can test the new version.
MODEL_MD = {'ja': Decimal('5'), 'nee': Decimal('10')}
REQUIRED_SECTIONS = {'product', 'uitval', 'buiten_kantooruren', 'as_is', 'modellen', 'runkost', 'producten'}
# Consumed by the calculation or shown with derived data; rendered by this module, not as a plain input section.
HIDDEN = {'product', 'as_is', 'buiten_kantooruren', 'modellen', 'runkost', 'producten'}
AI_TAG = ('<ac:structured-macro ac:name="status" ac:schema-version="1"><ac:parameter ac:name="colour">Yellow</ac:parameter>'
          '<ac:parameter ac:name="title">AI</ac:parameter></ac:structured-macro>')


def validate(cat_reports, report):
    spec = report.get('maintenance')
    if spec is None: return
    ids = {s['id'] for s in report['sections']}
    if (report.get('scope') != 'project' or report.get('tracking') or report.get('tracking_source') or not isinstance(spec, dict)
            or set(spec) != {'source'} or not (cat_reports.get(spec['source']) or {}).get('tracking') or REQUIRED_SECTIONS - ids):
        raise ValueError('maintenance vraagt een projectrapport zonder meting, een bronrapport met meting en de secties '+', '.join(sorted(REQUIRED_SECTIONS)))


def text(value):
    """Decimal comma, no trailing zeros; None is 'onvolledig'."""
    if value is None: return 'onvolledig'
    out = format(value.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP).normalize(), 'f')
    return out.replace('.', ',')


def parse(value):
    raw = (value or '').strip().replace(',', '.')
    return Decimal(raw) if re.fullmatch(r'\d+(?:\.\d+)?', raw) else None


def klasse(impacts):
    """Kritisch: groot (4) within an hour; belangrijk: groot within a working day or merkbaar (3) within four hours; else standaard."""
    if impacts['1u'] >= 4: return 'kritisch'
    if impacts['1d'] >= 4 or impacts['4u'] >= 3: return 'belangrijk'
    return 'standaard'


def link(title):
    # The link body keeps the title readable for parse_properties; a bare ri:page link has no text.
    t = escape(title, quote=True)
    return f'<ac:link><ri:page ri:content-title="{t}"/><ac:link-body>{escape(title)}</ac:link-body></ac:link>'


def valid_until(day):
    try: return day.replace(year=day.year+1)
    except ValueError: return day.replace(year=day.year+1, day=28)


def prepare(cat, spec, snapshot, data, target, initiative, period, inputs, datum):
    from . import report_history
    questions, notes = [], []
    ask = lambda section, question: questions.append({'section': section, 'question': question})
    # Product: the one linked to the initiative, or the one named in the input.
    linked = {p['key']: p for p in data['products'] if initiative in p.get('initiatives', [])}
    wanted = (inputs.get('product') or '').strip()
    product = None
    if wanted:
        if wanted not in linked: raise ValueError(f'{wanted} is geen product (PROD) gekoppeld aan {initiative}')
        product = linked[wanted]
    elif len(linked) == 1: product = next(iter(linked.values()))
    elif not linked: ask('product', f'Geen product (PROD) gekoppeld aan {initiative}. Koppel het in Jira; een project zonder product heeft geen onderhoudsplan nodig.')
    else: ask('product', 'Meer dan één product gekoppeld ('+', '.join(sorted(linked))+'); geef aan voor welk product dit plan geldt.')
    # Criticality: all six durations, impact never lower for a longer outage.
    rows = inputs.get('uitval') or []
    # Rows are validated by render_input first; missing rows or cells are its questions.
    impacts = {r['duur']: int(r['impact']) for r in rows if r.get('duur') and r.get('impact')}
    level = None
    if len(impacts) == len(DURATIONS):
        seq = [impacts[d] for d in DURATIONS]
        if any(a > b for a, b in zip(seq, seq[1:])): raise ValueError('Impact van uitval mag niet dalen naarmate de uitval langer duurt')
        level = klasse(impacts)
        if level == 'standaard' and inputs.get('buiten_kantooruren') == 'ja':
            notes.append('Ondersteuning buiten de kantooruren gevraagd bij klasse standaard; controleer of dat nodig is.')
    # Delta: Actual of the last progress report of this project.
    source = cat.reports[spec['maintenance']['source']]
    guard, delta = None, None
    if 'report_pages' not in snapshot or 'meetstanden' not in snapshot:
        ask('as_is', 'Deze bronmomentopname mist rapporthistoriek of meetstanden; verzamel opnieuw met de huidige collector.')
    else:
        history = report_history.load(source, snapshot, target, initiative)
        guard = report_history.guard(source, snapshot, target, initiative)
        if not history['records']:
            ask('as_is', f'Nog geen {source["title"].lower()}srapport met meetstand voor {target}; publiceer eerst het laatste {source["title"].lower()}srapport.')
        else:
            last = history['records'][-1]
            if period < last['period']: raise ValueError('Periode ligt vóór het laatste '+source['title'].lower()+'srapport ('+last['period']+')')
            actual = last['metrics'].get('actual_md')
            delta = None if actual is None else Decimal(str(actual))
            if delta is None: notes.append('Actual van het laatste vooruitgangsrapport is onbekend; de begroting is onvolledig.')
    # As-is: the active plan of the same product, across initiatives; without one, a human answer.
    previous, legacy = [], []
    for a in data['artifacts']:
        if 'onderhoudsplan' not in a.get('labels', []): continue
        props = conf.parse_properties(cat.schema, a.get('storage', ''), DETAILS_ID)
        if not props:
            if a.get('initiative') == initiative: legacy.append(a['title'])
        elif product and (props.get('Product') or '').split(' ')[0] == product['key'] and props.get('Status') == 'Actief':
            previous.append((a, props))
    if legacy: notes.append('Onderhoudsplannen zonder productkoppeling onder dit initiatief, niet automatisch vervangen: '+', '.join(sorted(legacy))+'.')
    if len(previous) > 1: raise ValueError(f"Meer dan één actief onderhoudsplan voor {product['key']}: "+', '.join(sorted(a['title'] for a, _ in previous)))
    replaces = None; as_is = None; as_is_bron = ''
    given = inputs.get('as_is') or []
    if previous:
        a, props = previous[0]
        if given: raise ValueError('Bestaande investering komt uit het vorige onderhoudsplan ('+a['title']+'); laat as_is leeg')
        replaces = {'page_id': str(a['page_id']), 'title': a['title']}
        # A new project builds on the whole previous investment; a corrected plan of the same project keeps its as-is.
        same = props.get('Project') == target
        as_is = parse(props.get('As-is (md)' if same else 'Investering (md)'))
        if as_is is None: notes.append('Investering in het vorige onderhoudsplan is onvolledig; de begroting blijft onvolledig.')
    elif product:
        if not given: ask('as_is', f"Geen vorig onderhoudsplan voor {product['key']}: geef de bestaande investering in md (0 bij green field) met bron, of laat md leeg als ze onbekend is.")
        elif len(given) > 1: raise ValueError('Bestaande investering: één rij')
        else:
            md = given[0].get('md')
            as_is = None if md is None or str(md).strip() == '' else Decimal(number(md, {'title': 'Investering (md)', 'type': 'decimal'}))
            as_is_bron = (given[0].get('bron') or '').strip()
            if as_is is None: notes.append('Bestaande investering onbekend; de begroting is onvolledig en telt niet mee in een som.')
    total = None if as_is is None or delta is None else as_is+delta
    # An absent list is a forgotten answer; an empty list means no model.
    if 'modellen' not in inputs: ask('modellen', 'Welke (taal)modellen gebruikt de toepassing, met of zonder referentiedataset? Geen AI-model? Geef een lege lijst.')
    models = [m for m in inputs.get('modellen') or [] if m.get('referentiedataset') in MODEL_MD]
    share = lambda part: None if part is None or level is None else SHARE[level]*part
    # Traceability of the existing investment: the previous plan, or the source given without one.
    existing = 'Recurrent obv bestaande investering'
    existing_html = escape(existing)+(': '+link(replaces['title']) if replaces else f' ({escape(as_is_bron)})' if as_is_bron else '')
    existing += f": {replaces['title']}" if replaces else f' ({as_is_bron})' if as_is_bron else ''
    cost = [('Basiskost (technische upgrades, security, ...)', FIXED_MD, False),
            (existing, share(as_is), False),
            ('Recurrent obv nieuwe investering', share(delta), False)]
    cost += [(f"Upgrade {m['model']} ({m['component']}), {'met' if m['referentiedataset'] == 'ja' else 'zonder'} referentiedataset", MODEL_MD[m['referentiedataset']], True) for m in models] \
        or [('Upgrades van (taal)modellen', Decimal(0), True)]
    yearly = None if any(v is None for _, v, _ in cost) else sum((v for _, v, _ in cost), Decimal(0))
    costs = [r for r in inputs.get('runkost') or [] if isinstance(r, dict) and str(r.get('bedrag') or '').strip()]
    run = sum((Decimal(number(r['bedrag'], {'title': 'Bedrag', 'type': 'decimal'})) for r in costs), Decimal(0))
    until = valid_until(date.fromisoformat(datum)).isoformat()
    after = {}
    if level:
        line = f'→ Afgeleide klasse: {level}.'
        after['uitval'] = ([line, ''], '<p><strong>'+escape(line)+'</strong></p>')
    md_text = lambda v: 'onvolledig' if v is None else text(v)+' md'
    rows_md = ['### Onderhoudskost', '', 'Jaarlijks terugkerende kost.', '', '| Post | Kost |', '| --- | --- |']
    rows_md += [f'| {name}{" (AI)" if ai else ""} | {md_text(v)} |' for name, v, ai in cost]+[f'| **Totaal** | **{md_text(yearly)}** |', '']
    model = ['10 md vast', '+ 15% (kritisch), 12,5% (belangrijk) of 10% (standaard) van de totale investering.',
             '5 md upgrade taalmodel indien referentiedataset beschikbaar, 10 md indien niet.']
    rows_md += ['Model:', '']+['- '+m for m in model]+['']
    cell = lambda name, ai: (existing_html if name == existing else escape(name))+(' '+AI_TAG if ai else '')
    storage = ('<h3>Onderhoudskost</h3><p>Jaarlijks terugkerende kost.</p><table><tbody><tr><th>Post</th><th>Kost</th></tr>'
               +''.join(f'<tr><td>{cell(name, ai)}</td><td>{md_text(v)}</td></tr>' for name, v, ai in cost)
               +f'<tr><th>Totaal</th><th>{md_text(yearly)}</th></tr></tbody></table>'
               +'<p>Model:</p><ul>'+''.join('<li>'+escape(m)+'</li>' for m in model)+'</ul>')
    after['as_is'] = (rows_md, storage)
    # Models: end of support and the plan after it; no section without a model.
    if models:
        heads = ['Onderdeel', 'Model en versie', 'Einde ondersteuning', 'Plan van aanpak', 'Referentiedataset']
        mrows = [[m['component'], m['model'], (m.get('einde') or '').strip() or 'onbekend', m.get('aanpak') or '', 'Ja' if m['referentiedataset'] == 'ja' else 'Nee'] for m in models]
        after['modellen'] = (['## Modellen', '', '| '+' | '.join(heads)+' |', '|'+' --- |'*len(heads)]+['| '+' | '.join(r)+' |' for r in mrows]+[''],
                             '<h2>Modellen</h2><table><thead><tr>'+''.join(f'<th>{h}</th>' for h in heads)+'</tr></thead><tbody>'
                             +''.join('<tr>'+''.join(f'<td>{escape(c)}</td>' for c in r)+'</tr>' for r in mrows)+'</tbody></table>')
    # Products this one depends on: an existing PROD key, never the product itself.
    if 'producten' not in inputs: ask('producten', 'Op welke andere producten (PROD-key) steunt de toepassing? Geen? Geef een lege lijst.')
    if 'product_catalog' not in snapshot: ask('producten', 'Deze bronmomentopname mist de productlijst; verzamel opnieuw met de huidige collector.')
    known = snapshot.get('product_catalog') or {}
    deps = []
    for r in inputs.get('producten') or []:
        key = (r.get('product') or '').strip().upper()
        if not re.fullmatch(r'PROD-\d+', key): raise ValueError(f'Producten: {key or "lege key"} is geen PROD-key')
        if product and key == product['key']: raise ValueError(f'Producten: {key} is het product zelf')
        if known and key not in known: raise ValueError(f'Producten: {key} bestaat niet in Jira')
        deps.append((f"{key} — {known.get(key, '')}".rstrip(' —'), r.get('waarvoor') or ''))
    after['producten'] = (['### Producten', '']+([f'- {n}: {w}' for n, w in deps] or ['Steunt op geen andere producten.'])+[''],
                          '<h3>Producten</h3>'+('<table><thead><tr><th>Product</th><th>Waarvoor</th></tr></thead><tbody>'
                          +''.join(f'<tr><td>{escape(n)}</td><td>{escape(w)}</td></tr>' for n, w in deps)+'</tbody></table>' if deps else '<p>Steunt op geen andere producten.</p>'))
    # Runkost: one row per post in enum order, with a total.
    posts = {r.get('post'): r for r in inputs.get('runkost') or [] if isinstance(r, dict)}
    label = {e['value']: e['label'] for e in spec['enums']['kostenpost']}
    run_rows = [(label[k], posts[k].get('omschrijving') or '', posts[k].get('bedrag') or '', k == 'inference') for k in label if k in posts]
    run_md = ['### Runkost', '', '| Post | Omschrijving | Bedrag (€/jaar) |', '| --- | --- | --- |']
    run_md += [f'| {p} | {o}{" (AI)" if ai else ""} | {b} |' for p, o, b, ai in run_rows]+[f"| **Totaal** | | **{text(run) if costs else 'onvolledig'}** |", '']
    after['runkost'] = (run_md, '<h3>Runkost</h3><table><thead><tr><th>Post</th><th>Omschrijving</th><th>Bedrag (€/jaar)</th></tr></thead><tbody>'
                        +''.join(f'<tr><td>{escape(p)}</td><td>{cell(o, ai)}</td><td>{escape(str(b))}</td></tr>' for p, o, b, ai in run_rows)
                        +f"<tr><th>Totaal</th><th></th><th>{text(run) if costs else 'onvolledig'}</th></tr></tbody></table>")
    team = (product or {}).get('verantwoordelijk_team') or 'onbekend'
    tasks = ', '.join(f'{k} ({b})' for k, b in zip((product or {}).get('onderhoud_keys', []), (product or {}).get('onderhoud_billingkeys', []))) or 'geen'
    rows_out = [('Product', escape(f"{product['key']} — {product.get('summary') or ''}") if product else 'onbekend'),
                ('Project', escape(target)),
                ('Status', 'Actief'),
                ('Klasse', level or 'onvolledig'),
                ('Ondersteuning buiten kantooruren', {'ja': 'Ja', 'nee': 'Nee'}.get(inputs.get('buiten_kantooruren'), 'onvolledig')),
                ('As-is (md)', text(as_is)),
                ('Delta (md)', text(delta)),
                ('Investering (md)', text(total)),
                ('Onderhoud (md/jaar)', text(yearly)),
                ('Runkost (€/jaar)', text(run) if costs else 'onvolledig'),
                ('Team', escape(team)),
                ('Onderhoudstaak', escape(tasks)),
                ('Geldig tot', until),
                ('Vervangt', link(replaces['title']) if replaces else '—')]
    return {'questions': questions, 'notes': notes, 'rows': rows_out, 'after': after, 'replaces': replaces, 'guard': guard}


def retire(schema, storage, new_title):
    """Status Actief -> Vervangen and a 'Vervangen door' row in the previous plan's properties block."""
    spans = conf.find_details_blocks(schema, storage, DETAILS_ID)
    if len(spans) != 1: raise ValueError('Vorig onderhoudsplan heeft geen eenduidig eigenschappenblok; eerst reviewen')
    s, e = spans[0]; block = storage[s:e]
    if 'Vervangen door' in conf.parse_properties(schema, storage, DETAILS_ID): raise ValueError('Vorig onderhoudsplan is al vervangen')
    hits = []
    for row in conf.ROW_RE.finditer(block):
        cells = list(conf.CELL_RE.finditer(row.group(1)))
        if len(cells) >= 2 and conf._cell_text(cells[0].group(2) or '') == 'Status' and cells[1].group(1):
            hits.append((row.start(1)+cells[1].start(2), row.start(1)+cells[1].end(2)))
    if len(hits) != 1: raise ValueError('Vorig onderhoudsplan: Status niet eenduidig gevonden')
    a, b = hits[0]; block = block[:a]+'Vervangen'+block[b:]
    pos = block.rfind('</tbody>')
    if pos < 0: raise ValueError('Vorig onderhoudsplan: geen tabel in het eigenschappenblok')
    block = block[:pos]+'<tr><th>Vervangen door</th><td>'+link(new_title)+'</td></tr>'+block[pos:]
    return storage[:s]+block+storage[e:]
