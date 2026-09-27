"""Typed, human-supplied report sections. No inference or data retrieval.

Report-local enums can be reused by a section and by input-table columns.
Missing answers become questions; malformed or ambiguous input is rejected.
"""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from html import escape
import re

INPUT_KINDS = {'input', 'choice', 'input_table'}
COLUMN_TYPES = {'text', 'integer', 'decimal', 'choice'}


def options(report, spec):
    return report['enums'][spec['enum']]


def validate_definitions(report):
    if not isinstance(report.get('enums', {}), dict):
        raise ValueError('Rapportkeuzelijsten moeten een object zijn')
    for name, choices in report.get('enums', {}).items():
        if not isinstance(choices, list) or not choices:
            raise ValueError(f'Lege keuzelijst: {name}')
        keys = []
        for choice in choices:
            if not isinstance(choice, dict) or not isinstance(choice.get('value'), str) or not choice['value'] or not choice.get('label'):
                raise ValueError(f'Ongeldige keuze in {name}')
            keys.append(choice['value'])
        if len(keys) != len(set(keys)):
            raise ValueError(f'Dubbele keuze in {name}')
    for section in report['sections']:
        kind = section['kind']
        if kind not in INPUT_KINDS:
            continue
        if not section.get('prompt'):
            raise ValueError('Invoersectie mist een vraag')
        if kind == 'choice':
            _validate_enum_ref(report, section)
        elif kind == 'input':
            for bound in ('min_lines', 'max_lines'):
                if bound in section and (type(section[bound]) is not int or section[bound] < 1):
                    raise ValueError('Ongeldige regelgrens')
            if section.get('min_lines', 1) > section.get('max_lines', 10**6):
                raise ValueError('Omgekeerde regelgrenzen')
        else:
            cols = section.get('columns')
            if not isinstance(cols, list) or not cols:
                raise ValueError('Invoertabel zonder kolommen')
            ids = []
            for col in cols:
                if not isinstance(col, dict) or not col.get('id') or not col.get('title') or col.get('type') not in COLUMN_TYPES:
                    raise ValueError('Ongeldige invoerkolom')
                ids.append(col['id'])
                if col['type'] == 'choice':
                    _validate_enum_ref(report, col)
            if len(ids) != len(set(ids)):
                raise ValueError('Dubbele invoerkolom')
            if type(section.get('min_rows', 1)) is not int or section.get('min_rows', 1) < 0:
                raise ValueError('Ongeldige minimumrijen')


def _validate_enum_ref(report, spec):
    if spec.get('enum') not in report.get('enums', {}):
        raise ValueError('Onbekende keuzelijst: ' + str(spec.get('enum')))


def blank(value):
    return value is None or (isinstance(value, str) and not value.strip())


def choice_text(report, spec, value):
    found = next((c for c in options(report, spec) if c['value'] == value), None)
    if found is None:
        raise ValueError(f"Onbekende keuze {value!r}; gebruik een waarde uit {spec['enum']}")
    return ' '.join(x for x in [found.get('symbol', ''), found['label']] if x)


def md_cell(value):
    # User text in a table must not inject HTML, columns, or Markdown links.
    text = escape(str(value), quote=False).replace('|', '&#124;').replace('\n', '<br>')
    return re.sub(r'([\\`*_\[\]])', r'\\\1', text)


def number(value, spec):
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{spec['title']}: verwacht een getal")
    raw = str(value).strip().replace(',', '.')
    if len(raw) > 60 or not re.fullmatch(r'\d+(?:\.\d+)?', raw):
        raise ValueError(f"{spec['title']}: verwacht een niet-negatief, eindig getal")
    try:
        n = Decimal(raw)
    except InvalidOperation:
        raise ValueError(f"{spec['title']}: ongeldig getal") from None
    if spec['type'] == 'integer' and n != n.to_integral_value():
        raise ValueError(f"{spec['title']}: verwacht een geheel getal")
    if n < Decimal(str(spec.get('minimum', 0))):
        raise ValueError(f"{spec['title']}: lager dan het minimum")
    text = format(n, 'f')
    return text.rstrip('0').rstrip('.') if '.' in text else text


def render_input(report, section, value):
    """Return Markdown lines, storage fragment, questions for ONE human-input section."""
    sid = section['id']
    questions = []
    md = []
    body = []

    def ask(question):
        questions.append({'section': sid, 'question': question})

    if section['kind'] == 'input':
        if value is not None and not isinstance(value, str):
            raise ValueError('Rapportinvoer moet tekst zijn: ' + sid)
        text = (value or '').strip()
        if not text:
            if section.get('required', True): ask(section['prompt'])
            md.append('**Nog in te vullen:** ' + section['prompt'])
        else:
            lines = [line for line in text.splitlines() if line.strip()]
            if len(lines) < section.get('min_lines', 1) or len(lines) > section.get('max_lines', 10**6):
                ask(f"{section['title']}: gebruik {section.get('min_lines', 1)}–{section.get('max_lines', 'onbeperkt')} korte regels.")
            md.append(text)
            body.append(''.join('<p>' + escape(p).replace('\n', '<br/>') + '</p>' for p in text.split('\n\n')))
    elif section['kind'] == 'choice':
        if blank(value):
            if section.get('required', True): ask(section['prompt'])
            md.append('**Nog in te vullen:** ' + section['prompt'])
        else:
            if not isinstance(value, str): raise ValueError('Keuze moet tekst zijn: ' + sid)
            label = choice_text(report, section, value)
            md.append(label)
            body.append('<p>' + escape(label) + '</p>')
    else:
        if value is None: value = []
        if not isinstance(value, list): raise ValueError('Invoertabel moet een lijst rijen zijn: ' + sid)
        cols = section['columns']
        if len(value) < section.get('min_rows', 1) and section.get('required', True): ask(section['prompt'])
        md += ['| ' + ' | '.join(md_cell(c['title']) for c in cols) + ' |',
               '| ' + ' | '.join('---' for c in cols) + ' |']
        body += ['<table><thead><tr>' + ''.join('<th>' + escape(c['title']) + '</th>' for c in cols) + '</tr></thead><tbody>']
        seen = {c['id']: set() for c in cols if c.get('unique')}
        for pos, row in enumerate(value, 1):
            if not isinstance(row, dict) or set(row) - {c['id'] for c in cols}:
                raise ValueError(f'{sid} rij {pos}: ongeldige of onbekende kolommen')
            rendered = []
            for col in cols:
                raw = row.get(col['id'])
                if blank(raw):
                    if col.get('required', True): ask(f"{section['title']}, rij {pos}: vul {col['title']} in.")
                    rendered.append(col.get('empty', 'onbekend'))
                    continue
                if col['type'] == 'text':
                    if not isinstance(raw, str): raise ValueError(f"{col['title']}: verwacht tekst")
                    text = raw.strip()
                elif col['type'] == 'choice':
                    text = choice_text(report, col, raw)
                else:
                    text = number(raw, col)
                if col['id'] in seen:
                    if text in seen[col['id']]: raise ValueError(f"Dubbele waarde in {col['title']}: {text}")
                    seen[col['id']].add(text)
                rendered.append(text)
            md.append('| ' + ' | '.join(md_cell(t) for t in rendered) + ' |')
            body.append('<tr>' + ''.join('<td>' + escape(t).replace('\n', '<br/>') + '</td>' for t in rendered) + '</tr>')
        body.append('</tbody></table>')
        if not value: md.append('Nog geen milestones of andere tabelrijen aangeleverd.')
    if section.get('help'):
        md += ['', '> Invulhulp: ' + section['help']]
    if section.get('caption'):
        md += ['', section['caption']]
        body.append('<p><em>' + escape(section['caption']) + '</em></p>')
    storage = f"<h2>{escape(section['title'])}</h2>" + ''.join(body) if body else ''
    return md + [''], storage, questions
