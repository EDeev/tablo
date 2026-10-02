from app.models import User


def test_register_and_login(client, app):
    response = client.post('/register', data={'login': 'student', 'password': 'secret123', 'confirm': 'secret123'})
    assert response.status_code in (200, 302)
    assert User.query.filter_by(login='student').one().check_password('secret123')
    client.get('/logout')
    response = client.post('/login', data={'login': 'student', 'password': 'secret123'})
    assert response.status_code == 302


def test_wrong_password_is_rejected(client, owner):
    response = client.post('/login', data={'login': 'owner', 'password': 'wrong'})
    assert response.status_code == 200
    assert client.get('/').status_code == 302


def test_password_is_hashed(owner):
    assert owner.password_hash != 'password123'


def test_login_next_redirect_stays_on_site(client, owner):
    response = client.post('/login?next=https://evil.example/phish', data={'login': 'owner', 'password': 'password123'})
    assert response.status_code == 302
    assert 'evil.example' not in response.headers['Location']


def test_login_next_relative_path_is_kept(client, owner):
    response = client.post('/login?next=/schedules/upload', data={'login': 'owner', 'password': 'password123'})
    assert response.headers['Location'].endswith('/schedules/upload')


def test_login_next_backslash_trick_is_rejected(client, owner):
    response = client.post('/login?next=/%5Cevil.example', data={'login': 'owner', 'password': 'password123'})
    assert 'evil.example' not in response.headers['Location']
