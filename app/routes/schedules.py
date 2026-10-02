import copy
from flask import (Blueprint, current_app, render_template, redirect, url_for,
                   flash, request, jsonify)
from flask_login import login_required, current_user
from app import db, csrf
from app.models.schedule import Schedule, SubjectConfig
from app.access import can_edit as _can_edit, can_view as _can_view
from app.services.ai_scan import scan_image
from app.services.merge import merge_schedules_data
from app.services.schedule_helpers import (
    build_week_view, get_week_dates, DAYS_DISPLAY, DAYS_RU
)
from datetime import date

bp = Blueprint('schedules', __name__)


@bp.route('/')
@login_required
def profile():
    schedules = current_user.schedules.order_by(Schedule.created_at.desc()).all()
    return render_template('profile/index.html', schedules=schedules)


@bp.route('/schedules/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        extra_prompt = request.form.get('extra_prompt', '').strip()
        file = request.files.get('image')

        if not name:
            flash('Введите название расписания', 'danger')
            return render_template('schedule/upload.html')
        if not file or file.filename == '':
            flash('Выберите картинку', 'danger')
            return render_template('schedule/upload.html')

        ext = '.' + file.filename.rsplit('.', 1)[-1].lower()
        allowed = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
        if ext not in allowed:
            flash('Неподдерживаемый формат изображения', 'danger')
            return render_template('schedule/upload.html')

        try:
            image_bytes = file.read()
            data = scan_image(image_bytes, ext, extra_prompt)
        except Exception:
            current_app.logger.exception('Ошибка распознавания расписания')
            flash('Не удалось распознать расписание. Попробуйте другое фото или повторите позже.', 'danger')
            return render_template('schedule/upload.html')

        schedule = Schedule(user_id=current_user.id, name=name, data=data)
        db.session.add(schedule)
        db.session.commit()
        flash('Расписание успешно создано', 'success')
        return redirect(url_for('schedules.view', schedule_id=schedule.id))

    return render_template('schedule/upload.html')


@bp.route('/schedules/<int:schedule_id>')
@login_required
def view(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not _can_view(schedule):
        flash('Нет доступа', 'danger')
        return redirect(url_for('schedules.profile'))

    week_dates = get_week_dates()
    week_view = build_week_view(schedule.data or [])
    today_idx = date.today().weekday()

    configs = {sc.subject_name: sc for sc in schedule.subject_configs}
    can_edit = _can_edit(schedule)

    # Все трекеры для дэшборда — сортируем по сохранённой позиции в сетке
    all_metrics = []
    for sc in schedule.subject_configs:
        for m in sc.metrics:
            all_metrics.append({'subject': sc.subject_name, 'metric': m})
    all_metrics.sort(key=lambda e: (e['metric'].grid_row, e['metric'].grid_col, e['metric'].id))

    return render_template('schedule/view.html',
                           schedule=schedule,
                           week_view=week_view,
                           week_dates=week_dates,
                           days_display=DAYS_DISPLAY,
                           days_ru=DAYS_RU,
                           today_idx=today_idx,
                           configs=configs,
                           can_edit=can_edit,
                           is_shared_view=False,
                           all_metrics=all_metrics)


@bp.route('/schedules/<int:schedule_id>/delete', methods=['POST'])
@login_required
def delete(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    if schedule.user_id != current_user.id:
        flash('Нет доступа', 'danger')
        return redirect(url_for('schedules.profile'))
    db.session.delete(schedule)
    db.session.commit()
    flash('Расписание удалено', 'success')
    return redirect(url_for('schedules.profile'))


@bp.route('/schedules/merge', methods=['POST'])
@login_required
def merge():
    ids = request.form.getlist('schedule_ids')
    name = request.form.get('name', '').strip()
    if len(ids) < 2:
        flash('Выберите хотя бы 2 расписания', 'danger')
        return redirect(url_for('schedules.profile'))
    if not name:
        flash('Введите название', 'danger')
        return redirect(url_for('schedules.profile'))

    schedules = Schedule.query.filter(
        Schedule.id.in_(ids),
        Schedule.user_id == current_user.id
    ).all()

    if len(schedules) < 2:
        flash('Расписания не найдены', 'danger')
        return redirect(url_for('schedules.profile'))

    merged_data = merge_schedules_data([s.data for s in schedules])
    merged = Schedule(user_id=current_user.id, name=name, data=merged_data)
    db.session.add(merged)
    db.session.commit()
    flash(f'Расписание "{name}" создано', 'success')
    return redirect(url_for('schedules.view', schedule_id=merged.id))


# ─── Переименование расписания ────────────────────────────────────────────────

@bp.route('/schedules/<int:schedule_id>/rename', methods=['POST'])
@csrf.exempt
@login_required
def rename_schedule(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not _can_edit(schedule):
        return jsonify({'error': 'Нет доступа'}), 403
    name = request.json.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Пустое имя'}), 400
    schedule.name = name
    db.session.commit()
    return jsonify({'ok': True})


# ─── Глобальное переименование поля предмета ─────────────────────────────────

@bp.route('/schedules/<int:schedule_id>/subjects/<path:subject_name>/field',
          methods=['POST'])
@csrf.exempt
@login_required
def rename_subject_field(schedule_id, subject_name):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not _can_edit(schedule):
        return jsonify({'error': 'Нет доступа'}), 403

    body = request.json or {}
    field     = body.get('field')          # name | classroom | teacher | type
    new_value = body.get('value', '').strip()
    old_type  = body.get('old_type', '')   # только для field=type

    data = copy.deepcopy(schedule.data or [])
    for item in data:
        if item.get('subject') != subject_name:
            continue
        if field == 'name':
            item['subject'] = new_value
        elif field == 'classroom':
            _replace_slot_field(item, idx=2, value=new_value or None)
        elif field == 'teacher':
            _replace_slot_field(item, idx=3, value=new_value or None)
        elif field == 'type' and old_type:
            types = item.get('types', {})
            if old_type in types:
                types[new_value] = types.pop(old_type)

    schedule.data = data

    if field == 'name':
        cfg = SubjectConfig.query.filter_by(
            schedule_id=schedule_id, subject_name=subject_name).first()
        if cfg:
            cfg.subject_name = new_value

    db.session.commit()
    return jsonify({'ok': True})


def _replace_slot_field(item: dict, idx: int, value):
    """Меняет поле слота по индексу во всех типах и датах"""
    for type_data in item.get('types', {}).values():
        date_ranges = type_data.get('dates', type_data) if isinstance(type_data, dict) and 'dates' in type_data else type_data
        for slots in date_ranges.values():
            for slot in slots:
                while len(slot) <= idx:
                    slot.append(None)
                slot[idx] = value


# ─── Изменение времени конкретного слота ─────────────────────────────────────

@bp.route('/schedules/<int:schedule_id>/subjects/<path:subject_name>/slot-time',
          methods=['POST'])
@csrf.exempt
@login_required
def edit_slot_time(schedule_id, subject_name):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not _can_edit(schedule):
        return jsonify({'error': 'Нет доступа'}), 403

    body      = request.json or {}
    day       = (body.get('day') or '').lower()
    old_time  = body.get('old_time', '')
    new_time  = body.get('new_time', '').strip()
    type_name = body.get('type_name', '')
    dr_key    = body.get('date_range', '')

    data = copy.deepcopy(schedule.data or [])
    for item in data:
        if item.get('subject') != subject_name:
            continue
        for tn, type_data in item.get('types', {}).items():
            if type_name and tn != type_name:
                continue
            drs = type_data.get('dates', type_data) if isinstance(type_data, dict) and 'dates' in type_data else type_data
            for dr, slots in drs.items():
                if dr_key and dr != dr_key:
                    continue
                for slot in slots:
                    if slot[0].lower() == day and (len(slot) < 2 or slot[1] == old_time):
                        if len(slot) > 1:
                            slot[1] = new_time

    schedule.data = data
    db.session.commit()
    return jsonify({'ok': True})


# ─── Полное редактирование одного слота ──────────────────────────────────────

@bp.route('/schedules/<int:schedule_id>/subjects/<path:subject_name>/slot',
          methods=['PATCH'])
@csrf.exempt
@login_required
def edit_slot(schedule_id, subject_name):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not _can_edit(schedule):
        return jsonify({'error': 'Нет доступа'}), 403

    body      = request.json or {}
    old_day   = (body.get('old_day') or '').lower()
    old_time  = body.get('old_time', '')
    type_name = body.get('type_name', '')
    dr_key    = body.get('date_range', '')

    new_day       = (body.get('day') or '').lower()
    new_time      = body.get('time', '').strip()
    new_classroom = body.get('classroom', '').strip() or None
    new_teacher   = body.get('teacher', '').strip() or None

    data = copy.deepcopy(schedule.data or [])
    changed = False
    for item in data:
        if item.get('subject') != subject_name:
            continue
        for tn, type_data in item.get('types', {}).items():
            if type_name and tn != type_name:
                continue
            drs = type_data.get('dates', type_data) if isinstance(type_data, dict) and 'dates' in type_data else type_data
            for dr, slots in drs.items():
                if dr_key and dr != dr_key:
                    continue
                for slot in slots:
                    if slot[0].lower() == old_day and (not old_time or (len(slot) > 1 and slot[1] == old_time)):
                        while len(slot) < 4:
                            slot.append(None)
                        slot[0] = new_day
                        slot[1] = new_time
                        slot[2] = new_classroom
                        slot[3] = new_teacher
                        changed = True

    if changed:
        schedule.data = data
        db.session.commit()
    return jsonify({'ok': True})


# ─── Добавление нового слота ──────────────────────────────────────────────────

@bp.route('/schedules/<int:schedule_id>/subjects/<path:subject_name>/slot',
          methods=['PUT'])
@csrf.exempt
@login_required
def add_slot(schedule_id, subject_name):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not _can_edit(schedule):
        return jsonify({'error': 'Нет доступа'}), 403

    body      = request.json or {}
    type_name = body.get('type_name', '').strip()
    dr_key    = body.get('date_range', '').strip()
    day       = (body.get('day') or '').lower().strip()
    time_val  = body.get('time', '').strip()
    classroom = body.get('classroom', '').strip() or None
    teacher   = body.get('teacher', '').strip() or None

    if not type_name or not dr_key or not day:
        return jsonify({'error': 'Укажите тип, период и день'}), 400

    data = copy.deepcopy(schedule.data or [])
    for item in data:
        if item.get('subject') != subject_name:
            continue
        types = item.setdefault('types', {})
        if type_name not in types:
            types[type_name] = {'color': 'gray', 'dates': {}}
        type_data = types[type_name]
        if isinstance(type_data, dict) and 'dates' in type_data:
            drs = type_data['dates']
        else:
            drs = type_data
        slot_list = drs.setdefault(dr_key, [])
        slot_list.append([day, time_val, classroom, teacher])
        schedule.data = data
        db.session.commit()
        return jsonify({'ok': True})

    return jsonify({'error': 'Предмет не найден'}), 404


# ─── Переименование периода (date_range ключа) ────────────────────────────────

@bp.route('/schedules/<int:schedule_id>/subjects/<path:subject_name>/period',
          methods=['POST'])
@csrf.exempt
@login_required
def rename_period(schedule_id, subject_name):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not _can_edit(schedule):
        return jsonify({'error': 'Нет доступа'}), 403

    body      = request.json or {}
    type_name = body.get('type_name', '')
    old_dr    = body.get('old_period', '').strip()
    new_dr    = body.get('new_period', '').strip()

    if not old_dr or not new_dr:
        return jsonify({'error': 'Укажите старый и новый период'}), 400

    data = copy.deepcopy(schedule.data or [])
    for item in data:
        if item.get('subject') != subject_name:
            continue
        for tn, type_data in item.get('types', {}).items():
            if type_name and tn != type_name:
                continue
            drs = type_data.get('dates', type_data) if isinstance(type_data, dict) and 'dates' in type_data else type_data
            if old_dr in drs:
                drs[new_dr] = drs.pop(old_dr)

    schedule.data = data
    db.session.commit()
    return jsonify({'ok': True})


# ─── Удаление предмета полностью ─────────────────────────────────────────────

@bp.route('/schedules/<int:schedule_id>/subjects/<path:subject_name>',
          methods=['DELETE'])
@csrf.exempt
@login_required
def delete_subject(schedule_id, subject_name):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not _can_edit(schedule):
        return jsonify({'error': 'Нет доступа'}), 403

    schedule.data = [item for item in (schedule.data or [])
                     if item.get('subject') != subject_name]

    cfg = SubjectConfig.query.filter_by(
        schedule_id=schedule_id, subject_name=subject_name).first()
    if cfg:
        db.session.delete(cfg)

    db.session.commit()
    return jsonify({'ok': True})


# ─── Удаление конкретного слота ───────────────────────────────────────────────

@bp.route('/schedules/<int:schedule_id>/subjects/<path:subject_name>/slot',
          methods=['DELETE'])
@csrf.exempt
@login_required
def delete_slot(schedule_id, subject_name):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not _can_edit(schedule):
        return jsonify({'error': 'Нет доступа'}), 403

    body      = request.json or {}
    day       = (body.get('day') or '').lower()
    time_val  = body.get('time', '')
    type_name = body.get('type_name', '')
    dr_key    = body.get('date_range', '')

    data = copy.deepcopy(schedule.data or [])
    for item in data:
        if item.get('subject') != subject_name:
            continue
        for tn in list(item.get('types', {}).keys()):
            if type_name and tn != type_name:
                continue
            type_data = item['types'][tn]
            new_format = isinstance(type_data, dict) and 'dates' in type_data
            drs = type_data['dates'] if new_format else type_data
            for dr in list(drs.keys()):
                if dr_key and dr != dr_key:
                    continue
                drs[dr] = [
                    s for s in drs[dr]
                    if not (s[0].lower() == day and
                            (len(s) < 2 or s[1] == time_val))
                ]
                if not drs[dr]:
                    del drs[dr]
            if not drs:
                del item['types'][tn]

    # Убираем предметы без слотов
    schedule.data = [item for item in data if item.get('types')]
    db.session.commit()
    return jsonify({'ok': True})

