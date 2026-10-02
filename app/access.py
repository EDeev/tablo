"""Права доступа к расписанию: владелец или редактор по ссылке на редактирование."""
from flask_login import current_user

from app.models.schedule import Schedule
from app.models.share import Share, ShareEditor


def can_edit(schedule: Schedule) -> bool:
    if not current_user.is_authenticated:
        return False
    if schedule.user_id == current_user.id:
        return True
    edit_share = Share.query.filter_by(schedule_id=schedule.id, share_type='edit').first()
    if edit_share is None:
        return False
    return ShareEditor.query.filter_by(share_id=edit_share.id, user_id=current_user.id).first() is not None


# Просмотр по id доступен тем же, кто может редактировать; остальные смотрят по ссылке /shared/<token>
can_view = can_edit
