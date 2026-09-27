"""Fixed baselines, append-only monthly measurements and approved PNG publication."""
import base64
import copy
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys
import pytest
from test_v2 import env
from test_monthly import answers, measurement_input
from aiec_v2 import tracking, report_history, report_charts
from aiec_v2.backend import FixtureBackend, LiveBackend
from aiec_v2.catalog import digest
from aiec_v2.reports import render
from aiec_v2.changes import make_plan, plan_markdown
from aiec_v2.execution import approve, execute, Refused
from aiec_v2.report_assets import attachment_bytes
from aiec_lib import http, config


def five_basis():
    values = [0, 20, 40, 60, 65, 70, 75, 80, 100]
    return {'baseline': {'budget_md': 100, 'source': 'Fictieve goedgekeurde 1/1/1/4/1-maandenplanning',
        'milestones': [{'nr': i, 'milestone': f'Milestone {i}', 'planned_md': 20} for i in range(1, 6)],
        'plan': [{'period': f'2026-{i+1:02d}', 'scope_md': v, 'effort_md': v} for i, v in enumerate(values)]}}


def five_answers(index=5):
    data = answers(); rows = []; cursor = 0
    for ident, duration in enumerate([1, 1, 1, 4, 1], 1):
        elapsed = max(0, min(index-cursor, duration)); actual = 20*elapsed/duration
        status = 'Opgeleverd' if elapsed == duration else ('Backlog' if elapsed == 0 else 'Bezig')
        rows.append({'nr': ident, 'milestone': f'Milestone {ident}', 'status': status, 'actual_md': actual,
                     'remaining_md': 20-actual, 'gezondheid': 'op-schema', 'notities': ''})
        cursor += duration
    data['milestones'] = rows
    return data


def prepared(env, index=5, data=None, measure=None):
    cat, cfg, backend, _ = env
    return tracking.prepare(cat.reports['vooruitgang'], backend.collect(), 'POR-1', 'AI-38', f'2026-{index+1:02d}',
                            five_answers(index) if data is None else data, five_basis() if measure is None else measure)


def publish(env, period='2026-09', data=None, measure=None):
    cat, cfg, backend, tmp = env
    request = {'kind': 'report', 'report': 'vooruitgang', 'target': 'POR-1', 'period': period,
               'inputs': answers() if data is None else data, 'tracking': measurement_input() if measure is None else measure}
    plan = make_plan(cat, backend, cfg, request)
    receipt = approve(plan, cat, cfg, backend, 'Fixturetester', 'Expliciet offline akkoord', plan['hash'])
    result = execute(plan, receipt, cat, cfg, backend, tmp/'state')
    return plan, result


@pytest.mark.parametrize('index,expected', [(4, 65), (5, 70), (6, 75)])
def test_five_equal_milestones(env, index, expected):
    p = prepared(env, index)
    assert not p['questions']
    m = p['state']['metrics']
    assert m['delivered_md'] == '60' and Decimal(m['estimated_md']) == expected
    assert Decimal(m['actual_md']) == expected and m['approved_md'] == '100' and not m['done']
    assert p['state']['milestones'][3]['weight_md'] == '20'


def test_raw_input_preserved_and_baseline_derived(env):
    data = five_answers(); before = copy.deepcopy(data)
    p = prepared(env, data=data)
    assert data == before and p['state']['inputs'] == before
    assert all(row['baseline_md'] == '20' for row in p['inputs']['milestones'])
    assert all('baseline_md' not in row for row in data['milestones'])


def test_conflicting_manual_baseline_and_remaining_are_not_replaced(env):
    data = five_answers(); data['milestones'][3]['baseline_md'] = 2
    p = prepared(env, data=data)
    assert not any('Baseline' in q['question'] for q in p['questions'])
    assert any('Baseline 2 genegeerd' in n for n in p['notes'])
    assert p['inputs']['milestones'][3]['baseline_md'] == '20' and data['milestones'][3]['baseline_md'] == 2
    data['milestones'][0]['remaining_md'] = 5
    p = prepared(env, data=data)
    assert any('opgeleverd maar' in q['question'] for q in p['questions'])
    assert p['inputs']['milestones'][0]['remaining_md'] == 5


def test_missing_remaining_and_zero_not_auto_closed(env):
    data = five_answers(); data['milestones'][3]['remaining_md'] = None
    assert any('Remaining ontbreekt' in q['question'] for q in prepared(env, data=data)['questions'])
    data['milestones'][3]['remaining_md'] = 0
    p = prepared(env, data=data)
    assert any('niet opgeleverd' in q['question'] for q in p['questions']) and not p['state']['metrics']['done']


def test_backlog_defaults_only_original_plan(env):
    data = five_answers(); data['milestones'][-1].pop('remaining_md')
    p = prepared(env, data=data)
    assert not p['questions'] and p['state']['milestones'][-1]['remaining_md'] == '20'


def test_unknown_actual_is_not_partial_total_or_zero(env):
    data = five_answers(); data['milestones'][0]['actual_md'] = None
    p = prepared(env, data=data)
    assert not p['questions'] and p['state']['metrics']['actual_md'] is None
    assert p['state']['metrics']['delivered_md'] == '60'


def addition():
    return {'id': 'scope-1', 'month': '2026-06', 'decision': {'by': 'Projectleider', 'date': '2026-06-01', 'source': 'Fictief besluit'},
            'milestones': [{'nr': 6, 'milestone': 'Extra scope', 'weight_md': 20}]}


@pytest.mark.parametrize('done,expected', [(False, ('100', '110', '110')), (True, ('120', '120', '124'))])
def test_added_scope_exceeds_original_reference(env, done, expected):
    measure = five_basis(); measure['scope_changes'] = [addition()]
    data = five_answers(8)
    data['milestones'].append({'nr': 6, 'milestone': 'Extra scope', 'status': 'Opgeleverd' if done else 'Bezig',
                              'actual_md': 24 if done else 10, 'remaining_md': 0 if done else 10, 'gezondheid': 'op-schema'})
    p = prepared(env, index=8, data=data, measure=measure)
    assert not p['questions']
    m = p['state']['metrics']
    assert (m['delivered_md'], m['estimated_md'], m['actual_md']) == expected
    assert m['scope_denominator_md'] == '100' and m['approved_md'] == '120' and m['done'] == done
    d = report_charts.series(p['state'], [])
    assert d['approved'][4] == 100 and d['approved'][5] == 120


def test_added_backlog_keeps_explicit_remaining(env):
    measure = five_basis(); measure['scope_changes'] = [addition()]
    data = five_answers(); data['milestones'].append({'nr': 6, 'milestone': 'Extra scope', 'status': 'Backlog', 'actual_md': 0, 'remaining_md': 20, 'gezondheid': 'op-schema'})
    p = prepared(env, data=data, measure=measure)
    assert not p['questions'] and p['state']['milestones'][-1]['remaining_md'] == '20'
    data['milestones'][-1].pop('remaining_md')
    assert any('Remaining ontbreekt' in q['question'] for q in prepared(env, data=data, measure=measure)['questions'])


def test_early_assumption_is_automatic_and_only_in_reported_month(env):
    data = five_answers(1)
    data['milestones'][0].update(status='Bezig', actual_md=2, remaining_md=None)
    p = prepared(env, 1, data, five_basis())  # No toggle needed: nothing delivered and no complete estimate.
    assert not p['questions'] and p['state']['metrics']['assumed_md'] == '20'
    assert p['state']['metrics']['estimated_md'] is None
    d = report_charts.series(p['state'], [])
    assert d['assumed'] == [None, 20, None, None, None, None, None, None, None]
    assert d['delivered'][0] is None and d['actual'][2] is None
    # After the first delivery, or with a complete Actual/Remaining estimate, there is no assumption.
    assert prepared(env, measure=five_basis())['state']['metrics']['assumed_md'] is None
    assert prepared(env, 0, five_answers(0), five_basis())['state']['metrics']['assumed_md'] is None
    # The former manual toggle in old files is ignored, not an error.
    measure = five_basis(); measure['assume_on_plan'] = True
    assert prepared(env, measure=measure)['state']['metrics']['assumed_md'] is None


def test_metadata_unknown_and_bad_numbers_refused(env):
    measure = five_basis(); measure['mystery'] = 1
    with pytest.raises(ValueError, match='onbekende'): prepared(env, measure=measure)
    measure = five_basis(); measure['baseline']['budget_md'] = 0
    with pytest.raises(ValueError, match='positief'): prepared(env, measure=measure)
    measure = five_basis(); measure['baseline']['plan'][2]['scope_md'] = 200
    with pytest.raises(ValueError, match='planning'): prepared(env, measure=measure)


def test_complete_publication_has_three_journalled_actions_and_portable_history(env):
    plan, outcome = publish(env)
    assert [a['kind'] for a in plan['actions']] == ['page.create', 'page.attachment', 'page.attachment', 'meetstand.archive']
    assert 'data:image/png;base64,' in plan['preview_html']
    assert 'content_base64": "iVBOR' not in plan_markdown(plan)
    page_id = outcome['results'][0]['result']['id']
    cat, cfg, b, tmp = env
    assert len(b.data['objects']['attachments'][page_id]) == 2
    # The measurement lives in the archive, not on the page; Confluence only shows the progress history.
    storage = b.data['objects']['page'][page_id]['body']['storage']['value']
    assert 'aiec-meetstand' not in storage and 'Vooruitgangshistoriek' in storage and 'Meetbasis' not in storage
    assert [e['page_id'] for e in b.data['meetstanden']] == [page_id]
    history = report_history.load(cat.reports['vooruitgang'], b.collect(), 'POR-1', 'AI-38')
    assert len(history['records']) == 1
    # Reload from the fixture on disk: history is not merely process-local state.
    other = FixtureBackend(b.path, cat, cfg)
    assert report_history.load(cat.reports['vooruitgang'], other.collect(), 'POR-1', 'AI-38')['records'] == history['records']
    for attachment in b.data['objects']['attachments'][page_id].values():
        assert attachment_bytes(attachment).startswith(b'\x89PNG')


def test_second_month_freezes_old_snapshot_and_gaps(env):
    _, out = publish(env, '2026-02', five_answers(1), five_basis())
    b = env[2]; first_id = out['results'][0]['result']['id']; before = copy.deepcopy(b.get('page', first_id))
    result = render(env[0], b.collect(), 'vooruitgang', 'POR-1', '2026-04', five_answers(3), env[1], tracking={})
    assert result['complete'] and result['chart_data']['delivered'][:4] == [None, 20, None, 60]
    assert result['measurement']['previous_hash'] == b.data['meetstanden'][0]['record']['hash']
    publish(env, '2026-04', five_answers(3), {})
    assert b.get('page', first_id) == before
    with pytest.raises(ValueError, match='bestaat al'):
        render(env[0], b.collect(), 'vooruitgang', 'POR-1', '2026-02', five_answers(1), env[1], tracking={})


def test_baseline_and_old_scope_immutable(env):
    publish(env, '2026-06', five_answers(5), five_basis())
    measure = five_basis(); measure['baseline']['source'] = 'Nieuwe baseline'
    with pytest.raises(ValueError, match='onveranderlijk'): prepared(env, 6, measure=measure)
    measure = {'scope_changes': [addition()]}
    with pytest.raises(ValueError, match='historiek'): prepared(env, 6, measure=measure)


@pytest.mark.parametrize('suffix', ['<p>Menselijk toegevoegd</p>', ' los toegevoegde menselijke tekst'])
def test_manual_content_change_requires_review(env, suffix):
    _, out = publish(env)
    page = env[2].data['objects']['page'][out['results'][0]['result']['id']]
    page['body']['storage']['value'] += suffix
    with pytest.raises(ValueError, match='handmatig gewijzigd'):
        report_history.load(env[0].reports['vooruitgang'], env[2].collect(), 'POR-1', 'AI-38')


def test_record_tamper_and_missing_history_detected(env):
    _, out = publish(env)
    env[2].data['meetstanden'][0]['record']['baseline']['source'] = 'Stiekem aangepaste planning'
    with pytest.raises(ValueError, match='gewijzigd'): report_history.load(env[0].reports['vooruitgang'], env[2].collect(), 'POR-1', 'AI-38')


def test_server_macro_ids_and_cdata_text_do_not_break_integrity(env):
    data = answers(); data['milestones'][0]['notities'] = 'Letterlijk &nbsp; ]]> <!DOCTYPE test> behouden'
    _, out = publish(env, data=data)
    page = env[2].data['objects']['page'][out['results'][0]['result']['id']]
    page['body']['storage']['value'] = page['body']['storage']['value'].replace('<ac:structured-macro ', '<ac:structured-macro ac:macro-id="server-generated" ')
    loaded = report_history.load(env[0].reports['vooruitgang'], env[2].collect(), 'POR-1', 'AI-38')
    assert loaded['records'][0]['inputs']['milestones'][0]['notities'] == data['milestones'][0]['notities']


def test_new_history_after_proposal_refuses_execution(env):
    cat, cfg, b, tmp = env
    request = {'kind': 'report', 'report': 'vooruitgang', 'target': 'POR-1', 'period': '2026-04', 'inputs': five_answers(3), 'tracking': five_basis()}
    plan = make_plan(cat, b, cfg, request)
    receipt = approve(plan, cat, cfg, b, 'Test', 'Akkoord', plan['hash'])
    publish(env, '2026-02', five_answers(1), five_basis())
    with pytest.raises(Refused, match='historiek is gewijzigd'):
        execute(plan, receipt, cat, cfg, b, tmp/'state')


def test_legacy_report_requires_explicit_new_start(env):
    cat, cfg, b, _ = env
    page = copy.deepcopy(b.data['objects']['page']['101']); page['id'] = '102'
    page['title'] = '[AI-38] Vooruitgang — POR-1 — 2026-08'
    page['metadata']['labels']['results'] = [{'name': 'vooruitgangsrapport'}]
    b.data['objects']['page']['102'] = page
    result = render(cat, b.collect(), 'vooruitgang', 'POR-1', '2026-09', answers(), cfg, tracking=measurement_input())
    assert not result['complete'] and any('legacy_ack' in q['question'] for q in result['questions'])
    measure = measurement_input(); measure['legacy_ack'] = {'pages': ['102'], 'reason': 'Oude cijfers zijn niet betrouwbaar reconstrueerbaar; nieuwe meetstart.'}
    assert render(cat, b.collect(), 'vooruitgang', 'POR-1', '2026-09', answers(), cfg, tracking=measure)['complete']


def test_decreasing_actual_needs_explicit_correction(env):
    publish(env, '2026-02', five_answers(1), five_basis())
    data = five_answers(2); data['milestones'][0]['actual_md'] = 18
    p = prepared(env, 2, data, {})
    assert any('gedaald' in q['question'] for q in p['questions'])
    p = prepared(env, 2, data, {'corrections': [{'nr': 1, 'reason': 'Boekingscorrectie, vorige meetstand blijft staan.'}]})
    assert not p['questions'] and any('Boekingscorrectie' in n for n in p['notes'])


def test_png_is_deterministic_and_has_fixed_palette(env):
    p = prepared(env); d = report_charts.series(p['state'], [])
    raw = report_charts.png(d, 'scope')
    assert raw == report_charts.png(d, 'scope')
    from PIL import Image
    from io import BytesIO
    colors = {color for _, color in Image.open(BytesIO(raw)).getcolors(maxcolors=65536)}
    assert Image.open(BytesIO(report_charts.png(d, 'scope', width=600))).size == (1200, 1350)
    assert (51, 51, 50) in colors and (0, 85, 204) in colors
    assert report_charts.runs([0, 20, None, 60]) == [[(0, 0), (1, 20)], [(3, 60)]]


@pytest.mark.parametrize('count,expected', [(1, [0]), (2, [0, 1]), (9, [0, 2, 4, 6, 8]), (10, [0, 2, 4, 6, 9])])
def test_last_axis_label_does_not_collide_with_previous(count, expected):
    assert report_charts.label_indices(count, 5) == expected


def test_attachment_path_and_hash_validation(env):
    p = prepared(env); _, assets = report_charts.build(p['state'], [])
    payload = {k: v for k, v in assets[0].items() if k != 'kind'}; payload['page_action'] = '1'
    assert attachment_bytes(payload)
    for filename in ('../bad.png', 'bad\r\nHeader.png', '/absolute.png', 'image.svg'):
        with pytest.raises(ValueError): attachment_bytes(dict(payload, filename=filename))
    with pytest.raises(ValueError): attachment_bytes(dict(payload, sha256='0'*64))


def test_upload_failure_is_journalled_and_not_retried(env, monkeypatch):
    cat, cfg, b, tmp = env
    plan = make_plan(cat, b, cfg, {'kind': 'report', 'report': 'vooruitgang', 'target': 'POR-1', 'period': '2026-09', 'inputs': answers(), 'tracking': measurement_input()})
    receipt = approve(plan, cat, cfg, b, 'Test', 'Akkoord', plan['hash'])
    mutate = b.mutate
    def fail(a):
        if a['kind'] == 'page.attachment': raise OSError('Fictieve uploadfout')
        return mutate(a)
    monkeypatch.setattr(b, 'mutate', fail)
    with pytest.raises(Refused, match='niet opnieuw'): execute(plan, receipt, cat, cfg, b, tmp/'state')
    assert b.title_exists('AI', plan['actions'][0]['payload']['title'])
    with pytest.raises(Refused, match='al uitgevoerd'): execute(plan, receipt, cat, cfg, b, tmp/'state')
    events = [json.loads(line)['event'] for line in (tmp/'state/fixture'/f"{plan['id']}.jsonl").read_text().splitlines()]
    assert events[-1] == 'stopped' and 'succeeded' in events


def test_attachment_cannot_target_existing_page(env):
    cat, cfg, b, _ = env
    p = make_plan(cat, b, cfg, {'kind': 'report', 'report': 'vooruitgang', 'target': 'POR-1', 'period': '2026-09', 'inputs': answers(), 'tracking': measurement_input()})
    p['actions'][1]['key'] = '100'; p['hash'] = digest({k: v for k, v in p.items() if k != 'hash'})
    with pytest.raises(Refused, match='eerdere nieuwe'): approve(p, cat, cfg, b, 'Test', 'Akkoord', p['hash'])


def test_http_upload_retains_read_only_guard_and_uses_multipart(monkeypatch):
    client = http.Client('https://example.invalid', 'fixture-token')
    with pytest.raises(config.GuardRefused): client.upload_attachment('100', 'graph.png', b'\x89PNG\r\n\x1a\nbytes')
    captured = {}
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return b'{"results":[{"id":"att1"}]}'
    class Opener:
        def open(self, req, timeout):
            captured['request'] = req
            return Response()
    monkeypatch.setattr(http, '_OPENER', Opener()); monkeypatch.setattr(http, 'PAUSE', 0)
    client.writable = True
    client.upload_attachment('100', 'graph.png', b'\x89PNG\r\n\x1a\nbytes')
    req = captured['request']
    assert req.get_header('Content-type').startswith('multipart/form-data; boundary=')
    assert b'filename="graph.png"' in req.data and b'Content-Type: image/png' in req.data
    assert req.get_header('X-atlassian-token') == 'no-check'


def test_legacy_other_project_does_not_block_this_project(env):
    cat, cfg, b, _ = env
    page = copy.deepcopy(b.data['objects']['page']['101']); page['id'] = '102'
    page['title'] = '[AI-38] Vooruitgang — POR-2 — 2026-08'
    page['metadata']['labels']['results'] = [{'name': 'vooruitgangsrapport'}]
    b.data['objects']['page']['102'] = page
    result = render(cat, b.collect(), 'vooruitgang', 'POR-1', '2026-09', answers(), cfg, tracking=measurement_input())
    assert result['complete']


def test_tracking_still_requires_status_when_custom_table_marks_it_optional(env):
    cat, cfg, b, _ = env
    report = cat.reports['vooruitgang']
    next(c for c in report['sections'][3]['columns'] if c['id'] == 'status')['required'] = False
    data = answers(); data['milestones'][0].pop('status')
    result = render(cat, b.collect(), 'vooruitgang', 'POR-1', '2026-09', data, cfg, tracking=measurement_input())
    assert not result['complete'] and not result['measurement']
    assert any('voortgangsstatus' in q['question'] for q in result['questions'])


def test_old_collector_snapshot_requires_fresh_history(env):
    cat, cfg, b, _ = env
    snapshot = b.collect(); snapshot.pop('report_pages')
    result = render(cat, snapshot, 'vooruitgang', 'POR-1', '2026-09', answers(), cfg, tracking=measurement_input())
    assert not result['complete'] and any('collector' in q['question'] for q in result['questions'])


def test_missing_chain_link_is_not_silently_skipped(env):
    _, first = publish(env, '2026-02', five_answers(1), five_basis())
    publish(env, '2026-04', five_answers(3), {})
    removed = env[2].data['meetstanden'].pop(0)
    with pytest.raises(ValueError, match='Onderbroken'):
        report_history.load(env[0].reports['vooruitgang'], env[2].collect(), 'POR-1', 'AI-38')
    # A page that disappears while its measurement remains is not skipped either.
    env[2].data['meetstanden'].insert(0, removed)
    env[2].data['objects']['page'].pop(first['results'][0]['result']['id'])
    with pytest.raises(ValueError, match='ontbreekt'):
        report_history.load(env[0].reports['vooruitgang'], env[2].collect(), 'POR-1', 'AI-38')


def test_live_adapter_upload_is_mocked_and_refuses_existing_attachment(env, monkeypatch):
    p = prepared(env); _, assets = report_charts.build(p['state'], [])
    payload = {k: v for k, v in assets[0].items() if k != 'kind'}; payload['page_action'] = '1'
    seen = []
    class Client:
        exists = False
        def get(self, path, params):
            seen.append(('get', path, params)); return {'results': [{'id': 'old'}] if self.exists else []}
        def upload_attachment(self, key, filename, content):
            seen.append(('upload', key, filename, content[:8])); return {'results': [{'id': 'new'}]}
    client = Client(); backend = LiveBackend.__new__(LiveBackend); backend.cc = client; backend.cfg = env[1]
    monkeypatch.setattr(http, 'writer', lambda *args: client)
    result = backend.mutate({'kind': 'page.attachment', 'scope': 'AI', 'key': '102', 'payload': payload})
    assert result['attachment_id'] == 'new' and seen[-1][3] == b'\x89PNG\r\n\x1a\n'
    client.exists = True
    with pytest.raises(ValueError, match='bestaat al'):
        backend.mutate({'kind': 'page.attachment', 'scope': 'AI', 'key': '102', 'payload': payload})
    assert len([s for s in seen if s[0] == 'upload']) == 1


def test_changed_new_page_prevents_attachment_upload(env, monkeypatch):
    cat, cfg, b, tmp = env
    plan = make_plan(cat, b, cfg, {'kind': 'report', 'report': 'vooruitgang', 'target': 'POR-1', 'period': '2026-09', 'inputs': answers(), 'tracking': measurement_input()})
    receipt = approve(plan, cat, cfg, b, 'Test', 'Akkoord', plan['hash']); mutate = b.mutate
    def modified(a):
        result = mutate(a)
        if a['kind'] == 'page.create':
            b.data['objects']['page'][result['id']]['body']['storage']['value'] += '<p>Gelijktijdige menselijke wijziging</p>'
        return result
    monkeypatch.setattr(b, 'mutate', modified)
    with pytest.raises(Refused, match='niet opnieuw'): execute(plan, receipt, cat, cfg, b, tmp/'state')
    assert not b.data['objects'].get('attachments')


def test_cli_outputs_self_contained_html_without_writes(env):
    cat, cfg, b, tmp = env
    snapshot = tmp/'snapshot.json'; snapshot.write_text(json.dumps(b.collect()))
    inputs = tmp/'inputs.json'; inputs.write_text(json.dumps(answers()))
    measure = tmp/'tracking.json'; measure.write_text(json.dumps(measurement_input()))
    out = tmp/'report.json'; before = b.path.read_bytes()
    cmd = [sys.executable, str(Path(__file__).parents[1]/'aiec.py'), '--fixture', str(b.path), 'report', 'vooruitgang', '--snapshot', str(snapshot), '--target', 'POR-1', '--period', '2026-09', '--inputs', str(inputs), '--tracking', str(measure), '--out', str(out)]
    run = subprocess.run(cmd, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    assert out.exists() and out.with_suffix('.md').exists() and 'data:image/png;base64,' in out.with_suffix('.html').read_text()
    assert b.path.read_bytes() == before
    assert 'Fictieve voorbeelddata' in out.with_suffix('.html').read_text()
    assert '<source media="(max-width:600px)"' in out.with_suffix('.html').read_text()
    again = subprocess.run(cmd, capture_output=True, text=True)
    assert again.returncode == 3 and 'niets overschreven' in again.stderr


def test_history_with_old_forecast_name_still_loads(env):
    _, out = publish(env)
    record = env[2].data['meetstanden'][0]['record']
    for row in [*record['milestones'], *record['inputs']['milestones']]:row['forecast_md'] = row.pop('baseline_md')
    record['hash'] = digest({k: v for k, v in record.items() if k != 'hash'})
    loaded = report_history.load(env[0].reports['vooruitgang'], env[2].collect(), 'POR-1', 'AI-38')['records'][0]
    assert all('forecast_md' not in r and 'baseline_md' in r for r in [*loaded['milestones'], *loaded['inputs']['milestones']])


def test_live_archive_writes_one_commit_and_never_overwrites(tmp_path):
    from aiec_v2.backend import archive
    root = tmp_path/'meetstanden'; root.mkdir()
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    subprocess.run(['git', '-C', str(root), 'config', 'user.email', 'test@example.invalid'], check=True)
    subprocess.run(['git', '-C', str(root), 'config', 'user.name', 'Test'], check=True)
    cfg = {'meetstanden': {'path': str(root), 'push': False}}
    record = {'report': 'vooruitgang', 'target': 'POR-1', 'period': '2026-09', 'hash': 'x'}
    result = archive(cfg, '123', record)
    assert result['archive'] == 'vooruitgang/POR-1/2026-09.json' and result['commit']
    assert report_history.read_archive(root) == [{'page_id': '123', 'record': record}]
    with pytest.raises(FileExistsError):archive(cfg, '124', record)
    with pytest.raises(ValueError, match='geen git-repo'):report_history.read_archive(tmp_path)
