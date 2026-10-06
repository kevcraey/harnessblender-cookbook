"""Append-only report measurements, kept in a dedicated git archive next to the report pages.

Each measurement is sealed with the content hash of its approved page and chained to the previous one.
Checksums detect accidental/manual edits, not a hostile editor who recomputes hashes.
No page or archive entry is repaired, normalized in place, or overwritten by this module.
"""
from __future__ import annotations
from copy import deepcopy
from html import escape
from html.entities import html5
import json
from pathlib import Path
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
        # On save, Handy turns the published handy-status-macro (set and status id) into status-handy with its
        # own instance id. Both forms carry the same Status name, which is the content.
        if node.tag == AC+'structured-macro' and node.get(AC+'name') in ('handy-status-macro', 'status-handy'):
            node.set(AC+'name', 'status-handy')
            for param in [p for p in node if p.tag == AC+'parameter' and p.get(AC+'name') in ('id', 'statusSetId', 'statusId')]:
                node.remove(param)
    xml = ET.tostring(root, encoding='unicode')
    return digest(ET.canonicalize(xml, strip_text=True, rewrite_prefixes=True))


def seal(storage, state):
    """The measurement for an approved page: the state plus the page content hash, hashed as a whole."""
    record = deepcopy(state)
    record['content_hash'] = content_hash(storage)
    record['hash'] = digest(record)
    return record


def archive_name(record):
    return f"{record['report']}/{record['target']}/{record['period']}.json"


RAPPORTERING = 'rapportering'


def rapportering_name(record):
    return f"{RAPPORTERING}/{record['key']}/{record['datum'][:19].replace(':', '')}.json"


def read_rapportering(root):
    """All recorded reporting frequencies; a changed frequency is a new file, never an overwrite."""
    from .periods import check_frequency
    root = Path(root).expanduser()
    if not (root/'.git').exists():
        raise ValueError(f'Meetstandenarchief ontbreekt of is geen git-repo: {root}')
    records = []
    for path in sorted((root/RAPPORTERING).glob('*/*.json')):
        record = check_frequency(json.loads(path.read_text()))
        if rapportering_name(record) != str(path.relative_to(root)):
            raise ValueError(f'Rapporteringsfrequentie staat op een verkeerde plaats in het archief: {path.relative_to(root)}')
        records.append(record)
    return records


UITZONDERING = 'uitzondering'
_DATUM = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?\+00:00')


def check_exception(record):
    """An exception record: key, rule, reason, who and when. Reviewing it again is a new record."""
    if not isinstance(record, dict) or set(record) != {'key', 'regel', 'reden', 'door', 'datum', 'ingetrokken'}:
        raise ValueError('Uitzondering vraagt key, regel, reden, door, datum en ingetrokken')
    if not re.fullmatch(r'[A-Z][A-Z0-9_]*-\d+(-intern-\d+)?', str(record['key'])): raise ValueError('Ongeldige key')
    if not re.fullmatch(r'(gate:)?[a-z0-9-]+', str(record['regel'])): raise ValueError('Ongeldige regel')
    if not str(record['reden']).strip() or not str(record['door']).strip(): raise ValueError('Uitzondering vraagt reden en door')
    if not _DATUM.fullmatch(str(record['datum'])): raise ValueError('Ongeldige datum')
    if not isinstance(record['ingetrokken'], bool): raise ValueError('ingetrokken is true of false')
    return record


def exception_name(record):
    return f"{UITZONDERING}/{record['key']}/{record['regel'].replace(':', '-')}/{record['datum'][:19].replace(':', '')}.json"


def read_exceptions(root):
    """All recorded exceptions; a review or withdrawal is a new file, never an overwrite."""
    root = Path(root).expanduser()
    if not (root/'.git').exists():
        raise ValueError(f'Meetstandenarchief ontbreekt of is geen git-repo: {root}')
    records = []
    for path in sorted((root/UITZONDERING).glob('*/*/*.json')):
        record = check_exception(json.loads(path.read_text()))
        if exception_name(record) != str(path.relative_to(root)):
            raise ValueError(f'Uitzondering staat op een verkeerde plaats in het archief: {path.relative_to(root)}')
        records.append(record)
    return records


REVIEW = 'review'


def review_name(run):
    return f"{REVIEW}/{run['datum'][:19].replace(':', '')}.json"


def read_reviews(root):
    """Saved review runs, oldest first. Derived data: each run is a new file, never an overwrite."""
    root = Path(root).expanduser()
    if not (root/'.git').exists():
        raise ValueError(f'Meetstandenarchief ontbreekt of is geen git-repo: {root}')
    runs = []
    for path in sorted((root/REVIEW).glob('*.json')):
        run = json.loads(path.read_text())
        if not isinstance(run, dict) or set(run) != {'datum', 'findings'} or not isinstance(run['findings'], list) or not _DATUM.fullmatch(str(run['datum'])):
            raise ValueError(f'Ongeldige reviewrun in archief: {path.relative_to(root)}')
        if review_name(run) != str(path.relative_to(root)):
            raise ValueError(f'Reviewrun staat op een verkeerde plaats in het archief: {path.relative_to(root)}')
        runs.append(run)
    return runs


REGELREVIEW = 'regelreview'


def rule_review_name(result):
    return f"{REGELREVIEW}/{result['kwartaal']}.json"


def read_rule_reviews(root):
    """Saved quarterly rule reviews, one file per quarter."""
    root = Path(root).expanduser()
    if not (root/'.git').exists():
        raise ValueError(f'Meetstandenarchief ontbreekt of is geen git-repo: {root}')
    out = []
    for path in sorted((root/REGELREVIEW).glob('*.json')):
        result = json.loads(path.read_text())
        if not isinstance(result, dict) or rule_review_name(result) != str(path.relative_to(root)):
            raise ValueError(f'Regelreview staat op een verkeerde plaats in het archief: {path.relative_to(root)}')
        out.append(result)
    return out


def read_archive(root):
    """All archived measurements as {'page_id', 'record'} entries; a missing archive is an error, not empty history."""
    root = Path(root).expanduser()
    if not (root/'.git').exists():
        raise ValueError(f'Meetstandenarchief ontbreekt of is geen git-repo: {root}')
    entries = []
    for path in sorted(root.glob('*/*/*.json')):
        # Reporting frequencies and exceptions share the archive but are no measurements.
        if path.relative_to(root).parts[0] in (RAPPORTERING, UITZONDERING): continue
        entry = json.loads(path.read_text())
        if not isinstance(entry, dict) or set(entry) != {'page_id', 'record'} or not isinstance(entry['record'], dict):
            raise ValueError(f'Ongeldige meetstand in archief: {path.relative_to(root)}')
        if archive_name(entry['record']) != str(path.relative_to(root)):
            raise ValueError(f'Meetstand staat op een verkeerde plaats in het archief: {path.relative_to(root)}')
        entries.append(entry)
    return entries


def load(spec, snapshot, target, initiative):
    if 'meetstanden' not in snapshot:
        raise ValueError('Verzamel opnieuw: meetstanden uit het archief ontbreken')
    pages_by_id = {str(p['page_id']): p for p in snapshot.get('report_pages', [])}
    records, legacy, pages, linked = [], [], [], set()
    for entry in snapshot['meetstanden']:
        record = entry['record']
        if record.get('report') != spec['id'] or record.get('target') != target:
            continue
        ident = str(entry['page_id'])
        if record.get('version') != 1 or record.get('model') != 'milestone_effort':
            raise ValueError(f'Onbekende meetstandversie voor pagina {ident}')
        if digest({k: v for k, v in record.items() if k != 'hash'}) != record.get('hash'):
            raise ValueError(f'Meetstand voor pagina {ident} is gewijzigd; eerst reviewen')
        page = pages_by_id.get(ident)
        if page is None:
            raise ValueError(f'Rapportpagina {ident} bij meetstand {record.get("period")} ontbreekt; eerst reviewen')
        if record.get('content_hash') != content_hash(page['storage']):
            raise ValueError(f'Rapportinhoud op pagina {ident} is handmatig gewijzigd; niet stilzwijgend overnemen')
        if record.get('title') != page['title'] or record.get('initiative') != initiative:
            raise ValueError(f'Titel of initiatief wijkt af van meetstand op pagina {ident}')
        if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', str(record.get('period', ''))):
            raise ValueError('Ongeldige periode in historische meetstand')
        records.append(deepcopy(record)); linked.add(ident)
        pages.append({'page_id': ident, 'revision': page['revision']})
    for page in snapshot.get('report_pages', []):
        ident = str(page['page_id'])
        if ident in linked:
            continue
        title = page.get('title', '')
        # An internal project is new: no legacy pages without a measurement exist for it.
        if re.fullmatch(r'.+-intern-\d+', target):
            continue
        refs = {r.upper() for r in re.findall(r'(?<![\w-])'+re.escape(target.rsplit('-', 1)[0])+r'-\d+(?![\w-])', title, re.I)}
        relevant = target in refs if refs else any(re.search(r'(?<![\w-])'+re.escape(key)+r'(?![\w-])', title, re.I) for key in (target, initiative) if key)
        if spec.get('label') in page.get('labels', []) and relevant:
            legacy.append(ident)
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
