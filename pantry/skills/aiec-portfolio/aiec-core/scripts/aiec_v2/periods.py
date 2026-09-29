"""Reporting periods and deadlines: a report on period N is on time until halfway period N+1.

Periods are 'JJJJ-MM' (maand), 'JJJJ-Qn' (kwartaal), 'JJJJ-Hn' (halfjaar) and 'JJJJ' (jaar).
"""
from __future__ import annotations
from calendar import monthrange
from datetime import date, timedelta
import re

FREQUENCIES = {'maand': 1, 'kwartaal': 3, 'halfjaar': 6, 'jaar': 12}
# 'niet': no periodic report is expected.
CHOICES = [*FREQUENCIES, 'niet']
DEFAULT = 'kwartaal'


def parse(period):
    """'2026-Q3' -> (2026, 7, 3): year, first month, length in months."""
    m = re.fullmatch(r'(\d{4})(?:-(\d{2})|-Q([1-4])|-H([12]))?', str(period or ''))
    if not m: raise ValueError(f'Ongeldige periode: {period!r}; verwacht JJJJ-MM, JJJJ-Qn, JJJJ-Hn of JJJJ')
    year, month, quarter, half = int(m.group(1)), m.group(2), m.group(3), m.group(4)
    if month:
        if not 1 <= int(month) <= 12: raise ValueError(f'Ongeldige maand in periode {period}')
        return year, int(month), 1
    if quarter: return year, int(quarter)*3-2, 3
    if half: return year, int(half)*6-5, 6
    return year, 1, 12


def name(year, month, months):
    if months == 1: return f'{year}-{month:02d}'
    if months == 3: return f'{year}-Q{(month+2)//3}'
    if months == 6: return f'{year}-H{(month+5)//6}'
    return str(year)


def _add(year, month, months):
    index = year*12+month-1+months
    return index//12, index % 12+1


def start(period):
    year, month, _ = parse(period)
    return date(year, month, 1)


def last_day(period):
    year, month, months = parse(period)
    year, month = _add(year, month, months-1)
    return date(year, month, monthrange(year, month)[1])


def containing(day, months):
    return name(day.year, (day.month-1)//months*months+1, months)


def deadline(period):
    """Last day on time: halfway the next period (the 15th for a month, 30 June for a year)."""
    year, month, months = parse(period)
    year, month = _add(year, month, months+months//2)
    first = date(year, month, 1)
    return first+timedelta(days=14) if months % 2 else first-timedelta(days=1)


def due(today, months):
    """The latest period of this length whose deadline has passed."""
    year, month, _ = parse(containing(today, months))
    while True:
        year, month = _add(year, month, -months)
        period = name(year, month, months)
        if deadline(period) < today: return period


def check_frequency(record):
    """A reporting-frequency record: initiative key, frequency and the first period it applies to."""
    if not isinstance(record, dict) or set(record) != {'key', 'frequentie', 'vanaf', 'datum'}:
        raise ValueError('Rapporteringsfrequentie vraagt key, frequentie, vanaf en datum')
    if not re.fullmatch(r'[A-Z][A-Z0-9_]*-\d+', str(record['key'])): raise ValueError('Ongeldige initiatiefkey')
    if record['frequentie'] not in CHOICES: raise ValueError('Frequentie moet een van '+', '.join(CHOICES)+' zijn')
    if record['frequentie'] == 'niet':
        if record['vanaf'] is not None: raise ValueError("Frequentie 'niet' heeft geen vanaf")
    elif parse(record['vanaf'])[2] != FREQUENCIES[record['frequentie']]:
        raise ValueError(f"vanaf moet een {record['frequentie']}periode zijn, zoals {name(2026, 1, FREQUENCIES[record['frequentie']])}")
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?\+00:00', str(record['datum'])): raise ValueError('Ongeldige datum')
    return record
