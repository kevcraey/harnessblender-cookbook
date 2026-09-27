#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml>=6,<7"]
# ///
"""Generate the vault's reference pages. Preview by default; back up before replacing."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
from aiec_v2.catalog import Catalog
from aiec_lib.schema import _verplicht_tekst
from aiec_v2.report_inputs import INPUT_KINDS, md_cell


def choice_legend(report, enum):
    return ['| Status | Label | Omschrijving |', '| --- | --- | --- |'] + [
        '| ' + ' | '.join(md_cell(c.get(k, '')) for k in ('symbol', 'label', 'description')) + ' |'
        for c in report['enums'][enum]]


def monthly_template(report):
    lines = header('Maandrapport — sjabloon', 'aiec-core/catalog/reports/vooruitgang.yaml')
    lines += ['Praktische uitleg: [[aiec-portfolio-rapporten]]. Cijfers invullen met live grafieken: [[aiec-maandrapport-invullen]].', '',
              '**Project:** POR-… · **Initiatief:** AI-… · **Rapportmaand:** JJJJ-MM', '',
              'Titel: `[AI-…] Vooruitgang — POR-… — JJJJ-MM`. Projectleider levert de inhoud; publicatie pas na akkoord.', '']
    for n, section in enumerate(report['sections'], 1):
        lines += [f"## {n}. {section['title']}", '']
        if section['kind'] == 'choice':
            lines += ['Kies één vlag voor het project.', ''] + choice_legend(report, section['enum']) + ['']
        elif section['kind'] == 'input_table':
            cols = section['columns']
            lines += ['| ' + ' | '.join(c['title'] for c in cols) + ' |',
                      '| ' + ' | '.join('---' for c in cols) + ' |',
                      '| ' + ' | '.join('' for c in cols) + ' |', '']
            lines += [section.get('caption', ''), '']
        else:
            lines += [section['prompt'], '', '*In te vullen.*', '']
        if section.get('help'): lines += [section['help'], '']
        if report.get('tracking') and section['id'] == report['tracking']['section']:
            lines += ['### Meetbasis en grafieken', '',
                      'Bij het eerste rapport bevestig je het oorspronkelijke budget, de scopegewichten per milestone, de maandplanning en de bron. Daarna blijven die vaste referenties staan.', '',
                      '- Baseline is de oorspronkelijke inschatting en wijzigt nooit. Een opgeleverde milestone levert in de scopegrafiek precies die Baseline op, ook bij meerwerk; Actual + Remaining is het verwachte totaal.',
                      '- Extra scope vraagt een formeel besluit, goedkeuringsmaand en vast positief gewicht. Nieuwe scope met oorspronkelijk plan nul vraagt een expliciete Remaining.',
                      '- Elke grafiek heeft een legende: **zwart Plan**, **blauw vol Opgeleverd**, **blauw gestippeld Opgeleverd incl. lopend**. Bij inzet: **Werkelijk besteed**.',
                      '- Blauwgroen is goedgekeurde scope. Lichtgroen is **±10 procentpunt** rond het oorspronkelijke plan. Scope en inzet mogen boven 100% uitkomen.',
                      '- Ontbrekende maanden blijven gaten. Zolang niets is opgeleverd en er geen volledige Actual/Remaining is, toont de grafiek automatisch een grijze aanname volgens plan.',
                      '- Bovenaan het rapport staan de vlag, de opgeleverde scope en het besteed budget, telkens als percentage van de meetbasis. De maandplanning zie je als oranje lijnen; meetbasis, scopebesluiten en vaste maandstanden staan ingeklapt als bijlage.',
                      '- Klaar betekent dat alle goedgekeurde milestones zijn opgeleverd. Een berekende schatting sluit niets af.',
                      '- De HTML-preview wordt beoordeeld vóór publicatie. Gepubliceerde maandstanden bewaren hun meetbasis en historiek; een nieuwe schatting verandert geen oude grafiekpunten.', '',
                      'Werkwijze en uitzonderingen: [[aiec-portfolio-rapporten]].', '']
    return '\n'.join(lines) + '\n'


def header(title,source):
    return ['---','tags: [type/note, expertisecentrum-ai]','generated: true',f'source: {source}','---',f'# {title}','',
            'Terug naar [[aiec-portfolio]]. Dit is een gegenereerde leeswijzer. Wijzig de bron via de onderhoudsskill,',
            'niet deze kopie. Zie [[aiec-portfolio-uitbreiden]].','']


def documents(cat):
    s=cat.schema;lines=header('Kenmerken en waarden','aiec-core/schema.yaml')
    lines+=['Kenmerken staan in één Confluence-detailsblok. Basisgegevens zijn uiterlijk bij ingang van Analyse nodig;',
            'classificatie en baten volgen uiterlijk bij Planning. Toepassingstype en AI-techniek zijn tijdens Analyse',
            'alleen aan te vullen. Onbekend blijft leeg, niet Other. EAG wordt als koppeling gecontroleerd.','',
            '## Pijlers','']
    for p in s['pijlers']:
        lines += [f"### {p['code']} — {p['naam']}",p['toelichting'],'']
        if p.get('grens'):lines += ['Grens: '+p['grens'],'']
    lines+=['## Velden','','| Veld | Waarden | Wanneer |','| --- | --- | --- |']
    for f in s['fields']:
        values=', '.join(f.get('values',[])) or ('pijlercode' if f['type']=='pijler' else 'vrije tekst')
        timing=_verplicht_tekst(f)
        if f.get('notice_when_v2'):timing+='; tijdens Analyse alleen melden'
        if f['key']=='eag_key':timing='afgebakend: koppeling controleren, uitzonderingen met Kenzo bespreken'
        if f['key']=='stopreden':timing='bij afsluiting zonder realisatie; resolution-mapping nog open'
        lines += [f"| {f['label']} (`{f['key']}`) | {values} | {timing} |"]
    for f in s['fields']:
        if f.get('hint') or f.get('value_hints'):
            lines += ['',f"### {f['label']}",f.get('hint','')]
            for value,hint in f.get('value_hints',{}).items():lines += [f'- **{value}:** {hint}']
    lines += ['','## Artefactlabels','']+[f'- `{k}` — {v}' for k,v in s['artefact_labels'].items()]
    lines += ['','De oude resolution-suggesties zijn niet bevestigd en worden niet gebruikt om automatisch af te sluiten.',
              'Fases en open proceskeuzes: [[aiec-portfolio-proces]].']
    out={'aiec-schema.md':'\n'.join(lines)+'\n'}
    lines=header('Rapportsjablonen','aiec-core/catalog/reports')
    lines+=['De projectkey hoort in projectrapporttitels. Maand: JJJJ-MM. Operationeel kwartaal: JJJJ-Qn.',
            'Feiten uit Jira blijven in Confluence live via macro’s. Inhoudelijke antwoorden komen van de maker.','']
    for r in cat.reports.values():
        lines += [f"## {r['title']} (`{r['id']}`)",f"Scope: {r['scope']} · label: `{r.get('label') or 'lokaal concept'}`.",'']
        if r.get('trigger'):lines += [r['trigger'],'']
        for enum in r.get('enums', {}):
            lines += choice_legend(r, enum) + ['']
        for section in r['sections']:
            if section['kind'] in INPUT_KINDS:
                name = section['group']+' · '+section['title'] if section.get('group') else section['title']
                lines += [f"- **{name}:** {section['prompt']}"]
                if section['kind'] == 'input_table':
                    lines += ['', '| ' + ' | '.join(c['title'] for c in section['columns']) + ' |',
                              '| ' + ' | '.join('---' for c in section['columns']) + ' |', '']
                if section.get('help'): lines += [section['help'], '']
            else:lines += [f"- **{section['title']}:** {section['kind']} uit `{section['source']}`; door code samengesteld."]
        if r.get('tracking'): lines += ['', 'Met vaste meetbasis, Remaining, onveranderlijke maandstanden en scope-/inzetgrafieken. Publicatie maakt een nieuwe pagina met twee PNG-bijlagen; eerst de HTML-preview goedkeuren.']
        if r.get('tracking_source'): lines += ['', f"Kopcijfers, grafieken zonder projectie, milestones tegenover Baseline, scopebesluiten en Vooruitgangshistoriek komen uit de laatste meetstand van `{r['tracking_source']['report']}`, vóór de sectie {r['tracking_source']['section']}. Er komt geen nieuwe meetstand bij."]
        if r.get('link_report'): lines += ['', f"Verwijst naar het gepubliceerde `{r['link_report']}` van hetzelfde project; zonder die pagina eerst dat rapport."]
        if r['id'] == 'vooruitgang': lines += ['', 'Los invulsjabloon: [[aiec-maandrapport]].']
        lines+=['']
    out['aiec-sjablonen.md']='\n'.join(lines)+'\n'
    if 'vooruitgang' in cat.reports:
        out['aiec-maandrapport.md'] = monthly_template(cat.reports['vooruitgang'])
    lines=header('Controles en mogelijkheden','aiec-core/catalog')
    lines += ['Dit zijn de losse, declaratieve regels. Daarnaast bewaakt code de basisstructuur: unieke identiteit,',
              'geldige waarden, verplichte velden, labels, bronkoppeling en voorstelveiligheid.','']
    for r in cat.rules.values():
        lines += [f"## {r['id']}",f"{r['severity']} · {r['scope']}",r['message'],r['action'],'',
                  'Voorwaarde:','```json',json.dumps(r.get('when',{}),ensure_ascii=False,indent=2),'```','']
    lines+=['## Mogelijkheden','']+[f"- **{c['id']}:** {c['description']}" for c in cat.capabilities.values()]
    out['aiec-portfolio-catalogus.md']='\n'.join(lines)+'\n'
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vault',required=True);p.add_argument('--apply',action='store_true');p.add_argument('--backup');a=p.parse_args()
    docs=documents(Catalog());root=Path(a.vault).expanduser()/'02 - Areas'
    changes={name:body for name,body in docs.items() if not (root/name).exists() or (root/name).read_text()!=body}
    print(json.dumps({'changes':list(changes),'apply':a.apply},indent=2))
    if not a.apply:return
    if not a.backup:raise ValueError('--backup vereist bij vervangen')
    backup=Path(a.backup);backup.mkdir(parents=True,exist_ok=False)
    manifest={}
    for name,body in changes.items():
        path=root/name
        if path.exists():shutil.copy2(path,backup/name);manifest[name]=hashlib.sha256(path.read_bytes()).hexdigest()
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(body)
    (backup/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':main()
