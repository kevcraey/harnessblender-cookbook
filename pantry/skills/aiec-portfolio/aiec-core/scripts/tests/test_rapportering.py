"""Internal reporting frequency: archived per initiative, drives when a usage report is due."""
import json
import subprocess
from datetime import date
import pytest
from test_v2 import env, approved
from aiec_v2 import report_history
from aiec_v2.changes import make_plan
from aiec_v2.execution import execute, Refused
from aiec_v2.reports import render
from aiec_v2.review import review


def git_archive(tmp_path):
    root = tmp_path/'meetstanden'; root.mkdir()
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    subprocess.run(['git', '-C', str(root), 'config', 'user.email', 'test@example.invalid'], check=True)
    subprocess.run(['git', '-C', str(root), 'config', 'user.name', 'Test'], check=True)
    return root, {'meetstanden': {'path': str(root), 'push': False}}


def record(**extra):
    return dict({'key': 'AI-38', 'frequentie': 'jaar', 'vanaf': '2026', 'datum': '2026-09-29T07:30:00+00:00'}, **extra)


def test_archive_keeps_frequencies_apart_from_measurements(tmp_path):
    from aiec_v2.backend import archive, archive_frequency
    root, cfg = git_archive(tmp_path)
    measurement = {'report': 'vooruitgang', 'target': 'POR-1', 'period': '2026-09', 'hash': 'x'}
    archive(cfg, '123', measurement)
    result = archive_frequency(cfg, record())
    assert result['archive'] == 'rapportering/AI-38/2026-09-29T073000.json' and result['commit']
    assert report_history.read_archive(root) == [{'page_id': '123', 'record': measurement}]
    assert report_history.read_rapportering(root) == [record()]
    with pytest.raises(FileExistsError):archive_frequency(cfg, record())
    moved = root/'rapportering'/'AI-39'; moved.mkdir()
    (moved/'2026-09-29T073000.json').write_text(json.dumps(record()))
    with pytest.raises(ValueError, match='verkeerde plaats'):report_history.read_rapportering(root)


@pytest.mark.parametrize('bad,error', [
    ({'frequentie': 'maandelijks'}, 'Frequentie'), ({'vanaf': '2026-Q1'}, 'jaarperiode'),
    ({'frequentie': 'niet'}, 'geen vanaf'), ({'frequentie': 'kwartaal', 'vanaf': None}, 'Ongeldige periode')])
def test_frequency_record_is_checked(bad, error):
    from aiec_v2.periods import check_frequency
    with pytest.raises(ValueError, match=error):check_frequency(record(**bad))


def test_proposal_archives_once_and_review_follows_it(env):
    cat, cfg, b, tmp = env
    s = b.collect(); s['issues'][0]['status_raw'] = 'Run'
    assert any(x['rule'] == 'kwartaalrapport' for x in review(cat, s, date(2026, 9, 29)))
    plan, receipt = approved(env, {'kind': 'rapportering', 'key': 'AI-38', 'frequentie': 'jaar', 'vanaf': '2026'})
    assert [(a['kind'], a['key'], a['payload']['frequentie']) for a in plan['actions']] == [('rapportering.archive', None, 'jaar')]
    execute(plan, receipt, cat, cfg, b, tmp/'state')
    with pytest.raises(Refused, match='al uitgevoerd'):execute(plan, receipt, cat, cfg, b, tmp/'state')
    s = b.collect(); s['issues'][0]['status_raw'] = 'Run'
    # Yearly from 2026: due only after 30 June 2027.
    assert not any(x['rule'] == 'kwartaalrapport' for x in review(cat, s, date(2027, 6, 30)))
    assert any(x['rule'] == 'kwartaalrapport' for x in review(cat, s, date(2027, 7, 1)))
    # The same answer again is no change.
    assert make_plan(cat, b, cfg, {'kind': 'rapportering', 'key': 'AI-38', 'frequentie': 'jaar', 'vanaf': '2026'})['actions'] == []
    with pytest.raises(ValueError, match='Onbekend AI-initiatief'):
        make_plan(cat, b, cfg, {'kind': 'rapportering', 'key': 'AI-99', 'frequentie': 'jaar', 'vanaf': '2026'})


def test_live_guard_does_not_treat_frequency_as_jira(env, monkeypatch):
    cat, cfg, b, tmp = env
    monkeypatch.setitem(cfg['writes'], 'mode', 'production'); b.identity['mode'] = 'live'
    plan, receipt = approved(env, {'kind': 'rapportering', 'key': 'AI-38', 'frequentie': 'halfjaar', 'vanaf': '2026-H2'})
    assert execute(plan, receipt, cat, cfg, b, tmp/'state')['results'][0]['result']['archive'].startswith('rapportering/AI-38/')


def usage_page(period, day):
    return {'page_id': '300', 'title': f'{day} - gebruik - proef', 'labels': ['vooruitgangsrapport'], 'last_modified': day,
            'storage': f'<p>Periode: {period}</p><h2>Gebruik</h2>'}


def test_usage_report_counts_for_its_own_period(env):
    cat, cfg, b, _ = env
    s = b.collect(); s['issues'][0]['status_raw'] = 'Run'
    s['rapportering'] = [record(vanaf='2025')]
    missing = lambda: any(x['rule'] == 'kwartaalrapport' for x in review(cat, s, date(2026, 9, 29)))
    assert missing()
    # A fourth-quarter report is dated 31 December too, but is no yearly report.
    s['pages'][0]['children'].append(usage_page('2025-Q4', '2025-12-31'))
    assert missing()
    s['pages'][0]['children'][-1] = usage_page('2025', '2025-12-31')
    assert not missing()
    s['rapportering'].append(record(frequentie='niet', vanaf=None, datum='2026-09-30T08:00:00+00:00'))
    s['pages'][0]['children'].pop()
    assert not missing()


def test_usage_report_takes_quarter_half_or_year(env):
    cat, cfg, b, _ = env
    s = b.collect()
    assert render(cat, s, 'gebruik', 'AI-38', '2026', {}, cfg, 'proef')['title'].startswith('2026-12-31 - gebruik - ')
    assert render(cat, s, 'gebruik', 'AI-38', '2026-H1', {}, cfg, 'proef')['title'].startswith('2026-06-30 - gebruik - ')
    with pytest.raises(ValueError, match='JJJJ-Qn, JJJJ-Hn of JJJJ'):render(cat, s, 'gebruik', 'AI-38', '2026-09', {}, cfg)
