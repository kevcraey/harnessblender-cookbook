"""Exceptions: internal records in the archive that soften a finding until they need review."""
import json
from datetime import date
import pytest
from test_v2 import env, approved, _gate_env
from test_rapportering import git_archive
from aiec_v2 import report_history
from aiec_v2.changes import make_plan
from aiec_v2.execution import execute, Refused
from aiec_v2.review import review


def record(**extra):
    return dict({'key': 'AI-38', 'regel': 'kwartaalrapport', 'reden': 'POR aangevraagd', 'door': 'Kenzo',
                 'datum': '2026-09-29T07:30:00+00:00', 'ingetrokken': False}, **extra)


def run(b):
    s = b.collect(); s['issues'][0]['status_raw'] = 'Run'
    return s


def rules(findings, key='AI-38'):
    return {(f['rule'], f['severity']) for f in findings if f['key'] == key}


def test_archive_keeps_exceptions_apart(tmp_path):
    from aiec_v2.backend import archive, archive_exception
    root, cfg = git_archive(tmp_path)
    archive(cfg, '123', {'report': 'vooruitgang', 'target': 'POR-1', 'period': '2026-09', 'hash': 'x'})
    result = archive_exception(cfg, record(regel='gate:opleveringsverslag'))
    assert result['archive'] == 'uitzondering/AI-38/gate-opleveringsverslag/2026-09-29T073000.json' and result['commit']
    assert len(report_history.read_archive(root)) == 1
    assert report_history.read_exceptions(root) == [record(regel='gate:opleveringsverslag')]
    with pytest.raises(FileExistsError):archive_exception(cfg, record(regel='gate:opleveringsverslag'))
    moved = root/'uitzondering'/'AI-39'/'kwartaalrapport'; moved.mkdir(parents=True)
    (moved/'2026-09-29T073000.json').write_text(json.dumps(record()))
    with pytest.raises(ValueError, match='verkeerde plaats'):report_history.read_exceptions(root)


@pytest.mark.parametrize('bad,error', [({'reden': ' '}, 'reden'), ({'regel': 'Gate:x'}, 'regel'), ({'ingetrokken': 'nee'}, 'ingetrokken')])
def test_record_is_checked(bad, error):
    with pytest.raises(ValueError, match=error):report_history.check_exception(record(**bad))


def test_review_follows_the_review_rhythm(env):
    cat, cfg, b, _ = env
    assert ('kwartaalrapport', 'warning') in rules(review(cat, run(b), date(2026, 10, 1)))
    s = run(b); s['uitzonderingen'] = [record()]
    fresh = review(cat, s, date(2026, 10, 1))
    assert ('kwartaalrapport', 'info') in rules(fresh) and ('kwartaalrapport', 'warning') not in rules(fresh)
    assert ('uitzondering-herzien', 'info') not in rules(fresh)
    assert ('uitzondering-herzien', 'info') in rules(review(cat, s, date(2026, 11, 15)))
    late = review(cat, s, date(2027, 1, 15))
    assert {('kwartaalrapport', 'warning'), ('uitzondering-te-herzien', 'warning')} <= rules(late)
    # Reviewing again is a new record; the latest counts.
    s['uitzonderingen'].append(record(datum='2027-01-10T08:00:00+00:00'))
    assert ('kwartaalrapport', 'info') in rules(review(cat, s, date(2027, 1, 15)))
    s['uitzonderingen'].append(record(datum='2027-01-11T08:00:00+00:00', ingetrokken=True))
    assert ('kwartaalrapport', 'warning') in rules(review(cat, s, date(2027, 1, 15)))
    # A gate exception has no finding of its own but follows the same rhythm.
    s['uitzonderingen'] = [record(regel='gate:opleveringsverslag')]
    assert not {r for r, _ in rules(review(cat, s, date(2026, 10, 1)))} & {'uitzondering-herzien', 'uitzondering-te-herzien', 'uitzondering-overbodig'}
    assert ('uitzondering-herzien', 'info') in rules(review(cat, s, date(2026, 11, 15)))
    assert ('uitzondering-te-herzien', 'warning') in rules(review(cat, s, date(2027, 1, 15)))


def test_exception_without_finding_is_flagged(env):
    cat, cfg, b, _ = env
    s = b.collect(); s['uitzonderingen'] = [record()]   # kwartaalrapport fires only in Run
    assert ('uitzondering-overbodig', 'info') in rules(review(cat, s, date(2026, 10, 1)))
    assert ('uitzondering-overbodig', 'info') not in rules(review(cat, run(b) | {'uitzonderingen': [record()]}, date(2026, 10, 1)))


def test_reports_hide_exceptions(env):
    from aiec_v2.reports import render
    cat, cfg, b, _ = env
    s = run(b); s['uitzonderingen'] = [record(datum='2026-01-01T08:00:00+00:00')]
    out = render(cat, s, 'stand', None, '2026-09', {}, cfg)
    assert 'Uitzondering' not in out['markdown'] and 'uitzondering' not in out['markdown']


def test_proposal_archives_each_rule_and_refuses_builtin_checks(env):
    cat, cfg, b, tmp = env
    req = {'kind': 'uitzondering', 'key': 'AI-38', 'regels': ['kwartaalrapport', 'gate:opleveringsverslag'], 'reden': 'POR aangevraagd', 'door': 'Iemand anders'}
    plan, receipt = approved(env, req)
    with pytest.raises(Refused, match='door moet gelijk'):execute(plan, receipt, cat, cfg, b, tmp/'state')
    plan, receipt = approved(env, dict(req, door='Fixturetester'))
    assert [(a['kind'], a['payload']['regel']) for a in plan['actions']] == [('uitzondering.archive', 'kwartaalrapport'), ('uitzondering.archive', 'gate:opleveringsverslag')]
    execute(plan, receipt, cat, cfg, b, tmp/'state')
    assert len(b.collect()['uitzonderingen']) == 2
    with pytest.raises(ValueError, match='ingebouwde controles'):make_plan(cat, b, cfg, dict(req, regels=['verplicht-veld']))
    with pytest.raises(ValueError, match='Onbekende key'):make_plan(cat, b, cfg, dict(req, key='AI-99'))
    with pytest.raises(ValueError, match='reden'):make_plan(cat, b, cfg, dict(req, reden=''))
    assert make_plan(cat, b, cfg, dict(req, key='POR-1', regels=['geen-eigenaar'], ingetrokken=True))['actions'] == []


def test_gate_accepts_a_reviewed_exception(env):
    cat, cfg, b, _ = env
    _gate_env(b, [('90', 'onderhoudsplan')])
    ask = lambda: make_plan(cat, b, cfg, {'kind': 'transition', 'key': 'AI-38', 'to': 'Uitvoering'})
    assert 'Gate-artefact ontbreekt voor project POR-1: opleveringsverslag' in ask()['questions']
    b.data['uitzonderingen'] = [record(key='POR-1', regel='gate:opleveringsverslag', datum=report_history_now())]
    plan = ask()
    assert not any('opleveringsverslag' in q for q in plan['questions'])
    assert any('onder uitzondering' in n for n in plan['notes'])
    b.data['uitzonderingen'] = [record(key='POR-1', regel='gate:opleveringsverslag', datum='2020-01-01T00:00:00+00:00')]
    assert 'Gate-artefact ontbreekt voor project POR-1: opleveringsverslag' in ask()['questions']


def report_history_now():
    from aiec_v2.backend import now
    return now()
