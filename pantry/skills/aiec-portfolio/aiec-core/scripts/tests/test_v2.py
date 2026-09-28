"""Offline behavior and safety tests. No live Jira/Confluence writes."""
import copy
import json
from pathlib import Path
import sys
from datetime import date
import pytest
import yaml
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from aiec_v2.catalog import Catalog, CORE, matches
from aiec_v2.backend import FixtureBackend, LiveBackend, normalize
from aiec_v2.changes import make_plan, patch_details
from aiec_v2.execution import approve, execute, Refused
from aiec_v2.reports import render
from aiec_v2.review import review, previous_period, in_period, datasets
from aiec_lib import config, confluence as conf


def sample(cat,cfg):
    vals={'ai_key':'AI-38','soort':'afgebakend','pijler':'P3','vrager':'Testvrager','afdeling':'Testafdeling','herkomst':'bottom-up','ai_act_klasse':'te bepalen','persoonsgegevens':'onbekend','eag_key':'EAG-1'}
    def issue(key,kind,status,links=None):return {'key':key,'fields':{'project':{'key':key.split('-')[0]},'issuetype':{'name':kind},'summary':'Proef '+key,'description':'Testdata','status':{'name':status},'updated':'2026-09-01T10:00:00','created':'2026-08-01T10:00:00','assignee':{'name':'testleider'},'issuelinks':links or []}}
    def link(key):return {'type':{'name':'Gerelateerd'},'outwardIssue':{'key':key}}
    page={'id':'100','type':'page','title':'[AI-38] Proef AI-38','version':{'number':1,'when':'2026-09-01T10:00:00'},'space':{'key':'AI'},'metadata':{'labels':{'results':[{'name':'ai-initiatief'}]}},'ancestors':[{'id':'99','title':'Initiatieven'}], 'body':{'storage':{'value':'<p>Menselijke notitie.</p>'+conf.render_details(cat.schema,vals)+'<p>Niet overschrijven.</p>','representation':'storage'}}}
    child={'id':'101','type':'page','title':'[AI-38] Captatierapport — 2026-09','version':{'number':1,'when':'2026-09-01T10:00:00'},'space':{'key':'AI'},'metadata':{'labels':{'results':[{'name':'captatierapport'}]}},'ancestors':[{'id':'100','title':page['title']}],'body':{'storage':{'value':'<p>Inhoudelijk goedgekeurd testverslag.</p>','representation':'storage'}}}
    # Project page (folder) under the initiative; id below 100 so created pages keep their ids.
    project={'id':'90','type':'page','title':'POR-1 - Proef POR-1','version':{'number':1,'when':'2026-09-01T10:00:00'},'space':{'key':'AI'},'metadata':{'labels':{'results':[]}},'ancestors':[{'id':'100','title':page['title']}],'body':{'storage':{'value':'<p>Projectmap</p>','representation':'storage'}}}
    # Initiation report (EAG): holds the decision for Captatie -> Analyse.
    initiatie={'id':'95','type':'page','title':'2026-09-01 - initiatie - proef','version':{'number':1,'when':'2026-09-01T10:00:00'},'space':{'key':'AI'},'metadata':{'labels':{'results':[{'name':'initiatierapport'}]}},'ancestors':[{'id':'100','title':page['title']}],'body':{'storage':{'value':'<p>Beslissing: verkennen.</p>','representation':'storage'}}}
    parent={'id':'99','type':'page','title':'Initiatieven','version':{'number':1},'space':{'key':'AI'},'ancestors':[],'metadata':{'labels':{'results':[]}},'body':{'storage':{'value':'<p>Index</p>','representation':'storage'}}}
    return {'objects':{'issue':{'AI-38':issue('AI-38','Initiative','Captatie',[link('EAG-1'),link('POR-1')]),'EAG-1':issue('EAG-1','Enterprise Requirement','Klaar voor verkenning'),'POR-1':issue('POR-1','Portfoliotaak','InUitvoering',[link('PROD-1')]),'PROD-1':issue('PROD-1','Product','build')},'page':{'90':project,'95':initiatie,'99':parent,'100':page,'101':child},'template':{'336528064':{'id':'336528064','version':{'number':33},'body':{'storage':{'value':(Path(__file__).parent/'fixtures'/'eag-sjabloon-initiatie-verkenning.xml').read_text()}}}}},'transitions':{'AI-38':[{'id':'21','name':'In Analyse','to':{'name':'In Analyse'},'fields':{}}]}}


@pytest.fixture
def env(tmp_path):
    cat=Catalog();cfg=config.load(str(tmp_path/'nonexistent.toml'));p=tmp_path/'sandbox.json';p.write_text(json.dumps(sample(cat,cfg)))
    return cat,cfg,FixtureBackend(p,cat,cfg),tmp_path


def approved(env,request):
    cat,cfg,backend,tmp=env;plan=make_plan(cat,backend,cfg,request)
    receipt=approve(plan,cat,cfg,backend,'Fixturetester','Expliciet testakkoord',plan['hash'])
    return plan,receipt


def test_catalog_and_extensions(env,tmp_path):
    import shutil
    cat,cfg,_,_=env
    assert 'retrospectieve' in cat.reports
    root=tmp_path/'extension';shutil.copytree(CORE,root,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
    new={'id':'nieuwe-regel','scope':'initiatives','severity':'info','when':{'field':'vrager','op':'empty'},'message':'Vraag vrager','action':'Bespreek dit'}
    (root/'catalog/rules/nieuwe-regel.yaml').write_text(yaml.safe_dump(new))
    extended=Catalog(root)
    assert 'nieuwe-regel' in extended.rules and extended.fingerprint!=cat.fingerprint
    new['when']['op']='run-python';(root/'catalog/rules/nieuwe-regel.yaml').write_text(yaml.safe_dump(new))
    with pytest.raises(ValueError):Catalog(root)
    new['when']={'field':'verkeerd_veld','op':'empty'}
    (root/'catalog/rules/nieuwe-regel.yaml').write_text(yaml.safe_dump(new))
    with pytest.raises(ValueError,match='Onbekend bronveld'):Catalog(root)


def test_no_inference_other(env):
    cat,cfg,b,_=env;s=b.collect();s['issues'][0]['status_raw']='In Analyse'
    found=review(cat,s,date(2026,9,25))
    assert any(f['rule']=='aan-te-vullen' and 'Toepassingstype' in f['message'] for f in found)
    assert not any(f['rule']=='verplicht-veld' and 'Toepassingstype' in f['message'] for f in found)
    s['issues'][0]['status_raw']='Prioritering en planning'
    assert any(f['rule']=='verplicht-veld' and 'Toepassingstype' in f['message'] for f in review(cat,s))


def test_unknown_properties_preserved(env):
    cat,cfg,b,_=env;p=b.get('page','100');s=p['body']['storage']['value'].replace('</tbody>','<tr><th>Eigen veld</th><td><b>Bewaren</b></td></tr></tbody>')
    changed=patch_details(cat,s,{'afdeling':'Nieuwe afdeling'})
    assert '<b>Bewaren</b>' in changed and 'Menselijke notitie.' in changed and 'Niet overschrijven.' in changed
    assert conf.parse_details(cat.schema,changed)[0]['afdeling']=='Nieuwe afdeling'
    with pytest.raises(ValueError):patch_details(cat,s,{'onbekend':'niet doen'})


def test_duplicate_details_refused(env):
    cat,_,b,_=env;s=b.get('page','100')['body']['storage']['value']
    with pytest.raises(ValueError):patch_details(cat,s+s,{'afdeling':'X'})


def test_duplicate_property_refused(env):
    cat,_,b,_=env;s=b.get('page','100')['body']['storage']['value'].replace('</tbody>','<tr><th>Afdeling</th><td>Andere</td></tr></tbody>')
    with pytest.raises(ValueError):patch_details(cat,s,{'afdeling':'X'})


def test_propose_does_not_write(env):
    cat,cfg,b,_=env;before=b.path.read_bytes();plan=make_plan(cat,b,cfg,{'kind':'details','key':'AI-38','values':{'afdeling':'Andere'}})
    assert b.path.read_bytes()==before and plan['actions']


def test_approval_and_replay(env):
    cat,cfg,b,tmp=env;plan,r=approved(env,{'kind':'details','key':'AI-38','values':{'afdeling':'Andere'}})
    assert execute(plan,r,cat,cfg,b,tmp/'state')['status']=='completed'
    assert 'Andere' in b.get('page','100')['body']['storage']['value']
    assert list((tmp/'state/fixture').glob('*.backup.json'))
    with pytest.raises(Refused):execute(plan,r,cat,cfg,b,tmp/'state')


def test_approval_bound_to_payload(env):
    cat,cfg,b,tmp=env;plan,r=approved(env,{'kind':'details','key':'AI-38','values':{'afdeling':'Andere'}})
    plan['actions'][0]['payload']['title']='Niet goedgekeurd'
    with pytest.raises(Refused):execute(plan,r,cat,cfg,b,tmp/'state')


def test_tampered_receipt(env):
    cat,cfg,b,tmp=env;plan,r=approved(env,{'kind':'details','key':'AI-38','values':{'afdeling':'Andere'}});r['plan_hash']='wrong'
    with pytest.raises(Refused):execute(plan,r,cat,cfg,b,tmp/'state')


def test_concurrent_manual_edit_refused(env):
    cat,cfg,b,tmp=env;plan,r=approved(env,{'kind':'details','key':'AI-38','values':{'afdeling':'Andere'}})
    b.data['objects']['page']['100']['body']['storage']['value']+='<p>Nieuwe menselijke input</p>'
    with pytest.raises(Refused):execute(plan,r,cat,cfg,b,tmp/'state')


BEAN='{summaryBean=com.atlassian.jira.plugin.devstatus.rest.SummaryBean@%s[summary={pullrequest=com.atlassian.jira.plugin.devstatus.rest.SummaryItemBean@%s[overall=PullRequestOverallBean{stateCount=%d}]}]}'


def test_java_identity_hash_is_not_a_change(env):
    cat,cfg,b,tmp=env;b.data['objects']['issue']['AI-38']['fields']['customfield_16110']=BEAN%('21e405f1','150a7eb7',0)
    p,r=approved(env,{'kind':'transition','key':'AI-38','to':'Analyse','decision':{'by':'Kris','date':'2026-09-25','source':'test','outcome':'Verkennen'}})
    b.data['objects']['issue']['AI-38']['fields']['customfield_16110']=BEAN%('7e9da981','194317f4',0)
    execute(p,r,cat,cfg,b,tmp/'state')
    assert b.get('issue','AI-38')['fields']['status']['name']=='In Analyse'


def test_real_change_in_java_field_refused(env):
    cat,cfg,b,tmp=env;b.data['objects']['issue']['AI-38']['fields']['customfield_16110']=BEAN%('21e405f1','150a7eb7',0)
    p,r=approved(env,{'kind':'transition','key':'AI-38','to':'Analyse','decision':{'by':'Kris','date':'2026-09-25','source':'test','outcome':'Verkennen'}})
    b.data['objects']['issue']['AI-38']['fields']['customfield_16110']=BEAN%('21e405f1','150a7eb7',1)
    with pytest.raises(Refused):execute(p,r,cat,cfg,b,tmp/'state')


def test_environment_change_refused(env):
    cat,cfg,b,tmp=env;plan,r=approved(env,{'kind':'details','key':'AI-38','values':{'afdeling':'Andere'}});cfg['writes']['mode']='production'
    with pytest.raises(Refused):execute(plan,r,cat,cfg,b,tmp/'state')


def test_failure_is_not_retried(env,monkeypatch):
    cat,cfg,b,tmp=env;plan,r=approved(env,{'kind':'details','key':'AI-38','values':{'afdeling':'Andere'}})
    def fail(a):raise TimeoutError('possibly committed')
    monkeypatch.setattr(b,'mutate',fail)
    with pytest.raises(Refused,match='niet opnieuw'):execute(plan,r,cat,cfg,b,tmp/'state')
    with pytest.raises(Refused,match='gedeeltelijk'):execute(plan,r,cat,cfg,b,tmp/'state')


def test_transition_requires_decision(env):
    # Without the initiation report there is no decision for Captatie -> Analyse.
    cat,cfg,b,_=env;del b.data['objects']['page']['95']
    p=make_plan(cat,b,cfg,{'kind':'transition','key':'AI-38','to':'Analyse'})
    assert any('sectie Beslissing van het initiatierapport' in q for q in p['questions']) and not p['actions']
    with pytest.raises(Refused):approve(p,cat,cfg,b,'X','ok',p['hash'])


def test_transition_decision_and_gate(env):
    cat,cfg,b,tmp=env;p,r=approved(env,{'kind':'transition','key':'AI-38','to':'Analyse','decision':{'by':'Kris','date':'2026-09-25','source':'https://example.test/decision','outcome':'Verkennen'}})
    assert execute(p,r,cat,cfg,b,tmp/'state')['status']=='completed'
    assert b.get('issue','AI-38')['fields']['status']['name']=='In Analyse'


def test_gate_child_changed_refuses(env):
    cat,cfg,b,tmp=env;p,r=approved(env,{'kind':'transition','key':'AI-38','to':'Analyse','decision':{'by':'Kris','date':'2026-09-25','source':'https://example.test/decision','outcome':'Verkennen'}})
    b.data['objects']['page']['101']['metadata']['labels']['results']=[]
    with pytest.raises(Refused):execute(p,r,cat,cfg,b,tmp/'state')


def test_incomplete_gate_not_guessed(env):
    cat,cfg,b,_=env;p=make_plan(cat,b,cfg,{'kind':'transition','key':'AI-38','to':'Implementatie'})
    assert any('nog niet' in q for q in p['questions']) and not p['actions']


def test_reports_questions_and_no_jira_copy(env):
    cat,cfg,b,_=env;s=b.collect();result=render(cat,s,'captatie','AI-38','2026-09',{},cfg)
    assert result['questions'] and not result['complete']
    inputs={x['id']:'Door de maker aangeleverde inhoud.' for x in cat.reports['captatie']['sections']}
    result=render(cat,s,'captatie','AI-38','2026-09',inputs,cfg,'proef')
    assert result['complete'] and 'ac:name="jira"' in result['storage'] and 'Captatie</td>' not in result['storage']


def test_retrospective_extension_works(env):
    cat,cfg,b,_=env;s=b.collect();r=render(cat,s,'retrospectieve','POR-1','2026-09',{},cfg)
    assert r['title'].endswith(' - retrospectieve - POR-1 - proef-por-1') and r['initiative']=='AI-38' and len(r['questions'])==3
    assert any('nog geen eindrapport' in q['question'] for q in r['questions'])


def test_monthly_and_quarterly_are_distinct(env):
    cat,cfg,b,_=env;s=b.collect();s['issues'][0]['status_raw']='Run'
    issues=review(cat,s,date(2026,9,25))
    assert any(x['rule']=='maandrapport' and x['key']=='POR-1' for x in issues)
    assert any(x['rule']=='kwartaalrapport' and x['key']=='AI-38' for x in issues)
    with pytest.raises(ValueError):render(cat,s,'gebruik','AI-38','2026-09',{},cfg)
    with pytest.raises(ValueError):render(cat,s,'vooruitgang','POR-1','2026-Q3',{},cfg)


def test_month_report_per_project(env):
    cat,cfg,b,_=env;s=b.collect();s['pages'][0]['children'].append({'page_id':'102','title':'[AI-38] Vooruitgang — POR-1 — 2026-08','labels':['vooruitgangsrapport'],'last_modified':'2026-09-01'})
    s['projects'].append(dict(s['projects'][0],key='POR-2'))
    f=review(cat,s,date(2026,9,25));missing=[x['key'] for x in f if x['rule']=='maandrapport']
    assert 'POR-1' not in missing and 'POR-2' in missing


def test_period_rollover():
    assert previous_period(date(2026,1,2))=='2025-12'
    assert previous_period(date(2026,1,2),True)=='2025-Q4'
    assert previous_period(date(2026,4,1),True)=='2026-Q1'


def test_duplicate_root_not_hidden(env):
    cat,cfg,b,_=env;p=copy.deepcopy(b.data['objects']['page']['100']);p['id']='200';b.data['objects']['page']['200']=p
    assert any(x['rule']=='pagina-koppeling' for x in review(cat,b.collect()))
    with pytest.raises(ValueError):make_plan(cat,b,cfg,{'kind':'details','key':'AI-38','values':{'afdeling':'X'}})


def test_no_empty_report_published(env):
    cat,cfg,b,_=env;p=make_plan(cat,b,cfg,{'kind':'report','report':'retrospectieve','target':'POR-1','period':'2026-09'})
    assert p['questions'] and not p['actions']


def test_create_report_with_label(env):
    cat,cfg,b,tmp=env;inputs={s['id']:'Afgesproken inhoud' for s in cat.reports['retrospectieve']['sections'] if s['kind']=='input'}
    _gate_env(b,[('90','opleveringsverslag')]);b.data['objects']['page']['201']['title']='2026-09-01 - eindrapport - POR-1 - proef-por-1'
    p,r=approved(env,{'kind':'report','report':'retrospectieve','target':'POR-1','period':'2026-09','inputs':inputs})
    execute(p,r,cat,cfg,b,tmp/'state');created=list(b.data['objects']['page'].values())[-1]
    # Project reports hang under the project page, not directly under the initiative.
    assert created['metadata']['labels']['results'][0]['name']=='retrospectieve' and created['ancestors'][0]['id']=='90'
    assert any(a['title'].endswith(' - retrospectieve - POR-1 - proef-por-1') for p in b.collect()['pages'] for a in p['children'])


def test_create_initiative_is_staged(env):
    cat,cfg,b,tmp=env;p,r=approved(env,{'kind':'new-initiative','title':'Nieuw voorbeeld','description':'Een testvraag.'})
    result=execute(p,r,cat,cfg,b,tmp/'state');assert result['results'][0]['result']['key']=='AI-39'
    assert not any('[AI-39]' in p['title'] for p in b.data['objects']['page'].values())


def test_title_race_refused(env):
    cat,cfg,b,tmp=env;p,r=approved(env,{'kind':'new-initiative','title':'Nieuw voorbeeld','description':'Een testvraag.'})
    b.data['objects']['issue']['AI-38']['fields']['summary']='Nieuw voorbeeld'
    with pytest.raises(Refused):execute(p,r,cat,cfg,b,tmp/'state')


def test_no_second_artifact_label(env):
    cat,cfg,b,_=env
    with pytest.raises(ValueError):make_plan(cat,b,cfg,{'kind':'label','page_id':'101','label':'analyserapport'})


def test_empty_noninferable_claim_not_cited(env):
    cat,cfg,b,_=env;s=b.collect();s['pages'][0]['details'].update(batenclaim='999 uur',aanname='')
    r=render(cat,s,'kwartaal',None,'2026-Q3',{},cfg)
    assert '999 uur' not in r['markdown']


def test_definition_approval_and_backup(env,tmp_path):
    import shutil
    from aiec_v2 import extensions
    cat,cfg,b,_=env;root=tmp_path/'core-copy';shutil.copytree(CORE,root,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
    c=Catalog(root)
    definition=yaml.safe_dump({'id':'extra-rapport','title':'Extra rapport','scope':'project','label':'verslag','sections':[{'id':'les','kind':'input','title':'Les','prompt':'Wat leren we?'}]})
    p=extensions.propose(c,'report',definition)
    assert not (root/p['path']).exists()
    r=extensions.approve(p,c,'Kenzo','fixture-akkoord',p['hash'])
    result=extensions.apply(p,r,c,tmp_path/'state')
    assert result['status']=='completed' and 'extra-rapport' in Catalog(root).reports
    assert Path(result['backup']).exists()
    with pytest.raises(Refused):extensions.apply(p,r,c,tmp_path/'state')


def test_expired_plan_refused(env):
    from aiec_v2.catalog import digest
    cat,cfg,b,tmp=env;p=make_plan(cat,b,cfg,{'kind':'details','key':'AI-38','values':{'afdeling':'X'}})
    p['expires_at']='2000-01-01T00:00:00+00:00';p['hash']=digest({k:v for k,v in p.items() if k!='hash'})
    with pytest.raises(Refused,match='verlopen'):approve(p,cat,cfg,b,'Kenzo','fixture',p['hash'])


def test_code_changed_refuses(env):
    cat,cfg,b,tmp=env;p,r=approved(env,{'kind':'details','key':'AI-38','values':{'afdeling':'X'}})
    cat.fingerprint='changed'
    with pytest.raises(Refused,match='Code of definities'):execute(p,r,cat,cfg,b,tmp/'state')


def test_wrong_environment_refuses(env):
    cat,cfg,b,tmp=env;p,r=approved(env,{'kind':'details','key':'AI-38','values':{'afdeling':'X'}})
    b.identity={'mode':'fixture','path':'another-file'}
    with pytest.raises(Refused,match='Andere omgeving'):execute(p,r,cat,cfg,b,tmp/'state')


def test_label_preserves_existing_labels(env):
    cat,cfg,b,tmp=env;b.data['objects']['page']['100']['metadata']['labels']['results']=[{'name':'menselijk-label'}]
    p,r=approved(env,{'kind':'label','page_id':'100','label':'ai-initiatief'})
    execute(p,r,cat,cfg,b,tmp/'state')
    assert {x['name'] for x in b.get('page','100')['metadata']['labels']['results']}=={'menselijk-label','ai-initiatief'}


def test_unknown_multivalue_preserved_during_other_update(env):
    cat,cfg,b,tmp=env;p=b.data['objects']['page']['100'];xml=p['body']['storage']['value']
    xml=xml.replace('<th>AI-techniek</th><td></td>','<th>AI-techniek</th><td>Generative AI, Menselijke uitbreiding</td>')
    p['body']['storage']['value']=xml
    plan,r=approved(env,{'kind':'details','key':'AI-38','values':{'afdeling':'X'}})
    execute(plan,r,cat,cfg,b,tmp/'state')
    assert 'Menselijke uitbreiding' in b.get('page','100')['body']['storage']['value']
    assert any(x['rule']=='structuur' for x in review(cat,b.collect()))


def test_invalid_report_input_cannot_inject_xml(env):
    cat,cfg,b,tmp=env;s=b.collect();inputs={x['id']:'<script>alert(1)</script>' for x in cat.reports['captatie']['sections']}
    r=render(cat,s,'captatie','AI-38','2026-09',inputs,cfg)
    assert '<script>' not in r['storage'] and '&lt;script&gt;' in r['storage']


def test_unknown_report_input_refused(env):
    cat,cfg,b,tmp=env
    with pytest.raises(ValueError,match='Onbekende'):render(cat,b.collect(),'captatie','AI-38','2026-09',{'wrong':'x'},cfg)


def test_untouched_targets_preflight_before_any_write(env):
    cat,cfg,b,tmp=env;p,r=approved(env,{'kind':'transition','key':'AI-38','to':'Analyse','decision':{'by':'Kris','date':'2026-09-25','source':'test','outcome':'Verkennen'}})
    b.data['objects']['page']['101']['body']['storage']['value']='Gewijzigd'
    with pytest.raises(Refused):execute(p,r,cat,cfg,b,tmp/'state')
    assert b.get('issue','AI-38')['fields']['status']['name']=='Captatie'
    assert not list((tmp/'state').rglob('*.jsonl'))


def test_declarative_required_field(env):
    cat,cfg,b,tmp=env
    cat.schema['fields'].append({'key':'eigenaar_data','label':'Data-eigenaar','type':'text','required_when_v2':{'field':'phase','op':'eq','value':'Captatie'}})
    assert any(x['message']=='Data-eigenaar ontbreekt.' for x in review(cat,b.collect()))


def test_schema_document_uses_current_generator(env,capsys):
    import aiec
    assert aiec.main(['schema-doc'])==0
    output=capsys.readouterr().out
    assert 'aiec-portfolio-uitbreiden' in output
    assert 'aiec.py schema --out' not in output
    assert 'oude resolution-suggesties zijn niet bevestigd' in output


def test_generic_rule_operators():
    assert matches({'all':[{'field':'a','op':'contains','value':'x'},{'not':{'field':'b','op':'filled'}}]}, {'a':['x']})
    assert not matches({'field':'a','op':'gt','value':5},{'a':None})


def _decision(slug='agent-built-verder',**extra):
    inputs={'overgang':'Uitvoering','besluit':'Verder met de gebouwde oplossing.','bevoegde':'Testbeslisser','datum':'2026-01-20','bron':'Geen formele bron.','gevolg':'Lage prioriteit.'}
    return dict({'kind':'report','report':'beslissing','target':'AI-38','period':'2026-01','slug':slug,'inputs':inputs},**extra)


def _with_decisions_page(b):
    page={'id':'102','type':'page','title':'[AI-38] Beslissingen','version':{'number':1,'when':'2026-09-01T10:00:00'},'space':{'key':'AI'},'metadata':{'labels':{'results':[]}},'ancestors':[{'id':'100','title':'[AI-38] Proef AI-38'}],'body':{'storage':{'value':'<p>Lijst</p>','representation':'storage'}}}
    b.data['objects']['page']['102']=page


def test_decision_title_and_default_parent(env):
    cat,cfg,b,tmp=env;_with_decisions_page(b)
    p,r=approved(env,_decision());execute(p,r,cat,cfg,b,tmp/'state')
    created=list(b.data['objects']['page'].values())[-1]
    assert created['title']=='2026-01-20 - beslissing - agent-built-verder'
    assert created['ancestors'][0]['id']=='102'


def test_decision_without_decisions_page_refused(env):
    cat,cfg,b,_=env
    with pytest.raises(ValueError,match='Beslissingen'):make_plan(cat,b,cfg,_decision())


def test_decision_parent_override(env):
    cat,cfg,b,_=env;p=make_plan(cat,b,cfg,_decision(parent_id='101'))
    assert p['actions'][0]['payload']['ancestors']==[{'id':'101'}]


def test_decision_slug_required_and_validated(env):
    cat,cfg,b,_=env;_with_decisions_page(b)
    p=make_plan(cat,b,cfg,_decision(slug=None))
    assert not p['actions'] and any('Slug' in q for q in p['questions'])
    for bad in ('Hoofdletters','met spatie','x--y','-x','a/b'):
        with pytest.raises(ValueError,match='Slug'):make_plan(cat,b,cfg,_decision(slug=bad))
    bad=_decision();bad['inputs']['datum']='20 januari'
    with pytest.raises(ValueError,match='JJJJ-MM-DD'):make_plan(cat,b,cfg,bad)


def test_title_template_placeholders_restricted(tmp_path):
    import shutil
    root=tmp_path/'core';shutil.copytree(CORE,root,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
    f=root/'catalog/reports/beslissing.yaml';d=json.loads(f.read_text())
    # beslissing is an initiative report: {project} is refused there.
    for tpl in ('{datum.__class__}','{onbekend}','{datum!r}','{datum} - beslissing - {project} - {slug}'):
        d['page_title']=tpl;f.write_text(json.dumps(d))
        with pytest.raises(ValueError):Catalog(root)


def test_live_create_sets_labels_separately(monkeypatch):
    # Confluence Server ignores metadata.labels on create: the label needs its own POST.
    calls=[]
    class Client:
        def request(self,method,path,body=None):
            calls.append((method,path,body));return {'id':'555'} if path=='/rest/api/content' else [{'name':'decisions'}]
    from aiec_v2 import backend as be
    monkeypatch.setattr(be.http,'writer',lambda cfg,target,scope,apply:Client())
    live=object.__new__(LiveBackend);live.cfg={}
    labels=[{'prefix':'global','name':'decisions'}]
    result=live.mutate({'kind':'page.create','scope':'AI','payload':{'type':'page','title':'T','metadata':{'labels':labels}}})
    assert calls[1]==('POST','/rest/api/content/555/label',labels) and result['id']=='555' and len(calls)==2
    calls.clear();live.mutate({'kind':'page.create','scope':'AI','payload':{'type':'page','title':'T'}})
    assert len(calls)==1


def test_people_sets_assignee_and_verantwoordelijke(env):
    cat,cfg,b,tmp=env;b.data['users']={'kenzo':{'active':True},'maja':{'active':True}}
    p,r=approved(env,{'kind':'people','key':'AI-38','assignee':'kenzo','verantwoordelijke':'maja'})
    assert [a['kind'] for a in p['actions']]==['issue.update']
    assert p['actions'][0]['payload']=={'fields':{'assignee':{'name':'kenzo'},'customfield_10614':{'name':'maja'}}}
    execute(p,r,cat,cfg,b,tmp/'state')
    f=b.get('issue','AI-38')['fields'];assert f['assignee']=={'name':'kenzo'} and f['customfield_10614']=={'name':'maja'}
    again=make_plan(cat,b,cfg,{'kind':'people','key':'AI-38','assignee':'kenzo'})
    assert not again['actions']


def test_people_refuses_unknown_user_and_empty_request(env):
    cat,cfg,b,_=env;b.data['users']={'oud':{'active':False}}
    for req in ({'kind':'people','key':'AI-38','assignee':'niemand'},{'kind':'people','key':'AI-38','verantwoordelijke':'oud'},{'kind':'people','key':'AI-38'}):
        with pytest.raises(ValueError):make_plan(cat,b,cfg,req)


def test_live_user_active_false_only_on_404():
    from aiec_lib import http as h
    live=object.__new__(LiveBackend)
    class J:
        def __init__(self,err):self.err=err
        def get(self,path,params=None):raise self.err
    live.jc=J(h.HttpError(404,'/u'));assert live.user_active('x') is False
    for err in (h.AuthError(401,'/u'),h.HttpError(500,'/u')):
        live.jc=J(err)
        with pytest.raises(h.HttpError):live.user_active('x')


def _split_page(cat):
    vals={'ai_key':'AI-38','soort':'afgebakend','pijler':'P3','eag_key':'EAG-1'}
    return conf.render_details(cat.schema,vals)


def test_details_split_in_visible_and_hidden_block(env):
    cat,_,_,_=env;s=_split_page(cat)
    blocks=conf.find_details_blocks(cat.schema,s)
    assert [conf.details_hidden(s[a:b]) for a,b in blocks]==[False,True]
    hidden={f['label'] for f in cat.schema['fields'] if f.get('verborgen')}
    assert hidden and all(l in s[blocks[1][0]:blocks[1][1]] for l in hidden)
    vals,raw,problems=conf.parse_details(cat.schema,s)
    assert not problems and vals['ai_key']=='AI-38' and vals['eag_key']=='EAG-1' and vals['soort']=='afgebakend'


def test_patch_details_edits_the_block_that_holds_the_field(env):
    cat,_,_,_=env;s=_split_page(cat)
    changed=patch_details(cat,s,{'afdeling':'A','stopreden':'geen data'})
    blocks=conf.find_details_blocks(cat.schema,changed)
    assert len(blocks)==2 and 'geen data' in changed[blocks[1][0]:blocks[1][1]] and '>A<' in changed[blocks[0][0]:blocks[0][1]]
    assert conf.parse_details(cat.schema,changed)[0]['stopreden']=='geen data'


def test_patch_details_adds_hidden_block_for_hidden_field(env):
    # Oude pagina met één blok zonder Stopreden-rij: het veld komt in een nieuw verborgen blok.
    cat,_,_,_=env;s='<p>x</p>'+conf.details_macro(cat.schema,'<tr><th>Soort</th><td>afgebakend</td></tr>')+'<p>y</p>'
    changed=patch_details(cat,s,{'stopreden':'geen data'})
    blocks=conf.find_details_blocks(cat.schema,changed)
    assert [conf.details_hidden(changed[a:b]) for a,b in blocks]==[False,True]
    assert changed.startswith('<p>x</p>') and changed.endswith('<p>y</p>')


def test_two_visible_blocks_still_refused(env):
    cat,_,_,_=env;one=conf.details_macro(cat.schema,'<tr><th>Soort</th><td>afgebakend</td></tr>')
    with pytest.raises(ValueError):patch_details(cat,one+one,{'afdeling':'X'})


def test_label_in_both_blocks_is_a_problem(env):
    cat,_,_,_=env;row='<tr><th>Soort</th><td>afgebakend</td></tr>'
    s=conf.details_macro(cat.schema,row)+conf.details_macro(cat.schema,row,hidden=True)
    assert conf.parse_details(cat.schema,s)[2]
    with pytest.raises(ValueError):patch_details(cat,s,{'soort':'doorlopend'})


def test_artifact_title_defaults_to_today_with_approved_slug(env):
    cat,cfg,b,_=env;s=b.collect();inputs={x['id']:'Inhoud.' for x in cat.reports['captatie']['sections']}
    r=render(cat,s,'captatie','AI-38','2026-09',inputs,cfg)
    assert any('Slug' in q['question'] for q in r['questions'])
    r=render(cat,s,'captatie','AI-38','2026-09',inputs,cfg,'proef-ai-38')
    assert r['title']==f"{date.today().isoformat()} - captatie - proef-ai-38"
    with pytest.raises(ValueError):render(cat,s,'captatie','AI-38','2026-09',dict(inputs),cfg,'Proef AI')


def test_periodic_title_uses_last_day_of_period(env):
    from aiec_v2.reports import title_date
    assert title_date({'cadence':'monthly'},'2026-02')=='2026-02-28'
    assert title_date({'cadence':'quarterly'},'2026-Q3')=='2026-09-30'
    assert title_date({'cadence':'quarterly'},'2026-Q1')=='2026-03-31'
    assert title_date({},'2026-09',date(2026,1,20))=='2026-01-20'


def test_project_report_title_has_key_and_slug(env):
    from aiec_v2.reports import slugify
    cat,cfg,b,_=env;s=b.collect()
    assert render(cat,s,'retrospectieve','POR-1','2026-09',{},cfg)['title'].endswith(' - retrospectieve - POR-1 - proef-por-1')
    assert render(cat,s,'retrospectieve','POR-1','2026-09',{},cfg,'eigen-keuze')['title'].endswith(' - POR-1 - eigen-keuze')
    with pytest.raises(ValueError):render(cat,s,'retrospectieve','POR-1','2026-09',{},cfg,'Geen Slug')
    assert slugify('Advies - Gezond uit eigen grond')=='advies-gezond-uit-eigen-grond' and slugify('Één café')=='een-cafe'


def test_in_period_reads_old_and_new_titles():
    assert in_period('[AI-38] Vooruitgang — POR-1 — 2026-08','2026-08','vooruitgang')
    assert in_period('2026-08-31 - vooruitgang - POR-1 - proef','2026-08','vooruitgang')
    assert not in_period('2026-08-31 - vooruitgang - por-1','2026-07','vooruitgang')
    assert in_period('2026-09-30 - gebruik - proef','2026-Q3','gebruik') and not in_period('2026-09-30 - gebruik - proef','2026-Q2','gebruik')
    # Een maandrapport van 30 september is geen kwartaalrapport, al valt het in Q3.
    assert not in_period('2026-09-30 - vooruitgang - por-1','2026-Q3','gebruik')
    assert not in_period('2026-09-30 - gebruik - proef','2026-09','vooruitgang')
    assert not in_period('Iets zonder datum','2026-08','vooruitgang')


def test_previous_report_found_with_new_title(env):
    cat,cfg,b,_=env;s=b.collect();today=date(2026,9,15)
    s['pages'][0]['children'].append({'page_id':'102','title':'2026-08-31 - vooruitgang - por-1','labels':['vooruitgangsrapport'],'last_modified':'2026-09-01'})
    from aiec_v2.review import datasets
    d=datasets(cat,s,today)
    assert next(p for p in d['projects'] if p['key']=='POR-1')['previous_report']


def _gate_env(b,labels_by_parent):
    """Artefactpagina's met label onder initiatief (100) of projectpagina's; zet AI-38 in implementatie."""
    pages=b.data['objects']['page'];n=200
    for parent,label in labels_by_parent:
        n+=1;pages[str(n)]={'id':str(n),'type':'page','title':f'2026-09-01 - x - {n}','version':{'number':1,'when':'2026-09-01T10:00:00'},'space':{'key':'AI'},
            'metadata':{'labels':{'results':[{'name':label}]}},'ancestors':[{'id':parent}],'body':{'storage':{'value':'<p>x</p>','representation':'storage'}}}
    b.data['objects']['issue']['AI-38']['fields']['status']={'name':'implementatie'}
    b.data['transitions']['AI-38']=[{'id':'31','name':'Run','to':{'name':'Run'},'fields':{}}]


def test_project_page_is_folder_for_project_artifacts(env):
    cat,cfg,b,_=env;_gate_env(b,[('90','vooruitgangsrapport')])
    s=b.collect();page=next(p for p in s['pages'] if p['ai_key']=='AI-38')
    folder=next(c for c in page['children'] if c['page_id']=='90')
    assert folder['project_page']=='POR-1'
    art=next(c for c in page['children'] if c.get('project')=='POR-1')
    assert art['parent_id']=='90'
    d=datasets(cat,s);por=next(p for p in d['projects'] if p['key']=='POR-1')
    assert por['page_id']=='90' and por['artifact_labels']==['vooruitgangsrapport']
    findings=review(cat,s)
    assert not any(f['rule']=='artefactlabel' and 'POR-1 - Proef' in f['message'] for f in findings)


def test_project_page_request_creates_folder_once(env):
    cat,cfg,b,tmp=env;cfg['atlassian']['jira_server_id']='abc'
    with pytest.raises(ValueError):make_plan(cat,b,cfg,{'kind':'project-page','key':'POR-1'})   # bestaat al (90)
    del b.data['objects']['page']['90']
    p,r=approved(env,{'kind':'project-page','key':'POR-1'})
    execute(p,r,cat,cfg,b,tmp/'state');created=list(b.data['objects']['page'].values())[-1]
    assert created['title']=='POR-1 - Proef POR-1' and created['ancestors'][0]['id']=='100'
    assert 'key = POR-1 OR issue in linkedIssues(POR-1)' in created['body']['storage']['value']
    assert 'ac:name="contentbylabel"' in created['body']['storage']['value']
    with pytest.raises(ValueError):make_plan(cat,b,cfg,{'kind':'project-page','key':'POR-99'})


def test_project_report_needs_project_page(env):
    from test_monthly import answers, measurement_input
    cat,cfg,b,_=env;del b.data['objects']['page']['90']
    with pytest.raises(ValueError,match='Projectpagina'):make_plan(cat,b,cfg,{'kind':'report','report':'vooruitgang','target':'POR-1','period':'2026-09','inputs':answers(),'tracking':measurement_input()})


def test_gate_single_project_eindrapport_counts_for_initiative(env):
    cat,cfg,b,_=env;_gate_env(b,[('90','opleveringsverslag'),('100','onderhoudsplan')])
    p=make_plan(cat,b,cfg,{'kind':'transition','key':'AI-38','to':'Uitvoering','decision':{'by':'X','date':'2026-09-25','source':'s','outcome':'o'}})
    assert not any('opleveringsverslag' in q for q in p['questions'])


def test_gate_every_project_needs_eindrapport_and_initiative_its_own(env):
    cat,cfg,b,_=env
    b.data['objects']['issue']['POR-2']=copy.deepcopy(b.data['objects']['issue']['POR-1']);b.data['objects']['issue']['POR-2']['key']='POR-2'
    b.data['objects']['issue']['AI-38']['fields']['issuelinks'].append({'type':{'name':'Gerelateerd'},'outwardIssue':{'key':'POR-2'}})
    _gate_env(b,[('90','opleveringsverslag'),('90','onderhoudsplan')])
    q=make_plan(cat,b,cfg,{'kind':'transition','key':'AI-38','to':'Uitvoering','decision':{'by':'X','date':'2026-09-25','source':'s','outcome':'o'}})['questions']
    assert 'Gate-artefact ontbreekt voor project POR-2: opleveringsverslag' in q
    # The maintenance plan belongs to each project; the initiative needs no copy of its own.
    assert 'Gate-artefact ontbreekt voor project POR-2: onderhoudsplan' in q and 'Gate-artefact ontbreekt: onderhoudsplan' not in q
    assert 'Gate-artefact ontbreekt: opleveringsverslag' in q     # twee projecten: initiatief heeft een eigen verslag nodig
    assert not any('POR-1' in x for x in q)


def _decision_page(b,page_id,parent,overgang=None):
    """Decision page (label decisions), optionally with its properties block."""
    props='' if overgang is None else conf.details_macro(Catalog().schema,f'<tr><th>Overgang naar</th><td>{overgang}</td></tr>',details_id='aiec-beslissing')
    b.data['objects']['page'][page_id]={'id':page_id,'type':'page','title':f'2026-09-01 - beslissing - {page_id}','version':{'number':1,'when':'2026-09-01T10:00:00'},'space':{'key':'AI'},
        'metadata':{'labels':{'results':[{'name':'decisions'}]}},'ancestors':[{'id':parent}],'body':{'storage':{'value':props+'<p>Besluit</p>','representation':'storage'}}}


def _phase(b,status):b.data['objects']['issue']['AI-38']['fields']['status']={'name':status}


def test_decision_found_as_grandchild_with_overgang(env):
    # AI-7 shape: the decision hangs under another artefact, not directly under the initiative.
    cat,cfg,b,_=env;_decision_page(b,'300','101','Uitvoering')
    page=next(p for p in b.collect()['pages'] if p['ai_key']=='AI-38')
    assert page['decisions']==[{'page_id':'300','title':'2026-09-01 - beslissing - 300','overgang':'Uitvoering'}]
    row=next(i for i in datasets(cat,b.collect())['initiatives'] if i['key']=='AI-38')
    assert row['decision_transitions']==['Uitvoering']


def test_review_flags_every_passed_transition_without_decision(env):
    cat,cfg,b,_=env;_phase(b,'Run')
    missing=[f['message'] for f in review(cat,b.collect()) if f['rule']=='beslissing-ontbreekt']
    assert any('Planning' in m and 'verkenningsrapport' in m for m in missing)
    assert any('Implementatie' in m for m in missing) and any('Uitvoering' in m for m in missing)
    assert not any('overgang naar Analyse' in m for m in missing)      # initiatierapport 95 staat er
    _decision_page(b,'300','100','Implementatie');_decision_page(b,'301','100','Uitvoering')
    missing=[f['message'] for f in review(cat,b.collect()) if f['rule']=='beslissing-ontbreekt']
    assert not any('Implementatie' in m or 'Uitvoering' in m for m in missing)


def test_closed_early_needs_only_closing_decision(env):
    cat,cfg,b,_=env;_phase(b,'Closed')
    missing=[f['message'] for f in review(cat,b.collect()) if f['rule']=='beslissing-ontbreekt']
    assert len(missing)==1 and 'Afgesloten' in missing[0]


def test_legacy_decision_without_overgang_is_info(env):
    cat,cfg,b,_=env;_decision_page(b,'300','100')
    f=[x for x in review(cat,b.collect()) if x['rule']=='beslissing-zonder-overgang']
    assert len(f)==1 and f[0]['severity']=='info'


def test_decision_report_writes_properties_and_counts(env):
    cat,cfg,b,tmp=env;_with_decisions_page(b)
    p,r=approved(env,_decision());execute(p,r,cat,cfg,b,tmp/'state')
    created=list(b.data['objects']['page'].values())[-1]
    props=conf.parse_properties(cat.schema,created['body']['storage']['value'],'aiec-beslissing')
    assert props=={'Overgang naar':'Uitvoering','Besluit':'Verder met de gebouwde oplossing.','Beslist door':'Testbeslisser','Datum':'2026-01-20','Bron':'Geen formele bron.','Gevolg':'Lage prioriteit.'}
    body=created['body']['storage']['value']
    assert '<h2>' not in body and 'Periode:' not in body and body.count('Testbeslisser')==1   # geen dubbele weergave
    assert 'ac:name="jira"' not in body                                                          # geen ticketverwijzing
    row=next(i for i in datasets(cat,b.collect())['initiatives'] if i['key']=='AI-38')
    assert 'Uitvoering' in row['decision_transitions']
    # The Beslissingen overview on the initiative page reads exactly these labels.
    assert '<ac:parameter ac:name="headings">Overgang naar, Datum, Beslist door</ac:parameter>' in conf.render_page(cat.schema,{'ai_key':'AI-38'},'x',cfg)


def test_transition_to_uitvoering_needs_decision_page(env):
    cat,cfg,b,_=env;_gate_env(b,[('90','opleveringsverslag'),('100','onderhoudsplan')])
    req={'kind':'transition','key':'AI-38','to':'Uitvoering'}
    assert any("'Overgang naar' Uitvoering" in q for q in make_plan(cat,b,cfg,req)['questions'])
    _decision_page(b,'300','100','Uitvoering')
    assert not any('Beslissing' in q for q in make_plan(cat,b,cfg,req)['questions'])


def test_decision_in_must_be_known_label(tmp_path):
    import shutil
    root=tmp_path/'core';shutil.copytree(CORE,root,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
    f=root/'catalog/process.yaml';d=json.loads(f.read_text())
    d['gates']['Planning']['decision_in']='analyserapport-x';f.write_text(json.dumps(d))
    with pytest.raises(ValueError):Catalog(root)
    d['gates']['Planning']['decision_in']='onderhoudsplan';f.write_text(json.dumps(d))   # label bestaat, maar is geen gate-artefact
    with pytest.raises(ValueError):Catalog(root)


def test_eag_template_in_sync_and_drift_detected(env):
    cat,cfg,b,_=env
    assert not [f for f in review(cat,b.collect()) if f['rule'].startswith('sjabloon')]
    tpl=b.data['objects']['template']['336528064']['body']['storage']
    tpl['value']=tpl['value'].replace('Wie wordt hier aan kant DIGI op ingezet?','Wie zet DIGI in?')
    drift=[f for f in review(cat,b.collect()) if f['rule']=='sjabloon-uit-sync']
    assert len(drift)==1 and 'initiatie' in drift[0]['message']      # enkel het deel Initiatie is gewijzigd
    del b.data['objects']['template']['336528064']
    assert len([f for f in review(cat,b.collect()) if f['rule']=='sjabloon-niet-gelezen'])==2


def test_template_questions_follow_the_part():
    from aiec_v2.templates import questions
    s=(Path(__file__).parent/'fixtures'/'eag-sjabloon-initiatie-verkenning.xml').read_text()
    assert questions(s,'Initiatie')[-1]=='Wie wordt hier aan kant DIGI op ingezet?'
    assert len(questions(s,'Verkenning'))==19 and questions(s,'Bestaat niet')==[]


def _analysis_page(b,dpia,dpo):
    rows=f'<tr><th>DPIA</th><td>{dpia}</td></tr><tr><th>DPO</th><td>{dpo}</td></tr>'
    b.data['objects']['page']['310']={'id':'310','type':'page','title':'2026-02-01 - analyse - proef','version':{'number':1,'when':'2026-09-01T10:00:00'},'space':{'key':'AI'},
        'metadata':{'labels':{'results':[{'name':'analyserapport'}]}},'ancestors':[{'id':'100'}],
        'body':{'storage':{'value':conf.details_macro(Catalog().schema,rows,details_id='aiec-analyse')+'<p>Analyse</p>','representation':'storage'}}}


def test_dpia_and_dpo_judged_in_analysis_report(env):
    cat,cfg,b,_=env;_phase(b,'Run')
    b.data['objects']['page']['100']['body']['storage']['value']=b.data['objects']['page']['100']['body']['storage']['value'].replace('onbekend','ja')
    rules=lambda:{f['rule'] for f in review(cat,b.collect()) if f['key']=='AI-38'}
    assert {'geen-dpia','geen-dpo-oordeel'}<=rules()
    _analysis_page(b,'Vereist','Gecontacteerd')
    assert 'geen-dpia' in rules() and 'geen-dpo-oordeel' not in rules()       # DPIA vereist maar nog niet aanwezig
    _analysis_page(b,'Niet van toepassing','Niet van toepassing')
    assert not {'geen-dpia','geen-dpo-oordeel'}&rules()


def test_analysis_report_properties_hold_dpia_and_dpo(env):
    cat,cfg,b,_=env;s=b.collect()
    inputs={x['id']:'Inhoud.' for x in cat.reports['analyse']['sections'] if x['kind']=='input'}
    inputs.update(dpia='niet-van-toepassing',dpo='gecontacteerd')
    r=render(cat,s,'analyse','AI-38','2026-09',inputs,cfg,'proef')
    assert conf.parse_properties(cat.schema,r['storage'],'aiec-analyse')=={'DPIA':'Niet van toepassing','DPO':'Gecontacteerd'}
    assert r['storage'].count('Niet van toepassing')==1
