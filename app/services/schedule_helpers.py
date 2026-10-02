from datetime import date, timedelta
from collections import defaultdict

DAYS_RU = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
DAYS_DISPLAY = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']


def _parse_date_range(dr: str):
    """Парсим 'ДД.ММ-ДД.ММ' в даты"""
    if not dr or dr == 'Весь период':
        return None, None
    try:
        start_str, end_str = dr[:5], dr[6:]
        year = date.today().year
        start_month, start_day = int(start_str[3:5]), int(start_str[0:2])
        end_month, end_day = int(end_str[3:5]), int(end_str[0:2])
        start = date(year, start_month, start_day)
        # Период может пересекать Новый год (например "01.09-03.01") —
        # тогда конец периода относится к следующему году
        end_year = year if (end_month, end_day) >= (start_month, start_day) else year + 1
        end = date(end_year, end_month, end_day)
        return start, end
    except Exception:
        return None, None


def get_week_dates():
    """Даты текущей недели Пн-Вс"""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    return [monday + timedelta(days=i) for i in range(7)]


def _merge_same_subject(slots: list) -> dict:
    """Несколько слотов одного предмета в одно время — объединяем различающиеся поля через /"""
    merged = dict(slots[0])
    for field in ('classroom', 'teacher', 'type'):
        vals = list(dict.fromkeys(str(s.get(field) or '') for s in slots))
        vals = [v for v in vals if v]
        merged[field] = ' / '.join(vals) if vals else None
    return merged


def _time_sort_key(time_str):
    """Ключ сортировки по времени начала занятия (устойчив к '9:00' вместо '09:00')"""
    if time_str:
        try:
            h, m = time_str.split('-', 1)[0].strip().split(':')
            return (int(h), int(m))
        except (ValueError, IndexError):
            pass
    return (99, 99)


def _group_by_time(slots: list) -> list:
    """Группирует слоты по времени; один предмет — мёрджит поля; разные предметы — группа"""
    by_time = defaultdict(list)
    for slot in slots:
        by_time[slot.get('time') or ''].append(slot)

    result = []
    for time_key in sorted(by_time.keys(), key=_time_sort_key):
        group = by_time[time_key]
        subjects = {s['subject'] for s in group}
        if len(subjects) == 1:
            result.append(_merge_same_subject(group))
        else:
            result.append({'_group': True, 'time': time_key, 'slots': group})
    return result


def build_day_view(schedule_data: list, target_date: date) -> list:
    """Занятия на конкретную дату с группировкой по времени"""
    day_name = DAYS_RU[target_date.weekday()]
    raw = []

    for item in schedule_data:
        subject = item.get('subject', '')
        for type_name, type_data in item.get('types', {}).items():
            # Support both old format (dates directly) and new format ({color, dates})
            if isinstance(type_data, dict) and 'dates' in type_data:
                type_color = type_data.get('color', 'gray')
                date_ranges = type_data['dates']
            else:
                type_color = 'gray'
                date_ranges = type_data
            for dr, slots in date_ranges.items():
                start, end = _parse_date_range(dr)
                if start and end and not (start <= target_date <= end):
                    continue
                for slot in slots:
                    if not slot or slot[0].lower() != day_name:
                        continue
                    raw.append({
                        'subject':    subject,
                        'type':       type_name,
                        'type_name':  type_name,
                        'color':      type_color,
                        'time':       slot[1] if len(slot) > 1 else None,
                        'classroom':  slot[2] if len(slot) > 2 else None,
                        'teacher':    slot[3] if len(slot) > 3 else None,
                        'date_range': dr,
                        'day':        day_name,
                    })

    raw.sort(key=lambda x: _time_sort_key(x.get('time')))
    return _group_by_time(raw)


def build_week_view(schedule_data: list) -> dict:
    """Расписание на всю неделю"""
    week_dates = get_week_dates()
    return {i: build_day_view(schedule_data, d) for i, d in enumerate(week_dates)}


def is_now(time_str: str) -> bool:
    """Идёт ли занятие прямо сейчас"""
    if not time_str or '-' not in time_str:
        return False
    from datetime import datetime
    try:
        parts = time_str.split('-')
        now = datetime.now()
        start = datetime.strptime(parts[0].strip(), '%H:%M').replace(
            year=now.year, month=now.month, day=now.day)
        end = datetime.strptime(parts[1].strip(), '%H:%M').replace(
            year=now.year, month=now.month, day=now.day)
        return start <= now <= end
    except Exception:
        return False


def get_all_subjects(schedule_data: list) -> list:
    """Список уникальных названий предметов"""
    return [item.get('subject', '') for item in schedule_data if item.get('subject')]
