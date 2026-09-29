"""Offline project exchange and browser/Python parity; no network or live writes."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import pytest
from test_v2 import env
from test_tracking import five_answers, five_basis, publish
from aiec_v2 import form_files
from aiec_v2.catalog import CORE
from aiec_v2.reports import render


def project(index=5):
    return {'format':'aiec-project','version':1,'project':{'key':'POR-1','name':'Fictief project'},
            'baseline':five_basis()['baseline'], 'periods':[{'period':f'2026-{index+1:02d}', 'inputs':five_answers(index),
            'tracking':{},'confirmed':[1,2,3,4,5],'stage':'draft'}]}


def browser_model(cat, docs, operation='evaluate'):
    script="""const fs=require('fs');eval(fs.readFileSync(process.argv[1],'utf8'));const input=JSON.parse(fs.readFileSync(0,'utf8'));const out=input.docs.map(d=>{try{return {ok:true,value:input.operation==='parse'?AIECModel.parse(d,input.contract):input.operation==='next'?AIECModel.newPeriod(d,AIECModel.nextMonth(d.periods.at(-1).period),input.contract):AIECModel.evaluate(d,input.contract)}}catch(e){return {ok:false,error:e.message}}});console.log(JSON.stringify(out));"""
    run=subprocess.run(['node','-e',script,str(CORE/'form/model.js')],input=json.dumps({'contract':form_files.contract(cat),'docs':docs,'operation':operation}),capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    return json.loads(run.stdout)


@pytest.mark.parametrize('index',[0,1,4,5,6,8])
def test_browser_matches_python_model(env,index):
    doc=project(index);py=form_files.evaluate(env[0],doc)[-1];js=browser_model(env[0],[doc])[0]
    assert js['ok'] and not js['value']['states'][-1]['errors'] and not py['questions']
    actual=js['value']['states'][-1];expected=py['state']
    for field,value in expected['metrics'].items():
        got=actual['metrics'][field]
        if field=='done' or value is None:assert got==value
        else:assert float(got)==pytest.approx(float(value),rel=1e-12)
    assert actual['rows']==expected['milestones']


def test_decimal_expected_total_exact_and_baseline_fixed(env):
    doc=project(5);row=doc['periods'][0]['inputs']['milestones'][3];row.update(actual_md='0,1',remaining_md='0,2')
    py=form_files.evaluate(env[0],doc)[0];js=browser_model(env[0],[doc])[0]['value']['states'][0]
    assert py['state']['milestones'][3]['expected_md']==js['rows'][3]['expected_md']=='0.3'
    assert py['state']['milestones'][3]['baseline_md']==js['rows'][3]['baseline_md']=='20'


def test_overrun_keeps_original_baseline_and_scope_increment(env):
    doc=project(5);doc['periods'][0]['inputs']['milestones'][3].update(actual_md=50,remaining_md=30)
    py=form_files.evaluate(env[0],doc)[0];js=browser_model(env[0],[doc])[0]['value']['states'][0]
    for row in (py['state']['milestones'][3],js['rows'][3]):
        assert (row['baseline_md'],row['expected_md'])==('20','80')
    # Milestone 4 contributes 20 * 50/80 = 12.5 of its fixed original 20, not 50.
    assert float(py['state']['metrics']['estimated_md'])==float(js['metrics']['estimated_md'])==72.5


def test_supplied_baseline_is_ignored_loudly(env):
    doc=project(5);doc['periods'][0]['inputs']['milestones'][3]['baseline_md']=35
    py=form_files.evaluate(env[0],doc)[0];js=browser_model(env[0],[doc])[0]['value']['states'][0]
    assert not py['questions'] and not js['errors']
    assert py['state']['milestones'][3]['baseline_md']==js['rows'][3]['baseline_md']=='20'
    assert any('genegeerd' in n for n in py['notes']) and any('genegeerd' in n for n in js['notes'])


def two_months(first=4,second=5):
    doc=project(first);p=doc['periods'][0];p['stage']='closed'
    doc['periods'].append({'period':f'2026-{second+1:02d}','inputs':five_answers(second),'tracking':{},'confirmed':[1,2,3,4,5],'stage':'draft'})
    return doc


def period_actuals(env,doc):
    py=[r['state']['period_actual_md'] for r in form_files.evaluate(env[0],doc)]
    js=[s['period_actual_md'] for s in browser_model(env[0],[doc])[0]['value']['states']]
    assert py==js
    return py


def test_period_actual_is_growth_since_previous_report(env):
    # First report counts the full Actual (65); the next month adds 5 md on milestone 4.
    assert period_actuals(env,two_months())==['65','5']


def test_period_actual_negative_correction_is_shown(env):
    doc=two_months();doc['periods'][1]['inputs']['milestones'][3].update(actual_md=3,remaining_md=17)
    doc['periods'][1]['tracking']={'corrections':[{'nr':4,'reason':'Boekingsfout'}]}
    assert period_actuals(env,doc)==['65','-2']
    py=form_files.evaluate(env[0],doc)[-1]
    assert any('negatief' in n for n in py['notes'])


def test_period_actual_unknown_is_not_zero(env):
    doc=two_months();doc['periods'][0]['inputs']['milestones'][4]['actual_md']=None
    assert period_actuals(env,doc)==[None,None]


@pytest.mark.parametrize('value',[None,'',0,'0','2,5','wat?',-1,True,'NaN','1e3'])
def test_unknown_zero_invalid_parity(env,value):
    doc=project();doc['periods'][0]['inputs']['milestones'][3]['remaining_md']=value
    try:
        py=form_files.evaluate(env[0],doc);valid=not any(r['questions'] for r in py)
    except ValueError:valid=False
    js=browser_model(env[0],[doc])[0]
    jsvalid=js['ok'] and not any(s['errors'] for s in js['value']['states'])
    assert bool(jsvalid)==valid


def test_new_month_preserves_prior_data_and_requires_review(env):
    doc=project();original=copy.deepcopy(doc);res=browser_model(env[0],[doc],'next')[0]
    assert res['ok'];out=res['value']
    assert doc==original and out['baseline']==doc['baseline']
    assert out['periods'][0]['inputs']==doc['periods'][0]['inputs']
    assert out['periods'][0]['stage']=='closed' and out['periods'][1]['period']=='2026-07'
    assert out['periods'][1]['confirmed']==[] and 'wijzigingen' not in out['periods'][1]['inputs']
    doc['periods'][0]['confirmed']=[]
    assert browser_model(env[0],[doc],'next')[0]['ok']  # Nagekeken is geen poort meer.


def test_invalid_draft_roundtrips_without_zeroing_or_dropping(env,tmp_path):
    doc=project();doc['periods'][0]['inputs']['milestones'][3]['actual_md']='nog navragen'
    path=tmp_path/'draft.json';path.write_text(json.dumps(doc))
    upgraded=form_files.upgrade(doc)
    assert form_files.read_document(path)==upgraded
    assert upgraded['periods'][0]['inputs']==doc['periods'][0]['inputs']
    assert browser_model(env[0],[json.dumps(doc)],'parse')[0]['value']==upgraded
    assert form_files.evaluate(env[0],doc)[0]['questions']


def test_unknown_fields_and_duplicate_json_keys_refused(env,tmp_path):
    doc=project();doc['mystery']='bewaren'
    with pytest.raises(ValueError):form_files.validate_document(doc)
    assert not browser_model(env[0],[json.dumps(doc)],'parse')[0]['ok']
    raw=json.dumps(project()).replace('"version": 1','"version": 1, "version": 1')
    path=tmp_path/'duplicate.json';path.write_text(raw)
    with pytest.raises(ValueError,match='Dubbele'):form_files.read_document(path)
    assert 'Dubbele' in browser_model(env[0],[raw],'parse')[0]['error']


@pytest.mark.parametrize('tracking_value', [{'scope_changes':{'bad':'shape'}},{'scope_changes':[{'id':'x'}]},{'corrections':None},{'legacy_ack':{'pages':[], 'reason':{},'extra':1}}])
def test_nested_damage_refused_before_opening(env,tracking_value):
    doc=project();doc['periods'][0]['tracking']=tracking_value
    with pytest.raises(ValueError):form_files.validate_document(doc)
    assert not browser_model(env[0],[json.dumps(doc)],'parse')[0]['ok']


def test_scope_and_assumption_parity(env):
    from test_tracking import addition
    doc=project(8);doc['periods'][0]['tracking']['scope_changes']=[addition()]
    doc['periods'][0]['inputs']['milestones'].append({'nr':6,'milestone':'Extra scope','status':'Bezig','actual_md':10,'remaining_md':10,'gezondheid':'op-schema'})
    doc['periods'][0]['confirmed'].append(6)
    py=form_files.evaluate(env[0],doc)[0]['state']['metrics'];js=browser_model(env[0],[doc])[0]['value']['states'][0]['metrics']
    assert float(py['estimated_md'])==js['estimated_md']==110 and py['approved_md']==js['approved_md']=='120'
    doc=project(1);doc['periods'][0]['inputs']['milestones'][0].update(status='Bezig',actual_md=2,remaining_md=None)
    doc['periods'][0]['tracking']['assume_on_plan']=True
    py=form_files.evaluate(env[0],doc)[0];js=browser_model(env[0],[doc])[0]['value']['states'][0]
    assert not py['questions'] and not js['errors'] and py['state']['metrics']['assumed_md']==js['metrics']['assumed_md']=='20'


def test_file_import_only_creates_request_and_recomputes(env):
    cat,cfg,b,_=env;doc=project();before=b.path.read_bytes()
    request=form_files.import_request(cat,b.collect(),doc)
    assert request['kind']=='report' and request['report']=='vooruitgang'
    result=render(cat,b.collect(),'vooruitgang','POR-1',request['period'],request['inputs'],cfg,tracking=request['tracking'])
    assert result['complete'] and result['measurement']['metrics']['delivered_md']=='60'
    assert b.path.read_bytes()==before
    doc['periods'][0]['confirmed']=[]
    assert form_files.import_request(cat,b.collect(),doc)['report']=='vooruitgang'  # Nagekeken is geen poort meer.


def test_unpublished_local_history_cannot_masquerade_as_official(env):
    doc=browser_model(env[0],[project(1)],'next')[0]['value'];doc['periods'][-1]['confirmed']=[1,2,3,4,5]
    with pytest.raises(ValueError,match='Dien eerst'):form_files.import_request(env[0],env[2].collect(),doc)
    # The earlier locally closed month can be submitted explicitly.
    assert form_files.import_request(env[0],env[2].collect(),doc,'2026-02')['period']=='2026-02'


def test_export_official_history_and_import_next_month(env):
    publish(env,'2026-02',five_answers(1),five_basis())
    cat,cfg,b,_=env
    doc=form_files.export_project(cat,b.collect(),'POR-1','2026-03')
    assert doc['periods'][0]['stage']=='published' and doc['periods'][0]['published_hash']
    assert doc['periods'][1]['confirmed']==[]
    doc['periods'][1]['inputs']=five_answers(2);doc['periods'][1]['confirmed']=[1,2,3,4,5]
    request=form_files.import_request(cat,b.collect(),doc)
    assert request['period']=='2026-03'
    doc['periods'][0]['inputs']['milestones'][0]['actual_md']=19
    doc['periods'][0]['inputs']['milestones'][0].pop('baseline_md',None)  # Even a recomputed tampered month must be refused.
    with pytest.raises(ValueError,match='meetstand wijkt af'):form_files.import_request(cat,b.collect(),doc)


def test_manual_old_health_and_text_not_discarded(env):
    publish(env,'2026-02',five_answers(1),five_basis());cat,cfg,b,_=env
    doc=form_files.export_project(cat,b.collect(),'POR-1','2026-03');doc['periods'][-1]['confirmed']=[1,2,3,4,5]
    doc['periods'][0]['inputs']['vlag']='escalatie'
    with pytest.raises(ValueError,match='handmatige'):form_files.import_request(cat,b.collect(),doc)


def test_newer_official_history_refuses_stale_file(env):
    cat,cfg,b,_=env;doc=project(3)
    publish(env,'2026-02',five_answers(1),five_basis())
    with pytest.raises(ValueError,match='historiek ontbreekt'):form_files.import_request(cat,b.collect(),doc)


def test_empty_export_needs_baseline(env):
    cat,cfg,b,_=env
    with pytest.raises(ValueError):form_files.export_project(cat,b.collect(),'POR-1','2026-06')
    doc=form_files.export_project(cat,b.collect(),'POR-1','2026-06',five_basis())
    assert all(r['actual_md'] is None for r in doc['periods'][0]['inputs']['milestones'])


def test_html_self_contained_deterministic_and_no_auto_feedback(env):
    html=form_files.build_html(env[0]);assert html==form_files.build_html(env[0])
    assert '/*__' not in html and '<script src=' not in html and '@import' not in html
    assert 'queuePrompt(' not in html and 'localStorage' not in html and 'fetch(' not in html
    assert 'type="file"' in html and 'Nieuwe maand' in html


def test_form_cli_roundtrip(env):
    cat,cfg,b,tmp=env;script=str(CORE/'scripts/aiec.py');snapshot=tmp/'snapshot.json';snapshot.write_text(json.dumps(b.collect()))
    file=tmp/'project.json';file.write_text(json.dumps(project()))
    out=tmp/'request.json';cmd=[sys.executable,script,'form','import','--snapshot',str(snapshot),'--file',str(file),'--out',str(out)]
    run=subprocess.run(cmd,capture_output=True,text=True);assert run.returncode==0,run.stderr
    assert json.loads(out.read_text())['kind']=='report'
    app=tmp/'app.html';run=subprocess.run([sys.executable,script,'form','build','--out',str(app)],capture_output=True,text=True)
    assert run.returncode==0 and '<!doctype html>' in app.read_text()
    assert subprocess.run([sys.executable,script,'form','build','--out',str(app)],capture_output=True).returncode==3


def test_old_forecast_field_in_project_file_is_dropped(env):
    doc=project(5);doc['periods'][0]['inputs']['milestones'][3]['forecast_md']=35
    assert all('forecast_md' not in r for p in form_files.upgrade(doc)['periods'] for r in p['inputs']['milestones'])
    py=form_files.evaluate(env[0],doc)[0];js=browser_model(env[0],[doc])[0]['value']['states'][0]
    assert not py['questions'] and not js['errors'] and py['state']['milestones'][3]['baseline_md']==js['rows'][3]['baseline_md']=='20'


def test_form_texts_reach_the_report(env):
    cat,cfg,b,_=env;doc=project()
    assert [t['id'] for t in form_files.contract(cat)['texts']]==['wijzigingen','beslissing','volgende']
    for key in ('wijzigingen','beslissing','volgende'):doc['periods'][0]['inputs'].pop(key,None)
    request=form_files.import_request(cat,b.collect(),doc)  # Empty text is completed later in the chat, not refused.
    result=render(cat,b.collect(),'vooruitgang','POR-1',request['period'],request['inputs'],cfg,tracking=request['tracking'])
    assert {'wijzigingen','beslissing','volgende'}<={q['section'] for q in result['questions']}
    doc['periods'][0]['inputs'].update(wijzigingen='Regel een.\nRegel twee.',beslissing='Nee.',volgende='Verder met milestone 5.')
    request=form_files.import_request(cat,b.collect(),doc)
    result=render(cat,b.collect(),'vooruitgang','POR-1',request['period'],request['inputs'],cfg,tracking=request['tracking'])
    assert result['complete'] and 'Regel twee.' in result['storage'] and 'Verder met milestone 5.' in result['storage']


def test_form_open_embeds_project_and_resumes_saved_draft(env):
    cat,cfg,b,tmp=env;snap=b.collect()
    doc,draft=form_files.prepare(cat,snap,'POR-1',tmp,'2026-06',five_basis())
    assert draft is None and doc['periods'][-1]['period']=='2026-06'
    html=form_files.build_html(cat,doc);assert '/*__' not in html and '"key": "POR-1"' in html
    assert '<script id="aiec-project" type="application/json">null</script>' in form_files.build_html(cat)
    saved=copy.deepcopy(doc);saved['periods'][-1]['inputs']['vlag']='groen'
    (tmp/'POR-1_2026-06.aiec.json').write_text(json.dumps(doc))
    newer=tmp/'POR-1_2026-06 (1).aiec.json';newer.write_text(json.dumps(saved))
    got,draft=form_files.prepare(cat,snap,'POR-1',tmp,'2026-06',five_basis())
    assert draft==newer and got['periods'][-1]['inputs']['vlag']=='groen'
    assert form_files.prepare(cat,snap,'POR-1',tmp,'2026-06',five_basis(),fresh=True)[1] is None
    with pytest.raises(ValueError):form_files.next_period(cat,snap,'POR-1')  # No meetstand yet: month must be given.


def test_form_open_cli(env):
    cat,cfg,b,tmp=env;script=str(CORE/'scripts/aiec.py');snapshot=tmp/'snapshot.json';snapshot.write_text(json.dumps(b.collect()))
    basis=tmp/'basis.json';basis.write_text(json.dumps(five_basis()))
    cmd=[sys.executable,script,'form','open','--snapshot',str(snapshot),'--target','POR-1','--period','2026-06','--tracking',str(basis),'--dir',str(tmp),'--no-open']
    run=subprocess.run(cmd,capture_output=True,text=True);assert run.returncode==0,run.stderr
    assert json.loads(run.stdout)['form']==str(tmp/'POR-1_2026-06.html') and 'Fictief' in (tmp/'POR-1_2026-06.html').read_text()
    assert subprocess.run(cmd,capture_output=True).returncode==0  # The form is regenerated, not refused.
