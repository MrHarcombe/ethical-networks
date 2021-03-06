import functools

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from ethical.db import get_db

bp = Blueprint('iauth', __name__, url_prefix='/iauth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif db.execute(
            'SELECT id FROM user WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = 'User {} is already registered.'.format(username)

        if error is None:
            db.execute(
                'INSERT INTO user (username, password) VALUES (?, ?)',
                (username, password)
            )
            db.commit()
            return redirect(url_for('iauth.login'))

        flash(error)

    return render_template('iauth/register.html')


###
# this login uses parameters, so is vulnerable to SQL-injection attacks
#
@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT id FROM user WHERE username = "' + username + '" and password = "' + password + '"'
        ).fetchone()

        if user is None:
            error = 'Unknown username'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['table'] = 'user'
            return redirect(url_for('home'))

        flash(error)

    return render_template('iauth/login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    table = session.get('table')

    if user_id is None or table is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM ' + table + ' WHERE id = ?', (user_id,)
        ).fetchone()
        
        
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
