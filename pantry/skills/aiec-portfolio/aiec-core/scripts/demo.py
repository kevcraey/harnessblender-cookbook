#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml>=6,<7", "pillow>=11,<13"]
# ///
"""Reproducible offline demonstration. The fixture approval is not a live authorization."""
import json
from pathlib import Path
import shutil
import tempfile
from aiec_lib import config
from aiec_v2.catalog import Catalog
from aiec_v2.backend import FixtureBackend
from aiec_v2.changes import make_plan, plan_markdown
from aiec_v2.execution import approve,execute,write_json
from aiec_v2.review import review,markdown
from aiec_v2.reports import render


def main():
    cat=Catalog();root=Path(tempfile.mkdtemp(prefix='aiec-demo-'));examples=Path(__file__).parent/'examples'
    cfg=config.load(str(root/'config.toml'));fixture=root/'sandbox.json';shutil.copy2(examples/'sandbox.json',fixture)
    backend=FixtureBackend(fixture,cat,cfg);snapshot=backend.collect();write_json(root/'snapshot.json',snapshot)
    findings=review(cat,snapshot);(root/'review.md').write_text(markdown(findings))
    plan=make_plan(cat,backend,cfg,json.loads((examples/'update.json').read_text()));write_json(root/'plan.json',plan);(root/'plan.md').write_text(plan_markdown(plan))
    receipt=approve(plan,cat,cfg,backend,'Offline test','Automatisch testakkoord op uitsluitend synthetische fixturedata',plan['hash'])
    result=execute(plan,receipt,cat,cfg,backend,root/'state');write_json(root/'result.json',result)
    inputs=json.loads((examples/'retrospectieve-antwoorden.json').read_text())
    report=render(cat,backend.collect(),'retrospectieve','POR-1','2026-09',inputs,cfg)
    (root/'retrospectieve.md').write_text(report['markdown'])
    # The sandbox has no final report yet; the retrospective must ask for it rather than publish without the link.
    assert [q['section'] for q in report['questions']]==['eindrapport']
    monthly=render(cat,backend.collect(),'vooruitgang','POR-1','2026-09',
                   json.loads((examples/'vooruitgang-antwoorden.json').read_text()),cfg,
                   tracking=json.loads((examples/'vooruitgang-meetgegevens.json').read_text()))
    assert monthly['complete'] and len(monthly['assets'])==2
    (root/'vooruitgang.html').write_text(monthly['html'])
    (root/'vooruitgang.md').write_text(monthly['markdown'])
    write_json(root/'vooruitgang.json',monthly)
    assert any('Bevestigde testafdeling' in p.get('storage','') for p in backend.collect()['pages'])
    print(json.dumps({'demo':'passed','network':'not used','directory':str(root),'review_findings':len(findings),'approved_change':result['status'],'retrospective_waits_for_eindrapport':not report['complete'],'monthly_complete':monthly['complete'],'monthly_charts':len(monthly['assets'])},indent=2))

if __name__=='__main__':main()
