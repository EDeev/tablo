from datetime import date

from app.services.merge import merge_schedules_data
from app.services.schedule_helpers import _parse_date_range, _time_sort_key, build_day_view, get_all_subjects
from tests.conftest import SAMPLE_DATA


def test_period_across_new_year_ends_next_year():
    start, end = _parse_date_range('01.09-03.01')
    assert start < end
    assert end.year == start.year + 1


def test_period_within_year():
    start, end = _parse_date_range('01.02-31.05')
    assert (start.month, end.month) == (2, 5)
    assert start.year == end.year


def test_whole_period_and_garbage():
    assert _parse_date_range('Весь период') == (None, None)
    assert _parse_date_range('ерунда') == (None, None)


def test_time_sort_key_handles_missing_leading_zero():
    times = ['10:40-12:10', '9:00-10:30', None, '08:00-09:30']
    assert sorted(times, key=_time_sort_key) == ['08:00-09:30', '9:00-10:30', '10:40-12:10', None]


def test_day_view_is_sorted_by_time():
    monday = date(date.today().year, 9, 1)
    while monday.weekday() != 0:
        monday = monday.replace(day=monday.day + 1)
    groups = build_day_view(SAMPLE_DATA, monday)
    times = [g['time'] if isinstance(g, dict) else g[0]['time'] for g in groups]
    assert times == ['9:00-10:30', '10:40-12:10']


def test_merge_combines_slots_without_duplicates():
    other = [{'subject': 'Базы данных', 'types': {'Практика': {'color': 'green', 'dates': {
        '01.09-31.12': [['среда', '12:20-13:50', 'АВ-210', 'Петров П.П.']]}}}}]
    merged = merge_schedules_data([SAMPLE_DATA, SAMPLE_DATA, other])
    assert len(merged) == 1
    types = merged[0]['types']
    assert set(types) == {'Лекция', 'Практика'}
    assert len(types['Лекция']['dates']['01.09-31.12']) == 2


def test_get_all_subjects():
    assert 'Базы данных' in get_all_subjects(SAMPLE_DATA)
