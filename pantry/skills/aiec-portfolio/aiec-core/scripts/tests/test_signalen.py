"""Signals: code picks portfolio-related lines from the routine bundle and sets the review ladder."""
import json
from datetime import date
from test_v2 import env
from aiec_v2.signals import scan, markdown


def bundle(tmp_path, files):
    for (dag, bron), text in files.items():
        d = tmp_path/'days'/dag; d.mkdir(parents=True, exist_ok=True); (d/f'{bron}.md').write_text(text)
    return tmp_path/'days'


def snapshot(b, reviews=()):
    s = b.collect()
    s['issues'][0]['summary'] = 'Rosetta: intelligent document processing'
    s['issues'].append(dict(s['issues'][0], key='AI-60', summary='AI-ondersteuning Milieu-Investerings-Aftrek (MIA)'))
    s['reviews'] = [{'datum': d+'T08:00:00+00:00', 'findings': []} for d in reviews]
    return s


def test_candidates_from_keys_names_and_terms(env, tmp_path):
    cat, cfg, b, _ = env
    days = bundle(tmp_path, {
        ('2026-10-05', 'graph'): '# graph\n- mail: Rosetta gaat live in november\n- mail: lunch vrijdag\n- mail: vraag aan het AI Expertisecentrum over vertaling\n',
        ('2026-10-05', 'atlassian'): '- AI-38 status → Run\n- AI-999 aangemaakt\n- Rosetta gaat live in november\n- POR-9999 Onderhoud ander team\n',
        ('2026-10-05', 'vault'): ' 01 - Projects/project-moc-Rosetta.md |   4 +-\n',
        ('2026-10-05', 'git'): '- aiec-portfolio 2.4.63 AI-38\n',          # own work: not scanned
        ('2026-10-05', 'rocketchat'): '- de mia-regeling\n- MIA-dossier besproken\n'})
    r = scan(snapshot(b), days, date(2026, 10, 6))
    texts = [c['tekst'] for c in r['kandidaten']]
    assert not any('POR-9999' in t or 'moc-Rosetta' in t for t in texts)
    assert '- mail: lunch vrijdag' not in texts and not any('2.4.63' in t for t in texts)
    assert texts.count('Rosetta gaat live in november') == 0 and sum('Rosetta gaat live' in t for t in texts) == 2
    by = {c['tekst']: c for c in r['kandidaten']}
    assert by['- mail: Rosetta gaat live in november']['namen'] == [snapshot(b)['issues'][0]['key']]
    assert by['- mail: vraag aan het AI Expertisecentrum over vertaling']['termen'] == ['AI Expertisecentrum']
    assert by['- AI-999 aangemaakt']['onbekend'] == ['AI-999'] and by['- AI-38 status → Run']['onbekend'] == []
    assert by['- MIA-dossier besproken']['namen'] == ['AI-60'] and '- de mia-regeling' not in by   # acronyms are case-sensitive


def test_review_ladder(env, tmp_path):
    cat, cfg, b, _ = env
    days = bundle(tmp_path, {('2026-10-05', 'graph'): '- niets\n'})
    level = lambda *runs: scan(snapshot(b, runs), days, date(2026, 10, 10))
    assert level()['niveau'] == 'verplicht' and level()['laatste_review'] is None
    assert level('2026-10-08')['niveau'] == 'info'
    assert level('2026-10-01', '2026-10-07')['niveau'] == 'vraag'
    r = level('2026-10-05')
    assert (r['niveau'], r['dagen']) == ('verplicht', 5) and 'review verplicht' in markdown(r)
