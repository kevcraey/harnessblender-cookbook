"""Intern project: a project without POR ticket, with the same structure and requirements."""
from datetime import date
import pytest
from test_v2 import env, approved
from test_monthly import answers, measurement_input
from aiec_lib import confluence as conf
from aiec_v2.catalog import matches
from aiec_v2.changes import make_plan
from aiec_v2.execution import execute
from aiec_v2.review import review, datasets

DECISION = '2026-09-21 - beslissing - reguliere-werking'


def _decision(b):
    """Decision page under the initiative (100), and POR-1 unlinked: AI-38 only has what the test adds."""
    body = conf.details_macro({}, '<tr><th>Overgang naar</th><td>Implementatie</td></tr>', details_id='aiec-beslissing')
    b.data['objects']['page']['96'] = {'id': '96', 'type': 'page', 'title': DECISION, 'version': {'number': 1, 'when': '2026-09-21T10:00:00'},
        'space': {'key': 'AI'}, 'metadata': {'labels': {'results': [{'name': 'decisions'}]}}, 'ancestors': [{'id': '100'}],
        'body': {'storage': {'value': body, 'representation': 'storage'}}}
    b.data['objects']['issue']['AI-38']['fields']['issuelinks'] = [l for l in b.data['objects']['issue']['AI-38']['fields']['issuelinks'] if l['outwardIssue']['key'] != 'POR-1']
    del b.data['objects']['page']['90']
    b.data['objects']['issue']['AI-38']['fields']['status'] = {'name': 'implementatie'}


def _create(env, status='InUitvoering', startdatum='2026-08-01'):
    cat, cfg, b, tmp = env; cfg['atlassian']['jira_server_id'] = 'abc'
    p, r = approved(env, {'kind': 'project-page', 'key': 'AI-38', 'intern': True, 'summary': 'Proef intern', 'status': status, 'startdatum': startdatum, 'beslissing': '96'})
    execute(p, r, cat, cfg, b, tmp/'state')
    return next(x for x in b.data['objects']['page'].values() if x['title'] == 'intern - Proef intern')


def test_intern_project_needs_formal_decision(env):
    cat, cfg, b, _ = env; cfg['atlassian']['jira_server_id'] = 'abc'; _decision(b)
    req = {'kind': 'project-page', 'key': 'AI-38', 'intern': True, 'summary': 'Proef intern', 'status': 'InUitvoering', 'startdatum': '2026-08-01'}
    with pytest.raises(ValueError, match='Beslissing'): make_plan(cat, b, cfg, req)
    with pytest.raises(ValueError, match='Beslissing'): make_plan(cat, b, cfg, dict(req, beslissing='95'))   # initiatierapport, geen beslissingspagina
    with pytest.raises(ValueError, match='Status'): make_plan(cat, b, cfg, dict(req, beslissing='96', status='Bezig'))
    with pytest.raises(ValueError, match='Startdatum'): make_plan(cat, b, cfg, {k: v for k, v in dict(req, beslissing='96').items() if k != 'startdatum'})
    with pytest.raises(ValueError, match='Startdatum'): make_plan(cat, b, cfg, dict(req, beslissing='96', startdatum='augustus'))


def test_intern_project_page_is_a_project(env):
    cat, cfg, b, _ = env; _decision(b)
    s = b.collect()
    assert any(f['rule'] == 'geen-project' and f['key'] == 'AI-38' for f in review(cat, s))
    page = _create(env)
    storage = page['body']['storage']['value']
    assert page['ancestors'][0]['id'] == '100' and 'aiec-project' in storage and 'key = AI-38' in storage and 'linkedIssues' not in storage
    s = b.collect(); d = datasets(cat, s)
    intern = next(p for p in d['projects'] if p['key'] == 'AI-38-intern-1')
    assert (intern['type'], intern['title_key'], intern['status'], intern['page_id'], intern['beslissing_ok']) == ('intern', 'intern', 'InUitvoering', page['id'], True)
    assert next(i for i in d['initiatives'] if i['key'] == 'AI-38')['project_keys'] == ['AI-38-intern-1']
    findings = review(cat, s, date(2026, 10, 20))
    assert not any(f['rule'] in ('geen-project', 'intern-zonder-beslissing', 'projectpagina', 'artefactlabel') for f in findings)
    # Same requirements as a POR project: a monthly progress report while InUitvoering.
    assert any(f['rule'] == 'maandrapport' and f['key'] == 'AI-38-intern-1' for f in findings)


def test_several_intern_projects_per_initiative(env):
    cat, cfg, b, tmp = env; _decision(b); first = _create(env)
    p, r = approved(env, {'kind': 'project-page', 'key': 'AI-38', 'intern': True, 'summary': 'Tweede luik', 'status': 'Backlog', 'startdatum': '2026-10-01', 'beslissing': '96'})
    execute(p, r, cat, cfg, b, tmp/'state')
    d = datasets(cat, b.collect())
    assert sorted(x['key'] for x in d['projects'] if x['type'] == 'intern') == ['AI-38-intern-1', 'AI-38-intern-2']
    # A report of one internal project is never taken for the other's: same title key, different project page.
    b.data['objects']['page']['300'] = {'id': '300', 'type': 'page', 'title': '2026-09-30 - vooruitgang - intern - proef-intern', 'version': {'number': 1, 'when': '2026-09-30T10:00:00'},
        'space': {'key': 'AI'}, 'metadata': {'labels': {'results': [{'name': 'vooruitgangsrapport'}]}}, 'ancestors': [{'id': first['id']}], 'body': {'storage': {'value': '<p>x</p>', 'representation': 'storage'}}}
    from aiec_v2.reports import linked_page
    d = datasets(cat, b.collect())
    assert linked_page(cat, d, 'vooruitgang', 'AI-38-intern-1', 'AI-38') and not linked_page(cat, d, 'vooruitgang', 'AI-38-intern-2', 'AI-38')


def test_intern_decision_must_exist(env):
    cat, cfg, b, _ = env; _decision(b); page = _create(env)
    # Confluence rewrites links on rename: link and decision title move together.
    b.data['objects']['page']['96']['title'] = 'Andere titel'
    body = b.data['objects']['page'][page['id']]['body']['storage']
    body['value'] = body['value'].replace(DECISION, 'Andere titel')
    assert not any(f['rule'] == 'intern-zonder-beslissing' for f in review(cat, b.collect()))
    # A link to a page that is not a decision under this initiative does not count.
    body['value'] = body['value'].replace('Andere titel', 'Losse pagina')
    assert any(f['rule'] == 'intern-zonder-beslissing' and f['key'] == 'AI-38-intern-1' for f in review(cat, b.collect()))


def test_intern_status_is_kept_on_the_page(env):
    cat, cfg, b, tmp = env; _decision(b); page = _create(env)
    p, r = approved(env, {'kind': 'project-eigenschappen', 'key': 'AI-38-intern-1', 'status': 'Uitgevoerd'})
    execute(p, r, cat, cfg, b, tmp/'state')
    intern = next(x for x in datasets(cat, b.collect())['projects'] if x['key'] == 'AI-38-intern-1')
    assert (intern['status'], intern['startdatum']) == ('Uitgevoerd', '2026-08-01') and 'Proef intern' in b.get('page', page['id'])['title']
    with pytest.raises(ValueError, match='Status'): make_plan(cat, b, cfg, {'kind': 'project-eigenschappen', 'key': 'AI-38-intern-1', 'status': 'Klaar'})
    with pytest.raises(ValueError, match='status en/of startdatum'): make_plan(cat, b, cfg, {'kind': 'project-eigenschappen', 'key': 'AI-38-intern-1'})


def test_por_status_stays_in_jira(env):
    cat, cfg, b, _ = env
    with pytest.raises(ValueError, match='POR-status staat in Jira'): make_plan(cat, b, cfg, {'kind': 'project-eigenschappen', 'key': 'POR-1', 'status': 'Uitgevoerd'})


def test_intern_progress_report_under_intern_page(env):
    cat, cfg, b, tmp = env; _decision(b); page = _create(env)
    plan = make_plan(cat, b, cfg, {'kind': 'report', 'report': 'vooruitgang', 'target': 'AI-38-intern-1', 'period': '2026-09', 'inputs': answers(), 'tracking': measurement_input()})
    assert not plan['questions']
    create = next(a for a in plan['actions'] if a['kind'] == 'page.create')
    assert create['payload']['title'].endswith(' - vooruitgang - intern - proef-intern')
    assert create['payload']['ancestors'] == [{'id': page['id']}]
    assert 'issue:AI-38-intern-1' not in {f"{x['kind']}:{x['key']}" for x in plan['preconditions']}
    assert 'key in (AI-38)' in create['payload']['body']['storage']['value']


def test_hours_rule_ignores_intern_projects(env):
    cat, cfg, b, _ = env; _decision(b); _create(env)
    s = b.collect(); s['hours'] = {'per_initiative': {'AI-38': {'period_h': 10.0, 'direct_h': 10.0}}}
    assert not any(f['rule'] == 'uren-op-initiatief' for f in review(cat, s))


def test_ceiling_rule(env):
    cat, _, _, _ = env; rule = cat.rules['intern-boven-plafond']['when']
    assert matches(rule, {'type': 'intern', 'actual_md': 10.5}) and not matches(rule, {'type': 'intern', 'actual_md': 10})
    assert not matches(rule, {'type': 'por', 'actual_md': 40})


def test_intern_actual_comes_from_last_measurement(env):
    cat, cfg, b, tmp = env; _decision(b); _create(env)
    p, r = approved(env, {'kind': 'report', 'report': 'vooruitgang', 'target': 'AI-38-intern-1', 'period': '2026-09', 'inputs': answers(), 'tracking': measurement_input()})
    execute(p, r, cat, cfg, b, tmp/'state')
    intern = next(x for x in datasets(cat, b.collect())['projects'] if x['key'] == 'AI-38-intern-1')
    assert intern['actual_md'] == 3.5


def test_intern_reports_from_start_month(env):
    """Monthly progress reports are required from the start date's month on, not before."""
    cat, cfg, b, tmp = env; _decision(b); _create(env, startdatum='2026-09-10')
    due = lambda today: any(f['rule'] == 'maandrapport' and f['key'] == 'AI-38-intern-1' for f in review(cat, b.collect(), today))
    assert not due(date(2026, 9, 29))    # August is before the start
    assert due(date(2026, 10, 20))       # September is the start month


def test_start_date_is_required(env):
    """A page made before the start date was required is flagged, and gets the row through project-eigenschappen."""
    cat, cfg, b, tmp = env; _decision(b); page = _create(env)
    body = b.data['objects']['page'][page['id']]['body']['storage']
    body['value'] = body['value'].replace('<tr><th>Startdatum</th><td>2026-08-01</td></tr>', '')
    assert any(f['rule'] == 'intern-zonder-startdatum' and f['severity'] == 'error' for f in review(cat, b.collect()))
    p, r = approved(env, {'kind': 'project-eigenschappen', 'key': 'AI-38-intern-1', 'startdatum': '2026-08-03'})
    execute(p, r, cat, cfg, b, tmp/'state')
    assert '<tr><th>Status</th><td>InUitvoering</td></tr><tr><th>Startdatum</th><td>2026-08-03</td></tr>' in b.get('page', page['id'])['body']['storage']['value']
    assert not any(f['rule'] == 'intern-zonder-startdatum' for f in review(cat, b.collect()))
