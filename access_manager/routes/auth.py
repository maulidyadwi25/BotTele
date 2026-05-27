"""Authentication routes."""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db
from models.user import AdminUser

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handler."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('login.html')

        user = AdminUser.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful.', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid credentials.', 'error')
            return render_template('login.html')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """Logout handler."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
