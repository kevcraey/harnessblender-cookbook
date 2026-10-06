"""Signals: lines in the routine's activity bundle that touch the portfolio, plus the review ladder.

Code finds candidates; judging what they mean for the portfolio is the model's job.
"""
from __future__ import annotations
from pathlib import Path
import re
from .review import day

# Sources from the routine collector that carry other people's activity. git and claude are our own
# portfolio work, notes and chrome are duplicates or noise.
BRONNEN = ('graph', 'rocketchat', 'atlassian', 'vault')
# Words that point at new demand, which no key or name can match yet.
TERMEN = ('AI Expertisecentrum', 'AI-expertisecentrum', 'AIEC', 'AI-initiatief', 'use case', 'AI Act', 'DPIA')
KEY = re.compile(r'\b(?:AI|POR|PROD|EAG)-\d+\b')
# An unknown AI or EAG key can be new demand; an unknown POR or PROD belongs to another team.
NIEUW = ('AI-', 'EAG-')
# 'path | 4 +-' lines of a git diff --stat say nothing about content.
DIFFSTAT = re.compile(r'\|\s+\d+ [+-]*$')
# Review ladder: days since the latest saved review.
VRAAG, VERPLICHT = 3, 5


def vocabulary(snapshot):
    """Name -> key for initiatives and products: the full summary, the part before ':' and an acronym in brackets."""
    names = {}
    for x in snapshot.get('issues', []) + snapshot.get('products', []):
        s = (x.get('summary') or '').strip()
        for name in {s, s.split(':')[0].strip(), *re.findall(r'\(([A-Z]{3,})\)', s)}:
            if len(name) >= 3: names.setdefault(name, x['key'])
    return names


def ladder(snapshot, today):
    runs = sorted(r['datum'] for r in snapshot.get('reviews', []))
    if not runs: return {'laatste_review': None, 'dagen': None, 'niveau': 'verplicht'}
    days = (today-day(runs[-1])).days
    return {'laatste_review': runs[-1][:10], 'dagen': days,
            'niveau': 'verplicht' if days >= VERPLICHT else 'vraag' if days >= VRAAG else 'info'}


def scan(snapshot, bundle, today):
    known = {x['key'] for x in snapshot.get('issues', []) + snapshot.get('projects', []) + snapshot.get('products', []) + snapshot.get('adhoc', [])}
    known |= {k for i in snapshot.get('issues', []) for k in i.get('eag_keys', [])}
    names = vocabulary(snapshot); seen = set(); found = []
    for folder in sorted(p for p in Path(bundle).expanduser().iterdir() if p.is_dir()):
        for bron in BRONNEN:
            path = folder/f'{bron}.md'
            if not path.exists(): continue
            for line in path.read_text(encoding='utf-8').splitlines():
                text = line.strip()
                if not text or text.startswith('#') or text in seen or DIFFSTAT.search(text): continue
                keys = sorted(k for k in set(KEY.findall(text)) if k in known or k.startswith(NIEUW))
                # Acronyms are case-sensitive words; other names and terms ignore case.
                hits = sorted({k for n, k in names.items() if (re.search(r'\b'+re.escape(n)+r'\b', text) if n.isupper() else n.lower() in text.lower())})
                terms = [t for t in TERMEN if (re.search(r'\b'+re.escape(t)+r'\b', text) if t.isupper() else t.lower() in text.lower())]
                if not (keys or hits or terms): continue
                seen.add(text)
                found.append({'dag': folder.name, 'bron': bron, 'tekst': text[:400], 'keys': keys,
                              'onbekend': [k for k in keys if k not in known], 'namen': hits, 'termen': terms})
    return {**ladder(snapshot, today), 'kandidaten': found}


def markdown(result):
    lad = {'info': '', 'vraag': ' — review aanbevolen', 'verplicht': ' — review verplicht'}[result['niveau']]
    last = f"{result['laatste_review']} ({result['dagen']} dagen)" if result['laatste_review'] else 'nooit'
    lines = ['# Portfoliosignalen', '', f"Laatste bewaarde review: {last}{lad}.", '', f"{len(result['kandidaten'])} kandidaten.", '']
    for c in result['kandidaten']:
        tags = ', '.join(dict.fromkeys(c['keys'] + c['namen'] + c['termen']))
        lines.append(f"- {c['dag']} · {c['bron']} · {tags}{' · onbekende key: '+', '.join(c['onbekend']) if c['onbekend'] else ''}: {c['tekst']}")
    return '\n'.join(lines)+'\n'
