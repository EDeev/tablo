from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.orm.attributes import flag_modified
from app import db, csrf
from app.models.schedule import Schedule, SubjectConfig, COMPLETION_TYPES
from app.models.metric import Metric, METRIC_TYPES, METRIC_LABELS
from app.services.ai_metrics import generate_metric_from_prompt

bp = Blueprint('subjects', __name__)


# ─── Страница предметов ───────────────────────────────────────────────────────

@bp.route('/schedules/<int:schedule_id>/subjects')
@login_required
def subjects_page(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    can_edit = _check_edit_access(schedule)
    configs = {sc.subject_name: sc for sc in schedule.subject_configs}
    return render_template('schedule/subjects.html',
                           schedule=schedule,
                           configs=configs,
                           can_edit=can_edit,
                           completion_types=COMPLETION_TYPES)


# ─── Описание предмета ────────────────────────────────────────────────────────

@bp.route('/schedules/<int:schedule_id>/subjects/<path:subject_name>/description',
          methods=['POST'])
@csrf.exempt
@login_required
def update_description(schedule_id, subject_name):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not _check_edit_access(schedule):
        return jsonify({'error': 'Нет доступа'}), 403
    config = _get_or_create_config(schedule_id, subject_name)
    config.description = request.json.get('description', '')
    db.session.commit()
    return jsonify({'ok': True})


# ─── Добавить метрику (вручную) ───────────────────────────────────────────────

@bp.route('/schedules/<int:schedule_id>/subjects/<path:subject_name>/metrics',
          methods=['POST'])
@csrf.exempt
@login_required
def add_metric(schedule_id, subject_name):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not _check_edit_access(schedule):
        return jsonify({'error': 'Нет доступа'}), 403

    body        = request.json or {}
    metric_type = body.get('type', '')
    label       = body.get('label', '').strip()
    config      = body.get('config', {})

    if metric_type not in METRIC_TYPES:
        return jsonify({'error': 'Неизвестный тип'}), 400
    if not label:
        label = METRIC_LABELS.get(metric_type, 'Метрика')

    cfg = _get_or_create_config(schedule_id, subject_name)
    metric = Metric(subject_config_id=cfg.id, type=metric_type,
                    label=label, config=config, progress={})
    db.session.add(metric)
    db.session.commit()
    return jsonify({'ok': True, 'html': _render_metric_html(metric)})


# ─── Добавить метрику через AI ────────────────────────────────────────────────

@bp.route('/schedules/<int:schedule_id>/subjects/<path:subject_name>/metrics/ai',
          methods=['POST'])
@csrf.exempt
@login_required
def add_metric_ai(schedule_id, subject_name):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not _check_edit_access(schedule):
        return jsonify({'error': 'Нет доступа'}), 403

    body = request.json or {}
    prompt = body.get('prompt', '').strip()
    if not prompt:
        return jsonify({'error': 'Пустой промт'}), 400

    try:
        result = generate_metric_from_prompt(subject_name, prompt)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    cfg = _get_or_create_config(schedule_id, subject_name)
    metric = Metric(subject_config_id=cfg.id,
                    type=result.get('type', 'checkpoints'),
                    label=result.get('label', 'Метрика'),
                    config=result.get('config', {}),
                    progress={},
                    ai_prompt=prompt)
    db.session.add(metric)
    db.session.commit()
    return jsonify({'ok': True, 'html': _render_metric_html(metric)})


# ─── Сохранить прогресс метрики ───────────────────────────────────────────────
# Принимает весь объект progress целиком и перезаписывает его в БД.

@bp.route('/api/metrics/<int:metric_id>/progress', methods=['POST'])
@csrf.exempt
@login_required
def save_progress(metric_id):
    metric = Metric.query.get_or_404(metric_id)
    if not _check_edit_access(metric.subject_config.schedule):
        return jsonify({'error': 'Нет доступа'}), 403

    metric.progress = request.json or {}
    flag_modified(metric, 'progress')
    db.session.commit()
    return jsonify({'ok': True})


# ─── Сохранить позицию/размер метрики в сетке ────────────────────────────────

@bp.route('/api/metrics/<int:metric_id>/layout', methods=['POST'])
@csrf.exempt
@login_required
def save_layout(metric_id):
    metric = Metric.query.get_or_404(metric_id)
    if not _check_edit_access(metric.subject_config.schedule):
        return jsonify({'error': 'Нет доступа'}), 403
    body = request.json or {}
    for field in ('grid_col', 'grid_row', 'grid_w', 'grid_h'):
        if field in body:
            setattr(metric, field, int(body[field]))
    db.session.commit()
    return jsonify({'ok': True})


# ─── Переименовать метрику ────────────────────────────────────────────────────

@bp.route('/api/metrics/<int:metric_id>/rename', methods=['POST'])
@csrf.exempt
@login_required
def rename_metric(metric_id):
    metric = Metric.query.get_or_404(metric_id)
    if not _check_edit_access(metric.subject_config.schedule):
        return jsonify({'error': 'Нет доступа'}), 403
    label = (request.json or {}).get('label', '').strip()
    if not label:
        return jsonify({'error': 'Пустое название'}), 400
    metric.label = label
    db.session.commit()
    return jsonify({'ok': True})


# ─── Скрыть / показать предмет в расписании ──────────────────────────────────

@bp.route('/schedules/<int:schedule_id>/subjects/<path:subject_name>/visibility',
          methods=['POST'])
@csrf.exempt
@login_required
def toggle_subject_visibility(schedule_id, subject_name):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not _check_edit_access(schedule):
        return jsonify({'error': 'Нет доступа'}), 403
    cfg = _get_or_create_config(schedule_id, subject_name)
    cfg.hidden = not cfg.hidden
    db.session.commit()
    return jsonify({'ok': True, 'hidden': cfg.hidden})


# ─── Тип сдачи предмета ──────────────────────────────────────────────────────

@bp.route('/schedules/<int:schedule_id>/subjects/<path:subject_name>/completion_type',
          methods=['POST'])
@csrf.exempt
@login_required
def set_completion_type(schedule_id, subject_name):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not _check_edit_access(schedule):
        return jsonify({'error': 'Нет доступа'}), 403
    value = (request.json or {}).get('completion_type')
    if value and value not in COMPLETION_TYPES:
        return jsonify({'error': 'Неверный тип'}), 400
    cfg = _get_or_create_config(schedule_id, subject_name)
    cfg.completion_type = value or None
    db.session.commit()
    return jsonify({'ok': True, 'completion_type': cfg.completion_type})


# ─── Завершить / возобновить предмет ─────────────────────────────────────────

@bp.route('/schedules/<int:schedule_id>/subjects/<path:subject_name>/completed',
          methods=['POST'])
@csrf.exempt
@login_required
def toggle_completed(schedule_id, subject_name):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not _check_edit_access(schedule):
        return jsonify({'error': 'Нет доступа'}), 403
    cfg = _get_or_create_config(schedule_id, subject_name)
    cfg.completed = not cfg.completed
    db.session.commit()
    return jsonify({'ok': True, 'completed': cfg.completed})


# ─── Ссылка на СДО ───────────────────────────────────────────────────────────

@bp.route('/schedules/<int:schedule_id>/subjects/<path:subject_name>/sdo_url',
          methods=['POST'])
@csrf.exempt
@login_required
def set_sdo_url(schedule_id, subject_name):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not _check_edit_access(schedule):
        return jsonify({'error': 'Нет доступа'}), 403
    url = (request.json or {}).get('sdo_url', '').strip()
    cfg = _get_or_create_config(schedule_id, subject_name)
    cfg.sdo_url = url or None
    db.session.commit()
    return jsonify({'ok': True})


# ─── Получить промт AI-трекера ────────────────────────────────────────────────

@bp.route('/api/metrics/<int:metric_id>/ai_prompt', methods=['GET'])
@login_required
def get_metric_ai_prompt(metric_id):
    metric = Metric.query.get_or_404(metric_id)
    if not _check_edit_access(metric.subject_config.schedule):
        return jsonify({'error': 'Нет доступа'}), 403
    return jsonify({'ok': True, 'prompt': metric.ai_prompt or ''})


# ─── Сохранить порядок/размеры метрик батчем ─────────────────────────────────

@bp.route('/api/metrics/layout_batch', methods=['POST'])
@csrf.exempt
@login_required
def save_layout_batch():
    items = (request.json or {}).get('items', [])
    if not items:
        return jsonify({'ok': True})
    ids = [int(item['id']) for item in items]
    metrics_map = {m.id: m for m in Metric.query.filter(Metric.id.in_(ids)).all()}
    for item in items:
        metric = metrics_map.get(int(item['id']))
        if not metric:
            continue
        if not _check_edit_access(metric.subject_config.schedule):
            return jsonify({'error': 'Нет доступа'}), 403
        for field in ('grid_col', 'grid_row', 'grid_w', 'grid_h'):
            if field in item:
                setattr(metric, field, int(item[field]))
    db.session.commit()
    return jsonify({'ok': True})


# ─── Удалить метрику ──────────────────────────────────────────────────────────

@bp.route('/api/metrics/<int:metric_id>', methods=['DELETE'])
@csrf.exempt
@login_required
def delete_metric(metric_id):
    metric = Metric.query.get_or_404(metric_id)
    if not _check_edit_access(metric.subject_config.schedule):
        return jsonify({'error': 'Нет доступа'}), 403
    db.session.delete(metric)
    db.session.commit()
    return jsonify({'ok': True})


# ─── Вспомогательные функции ──────────────────────────────────────────────────

def _get_or_create_config(schedule_id: int, subject_name: str) -> SubjectConfig:
    config = SubjectConfig.query.filter_by(
        schedule_id=schedule_id, subject_name=subject_name).first()
    if not config:
        config = SubjectConfig(schedule_id=schedule_id, subject_name=subject_name)
        db.session.add(config)
        db.session.flush()
    return config


def _check_edit_access(schedule: Schedule) -> bool:
    if schedule.user_id == current_user.id:
        return True
    from app.models.share import Share, ShareEditor
    share = Share.query.filter_by(schedule_id=schedule.id, share_type='edit').first()
    if share:
        return ShareEditor.query.filter_by(
            share_id=share.id, user_id=current_user.id).first() is not None
    return False


def _render_metric_html(metric: Metric) -> str:
    from flask import render_template_string
    return render_template_string(
        '{% from "macros/metrics.html" import render_metric %}{{ render_metric(metric, True) }}',
        metric=metric
    )
