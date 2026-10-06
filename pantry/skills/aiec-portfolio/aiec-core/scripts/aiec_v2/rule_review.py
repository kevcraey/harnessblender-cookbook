"""Quarterly rule review: how each rule behaved, computed from the saved review runs.

Code computes and flags; whether a rule should change is the model's suggestion and Kenzo's decision.
"""
from __future__ import annotations
from statistics import median
from . import periods
from .review import day

UITZONDERINGSAANDEEL, HARDNEKKIG = 0.5, 90


def previous_quarter(today):
    return periods.name(*periods._add(*periods.parse(periods.containing(today, 3))[:2], -3), 3)


def compute(cat, snapshot, quarter):
    if periods.parse(quarter)[2] != 3: raise ValueError('Regelreview vraagt een kwartaal: JJJJ-Qn')
    first, last = periods.start(quarter), periods.last_day(quarter)
    runs = sorted((r for r in snapshot.get('reviews', []) if first <= day(r['datum']) <= last), key=lambda r: r['datum'])
    if not runs: raise ValueError(f'Geen bewaarde reviews in {quarter}')
    end = runs[-1]; end_day = day(end['datum'])
    seen = {}
    for run in runs:
        for f in run['findings']:
            if not f['rule'].startswith('uitzondering-'): seen.setdefault(f['rule'], {})[f['id']] = f
    rules = []
    for rule in sorted(set(cat.rules) | set(seen)):
        found = seen.get(rule, {}); open_ = [f for f in end['findings'] if f['rule'] == rule]
        open_ids = {f['id'] for f in open_}
        ages = [(end_day-day(f['sinds'])).days for f in open_ if f.get('sinds')]
        share = sum(1 for f in open_ if f.get('uitzondering'))/len(open_) if open_ else 0
        solved = len(set(found)-open_ids)
        flags = []
        if rule in cat.rules and not found: flags.append('dood')
        if open_ and share >= UITZONDERINGSAANDEEL: flags.append('uitzonderingsregel')
        if ages and max(ages) > HARDNEKKIG and not solved: flags.append('hardnekkig')
        rules.append({'regel': rule, 'catalogus': rule in cat.rules, 'keys': len({f['key'] for f in found.values()}),
                      'bevindingen': len(found), 'opgelost': solved, 'open': len(open_),
                      'mediane_open_dagen': median(ages) if ages else None, 'uitzonderingsaandeel': round(share, 2), 'markering': flags})
    return {'kwartaal': quarter, 'runs': len(runs), 'van': runs[0]['datum'][:10], 'tot': end['datum'][:10], 'regels': rules}


def markdown(result):
    lines = [f"# Regelreview {result['kwartaal']}", '', f"{result['runs']} bewaarde reviews, {result['van']} tot {result['tot']}.", '',
             '| Regel | Keys | Opgelost | Open | Mediaan open (d) | Uitzondering | Markering |', '|---|---|---|---|---|---|---|']
    for r in sorted(result['regels'], key=lambda r: (not r['markering'], r['regel'])):
        name = r['regel'] if r['catalogus'] else r['regel']+' (ingebouwd)'
        lines.append(f"| {name} | {r['keys']} | {r['opgelost']} | {r['open']} | {r['mediane_open_dagen'] if r['mediane_open_dagen'] is not None else '–'} | "
                     f"{round(r['uitzonderingsaandeel']*100)}% | {', '.join(r['markering']) or '–'} |")
    return '\n'.join(lines)+'\n'
