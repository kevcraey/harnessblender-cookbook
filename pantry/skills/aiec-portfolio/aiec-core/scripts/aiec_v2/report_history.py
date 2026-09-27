"""Portable, append-only report measurements embedded in approved report pages.

Checksums detect accidental/manual edits, not a hostile editor who recomputes hashes.
No page is repaired, normalized in place, or overwritten by this module.
"""
from __future__ import annotations
from copy import deepcopy
from html import escape
from html.entities import html5
import json
import re
import xml.etree.ElementTree as ET
from .catalog import digest

MARKER = 'aiec-meetstand-v1'
AC = '{urn:ac}'
RI = '{urn:ri}'


def _xml(storage):
    parts = re.split(r'(<!\[CDATA\[.*?\]\]>)', storage, flags=re.S)
    markup = ''.join(p for p in parts if not p.startswith('<![CDATA['))
    if '<!DOCTYPE' in markup.upper() or '<!ENTITY' in markup.upper():
        raise ValueError('Meetstand bevat een verboden XML-declaratie')
    def entity(m):
        name = m[1]
        return m[0] if name in {'amp', 'lt', 'gt', 'quot', 'apos'} else html5.get(name+';', m[0])
    text = ''.join(p if p.startswith('<![CDATA[') else re.sub(r'&([A-Za-z][A-Za-z0-9]+);', entity, p) for p in parts)
    try:
        return ET.fromstring('<root xmlns:ac="urn:ac" xmlns:ri="urn:ri">'+text+'</root>')
    except ET.ParseError as exc:
        raise ValueError('Rapportopmaak kan niet veilig als meetstand worden gelezen') from exc


def _blocks(root):
    parents = {child: parent for parent in root.iter() for child in parent}
    found = []
    for node in root.iter(AC+'structured-macro'):
        title = next((p.text for p in node.findall(AC+'parameter') if p.get(AC+'name') == 'title'), None)
        if node.get(AC+'name') == 'code' and title == MARKER:
            outer = node
            parent = parents.get(node)
            if parent is not None and parent.tag == AC+'rich-text-body':
                grand = parents.get(parent)
                if grand is not None and grand.get(AC+'name') == 'expand' and list(parent) == [node] and not (parent.text or '').strip() and not (node.tail or '').strip():
                    outer = grand
            found.append((node, outer, parents[outer]))
    return found


def content_hash(storage):
    root = _xml(storage)
    for _, outer, parent in _blocks(root):
        if outer.tail:
            index = list(parent).index(outer)
            if index:parent[index-1].tail = (parent[index-1].tail or '')+outer.tail
            else:parent.text = (parent.text or '')+outer.tail
        parent.remove(outer)
    for node in root.iter():
        # Confluence generates these identifiers; they do not change report content.
        for name in ('macro-id', 'local-id', 'schema-version'):
            node.attrib.pop(AC+name, None)
    xml = ET.tostring(root, encoding='unicode')
    return digest(ET.canonicalize(xml, strip_text=True, rewrite_prefixes=True))


def embed(storage, state):
    record = deepcopy(state)
    record['content_hash'] = content_hash(storage)
    record['hash'] = digest(record)
    # JSON escapes round-trip exactly, without leaving HTML-looking user text in storage.
    text = json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2)
    for char, code in [('<', '003c'), ('>', '003e'), ('&', '0026')]:
        text = text.replace(char, '\\u'+code)
    macro = ('<ac:structured-macro ac:name="expand"><ac:parameter ac:name="title">'
             'Technische meetstand — vaste referentie, niet handmatig aanpassen</ac:parameter>'
             '<ac:rich-text-body><ac:structured-macro ac:name="code">'
             '<ac:parameter ac:name="title">'+MARKER+'</ac:parameter>'
             '<ac:parameter ac:name="language">json</ac:parameter><ac:plain-text-body><![CDATA['+
             text+']]></ac:plain-text-body></ac:structured-macro></ac:rich-text-body></ac:structured-macro>')
    return storage+macro, record


def extract(storage):
    if MARKER not in storage:
        return None
    blocks = _blocks(_xml(storage))
    if len(blocks) != 1:
        raise ValueError('Verwacht precies één technische meetstand; eerst reviewen')
    body = blocks[0][0].find(AC+'plain-text-body')
    try:
        record = json.loads(body.text if body is not None else '')
    except (ValueError, TypeError) as exc:
        raise ValueError('Technische meetstand is geen geldige JSON; eerst reviewen') from exc
    if not isinstance(record, dict):
        raise ValueError('Technische meetstand moet een object zijn')
    return record


def load(spec, snapshot, target, initiative):
    records, legacy, pages = [], [], []
    for page in snapshot.get('report_pages', []):
        record = extract(page['storage'])
        if record is None:
            title = page.get('title', '')
            refs = {r.upper() for r in re.findall(r'(?<![\w-])'+re.escape(target.rsplit('-', 1)[0])+r'-\d+(?![\w-])', title, re.I)}
            relevant = target in refs if refs else any(re.search(r'(?<![\w-])'+re.escape(key)+r'(?![\w-])', title, re.I) for key in (target, initiative) if key)
            if spec.get('label') in page.get('labels', []) and relevant:
                legacy.append(str(page['page_id']))
                pages.append({'page_id': str(page['page_id']), 'revision': page['revision']})
            continue
        if record.get('report') != spec['id'] or record.get('target') != target:
            continue
        ident = str(page['page_id'])
        if record.get('version') != 1 or record.get('model') != 'milestone_effort':
            raise ValueError(f'Onbekende meetstandversie op pagina {ident}')
        if digest({k: v for k, v in record.items() if k != 'hash'}) != record.get('hash'):
            raise ValueError(f'Meetstand op pagina {ident} is gewijzigd; eerst reviewen')
        if record.get('content_hash') != content_hash(page['storage']):
            raise ValueError(f'Rapportinhoud op pagina {ident} is handmatig gewijzigd; niet stilzwijgend overnemen')
        if record.get('title') != page['title'] or record.get('initiative') != initiative:
            raise ValueError(f'Titel of initiatief wijkt af van meetstand op pagina {ident}')
        if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', str(record.get('period', ''))):
            raise ValueError('Ongeldige periode in historische meetstand')
        records.append(record)
        pages.append({'page_id': ident, 'revision': page['revision']})
    records.sort(key=lambda r: r['period'])
    for record in records:
        # Before the rename, the fixed original estimate was stored as forecast_md; the hash above covers the stored form.
        for row in [*record.get('milestones', []), *record.get('inputs', {}).get('milestones', [])]:
            if 'forecast_md' in row:row['baseline_md'] = row.pop('forecast_md')
    previous = None
    for record in records:
        if record.get('previous_hash') != (previous['hash'] if previous else None):
            raise ValueError('Onderbroken of vertakte rapporthistoriek; eerst reconciliëren')
        if previous:
            if record['period'] <= previous['period']:
                raise ValueError('Dubbele rapportmaand; eerst reviewen')
            if record['baseline'] != previous['baseline']:
                raise ValueError('Oorspronkelijke baseline is gewijzigd in de historiek')
            old = previous['scope_changes']
            if record['scope_changes'][:len(old)] != old:
                raise ValueError('Bestaande scopebesluiten zijn gewijzigd in de historiek')
        previous = record
    return {'records': records, 'legacy': sorted(legacy), 'pages': sorted(pages, key=lambda p: p['page_id'])}


def guard(spec, snapshot, target, initiative):
    history = load(spec, snapshot, target, initiative)
    return {'report': spec['id'], 'target': target, 'initiative': initiative,
            'pages': history['pages'], 'head': history['records'][-1]['hash'] if history['records'] else None}
