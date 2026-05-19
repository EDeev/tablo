from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, jsonify)
from flask_login import login_required, current_user
from app import db, csrf
from app.models.schedule import Schedule, SubjectConfig
from app.models.share import Share, ShareEditor
from app.models.user import User
from app.services.schedule_helpers import build_week_view, get_week_dates, DAYS_DISPLAY, DAYS_RU
from app.services.merge import merge_schedules_data
from datetime import date

bp = Blueprint('shares', __name__)


@bp.route('/schedules/<int:schedule_id>/share', methods=['POST'])
@csrf.exempt
@login_required
def create_share(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    if schedule.user_id != current_user.id:
        return jsonify({'error': 'Нет доступа'}), 403

    share_type = request.json.get('type', 'view')
    if share_type not in ('view', 'edit', 'template'):
        return jsonify({'error': 'Неизвестный тип'}), 400

    # Один тип = одна ссылка на расписание
    existing = Share.query.filter_by(
        schedule_id=schedule_id, share_type=share_type).first()
    if existing:
        return jsonify({'ok': True, 'token': existing.token})

    share = Share(schedule_id=schedule_id, owner_id=current_user.id,
                  share_type=share_type)
    db.session.add(share)
    db.session.commit()
    return jsonify({'ok': True, 'token': share.token})


@bp.route('/schedules/<int:schedule_id>/share/editors', methods=['POST'])
@csrf.exempt
@login_required
def add_editor(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    if schedule.user_id != current_user.id:
        return jsonify({'error': 'Нет доступа'}), 403

    login = request.json.get('login', '').strip()
    user = User.query.filter_by(login=login).first()
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404

    edit_share = Share.query.filter_by(
        schedule_id=schedule_id, share_type='edit').first()
    if not edit_share:
        edit_share = Share(schedule_id=schedule_id, owner_id=current_user.id,
                           share_type='edit')
        db.session.add(edit_share)
        db.session.flush()

    existing = ShareEditor.query.filter_by(
        share_id=edit_share.id, user_id=user.id).first()
    if not existing:
        db.session.add(ShareEditor(share_id=edit_share.id, user_id=user.id))
        db.session.commit()
    return jsonify({'ok': True, 'token': edit_share.token})


@bp.route('/shared/<token>')
def view_shared(token):
    share = Share.query.filter_by(token=token).first_or_404()
    schedule = share.schedule

    if share.share_type == 'template':
        # Клонирование — только для авторизованных
        from flask_login import current_user
        if not current_user.is_authenticated:
            flash('Войдите чтобы использовать шаблон', 'warning')
            return redirect(url_for('auth.login'))
        cloned = Schedule(
            user_id=current_user.id,
            name=f'{schedule.name} (копия)',
            data=schedule.data,
        )
        db.session.add(cloned)
        db.session.commit()
        flash('Расписание добавлено в ваш профиль', 'success')
        return redirect(url_for('schedules.view', schedule_id=cloned.id))

    week_dates = get_week_dates()
    week_view = build_week_view(schedule.data or [])
    today_idx = date.today().weekday()
    configs = {sc.subject_name: sc for sc in schedule.subject_configs}

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
                           can_edit=False,
                           is_shared_view=True,
                           all_metrics=all_metrics)
