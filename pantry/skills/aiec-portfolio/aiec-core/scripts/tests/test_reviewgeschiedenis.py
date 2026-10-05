"""Review history: saved runs give each finding a 'sinds' and each review a trend."""
import json
from datetime import date
import pytest
from test_v2 import env
from test_rapportering import git_archive
from aiec_v2 import report_history
from aiec_v2.review import review, trend, markdown


def run(datum, findings):
    return {'datum': datum+'T08:00:00+00:00', 'findings': findings}


def ids(findings):
    return [{'id': f['id']} for f in findings]


def test_archive_saves_runs_apart(tmp_path):
    from aiec_v2.backend import archive_review
    root, cfg = git_archive(tmp_path)
    result = archive_review(cfg, [{'id': 'AI-1|x|y'}])
    assert result['archive'].startswith('review/') and result['commit']
    assert report_history.read_archive(root) == [] and report_history.read_exceptions(root) == []
    assert [r['findings'] for r in report_history.read_reviews(root)] == [[{'id': 'AI-1|x|y'}]]
    (root/'review'/'2026-01-01T000000.json').write_text(json.dumps(run('2026-02-01', [])))
    with pytest.raises(ValueError, match='verkeerde plaats'):report_history.read_reviews(root)


def test_since_follows_the_unbroken_streak(env):
    cat, cfg, b, _ = env
    s = b.collect(); today = date(2026, 10, 10)
    now = review(cat, s, today)
    assert now and all(f['sinds'] == '2026-10-10' for f in now)        # no history: today
    first = now[0]
    s['reviews'] = [run('2026-09-01', ids(now)), run('2026-09-15', []), run('2026-10-01', ids(now)), run('2026-10-05', ids(now))]
    again = {f['id']: f for f in review(cat, s, today)}
    assert again[first['id']]['sinds'] == '2026-10-01'                  # gap on 09-15 restarts the streak


def test_excepted_finding_keeps_its_history(env):
    cat, cfg, b, _ = env
    s = b.collect(); s['issues'][0]['status_raw'] = 'Run'
    before = [f for f in review(cat, s, date(2026, 10, 1)) if f['rule'] == 'kwartaalrapport']
    s['reviews'] = [run('2026-09-20', ids(before))]
    s['uitzonderingen'] = [{'key': 'AI-38', 'regel': 'kwartaalrapport', 'reden': 'r', 'door': 'K', 'datum': '2026-09-29T07:30:00+00:00', 'ingetrokken': False}]
    after = [f for f in review(cat, s, date(2026, 10, 1)) if f['rule'] == 'kwartaalrapport']
    assert after[0]['severity'] == 'info' and after[0]['id'] == before[0]['id'] and after[0]['sinds'] == '2026-09-20'


def test_trend_and_markdown(env):
    cat, cfg, b, _ = env
    s = b.collect(); now = review(cat, s, date(2026, 10, 10))
    assert trend(s, now) is None
    s['reviews'] = [run('2026-10-01', ids(now[1:]) + [{'id': 'AI-9|weg|opgelost'}])]
    t = trend(s, now)
    assert t == {'vorige': '2026-10-01', 'nieuw': [now[0]['id']], 'opgelost': ['AI-9|weg|opgelost']}
    text = markdown(now, t)
    assert '1 nieuw, 1 opgelost' in text and 'Sinds: 2026-10-10' in text


def test_cli_refuses_to_save_a_fixture_run(env, tmp_path):
    import aiec
    cat, cfg, b, _ = env
    snap = tmp_path/'snap.json'; snap.write_text(json.dumps(b.collect()))
    assert aiec.main(['review', '--snapshot', str(snap), '--bewaar']) != 0
