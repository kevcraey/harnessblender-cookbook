#!/usr/bin/env python3
"""Werk een ingevulde presentatie af: fonts inbakken en controleren.

    scripts/afwerken.py <presentatie.html>

Bakt de Flanders Art Sans-woff2's in als data-URI en rapporteert wat er nog
mis is: achtergebleven placeholders, niet-oplopende slide-ids, externe
resources. Idempotent: al ingebakken fonts blijven ongemoeid.
"""

import base64
import re
import sys
from pathlib import Path

FONTS = {
    "domg": {
        "__FONT_REGULAR__": "FlandersArtSans-Regular.woff2",
        "__FONT_MEDIUM__": "FlandersArtSans-Medium.woff2",
        "__FONT_BOLD__": "FlandersArtSans-Bold.woff2",
    },
    "stencil": {
        "__FONT_DISPLAY__": "BebasNeue-Regular.woff2",
        "__FONT_COND_600__": "BarlowCondensed-SemiBold.woff2",
        "__FONT_COND_800__": "BarlowCondensed-ExtraBold.woff2",
        "__FONT_INTER__": "Inter-Regular.woff2",
    },
}

ASSETS = Path(__file__).resolve().parent.parent / "assets" / "fonts"


def data_uri(pad: Path) -> str:
    b64 = base64.b64encode(pad.read_bytes()).decode("ascii")
    return f"data:font/woff2;base64,{b64}"


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2

    doel = Path(sys.argv[1])
    if not doel.is_file():
        print(f"FOUT: {doel} bestaat niet", file=sys.stderr)
        return 1

    html = doel.read_text(encoding="utf-8")
    meldingen: list[str] = []
    gewijzigd = False

    # 0. De invulinstructie van de template hoort niet in een presentatie.
    html, n = re.subn(
        r"<!--\s*PRESENTATIE-TEMPLATE.*?-->\s*", "", html, count=1, flags=re.DOTALL
    )
    gewijzigd |= bool(n)

    # 1. Fonts inbakken — alleen die van de gekozen stijl. De @font-face-regels
    #    van de andere stijl vallen weg, zodat een deck niet twee sets meesleept.
    m = re.search(r'<html[^>]*data-stijl="([a-z-]+)"', html)
    stijl = m.group(1) if m and m.group(1) in FONTS else "domg"
    ingebakken = 0
    for placeholder, bestand in FONTS[stijl].items():
        if placeholder not in html:
            continue
        bron = ASSETS / bestand
        if not bron.is_file():
            print(f"FOUT: fontbestand ontbreekt: {bron}", file=sys.stderr)
            return 1
        html = html.replace(placeholder, data_uri(bron))
        ingebakken += 1

    ongebruikt = [ph for st, fs in FONTS.items() if st != stijl for ph in fs]
    for ph in ongebruikt:
        html, n = re.subn(r"[ \t]*@font-face \{[^}]*" + ph + r"[^}]*\}\n?", "", html)
        gewijzigd |= bool(n)

    if ingebakken or gewijzigd:
        doel.write_text(html, encoding="utf-8")

    if 'src: url(data:font/woff2' not in html:
        meldingen.append("FOUT: geen enkel font ingebakken — @font-face-regels ontbreken.")

    # 2. Slides tellen en ids controleren.
    ids = re.findall(r'<section class="slide" id="(slide-\d+)"', html)
    secties = len(re.findall(r'<section class="slide"', html))
    if secties == 0:
        meldingen.append("FOUT: geen enkele <section class=\"slide\"> gevonden.")
    if len(ids) != secties:
        meldingen.append(f"FOUT: {secties - len(ids)} slide(s) zonder id=\"slide-N\".")
    verwacht = [f"slide-{i + 1}" for i in range(len(ids))]
    if ids != verwacht:
        meldingen.append(f"FOUT: slide-ids lopen niet op: {', '.join(ids)}")

    # 3. Placeholders die zijn blijven staan.
    vulin = len(re.findall(r"VUL IN", html))
    if vulin:
        meldingen.append(f"FOUT: {vulin} keer 'VUL IN' blijven staan.")
    for rest in ("__BEELD__", "__FONT_"):
        if rest in html:
            meldingen.append(f"FOUT: placeholder {rest} blijven staan.")

    # 4. Standalone: geen externe resources.
    extern = re.findall(r'(?:src|href)="(https?://[^"]+)"', html)
    for url in sorted(set(extern)):
        meldingen.append(f"FOUT: externe resource: {url}")

    # 5. Figuren: elke SVG toegankelijk, elk id uniek (markers botsen anders).
    svgs = re.findall(r"<svg\b[^>]*>", html)
    for tag in svgs:
        if 'role="img"' not in tag:
            meldingen.append("FOUT: <svg> zonder role=\"img\".")
        if 'aria-label="' not in tag and "aria-labelledby=" not in tag:
            meldingen.append("FOUT: <svg> zonder aria-label.")
    ids = re.findall(r'\sid="([^"]+)"', html)
    dubbel = sorted({i for i in ids if ids.count(i) > 1})
    for i in dubbel:
        meldingen.append(f"FOUT: id komt meermaals voor: {i}")

    # 6. Rapport.
    kb = doel.stat().st_size / 1024
    formaat = "A4 landscape" if re.search(r'<html[^>]*data-format="a4"', html) else "16:9"
    print(f"{doel}")
    print(f"  stijl:    {stijl}")
    print(f"  slides:   {secties}")
    print(f"  figuren:  {len(svgs)}")
    print(f"  formaat:  {formaat}")
    print(f"  fonts:    {ingebakken} ingebakken" if ingebakken else "  fonts:    al ingebakken")
    print(f"  grootte:  {kb:.0f} KB")

    if meldingen:
        print()
        for m in meldingen:
            print(f"  {m}")
        return 1

    print("  controle: in orde")
    return 0


if __name__ == "__main__":
    sys.exit(main())
