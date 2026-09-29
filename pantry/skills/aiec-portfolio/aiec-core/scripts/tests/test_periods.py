"""Periods and the halfway-next-period deadline."""
from datetime import date
import pytest
from aiec_v2 import periods as P


def test_parse_and_name_round_trip():
    for period, parsed in (('2026-09', (2026, 9, 1)), ('2026-Q3', (2026, 7, 3)), ('2026-H2', (2026, 7, 6)), ('2026', (2026, 1, 12))):
        assert P.parse(period) == parsed and P.name(*parsed) == period
    for bad in ('2026-13', '2026-Q5', '2026-H3', '26', 'Q3'):
        with pytest.raises(ValueError):P.parse(bad)


def test_last_day_and_containing():
    assert P.last_day('2028-02') == date(2028, 2, 29) and P.last_day('2026-Q3') == date(2026, 9, 30)
    assert P.last_day('2026-H1') == date(2026, 6, 30) and P.last_day('2026') == date(2026, 12, 31)
    assert [P.containing(date(2026, 8, 5), m) for m in (1, 3, 6, 12)] == ['2026-08', '2026-Q3', '2026-H2', '2026']


def test_deadline_is_halfway_next_period():
    assert P.deadline('2026-08') == date(2026, 9, 15)
    assert P.deadline('2026-12') == date(2027, 1, 15)
    assert P.deadline('2026-Q3') == date(2026, 11, 15)
    assert P.deadline('2026-Q4') == date(2027, 2, 15)
    assert P.deadline('2026-H1') == date(2026, 9, 30)
    assert P.deadline('2026-H2') == date(2027, 3, 31)
    assert P.deadline('2026') == date(2027, 6, 30)


@pytest.mark.parametrize('months,boundary,before,after', [
    (1, date(2026, 9, 15), '2026-07', '2026-08'),
    (3, date(2026, 11, 15), '2026-Q2', '2026-Q3'),
    (6, date(2026, 9, 30), '2025-H2', '2026-H1'),
    (12, date(2027, 6, 30), '2025', '2026')])
def test_due_moves_the_day_after_the_deadline(months, boundary, before, after):
    from datetime import timedelta
    assert P.due(boundary-timedelta(days=1), months) == before
    assert P.due(boundary, months) == before
    assert P.due(boundary+timedelta(days=1), months) == after
