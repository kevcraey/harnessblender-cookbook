"""External templates we mirror but do not own (EAG Initiatie & Verkenning in DigiAg).

A report definition records a fingerprint of the questions in its part of the template. Review compares it
with the live template, so a change on the EAG side becomes visible instead of silently drifting.
"""
from __future__ import annotations
import re
from aiec_lib import confluence as conf
from .catalog import digest

H1_RE = re.compile(r'<h1\b[^>]*>(.*?)</h1>', re.S)


def questions(storage, part):
    """First-column texts of every table row in the part under <h1>part</h1>, in order."""
    heads = list(H1_RE.finditer(storage or ''))
    for n, h in enumerate(heads):
        if conf._cell_text(h.group(1)) == part:
            end = heads[n+1].start() if n+1 < len(heads) else len(storage)
            block = storage[h.end():end]
            return [conf._cell_text(m.group(2) or '') for r in conf.ROW_RE.finditer(block)
                    for m in [next(conf.CELL_RE.finditer(r.group(1)), None)] if m]
    return []


def fingerprint(storage, part):
    found = questions(storage, part)
    return digest(found)[:16] if found else None
