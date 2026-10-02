from urllib.parse import urlsplit

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User

bp = Blueprint('auth', __name__)


def _is_safe_next(target: str) -> bool:
    """Переход после входа — только на страницы этого же сайта (защита от открытого редиректа)."""
    parts = urlsplit(target)
    return (bool(target) and target.startswith('/') and not target.startswith(('//', '/\\'))
            and not parts.netloc and not parts.scheme)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('schedules.profile'))
    if request.method == 'POST':
        login = request.form.get('login', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        if not login or not password:
            flash('Заполните все поля', 'danger')
        elif len(login) < 3:
            flash('Логин не менее 3 символов', 'danger')
        elif password != confirm:
            flash('Пароли не совпадают', 'danger')
        elif User.query.filter_by(login=login).first():
            flash('Логин уже занят', 'danger')
        else:
            user = User(login=login)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('schedules.profile'))
    return render_template('auth/register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('schedules.profile'))
    if request.method == 'POST':
        login = request.form.get('login', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(login=login).first()
        if user and user.check_password(password):
            login_user(user, remember=bool(request.form.get('remember')))
            next_page = request.args.get('next', '')
            if not _is_safe_next(next_page):
                next_page = url_for('schedules.profile')
            return redirect(next_page)
        flash('Неверный логин или пароль', 'danger')
    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
