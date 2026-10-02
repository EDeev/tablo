"""Тесты на настоящем PostgreSQL (JSON-поля): адрес базы — в TEST_DATABASE_URL."""
import os

import pytest
from sqlalchemy import text

from app import create_app, db
from app.models import Schedule, Share, ShareEditor, User

DB_URL = os.getenv('TEST_DATABASE_URL', 'postgresql://tablo:tablo@localhost:5432/tablo_test')

SAMPLE_DATA = [
    {
        'subject': 'Базы данных',
        'types': {
            'Лекция': {'color': 'blue', 'dates': {'01.09-31.12': [
                ['понедельник', '10:40-12:10', 'АВ-301', 'Иванов И.И.'],
                ['понедельник', '9:00-10:30', 'АВ-301', 'Иванов И.И.'],
            ]}},
        },
    },
]


@pytest.fixture(scope='session')
def _app():
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-secret',
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': DB_URL,
    })
    with app.app_context():
        db.drop_all()
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()


@pytest.fixture(autouse=True)
def app(_app):
    """Свой контекст приложения на каждый тест, после теста таблицы очищаются."""
    ctx = _app.app_context()
    ctx.push()
    yield _app
    db.session.remove()
    tables = ', '.join(t.name for t in db.metadata.sorted_tables)
    with db.engine.begin() as conn:
        conn.execute(text(f'TRUNCATE {tables} RESTART IDENTITY CASCADE'))
    ctx.pop()


def make_user(login, password='password123'):
    user = User(login=login)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def owner():
    return make_user('owner')


@pytest.fixture
def stranger():
    return make_user('stranger')


@pytest.fixture
def schedule(owner):
    s = Schedule(user_id=owner.id, name='Весенний семестр', data=SAMPLE_DATA)
    db.session.add(s)
    db.session.commit()
    return s


def login(client, user_login, password='password123'):
    return client.post('/login', data={'login': user_login, 'password': password})


@pytest.fixture
def share_edit(schedule, owner):
    share = Share(schedule_id=schedule.id, owner_id=owner.id, share_type='edit')
    db.session.add(share)
    db.session.commit()
    return share


def add_editor(share, user):
    db.session.add(ShareEditor(share_id=share.id, user_id=user.id))
    db.session.commit()


@pytest.fixture
def client(app):
    return app.test_client()
