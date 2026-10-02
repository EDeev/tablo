import pytest

from app import db
from app.models import Share
from tests.conftest import add_editor, login, make_user

EXPORTS = ['json', 'csv']


def test_owner_sees_schedule(client, owner, schedule):
    login(client, 'owner')
    assert client.get(f'/schedules/{schedule.id}').status_code == 200


def test_anonymous_is_redirected_to_login(client, schedule):
    response = client.get(f'/schedules/{schedule.id}')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_stranger_cannot_open_schedule(client, schedule, stranger):
    login(client, 'stranger')
    response = client.get(f'/schedules/{schedule.id}', follow_redirects=False)
    assert response.status_code in (302, 403)


@pytest.mark.parametrize('fmt', EXPORTS)
def test_owner_can_export(client, schedule, fmt):
    login(client, 'owner')
    response = client.get(f'/schedules/{schedule.id}/export/{fmt}')
    assert response.status_code == 200
    assert 'Базы данных' in response.get_data(as_text=True)


@pytest.mark.parametrize('fmt', EXPORTS)
def test_view_share_does_not_open_export_by_id(client, schedule, owner, stranger, fmt):
    """Ссылка на просмотр открывает расписание по токену, но не экспорт по id."""
    db.session.add(Share(schedule_id=schedule.id, owner_id=owner.id, share_type='view'))
    db.session.commit()
    login(client, 'stranger')
    response = client.get(f'/schedules/{schedule.id}/export/{fmt}')
    assert response.status_code == 302
    assert 'Базы данных' not in response.get_data(as_text=True)


def test_editor_can_view_and_export(client, schedule, share_edit):
    editor = make_user('editor')
    add_editor(share_edit, editor)
    login(client, 'editor')
    assert client.get(f'/schedules/{schedule.id}').status_code == 200
    assert client.get(f'/schedules/{schedule.id}/export/json').status_code == 200


def test_view_share_link_works_without_login(client, schedule, owner):
    share = Share(schedule_id=schedule.id, owner_id=owner.id, share_type='view')
    db.session.add(share)
    db.session.commit()
    response = client.get(f'/shared/{share.token}')
    assert response.status_code == 200
    assert 'Базы данных' in response.get_data(as_text=True)


def test_stranger_cannot_rename(client, schedule, stranger):
    login(client, 'stranger')
    client.post(f'/schedules/{schedule.id}/rename', data={'name': 'Взлом'})
    db.session.refresh(schedule)
    assert schedule.name == 'Весенний семестр'


def test_app_refuses_to_start_without_secret_key(monkeypatch):
    from app import create_app

    monkeypatch.delenv('SECRET_KEY', raising=False)
    monkeypatch.delenv('FLASK_DEBUG', raising=False)
    with pytest.raises(RuntimeError):
        create_app({'SECRET_KEY': None})
