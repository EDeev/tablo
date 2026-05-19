def merge_schedules_data(schedules_data: list[list]) -> list[dict]:
    """Объединяет данные нескольких расписаний"""
    subjects: dict[str, dict] = {}

    for schedule in schedules_data:
        for item in schedule:
            name = item.get('subject', '').strip()
            if not name:
                continue
            entry = subjects.setdefault(name, {'subject': name, 'types': {}})
            for type_name, type_data in item.get('types', {}).items():
                new_fmt = isinstance(type_data, dict) and 'dates' in type_data
                color = type_data.get('color', 'gray') if new_fmt else 'gray'
                date_ranges = type_data['dates'] if new_fmt else type_data
                typ = entry['types'].setdefault(type_name, {'color': color, 'dates': {}})
                typ_dates = typ['dates']
                for dr, slots in date_ranges.items():
                    slot_list = typ_dates.setdefault(dr, [])
                    for slot in slots:
                        if slot not in slot_list:
                            slot_list.append(slot)

    return list(subjects.values())
