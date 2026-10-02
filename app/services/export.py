import csv
import io
import json

from flask import current_app, render_template

DAYS_ORDER = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']


def _flatten_schedule(schedule_data: list) -> list[dict]:
    """Разворачивает вложенную JSON-структуру расписания в плоский список строк."""
    rows = []
    for item in schedule_data:
        subject = item.get('subject', '')
        for type_name, type_data in item.get('types', {}).items():
            if isinstance(type_data, dict) and 'dates' in type_data:
                date_ranges = type_data['dates']
            else:
                date_ranges = type_data
            for period, slots in date_ranges.items():
                for slot in slots:
                    rows.append({
                        'subject':   subject,
                        'type':      type_name,
                        'period':    period,
                        'day':       slot[0] if len(slot) > 0 else '',
                        'time':      slot[1] if len(slot) > 1 else '',
                        'classroom': slot[2] if len(slot) > 2 else '',
                        'teacher':   slot[3] if len(slot) > 3 else '',
                    })
    rows.sort(key=lambda r: (
        r['subject'],
        r['type'],
        r['period'],
        DAYS_ORDER.index(r['day'].lower()) if r['day'].lower() in DAYS_ORDER else 99,
        r['time'],
    ))
    return rows


def export_json(schedule) -> bytes:
    return json.dumps(schedule.data, ensure_ascii=False, indent=2).encode('utf-8')


def export_csv(schedule) -> bytes:
    rows = _flatten_schedule(schedule.data or [])
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=['subject', 'type', 'period', 'day', 'time', 'classroom', 'teacher'],
        extrasaction='ignore',
    )
    writer.writerow({
        'subject': 'Предмет',
        'type': 'Тип занятия',
        'period': 'Период',
        'day': 'День',
        'time': 'Время',
        'classroom': 'Кабинет',
        'teacher': 'Преподаватель',
    })
    writer.writerows(rows)
    return buf.getvalue().encode('utf-8-sig')  # BOM для корректного открытия в Excel


def _build_week_view_active(schedule_data: list) -> dict:
    """Слоты по дням — только из периодов, которые ещё не закончились на сегодня."""
    from datetime import date
    from app.services.schedule_helpers import _parse_date_range, _time_sort_key
    today = date.today()
    days = {i: [] for i in range(7)}
    for item in schedule_data:
        subject = item.get('subject', '')
        for type_name, type_data in item.get('types', {}).items():
            if isinstance(type_data, dict) and 'dates' in type_data:
                color = type_data.get('color', 'gray')
                date_ranges = type_data['dates']
            else:
                color = 'gray'
                date_ranges = type_data
            for period, slots in date_ranges.items():
                start, end = _parse_date_range(period)
                # Пропускаем период только если у него есть явная дата конца и она уже прошла
                if end is not None and end < today:
                    continue
                for slot in slots:
                    day_name = (slot[0] if slot else '').lower()
                    if day_name not in DAYS_ORDER:
                        continue
                    day_idx = DAYS_ORDER.index(day_name)
                    days[day_idx].append({
                        'subject':   subject,
                        'type':      type_name,
                        'color':     color,
                        'time':      slot[1] if len(slot) > 1 else '',
                        'classroom': slot[2] if len(slot) > 2 else '',
                        'teacher':   slot[3] if len(slot) > 3 else '',
                        'period':    period,
                    })
    # Убираем дубликаты одного слота (предмет+день+время из нескольких периодов)
    for i in days:
        seen = set()
        unique = []
        for s in days[i]:
            key = (s['subject'], s['type'], s['time'])
            if key not in seen:
                seen.add(key)
                unique.append(s)
        days[i] = sorted(unique, key=lambda s: _time_sort_key(s.get('time')))
    return days


def _render_html(schedule, fmt: str) -> str:
    rows = _flatten_schedule(schedule.data or [])
    return render_template(
        'export/schedule_print.html',
        schedule=schedule,
        rows=rows,
        fmt=fmt,
    )


def _render_html_png(schedule) -> str:
    week_view = _build_week_view_active(schedule.data or [])
    days_display = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    return render_template(
        'export/schedule_png.html',
        schedule=schedule,
        week_view=week_view,
        days_display=days_display,
    )


def export_pdf(schedule) -> bytes:
    from playwright.sync_api import sync_playwright
    html = _render_html(schedule, 'pdf')
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until='load')
        pdf_bytes = page.pdf(format='A4', landscape=True, print_background=True)
        browser.close()
    return pdf_bytes


def export_png(schedule) -> bytes:
    from playwright.sync_api import sync_playwright
    html = _render_html_png(schedule)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1200, 'height': 800})
        page.set_content(html, wait_until='load')
        # Подгоняем высоту под реальный контент
        height = page.evaluate('document.documentElement.scrollHeight')
        page.set_viewport_size({'width': 1200, 'height': height})
        png_bytes = page.screenshot(full_page=True)
        browser.close()
    return png_bytes
