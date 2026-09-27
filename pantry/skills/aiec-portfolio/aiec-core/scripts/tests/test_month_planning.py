"""Monthly input, Actual/Remaining coupling, immutable per-report future planning."""
import copy
import json
import subprocess
import pytest
from test_v2 import env
from test_form import project, browser_model
from test_tracking import five_answers, five_basis, publish
from aiec_v2 import form_files, monthly_planning, report_charts
from aiec_v2.catalog import CORE
from aiec_v2.reports import render


def js_call(method,args):
    code="const fs=require('fs');eval(fs.readFileSync(process.argv[1],'utf8'));const x=JSON.parse(fs.readFileSync(0,'utf8'));try{console.log(JSON.stringify({value:AIECModel[x.method](...x.args)}))}catch(e){console.log(JSON.stringify({error:e.message}))}"
    p=subprocess.run(['node','-e',code,str(CORE/'form/model.js')],input=json.dumps({'method':method,'args':args}),capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    return json.loads(p.stdout)


@pytest.mark.parametrize('a,r,new,enabled,done,expected,mode',[
    ('20','30','30',True,False,'20','coupled'),
    ('20','30','10',True,False,'40','coupled'),
    ('1,5','2,5','2',True,False,'2','coupled'),
    ('20','30','30',False,False,'30','off'),
    (None,'30','10',True,False,'30','unknown'),
    ('10',None,'20',True,False,None,'unknown'),
    ('20','0','25',True,True,'0','delivered'),
    ('10','10','30',True,False,'0','capped'),
])
def test_actual_remaining_coupling(a,r,new,enabled,done,expected,mode):
    result=js_call('coupledRemaining',[a,r,new,enabled,done])['value']
    assert result['remaining']==expected and result['mode']==mode


def test_typing_after_overshoot_uses_original_anchor():
    assert js_call('coupledRemaining',['10','10','100'])['value']['remaining']=='0'
    assert js_call('coupledRemaining',['10','10','17'])['value']['remaining']=='3'
    assert js_call('coupledRemaining',['10','10','abc']).get('error')


@pytest.mark.parametrize('budget,weights,amounts',[(10,[4,6],[0,4,6]),(100,[20,30],[10,20,70]),('0.3',['0.1','0.2'],['0.1','0.2'])])
def test_one_monthly_input_builds_cumulative_and_scope(budget,weights,amounts):
    milestones=[{'nr':i+1,'milestone':f'M{i+1}','planned_md':w} for i,w in enumerate(weights)]
    rows=[{'period':f'2026-{i+1:02d}','effort_md':v} for i,v in enumerate(amounts)]
    py=monthly_planning.baseline_from_months(budget,milestones,rows,'Oorspronkelijke afspraak')
    js=js_call('baselineFromMonths',[budget,milestones,rows,'Oorspronkelijke afspraak'])['value']
    assert py==js
    assert py['plan'][-1]['effort_md']==str(budget)
    if budget==10:assert [p['effort_md'] for p in py['plan']]==['0','4','10']


def test_baseline_months_not_reinterpreted_on_upgrade(env):
    old=project();before=copy.deepcopy(old)
    old['baseline']['plan'][1]['scope_md']=19
    before=copy.deepcopy(old)
    upgraded=form_files.upgrade(old)
    assert old==before and upgraded['baseline']==old['baseline']
    assert upgraded['version']==2 and upgraded['settings']['auto_remaining'] is True
    assert upgraded['periods'][0]['inputs']==old['periods'][0]['inputs']
    assert upgraded['periods'][0]['planning']==[{'period':'2026-07','effort_md':'5'},{'period':'2026-08','effort_md':'5'},{'period':'2026-09','effort_md':'20'}]
    assert browser_model(env[0],[json.dumps(old)],'parse')[0]['value']==upgraded


def test_upgrade_does_not_fabricate_historical_replans(env):
    old=project(4);first=copy.deepcopy(old['periods'][0]);first['stage']='closed'
    second=copy.deepcopy(first);second.update(period='2026-06',stage='draft');old['periods']=[first,second]
    new=form_files.upgrade(old)
    assert new['periods'][0]['planning'] is None
    assert new['periods'][0]['inputs']==old['periods'][0]['inputs']
    assert new['periods'][1]['planning'] is not None


def test_gaps_in_old_cumulative_planning_not_spread_or_zeroed():
    base=five_basis()['baseline'];base['plan'].pop(6)
    rows=monthly_planning.from_baseline(base,'2026-06')
    assert rows[0]=={'period':'2026-08','effort_md':None}
    assert js_call('baselineMonths',[base,'2026-06'])['value']==rows


@pytest.mark.parametrize('rows',[
    [{'period':'2026-06','effort_md':3}],
    [{'period':'2026-07','effort_md':-1}],
    [{'period':'2026-07','effort_md':None}],
    [{'period':'2026-07','effort_md':3},{'period':'2026-07','effort_md':4}],
])
def test_bad_future_plan_cannot_close_but_can_be_saved(env,rows):
    doc=form_files.upgrade(project());doc['periods'][0]['planning']=rows
    assert form_files.validate_document(doc)
    py=form_files.evaluate(env[0],doc)[0];js=browser_model(env[0],[doc])[0]['value']['states'][0]
    assert py['questions'] and js['errors']
    assert py['state']['metrics']['delivered_md']==js['metrics']['delivered_md']=='60'


def test_v2_settings_preserved_unknown_fields_refused(env):
    doc=form_files.upgrade(project());doc['settings']['auto_remaining']=False
    assert form_files.upgrade(doc)==doc
    assert browser_model(env[0],[json.dumps(doc)],'parse')[0]['value']==doc
    doc['settings']['unknown']=1
    with pytest.raises(ValueError):form_files.validate_document(doc)


def test_future_plan_totals_parity_and_mismatch_is_visible_not_auto_distributed(env):
    doc=form_files.upgrade(project());doc['periods'][0]['planning']=[{'period':'2026-07','effort_md':20},{'period':'2026-10','effort_md':30}]
    before=copy.deepcopy(doc['periods'][0]['inputs'])
    py=form_files.evaluate(env[0],doc)[0];js=browser_model(env[0],[doc])[0]['value']['states'][0]
    assert not py['questions'] and not js['errors']
    assert py['state']['planning_summary']==js['planning_summary']=={'planned_remaining_md':'50','remaining_md':'30','end_total_md':'120','difference_md':'20'}
    assert py['notes'] and js['notes'] and doc['periods'][0]['inputs']==before


def test_new_month_keeps_old_plan_and_only_carries_future(env):
    doc=form_files.upgrade(project());old=copy.deepcopy(doc['periods'][0]['planning'])
    new=browser_model(env[0],[doc],'next')[0]['value']
    assert new['periods'][0]['planning']==old
    assert new['periods'][1]['planning']==[r for r in old if r['period']>'2026-07']
    assert new['periods'][1]['confirmed']==[]


def test_plan_appears_in_report_and_is_not_actual_or_rebaseline(env):
    cat,cfg,b,_=env
    # 20 md planned against 30 md Remaining: scope is not reached, so the axis keeps every planned month.
    plan=[{'period':'2026-07','effort_md':5},{'period':'2026-08','effort_md':5},{'period':'2026-10','effort_md':10}]
    tracked=dict(five_basis(),planning=plan)
    result=render(cat,b.collect(),'vooruitgang','POR-1','2026-06',five_answers(5),cfg,tracking=tracked)
    assert result['complete'] and result['measurement']['planning']==[{'period':r['period'],'effort_md':str(r['effort_md'])} for r in plan]
    data=result['chart_data'];positions={m:i for i,m in enumerate(data['periods'])}
    assert data['forward'][positions['2026-06']]==70
    assert data['forward'][positions['2026-07']]==75
    assert data['forward'][positions['2026-08']]==80
    assert data['forward'][positions['2026-09']] is None
    assert data['forward'][positions['2026-10']]==90
    assert data['actual'][positions['2026-10']] is None and data['plan_effort'][positions['2026-10']] is None
    assert data['y_max_scope']>=140 and data['y_max_effort']>=140 and 'Inzet deze maand (md)' not in result['storage']  # The planning shows in the charts only.
    assert result['measurement']['baseline']['budget_md']=='100'


def test_changed_historical_plan_refused_on_import(env):
    cat,cfg,b,_=env
    tracked=dict(five_basis(),planning=[{'period':'2026-06','effort_md':5},{'period':'2026-07','effort_md':5},{'period':'2026-08','effort_md':5},{'period':'2026-09','effort_md':20}])
    publish(env,'2026-05',five_answers(4),tracked)
    doc=form_files.export_project(cat,b.collect(),'POR-1','2026-06')
    doc['periods'][-1]['inputs']=five_answers(5);doc['periods'][-1]['confirmed']=[1,2,3,4,5]
    assert form_files.import_request(cat,b.collect(),doc)['tracking']['planning']
    doc['periods'][0]['planning'][0]['effort_md']='6'
    with pytest.raises(ValueError,match='meetstand wijkt af'):form_files.import_request(cat,b.collect(),doc)


def test_effort_overrun_does_not_stretch_scope_scale(env):
    cat,cfg,b,_=env
    answers=five_answers(5);answers['milestones'][3].update(actual_md=240,remaining_md=10)
    result=render(cat,b.collect(),'vooruitgang','POR-1','2026-06',answers,cfg,tracking=five_basis())
    data=result['chart_data']
    assert data['y_max_effort']>=300 and data['y_max_scope']==140


@pytest.mark.parametrize('plan,expected_open,reaches',[
    # Five-milestone example in 2026-06: 70 delivered incl. running, 30 md Remaining, approved 100.
    ([{'period':'2026-07','effort_md':30}],['0'],'2026-07'),                                   # more effort: done earlier
    ([{'period':'2026-07','effort_md':5},{'period':'2026-08','effort_md':5},{'period':'2026-09','effort_md':20}],['25','20','0'],'2026-09'),
    ([{'period':'2026-07','effort_md':5},{'period':'2026-08','effort_md':5}],['25','20'],None),  # too little: stays below 100%
])
def test_planned_effort_shifts_expected_scope(env,plan,expected_open,reaches):
    doc=form_files.upgrade(project());doc['periods'][0]['planning']=plan
    state=form_files.evaluate(env[0],doc)[0]['state']
    py=monthly_planning.cumulative(state['planning'],state)
    js=js_call('forwardProjection',[browser_model(env[0],[doc])[0]['value']['states'][0]['planning'],browser_model(env[0],[doc])[0]['value']['states'][0]])['value']
    assert [r['open_md'] for r in py]==[r['open_md'] for r in js]==expected_open
    for a,b in zip(py,js):assert a['scope_md']==pytest.approx(b['scope_md'])
    full=[r['period'] for r in py if r['scope_md']==pytest.approx(100)]
    assert (full[0] if full else None)==reaches
    assert all(r['scope_md']<100 for r in py) if reaches is None else True


@pytest.mark.parametrize('plan,shown',[
    ([{'period':'2026-07','effort_md':5},{'period':'2026-08','effort_md':5},{'period':'2026-09','effort_md':20}],False),  # follows the original plan
    ([{'period':'2026-07','effort_md':30}],True),
])
def test_plan_lines_only_shown_when_deviating(env,plan,shown):
    cat,cfg,b,_=env
    result=render(cat,b.collect(),'vooruitgang','POR-1','2026-06',five_answers(5),cfg,tracking=dict(five_basis(),planning=plan))
    data=result['chart_data']
    for key in ('forward','expected_scope'):
        assert any(v is not None for v in data[key])==shown


@pytest.mark.parametrize('plan,last',[
    ([{'period':'2026-07','effort_md':30},{'period':'2026-08','effort_md':5}],'2026-07'),  # extra effort: axis stops at delivery
    ([{'period':'2026-07','effort_md':5},{'period':'2026-08','effort_md':5},{'period':'2026-09','effort_md':20}],'2026-09'),
    ([{'period':'2026-07','effort_md':5},{'period':'2026-08','effort_md':5},{'period':'2026-11','effort_md':5}],'2026-11'),  # never reached: all months stay
])
def test_axis_stops_when_everything_is_delivered(env,plan,last):
    cat,cfg,b,_=env
    result=render(cat,b.collect(),'vooruitgang','POR-1','2026-06',five_answers(5),cfg,tracking=dict(five_basis(),planning=plan))
    assert result['chart_data']['periods'][-1]==last


def test_axis_stops_at_report_month_when_done(env):
    cat,cfg,b,_=env
    result=render(cat,b.collect(),'vooruitgang','POR-1','2026-06',five_answers(9),cfg,tracking=dict(five_basis(),planning=[]))
    assert result['measurement']['metrics']['done'] and result['chart_data']['periods'][-1]=='2026-06'


def factor_doc(factor, plan):
    doc=form_files.upgrade(project());p=doc['periods'][0]
    p['inputs']['milestones'][3].update(actual_md=10,remaining_md=20)  # expected 30 against Baseline 20
    p['planning']=plan
    if factor is not None:p['tracking']['future_factor']=factor
    return doc


@pytest.mark.parametrize('factor,used,projected',[(None,1,'40'),('ratio',1.125,'42.5'),('2','2','60')])
def test_ratio_and_backlog_factor_only_change_projection(env,factor,used,projected):
    plan=[{'period':'2026-07','effort_md':20},{'period':'2026-08','effort_md':20},{'period':'2026-09','effort_md':20}]
    doc=factor_doc(factor,plan)
    py=form_files.evaluate(env[0],doc)[0];js=browser_model(env[0],[doc])[0]['value']['states'][0]
    assert not py['questions'] and not js['errors']
    # Delivered + running: (20+20+20+30)/(4*20); backlog is excluded from the ratio.
    assert py['state']['effort_ratio']==js['effort_ratio']==1.125
    assert py['state']['future_factor']==js['future_factor']==float(used)
    # Remaining itself is untouched; only the projection scales the backlog.
    assert py['state']['milestones'][4]['remaining_md']==js['rows'][4]['remaining_md']=='20'
    from aiec_v2.tracking import text
    assert text(monthly_planning.projected_remaining(py['state']))==js_call('projectedRemaining',[js])['value']==projected
    pyf=monthly_planning.cumulative(py['state']['planning'],py['state']);jsf=js_call('forwardProjection',[js['planning'],js])['value']
    assert [r['open_md'] for r in pyf]==[r['open_md'] for r in jsf]
    for a,b in zip(pyf,jsf):assert a['scope_md']==pytest.approx(b['scope_md'])


def test_factor_choice_carries_to_next_month(env):
    doc=factor_doc('ratio',[{'period':'2026-07','effort_md':40}]);doc['periods'][0]['confirmed']=[1,2,3,4,5]
    nxt=browser_model(env[0],[doc],'next')[0]
    assert nxt['ok'] and nxt['value']['periods'][-1]['tracking']=={'future_factor':'ratio'}


def test_report_shows_ratio_and_factor(env):
    cat,cfg,b,_=env
    answers=five_answers(5);answers['milestones'][3].update(actual_md=10,remaining_md=20)
    tracked=dict(five_basis(),planning=[{'period':'2026-07','effort_md':30}],future_factor='2')
    result=render(cat,b.collect(),'vooruitgang','POR-1','2026-06',answers,cfg,tracking=tracked)
    assert 1.12 <= result['measurement']['effort_ratio'] <= 1.13
    assert 'Backlog is in de projectie geschaald met factor 2,00.' in result['storage']
