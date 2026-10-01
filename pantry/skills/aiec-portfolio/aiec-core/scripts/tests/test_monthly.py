"""The user's five-part monthly report, including typed milestone input."""
import copy
import json
import shutil
import xml.etree.ElementTree as ET
import pytest
import yaml
from test_v2 import env
from aiec_v2.catalog import Catalog, CORE
from aiec_v2.changes import make_plan
from aiec_v2.execution import approve, execute
from aiec_v2.reports import render
from aiec_v2 import extensions
from export_docs import documents


def answers():
    return {
        'vlag': 'afwijking-geen-actie',
        'wijzigingen': 'De functionele analyse is afgerond.\nDe datalevering komt een week later; scope en batenaanname blijven gelijk.',
        'milestones': [
            {'nr': 1, 'milestone': 'Functionele analyse', 'status': 'uitgevoerd', 'baseline_md': '3,5',
             'actual_md': 3.5, 'gezondheid': 'op-schema', 'notities': 'Gevalideerd door de projectleider.'},
            {'nr': 2, 'milestone': 'Datalevering', 'status': 'lopend', 'baseline_md': None,
             'actual_md': 0, 'remaining_md': 5, 'gezondheid': 'afwijking-geen-actie', 'notities': 'Nieuwe leverdatum afspreken.'},
        ],
        'beslissing': 'Akkoord op nieuwe leverdatum door de data-eigenaar vóór 30 september.',
        'volgende': 'Datalevering afronden en de eerste validatie uitvoeren.',
    }


def measurement_input():
    return {'baseline': {'budget_md': 8.5, 'source': 'Fictieve goedgekeurde planning',
            'milestones': [{'nr': 1, 'milestone': 'Functionele analyse', 'planned_md': 3.5},
                           {'nr': 2, 'milestone': 'Datalevering', 'planned_md': 5}],
            'plan': [{'period': '2026-08', 'scope_md': 0, 'effort_md': 0},
                     {'period': '2026-09', 'scope_md': 5, 'effort_md': 5},
                     {'period': '2026-10', 'scope_md': 8.5, 'effort_md': 8.5}]}}


def monthly(env, data=None):
    cat, cfg, b, _ = env
    return render(cat, b.collect(), 'vooruitgang', 'POR-1', '2026-09', answers() if data is None else data, cfg, tracking=measurement_input())


def test_exact_five_sections_and_shared_flags(env):
    cat, _, _, _ = env
    r = cat.reports['vooruitgang']
    assert [s['id'] for s in r['sections']] == ['vlag', 'wijzigingen', 'beslissing', 'milestones', 'volgende']
    assert r['sections'][0]['enum'] == r['sections'][3]['columns'][6]['enum'] == 'projectgezondheid'
    assert [c['label'] for c in r['enums']['projectgezondheid']] == ['Op schema', 'Afwijking - Geen actie vereist', 'Afwijking - Actie vereist']
    assert [c['handy'] for c in r['enums']['projectgezondheid']] == [{'set': 154, 'status': s} for s in (686, 687, 688)]
    assert r['sections'][3]['columns'][2]['enum'] == 'voortgang'
    assert [c['label'] for c in r['enums']['voortgang']] == ['Backlog', 'In Voorbereiding', 'Lopend', 'Uitgevoerd', 'Niet Uitgevoerd']


def test_monthly_markdown_and_storage_table(env):
    result = monthly(env)
    assert result['complete']
    assert result['title'] == '2026-09-30 - vooruitgang - POR-1 - proef-por-1'
    assert '| Nr | Milestone | Voortgang | Baseline (md) | Actual (md) | Remaining (md) | Gezondheid | Notities |' in result['markdown']
    assert '| 2 | Datalevering | Lopend | 5 | 0 | 5 | Afwijking - Geen actie vereist |' in result['markdown']
    # Voortgang and Gezondheid as Handy Status macros; the project flag too.
    assert '<td><ac:structured-macro ac:name="handy-status-macro" ac:schema-version="1"><ac:parameter ac:name="statusSetId">199</ac:parameter><ac:parameter ac:name="statusId">905</ac:parameter><ac:parameter ac:name="Status">Lopend</ac:parameter></ac:structured-macro></td>' in result['storage']
    assert '<td><ac:structured-macro ac:name="handy-status-macro" ac:schema-version="1"><ac:parameter ac:name="statusSetId">154</ac:parameter><ac:parameter ac:name="statusId">687</ac:parameter><ac:parameter ac:name="Status">Afwijking - Geen actie vereist</ac:parameter></ac:structured-macro></td>' in result['storage']
    assert result['storage'].count('<ac:structured-macro ac:name="handy-status-macro" ac:schema-version="1"><ac:parameter ac:name="statusSetId">154</ac:parameter><ac:parameter ac:name="statusId">687</ac:parameter><ac:parameter ac:name="Status">Afwijking - Geen actie vereist</ac:parameter></ac:structured-macro>') == 2  # vlag and milestone 2
    assert '<table>' in result['storage'] and '<th>Baseline (md)</th>' in result['storage']
    assert result['storage'].count('<h2>') == 5
    assert 'Invulhulp:' not in result['storage']
    ET.fromstring('<root xmlns:ac="urn:ac" xmlns:ri="urn:ri">' + result['storage'] + '</root>')


@pytest.mark.parametrize('flag', ['op-schema', 'afwijking-geen-actie', 'afwijking-actie'])
def test_every_flag_at_both_levels(env, flag):
    a = answers(); a['vlag'] = flag; a['milestones'][0]['gezondheid'] = flag
    result = monthly(env, a)
    assert result['complete']
    label = next(c['label'] for c in env[0].reports['vooruitgang']['enums']['projectgezondheid'] if c['value'] == flag)
    assert result['storage'].count(label) >= 2


def test_no_health_inferred_from_numbers(env):
    a = answers(); a['milestones'][0].update(baseline_md=1, actual_md=200, gezondheid='op-schema')
    result = monthly(env, a)
    assert 'Afwijking - Actie vereist' not in result['storage']
    assert '>Op schema</ac:parameter>' in result['storage']


def test_missing_input_is_question_not_white_or_zero(env):
    result = monthly(env, {})
    assert not result['complete']
    assert {q['section'] for q in result['questions']} == {'vlag', 'wijzigingen', 'milestones', 'beslissing', 'volgende'}
    assert '⚪ Geen status' not in result['storage']


def test_empty_milestone_row_blocks_publication(env):
    a = answers(); a['milestones'] = [{}]
    result = monthly(env, a)
    assert not result['complete']
    assert len([q for q in result['questions'] if q['section'] == 'milestones']) >= 4
    cat, cfg, b, _ = env
    plan = make_plan(cat, b, cfg, {'kind': 'report', 'report': 'vooruitgang', 'target': 'POR-1', 'period': '2026-09', 'inputs': a})
    assert plan['questions'] and not plan['actions']


@pytest.mark.parametrize('lines', [1, 6])
def test_changes_are_two_to_five_nonempty_lines(env, lines):
    a = answers(); a['wijzigingen'] = '\n'.join('Korte wijziging.' for _ in range(lines))
    result = monthly(env, a)
    assert not result['complete']
    assert any(q['section'] == 'wijzigingen' for q in result['questions'])


def test_blank_lines_do_not_count_as_changes(env):
    a = answers(); a['wijzigingen'] = 'Eerste wijziging.\n\nTweede wijziging.'
    assert monthly(env, a)['complete']


@pytest.mark.parametrize('value', [-1, True, float('nan'), float('inf'), 'NaN', '-2', '3 dagen'])
def test_invalid_effort_refused(env, value):
    a = answers(); a['milestones'][0]['actual_md'] = value
    with pytest.raises(ValueError): monthly(env, a)


@pytest.mark.parametrize('value', [0, 1.5, True])
def test_bad_milestone_numbers_refused(env, value):
    a = answers(); a['milestones'][0]['nr'] = value
    with pytest.raises(ValueError): monthly(env, a)


def test_duplicate_milestone_numbers_refused(env):
    a = answers(); a['milestones'][1]['nr'] = '1.0'
    with pytest.raises(ValueError, match='Dubbele'): monthly(env, a)


def test_unknown_column_or_choice_refused(env):
    a = answers(); a['milestones'][0]['extra'] = 'Verborgen inhoud'
    with pytest.raises(ValueError, match='onbekende kolommen'): monthly(env, a)
    a = answers(); a['vlag'] = 'ongeveer groen'
    with pytest.raises(ValueError, match='Onbekende keuze'): monthly(env, a)


def test_milestone_text_is_escaped(env):
    a = answers(); a['milestones'][0]['milestone'] = '<script>alert(1)</script> | [klik](https://example.invalid)'
    a['milestones'][0]['notities'] = 'Menselijk & <b>niet HTML</b>\nNieuwe regel'
    result = monthly(env, a)
    assert '<script>' not in result['storage'] and '&lt;script&gt;' in result['storage']
    assert '&#124;' in result['markdown'] and '\\[klik\\]' in result['markdown']
    ET.fromstring('<root xmlns:ac="urn:ac" xmlns:ri="urn:ri">' + result['storage'] + '</root>')


def test_wrong_table_type_refused(env):
    a = answers(); a['milestones'] = 'losse proza in plaats van een tabel'
    with pytest.raises(ValueError, match='lijst rijen'): monthly(env, a)


def test_definitions_validate_enum_refs_and_duplicate_columns(env, tmp_path):
    root = tmp_path/'core'; shutil.copytree(CORE, root, ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
    file = root/'catalog/reports/vooruitgang.yaml'; spec = yaml.safe_load(file.read_text())
    spec['sections'][3]['columns'][6]['enum'] = 'ontbreekt'; file.write_text(yaml.safe_dump(spec))
    with pytest.raises(ValueError, match='Onbekende keuzelijst'): Catalog(root)
    spec['sections'][3]['columns'][6]['enum'] = 'projectgezondheid'
    spec['sections'][3]['columns'][1]['id'] = 'nr'; file.write_text(yaml.safe_dump(spec))
    with pytest.raises(ValueError, match='Dubbele invoerkolom'): Catalog(root)


def test_typed_report_can_be_added_without_new_handler(env, tmp_path):
    root = tmp_path/'core'; shutil.copytree(CORE, root, ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
    cat = Catalog(root); spec = copy.deepcopy(cat.reports['vooruitgang']); spec['id'] = 'teammaandrapport'
    plan = extensions.propose(cat, 'report', yaml.safe_dump(spec, allow_unicode=True))
    receipt = extensions.approve(plan, cat, 'Kenzo', 'Testakkoord', plan['hash'])
    extensions.apply(plan, receipt, cat, tmp_path/'state')
    assert 'teammaandrapport' in Catalog(root).reports


def test_monthly_fixture_publish_includes_table_and_needs_approval(env):
    cat, cfg, b, tmp = env
    before = b.path.read_bytes()
    plan = make_plan(cat, b, cfg, {'kind': 'report', 'report': 'vooruitgang', 'target': 'POR-1', 'period': '2026-09', 'inputs': answers(), 'tracking': measurement_input()})
    assert b.path.read_bytes() == before and not plan['questions']
    receipt = approve(plan, cat, cfg, b, 'Test', 'Offline akkoord', plan['hash'])
    outcome = execute(plan, receipt, cat, cfg, b, tmp/'state')
    created = b.get('page', outcome['results'][0]['result']['id'])
    assert '<table>' in created['body']['storage']['value']
    assert '<td>3.5</td>' in created['body']['storage']['value']
    assert created['metadata']['labels']['results'][0]['name'] == 'vooruitgangsrapport'


def test_generated_template_matches_report_definition(env):
    cat, _, _, _ = env
    docs = documents(cat); text = docs['aiec-maandrapport.md']
    assert text.count('\n## ') == 5
    assert '| Label | Omschrijving |' in text
    assert '| Baseline (md) | Actual (md) | Remaining (md) | Gezondheid |' in text
    assert 'Afwijking - Geen actie vereist' in text and 'Niet Uitgevoerd' in text
    assert '[[aiec-maandrapport]]' in docs['aiec-sjablonen.md']
