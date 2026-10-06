"""Quarterly rule review: computed from saved runs; flags dead, excepted and stubborn rules."""
from datetime import date
import pytest
from test_v2 import env
from test_rapportering import git_archive
from aiec_v2 import report_history
from aiec_v2.rule_review import compute, markdown, previous_quarter
from aiec_v2.signals import rule_review_due


def f(key, rule, sinds, **extra):
    return dict({'id': f'{key}|{rule}|m', 'key': key, 'rule': rule, 'severity': 'warning', 'sinds': sinds}, **extra)


def run(datum, findings):
    return {'datum': datum+'T08:00:00+00:00', 'findings': findings}


def by_rule(result):
    return {r['regel']: r for r in result['regels']}


def test_flags(env):
    cat, cfg, b, _ = env
    exc = {'datum': '2026-10-01T00:00:00+00:00'}
    s = {'reviews': [
        run('2026-10-05', [f('AI-1', 'geen-project', '2026-06-01'), f('AI-2', 'geen-dpia', '2026-10-05'), f('AI-3', 'geen-eigenaar', '2026-10-05')]),
        run('2026-12-20', [f('AI-1', 'geen-project', '2026-06-01'), f('AI-2', 'geen-dpia', '2026-10-05', severity='info', uitzondering=exc),
                           f('AI-9', 'verplicht-veld', '2026-12-20')]),
        run('2027-01-03', [])]}                                    # next quarter: ignored
    r = by_rule(compute(cat, s, '2026-Q4'))
    assert r['geen-project']['markering'] == ['hardnekkig'] and r['geen-project']['mediane_open_dagen'] == 202
    assert r['geen-dpia']['markering'] == ['uitzonderingsregel'] and r['geen-dpia']['uitzonderingsaandeel'] == 1
    assert r['geen-eigenaar']['opgelost'] == 1 and r['geen-eigenaar']['markering'] == []
    assert r['stilgevallen']['markering'] == ['dood']
    assert r['verplicht-veld']['catalogus'] is False and r['verplicht-veld']['markering'] == []
    text = markdown(compute(cat, s, '2026-Q4'))
    assert '2 bewaarde reviews' in text and 'verplicht-veld (ingebouwd)' in text
    with pytest.raises(ValueError, match='Geen bewaarde reviews'):compute(cat, s, '2026-Q3')
    with pytest.raises(ValueError, match='kwartaal'):compute(cat, s, '2026-10')


def test_due_once_per_quarter_with_data():
    assert previous_quarter(date(2027, 1, 4)) == '2026-Q4' and previous_quarter(date(2026, 10, 6)) == '2026-Q3'
    s = {'reviews': [run('2026-10-05', [])], 'regelreviews': []}
    assert rule_review_due(s, date(2026, 10, 6)) == {'kwartaal': '2026-Q3', 'nodig': False}   # no runs in Q3
    assert rule_review_due(s, date(2027, 1, 4))['nodig'] is True
    s['regelreviews'] = [{'kwartaal': '2026-Q4'}]
    assert rule_review_due(s, date(2027, 1, 4))['nodig'] is False


def test_archive_one_per_quarter(tmp_path):
    from aiec_v2.backend import archive_rule_review
    root, cfg = git_archive(tmp_path)
    assert archive_rule_review(cfg, {'kwartaal': '2026-Q4', 'regels': []})['archive'] == 'regelreview/2026-Q4.json'
    assert report_history.read_rule_reviews(root) == [{'kwartaal': '2026-Q4', 'regels': []}]
    with pytest.raises(FileExistsError):archive_rule_review(cfg, {'kwartaal': '2026-Q4', 'regels': []})
