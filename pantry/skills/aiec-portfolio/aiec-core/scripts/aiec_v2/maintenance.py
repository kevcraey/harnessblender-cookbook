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
CLASSES = {'P1': 'Essentieel', 'P2': 'Belangrijk', 'P3': 'Standaard'}
FIXED_MD = Decimal('10')
SHARE = {'P1': Decimal('0.15'), 'P2': Decimal('0.10'), 'P3': Decimal('0.075')}
REQUIRED_SECTIONS = {'product', 'uitval', 'buiten_kantooruren', 'as_is', 'runkost'}
# Consumed by the calculation; shown in the properties and the cost text, not as a section of their own.
HIDDEN = {'product', 'as_is', 'buiten_kantooruren'}


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
    """P1: groot (4) within an hour; P2: groot within a working day or merkbaar (3) within four hours; else P3."""
    if impacts['1u'] >= 4: return 'P1'
    if impacts['1d'] >= 4 or impacts['4u'] >= 3: return 'P2'
    return 'P3'


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
        if level == 'P3' and inputs.get('buiten_kantooruren') == 'ja':
            notes.append('Ondersteuning buiten de kantooruren gevraagd bij klasse P3; controleer of dat nodig is.')
    # Delta: Actual of the last progress report of this project.
    source = cat.reports[spec['maintenance']['source']]
    guard, delta, delta_from = None, None, None
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
            delta_from = last['period']
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
    replaces = None; as_is = None; as_is_from = None
    given = inputs.get('as_is') or []
    if previous:
        a, props = previous[0]
        if given: raise ValueError('Bestaande investering komt uit het vorige onderhoudsplan ('+a['title']+'); laat as_is leeg')
        replaces = {'page_id': str(a['page_id']), 'title': a['title']}
        # A new project builds on the whole previous investment; a corrected plan of the same project keeps its as-is.
        same = props.get('Project') == target
        as_is = parse(props.get('As-is (md)' if same else 'Investering (md)'))
        as_is_from = ('as-is van het vorige onderhoudsplan van dit project ' if same else 'vorig onderhoudsplan ')+a['title']
        if as_is is None: notes.append('Investering in het vorige onderhoudsplan is onvolledig; de begroting blijft onvolledig.')
    elif product:
        if not given: ask('as_is', f"Geen vorig onderhoudsplan voor {product['key']}: geef de bestaande investering in md (0 bij green field) met bron, of laat md leeg als ze onbekend is.")
        elif len(given) > 1: raise ValueError('Bestaande investering: één rij')
        else:
            md = given[0].get('md')
            as_is = None if md is None or str(md).strip() == '' else Decimal(number(md, {'title': 'Investering (md)', 'type': 'decimal'}))
            as_is_from = (given[0].get('bron') or '').strip()
            if as_is is None: notes.append('Bestaande investering onbekend; de begroting is onvolledig en telt niet mee in een som.')
    total = None if as_is is None or delta is None else as_is+delta
    yearly = None if total is None or level is None else FIXED_MD+SHARE[level]*total
    costs = [r for r in inputs.get('runkost') or [] if isinstance(r, dict) and str(r.get('bedrag') or '').strip()]
    run = sum((Decimal(number(r['bedrag'], {'title': 'Bedrag', 'type': 'decimal'})) for r in costs), Decimal(0))
    until = valid_until(date.fromisoformat(datum)).isoformat()
    after = {}
    if level:
        rule = {'P1': 'impact groot of hoger binnen 1 uur', 'P2': 'impact groot binnen 1 werkdag, of merkbaar binnen 4 uur', 'P3': 'lagere impact dan bij P2'}[level]
        line = f'Afgeleide klasse: {level} ({CLASSES[level].lower()}): {rule}.'
        after['uitval'] = ([line, ''], '<p><strong>'+escape(line)+'</strong></p>')
    parts = []
    if level and total is not None:
        pct = text(SHARE[level]*100)+'%'
        parts.append(f'Onderhoud per jaar: {text(FIXED_MD)} md vast + {pct} van {text(total)} md investering = {text(yearly)} md.')
    else:
        parts.append('Onderhoud per jaar: onvolledig, want '+('de klasse ontbreekt' if not level else 'de investering is onbekend')+'.')
    parts.append(f"Investering: {text(as_is)} md as-is ({as_is_from or 'bron ontbreekt'}) + {text(delta)} md delta (Actual van {target}"+(f', vooruitgangsrapport {delta_from}' if delta_from else '')+').')
    parts.append('Formule: 10 md vast + 15% (P1), 10% (P2) of 7,5% (P3) van de totale investering. Runkost staat hieronder, apart in euro.')
    after['as_is'] = ([x for p in parts for x in (p, '')], ''.join('<p>'+escape(p)+'</p>' for p in parts))
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
