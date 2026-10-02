from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.from_object('app.config.Config')
    if config_overrides:
        app.config.update(config_overrides)
    if not app.config.get('SECRET_KEY'):
        if not (app.debug or app.testing):
            raise RuntimeError('Задайте SECRET_KEY: без него cookie сессий можно подделать')
        app.config['SECRET_KEY'] = 'dev-only-secret'  # noqa: S105 — только для отладки и тестов

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Войдите для доступа'
    login_manager.login_message_category = 'warning'

    from app.routes import auth, schedules, subjects, shares, export
    app.register_blueprint(auth.bp)
    app.register_blueprint(schedules.bp)
    app.register_blueprint(subjects.bp)
    app.register_blueprint(shares.bp)
    app.register_blueprint(export.bp)

    return app
