"""Maintenance plan: class from the outage matrix, cost from as-is plus delta, one active plan per product."""
import copy
import pytest
from test_v2 import env
from test_tracking import publish, five_answers, five_basis
from aiec_lib import confluence as conf
from aiec_v2.reports import render
from aiec_v2.changes import make_plan
from aiec_v2.execution import approve, execute
from aiec_v2.maintenance import klasse, retire, DURATIONS


def matrix(*scores):
    return [{'duur': d, 'impact': str(s)} for d, s in zip(DURATIONS, scores)]


def plan_answers(**extra):
    data = {'uitval': matrix(1, 1, 2, 3, 4, 5), 'buiten_kantooruren': 'nee',
            'terugval': 'Dossierbehandelaars werken handmatig verder.',
            'as_is': [{'md': '0', 'bron': 'Green field'}],
            'runkost': [{'post': 'inference', 'omschrijving': 'Tokens', 'bedrag': '1200'},
                        {'post': 'hosting', 'omschrijving': 'Container', 'bedrag': '800,50'},
                        {'post': 'licenties', 'omschrijving': 'Geen.', 'bedrag': '0'},
                        {'post': 'overige', 'omschrijving': 'Geen.', 'bedrag': '0'}],
            'modellen': [{'component': 'Samenvatting', 'model': 'Model X 1.0', 'einde': '2027-06', 'aanpak': 'Upgrade naar Model X 2.0', 'referentiedataset': 'ja'}],
            'producten': [],
            'kwaliteit': 'Evaluatieset van 50 dossiers, elk kwartaal.',
            'afhankelijkheden': [{'afhankelijkheid': 'Dossier-API', 'einde': ''}],
            'incidenten': 'Servicedesk, dan het AIEC-team.',
            'afbouw': 'Minder dan 10 gebruikers per maand.'}
    data.update(extra)
    return data


def delivered(env):
    """Two published months: 100 md Actual."""
    publish(env, '2026-04', five_answers(3), five_basis())
    publish(env, '2026-09', five_answers(8), {})


def publish_plan(env, inputs=None, period='2026-10', slug=None):
    cat, cfg, b, tmp = env
    request = {'kind': 'report', 'report': 'onderhoud', 'target': 'POR-1', 'period': period, 'inputs': inputs or plan_answers()}
    if slug: request['slug'] = slug
    plan = make_plan(cat, b, cfg, request)
    execute(plan, approve(plan, cat, cfg, b, 'Fixturetester', 'Expliciet offline akkoord', plan['hash']), cat, cfg, b, tmp/'state')
    return plan


def props(storage):
    return conf.parse_properties(None, storage, 'aiec-onderhoud')


def test_class_rule():
    assert klasse(dict(zip(DURATIONS, [1, 1, 4, 4, 5, 5]))) == 'kritisch'
    assert klasse(dict(zip(DURATIONS, [1, 1, 2, 3, 3, 5]))) == 'belangrijk'
    assert klasse(dict(zip(DURATIONS, [1, 1, 1, 2, 4, 5]))) == 'belangrijk'
    assert klasse(dict(zip(DURATIONS, [1, 1, 1, 2, 3, 4]))) == 'standaard'


def test_green_field_plan_derives_class_and_cost(env):
    cat, cfg, b, _ = env
    delivered(env)
    r = render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-10', plan_answers(), cfg)
    assert r['complete'], r['questions']
    p = props(r['storage'])
    assert p['Product'].startswith('PROD-1 ') and p['Status'] == 'Actief' and p['Klasse'] == 'belangrijk'
    # 10 md + 12,5% of 0 as-is and of 100 delta + 5 md upgrade of one model with a reference dataset.
    assert p['Investering (md)'] == '100' and p['Onderhoud (md/jaar)'] == '27,5' and p['Runkost (€/jaar)'] == '2000,5'
    assert p['Vervangt'] == '—' and p['Geldig tot'][:4] == str(int(r['title'][:4])+1)
    s = r['storage']
    assert '→ Afgeleide klasse: belangrijk.' in s and '<td>Recurrent obv nieuwe investering</td><td>12,5 md</td>' in s
    assert 'Upgrade Model X 1.0 (Samenvatting), met referentiedataset' in s and '<th>Totaal</th><th>27,5 md</th>' in s
    assert '<th>Totaal</th><th></th><th>2000,5</th>' in s and s.index('<td>Hosting</td>') < s.index('<td>Licentie</td>') < s.index('<td>Inference</td>')
    assert '<ac:parameter ac:name="hidden">true</ac:parameter><ac:parameter ac:name="id">aiec-onderhoud</ac:parameter>' in s
    # The outage group carries the heading once; model and cost inputs are no section of their own.
    assert s.count('<h2>Impact van uitval</h2>') == 1 and '<h3>Impact van uitval</h3>' not in s and '<h3>Terugval bij uitval</h3>' in s
    assert '<h2>Product</h2>' not in s and '<h3>Bestaande investering</h3>' not in s
    assert '<h2>Modellen</h2>' in s and '<td>2027-06</td><td>Upgrade naar Model X 2.0</td><td>Ja</td>' in s
    assert '<td>Recurrent obv bestaande investering (Green field)</td><td>0 md</td>' in s
    assert s.count('<h2>Afhankelijkheden</h2>') == 1 and '<h3>Producten</h3><p>Steunt op geen andere producten.</p>' in s
    assert r['history_guard']['report'] == 'vooruitgang' and r['replaces'] is None and 'onderhoudsplan - POR-1' in r['title']


def test_matrix_must_not_decrease_and_needs_all_durations(env):
    cat, cfg, b, _ = env
    delivered(env)
    with pytest.raises(ValueError, match='niet dalen'):
        render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-10', plan_answers(uitval=matrix(1, 1, 3, 2, 4, 5)), cfg)
    r = render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-10', plan_answers(uitval=matrix(1, 1, 2)), cfg)
    assert any(q['section'] == 'uitval' for q in r['questions']) and props(r['storage'])['Klasse'] == 'onvolledig'


def test_off_hours_with_p3_is_a_note(env):
    cat, cfg, b, _ = env
    delivered(env)
    r = render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-10', plan_answers(uitval=matrix(1, 1, 1, 2, 2, 3), buiten_kantooruren='ja'), cfg)
    assert r['complete'] and any('buiten de kantooruren' in n for n in r['notes'])
    assert props(r['storage'])['Onderhoud (md/jaar)'] == '25'


def test_needs_progress_report_and_as_is(env):
    cat, cfg, b, _ = env
    r = render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-10', plan_answers(as_is=[]), cfg)
    sections = [q['section'] for q in r['questions']]
    assert sections.count('as_is') == 2 and props(r['storage'])['Investering (md)'] == 'onvolledig'


def test_unknown_as_is_is_incomplete_not_zero(env):
    cat, cfg, b, _ = env
    delivered(env)
    r = render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-10', plan_answers(as_is=[{'md': '', 'bron': 'Bestaande toepassing, niet gekend'}]), cfg)
    assert r['complete'] and props(r['storage'])['Onderhoud (md/jaar)'] == 'onvolledig'
    assert any('onbekend' in n for n in r['notes'])


def test_product_must_be_linked_and_unambiguous(env):
    cat, cfg, b, _ = env
    delivered(env)
    with pytest.raises(ValueError, match='PROD-9'):
        render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-10', plan_answers(product='PROD-9'), cfg)
    issues = b.data['objects']['issue']
    issues['PROD-2'] = copy.deepcopy(issues['PROD-1']); issues['PROD-2']['key'] = 'PROD-2'
    issues['POR-1']['fields']['issuelinks'].append({'type': {'name': 'Gerelateerd'}, 'outwardIssue': {'key': 'PROD-2'}})
    r = render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-10', plan_answers(), cfg)
    assert any('PROD-1, PROD-2' in q['question'] for q in r['questions'])
    assert render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-10', plan_answers(product='PROD-2'), cfg)['complete']


def test_new_version_replaces_previous_plan(env):
    cat, cfg, b, _ = env
    delivered(env)
    first = publish_plan(env)
    first_title = first['actions'][0]['payload']['title']
    with pytest.raises(ValueError, match='vorige onderhoudsplan'):
        render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-11', plan_answers(), cfg, 'tweede')
    # A corrected plan of the same project keeps the as-is: no double count of its own delta.
    same = render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-11', plan_answers(as_is=[]), cfg, 'tweede')
    assert same['complete'] and same['replaces']['title'] == first_title and props(same['storage'])['Investering (md)'] == '100'
    assert 'Recurrent obv bestaande investering: <ac:link><ri:page ri:content-title="'+first_title+'"/>' in same['storage']
    # A plan from another project builds on the whole previous investment.
    page = next(v for v in b.data['objects']['page'].values() if v['title'] == first_title)
    page['body']['storage']['value'] = page['body']['storage']['value'].replace('<th>Project</th><td>POR-1</td>', '<th>Project</th><td>POR-9</td>')
    r = render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-11', plan_answers(as_is=[]), cfg, 'tweede')
    p = props(r['storage'])
    assert p['As-is (md)'] == '100' and p['Delta (md)'] == '100' and p['Investering (md)'] == '200' and p['Vervangt'] == first_title
    plan = make_plan(cat, b, cfg, {'kind': 'report', 'report': 'onderhoud', 'target': 'POR-1', 'period': '2026-11', 'inputs': plan_answers(as_is=[]), 'slug': 'tweede'})
    assert [a['kind'] for a in plan['actions']] == ['page.create', 'page.update']
    old = props(plan['actions'][1]['payload']['body']['storage']['value'])
    assert old['Status'] == 'Vervangen' and old['Vervangen door'] == r['title']
    execute(plan, approve(plan, cat, cfg, b, 'Fixturetester', 'Expliciet offline akkoord', plan['hash']), cat, cfg, b, env[3]/'state')
    # Only the new version is active; a third plan replaces that one.
    third = render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-12', plan_answers(as_is=[]), cfg, 'derde')
    assert third['replaces']['title'] == r['title']


def test_retire_refuses_twice_and_two_active_plans_refuse(env):
    cat, cfg, b, _ = env
    delivered(env)
    first = publish_plan(env)
    storage = first['actions'][0]['payload']['body']['storage']['value']
    once = retire(cat.schema, storage, 'Nieuw')
    with pytest.raises(ValueError, match='al vervangen'):
        retire(cat.schema, once, 'Nog nieuwer')
    pages = b.data['objects']['page']
    new_id = next(k for k, v in pages.items() if v['title'] == first['actions'][0]['payload']['title'])
    pages['999'] = copy.deepcopy(pages[new_id]); pages['999']['id'] = '999'; pages['999']['title'] = '2026-10-01 - onderhoudsplan - POR-1 - kopie'
    with pytest.raises(ValueError, match='Meer dan één actief'):
        render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-11', plan_answers(as_is=[]), cfg, 'tweede')


def test_legacy_plan_without_properties_is_named(env):
    from test_v2 import _gate_env
    cat, cfg, b, _ = env
    delivered(env)
    _gate_env(b, [('100', 'onderhoudsplan')])
    r = render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-10', plan_answers(), cfg)
    assert any('zonder productkoppeling' in n for n in r['notes'])


def test_gate_asks_onderhoudsplan_per_project_only(env):
    from test_v2 import _gate_env
    cat, cfg, b, _ = env
    _gate_env(b, [('90', 'opleveringsverslag')])
    q = make_plan(cat, b, cfg, {'kind': 'transition', 'key': 'AI-38', 'to': 'Uitvoering'})['questions']
    assert 'Gate-artefact ontbreekt voor project POR-1: onderhoudsplan' in q and 'Gate-artefact ontbreekt: onderhoudsplan' not in q


def test_models_drive_upgrade_cost_and_must_be_answered(env):
    cat, cfg, b, _ = env
    delivered(env)
    none = render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-10', plan_answers(modellen=[]), cfg)
    assert none['complete'] and props(none['storage'])['Onderhoud (md/jaar)'] == '22,5'
    assert 'Upgrades van (taal)modellen <ac:structured-macro' in none['storage']
    assert '<h2>Modellen</h2>' not in none['storage']
    two = [{'component': 'A', 'model': 'M1', 'aanpak': 'Equivalent model', 'referentiedataset': 'ja'},
           {'component': 'B', 'model': 'M2', 'aanpak': 'Equivalent model', 'referentiedataset': 'nee'}]
    assert props(render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-10', plan_answers(modellen=two), cfg)['storage'])['Onderhoud (md/jaar)'] == '37,5'
    answers = plan_answers(); del answers['modellen']
    r = render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-10', answers, cfg)
    assert any(q['section'] == 'modellen' for q in r['questions'])


def test_runkost_needs_every_post(env):
    cat, cfg, b, _ = env
    delivered(env)
    r = render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-10', plan_answers(runkost=[{'post': 'hosting', 'omschrijving': 'Geen.', 'bedrag': '0'}]), cfg)
    assert any(q['section'] == 'runkost' for q in r['questions'])


def test_product_dependencies_need_existing_keys(env):
    cat, cfg, b, _ = env
    delivered(env)
    issues = b.data['objects']['issue']
    issues['PROD-7'] = copy.deepcopy(issues['PROD-1']); issues['PROD-7']['key'] = 'PROD-7'; issues['PROD-7']['fields']['summary'] = 'Kaartdienst'
    r = render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-10', plan_answers(producten=[{'product': 'PROD-7', 'waarvoor': 'Kaartlagen'}]), cfg)
    assert r['complete'] and '<td>PROD-7 — Kaartdienst</td><td>Kaartlagen</td>' in r['storage']
    for key, error in (('PROD-8', 'bestaat niet'), ('PROD-1', 'het product zelf'), ('Kaartdienst', 'geen PROD-key')):
        with pytest.raises(ValueError, match=error):
            render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-10', plan_answers(producten=[{'product': key, 'waarvoor': 'x'}]), cfg)
    answers = plan_answers(); del answers['producten']
    assert any(q['section'] == 'producten' for q in render(cat, b.collect(), 'onderhoud', 'POR-1', '2026-10', answers, cfg)['questions'])
