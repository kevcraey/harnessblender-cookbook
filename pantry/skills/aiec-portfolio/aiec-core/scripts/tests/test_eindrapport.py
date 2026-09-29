"""Final report on the last progress measurement, and the retrospective that refers to it."""
import pytest
from test_v2 import env
from test_tracking import publish, five_answers, five_basis
from test_onderhoud import publish_plan
from aiec_v2.reports import render
from aiec_v2.changes import make_plan
from aiec_v2.execution import approve, execute


def closing():
    return {'vlag': 'kleine-afwijking',
            'context': 'Aanleiding, doel en opdrachtgever.',
            'resultaat': 'Alle vijf milestones opgeleverd.',
            'rijpheid': 'MVP',
            'waarde': 'Nog niet gemeten; meting in het eerste kwartaal.',
            'wendingen': 'Datalevering een maand later.\nScope gelijk gebleven.',
            'productverantwoordelijke': 'Afdeling X, teamleider Y.',
            'beslissingen': 'nee',
            'vervolgstappen': [{'stap': 'Eerste meting', 'verantwoordelijke': 'Y', 'datum': '2027-03'}]}


def closed(env, plan=True):
    """Two published months; the second delivers everything. The maintenance plan comes before the final report."""
    publish(env, '2026-04', five_answers(3), five_basis())
    publish(env, '2026-09', five_answers(8), {})
    last = env[2].data['meetstanden'][-1]['record']
    if plan: publish_plan(env)
    return last


def test_final_report_reads_last_measurement_without_adding_one(env):
    cat, cfg, b, tmp = env
    last = closed(env)
    r = render(cat, b.collect(), 'eindrapport', 'POR-1', '2026-10', closing(), cfg)
    assert r['complete'] and r['measurement'] is None
    assert r['history_guard']['report'] == 'vooruitgang' and r['history_guard']['head'] == last['hash']
    assert all(v is None for v in r['chart_data']['forward']+r['chart_data']['expected_scope'])
    assert r['chart_data']['closed'] and 'geel gestippeld' not in r['storage']
    assert [a['filename'] for a in r['assets']] == ['aiec-eindrapport-por-1-2026-09-scope.png', 'aiec-eindrapport-por-1-2026-09-effort.png']
    s = r['storage']
    assert s.index('<h2>Samenvatting</h2>') < s.index('<h3>Context</h3>') < s.index('<h2>Verloop</h2>') < s.index('<h3>Milestones</h3>')
    assert s.index('<h3>Scopebesluiten</h3>') < s.index('<h3>Belangrijkste wendingen</h3>') < s.index('<h2>Vervolg</h2>') < s.index('<h3>Technisch beheer</h3>') < s.index('<h3>Vervolgstappen</h3>')
    assert 'ri:content-title="'+next(p['title'] for p in b.data['objects']['page'].values() if ' - onderhoudsplan - ' in p['title'])+'"' in s
    assert 'Looptijd' in s and '2026-01 tot 2026-09 (gepland tot 2026-09)' in s and 'Vooruitgangshistoriek' in s
    assert 'Periode:' not in s and 'Bronmateriaal' not in s and 'Bronmateriaal' in r['markdown']
    assert '<td>20</td><td>20</td><td>0</td>' in s
    titles = [e['record']['title'] for e in b.data['meetstanden']]
    assert len(titles) == 2 and all('ri:content-title="'+t+'"' in s for t in titles)
    plan = make_plan(cat, b, cfg, {'kind': 'report', 'report': 'eindrapport', 'target': 'POR-1', 'period': '2026-10', 'inputs': closing()})
    assert [a['kind'] for a in plan['actions']] == ['page.create', 'page.attachment', 'page.attachment']
    count = len(b.data['meetstanden'])
    receipt = approve(plan, cat, cfg, b, 'Fixturetester', 'Expliciet offline akkoord', plan['hash'])
    execute(plan, receipt, cat, cfg, b, tmp/'state')
    assert len(b.data['meetstanden']) == count


def test_final_report_without_measurement_asks_for_last_progress_report(env):
    cat, cfg, b, _ = env
    r = render(cat, b.collect(), 'eindrapport', 'POR-1', '2026-10', closing(), cfg)
    assert not r['complete'] and r['assets'] == [] and r['measurement'] is None
    assert any('publiceer eerst het laatste vooruitgangsrapport' in q['question'] for q in r['questions'])


def test_final_report_refuses_period_before_last_measurement_and_tracking_input(env):
    cat, cfg, b, _ = env
    closed(env)
    with pytest.raises(ValueError, match='vóór het laatste'):
        render(cat, b.collect(), 'eindrapport', 'POR-1', '2026-08', closing(), cfg)
    with pytest.raises(ValueError, match='meetinvoer'):
        render(cat, b.collect(), 'eindrapport', 'POR-1', '2026-10', closing(), cfg, tracking={})


def test_final_report_shows_undelivered_and_unknown_honestly(env):
    cat, cfg, b, _ = env
    publish(env, '2026-04', five_answers(3), five_basis())
    r = render(cat, b.collect(), 'eindrapport', 'POR-1', '2026-05', closing(), cfg)
    assert 'Niet alle goedgekeurde milestones zijn opgeleverd.' in r['storage']
    assert '<td>Backlog</td><td>20</td><td>0</td><td>—</td>' in r['storage'] and 'Totaal (verschil: opgeleverde milestones)' in r['storage']
    assert r['chart_data']['periods'][-1] == '2026-04'


def test_retrospective_links_final_report(env):
    cat, cfg, b, tmp = env
    r = render(cat, b.collect(), 'retrospectieve', 'POR-1', '2026-10', {'goed': 'a', 'anders': 'b'}, cfg)
    assert [q['section'] for q in r['questions']] == ['eindrapport']
    closed(env)
    plan = make_plan(cat, b, cfg, {'kind': 'report', 'report': 'eindrapport', 'target': 'POR-1', 'period': '2026-10', 'inputs': closing()})
    execute(plan, approve(plan, cat, cfg, b, 'Fixturetester', 'Expliciet offline akkoord', plan['hash']), cat, cfg, b, tmp/'state')
    r = render(cat, b.collect(), 'retrospectieve', 'POR-1', '2026-10', {'goed': 'a', 'anders': 'b'}, cfg)
    assert r['complete'] and 'ri:content-title="'+plan['actions'][0]['payload']['title']+'"' in r['storage']
    assert r['storage'].index('<h2>Lessons learned</h2>') < r['storage'].index('<h3>Wat werkte</h3>')


def test_final_report_asks_maturity(env):
    # rijpheid is een verplichte keuze in het eigenschappenblok, met dezelfde waarden als het kenmerk
    cat, cfg, b, tmp = env
    closed(env)
    r = render(cat, b.collect(), 'eindrapport', 'POR-1', '2026-10', closing(), cfg)
    assert r['complete'] and 'Rijpheid' in r['storage'] and 'MVP' in r['storage']
    missing = {k: v for k, v in closing().items() if k != 'rijpheid'}
    assert not render(cat, b.collect(), 'eindrapport', 'POR-1', '2026-10', missing, cfg)['complete']
    enum = [e['value'] for e in cat.reports['eindrapport']['enums']['rijpheid']]
    assert enum == next(f['values'] for f in cat.schema['fields'] if f['key'] == 'rijpheid')
