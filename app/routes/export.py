import urllib.parse
from flask import Blueprint, Response, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.schedule import Schedule
from app.models.share import Share
from app import db

bp = Blueprint('export', __name__)


def _can_view(schedule: Schedule) -> bool:
    if schedule.user_id == current_user.id:
        return True
    share = Share.query.filter_by(schedule_id=schedule.id).first()
    return share is not None


@bp.route('/schedules/<int:schedule_id>/export/json')
@login_required
def export_json(schedule_id: int):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not _can_view(schedule):
        flash('Нет доступа', 'danger')
        return redirect(url_for('schedules.profile'))
    from app.services.export import export_json as svc_json
    data = svc_json(schedule)
    filename = _safe_name(schedule.name) + '.json'
    return Response(
        data,
        mimetype='application/json',
        headers={'Content-Disposition': _cd(filename)},
    )


@bp.route('/schedules/<int:schedule_id>/export/csv')
@login_required
def export_csv(schedule_id: int):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not _can_view(schedule):
        flash('Нет доступа', 'danger')
        return redirect(url_for('schedules.profile'))
    from app.services.export import export_csv as svc_csv
    data = svc_csv(schedule)
    filename = _safe_name(schedule.name) + '.csv'
    return Response(
        data,
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': _cd(filename)},
    )


@bp.route('/schedules/<int:schedule_id>/export/pdf')
@login_required
def export_pdf(schedule_id: int):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not _can_view(schedule):
        flash('Нет доступа', 'danger')
        return redirect(url_for('schedules.profile'))
    from app.services.export import export_pdf as svc_pdf
    data = svc_pdf(schedule)
    filename = _safe_name(schedule.name) + '.pdf'
    return Response(
        data,
        mimetype='application/pdf',
        headers={'Content-Disposition': _cd(filename)},
    )


@bp.route('/schedules/<int:schedule_id>/export/png')
@login_required
def export_png(schedule_id: int):
    schedule = Schedule.query.get_or_404(schedule_id)
    if not _can_view(schedule):
        flash('Нет доступа', 'danger')
        return redirect(url_for('schedules.profile'))
    from app.services.export import export_png as svc_png
    data = svc_png(schedule)
    filename = _safe_name(schedule.name) + '.png'
    return Response(
        data,
        mimetype='image/png',
        headers={'Content-Disposition': _cd(filename)},
    )


def _safe_name(name: str) -> str:
    safe = ''.join(c if c.isalnum() or c in ' ._-' else '_' for c in name)
    return safe.strip() or 'schedule'


def _cd(filename: str) -> str:
    """Content-Disposition с поддержкой Unicode (RFC 5987)."""
    ascii_name = filename.encode('ascii', 'replace').decode('ascii')
    utf8_name = urllib.parse.quote(filename, safe='')
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{utf8_name}"
