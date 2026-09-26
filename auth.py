import hashlib
import secrets
import time
from functools import wraps
from flask import Blueprint, abort, current_app, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash
from .db import db, one, audit

bp = Blueprint('auth', __name__)
PUBLIC = {'/api/login', '/api/health'}

def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()

def require(*roles):
    def decorate(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            if g.user['role'] not in roles:
                abort(403, 'Your account cannot perform this action.')
            return fn(*a, **kw)
        return wrapper
    return decorate

def text(data, key, maximum=10000, required=True):
    value = data.get(key, '')
    if not isinstance(value, str) or len(value) > maximum or (required and not value.strip()):
        abort(400, f'Please enter a valid {key.replace("_", " ")}.')
    return value.strip()

def number(data, key, low=1, high=2**31-1):
    value = data.get(key)
    if isinstance(value, bool):
        abort(400, f'Invalid {key}.')
    try:
        n = int(value)
        if str(n) != str(value) or not low <= n <= high:
            raise ValueError()
        return n
    except (ValueError, TypeError):
        abort(400, f'Invalid {key}.')

def password_hash(value):
    if not isinstance(value, str) or not 14 <= len(value) <= 128:
        abort(400, 'Use a password or passphrase of 14–128 characters.')
    return generate_password_hash(value, method='scrypt')

def learner_access(learner_id):
    learner = one("SELECT id,name FROM users WHERE id=? AND role='learner'", (learner_id,))
    if not learner:
        abort(404, 'Learner not found.')
    u = g.user
    allowed = u['role'] == 'admin' or (u['role'] == 'learner' and u['id'] == learner_id)
    if u['role'] in ('assessor', 'iqa'):
        allowed = one('SELECT 1 FROM assignments WHERE staff_id=? AND learner_id=?', (u['id'], learner_id))
    if not allowed:
        abort(403, 'This learner is not assigned to you.')
    return learner

def install_auth(app):
    @app.before_request
    def authenticate():
        g.user = None
        if not request.path.startswith('/api/') or request.path in PUBLIC:
            return
        token = request.cookies.get('hf_session', '')
        session = one('SELECT * FROM sessions WHERE token=? AND expires>?', (digest(token), int(time.time())))
        if not session:
            abort(401, 'Please sign in.')
        g.user = one('SELECT id,name,email,role,must_change FROM users WHERE id=? AND active=1', (session['user_id'],))
        if not g.user:
            abort(401, 'Please sign in.')
        g.session = session
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            if not secrets.compare_digest(request.headers.get('X-CSRF-Token', ''), session['csrf']):
                abort(403, 'Your session changed. Refresh the page and try again.')
        if g.user['must_change'] and request.path not in ('/api/me','/api/password','/api/logout'):
            abort(403, 'Change your temporary password before continuing.')

@bp.post('/api/login')
def login():
    data = request.get_json()
    if not isinstance(data, dict):
        abort(400)
    email = text(data, 'email', 254).lower()
    password = data.get('password', '')
    if not isinstance(password, str) or len(password) > 128:
        abort(400, 'Invalid password.')
    now = int(time.time())
    # Persistent per-address and per-account rate limits. Reverse proxy must also rate-limit.
    subjects = [digest('ip:' + (request.remote_addr or '')), digest('email:' + email)]
    db().execute('DELETE FROM login_attempts WHERE at<?', (now-900,))
    attempt_ids=[]
    for subject, limit in zip(subjects, (40, 10)):
        if one('SELECT COUNT(*) n FROM login_attempts WHERE subject=?', (subject,))['n'] >= limit:
            abort(429, 'Too many attempts. Try again in 15 minutes.')
        attempt_ids.append(db().execute('INSERT INTO login_attempts VALUES(?,?)', (subject, now)).lastrowid)
    db().commit()
    user = one('SELECT * FROM users WHERE email=? AND active=1', (email,))
    valid = check_password_hash(user['password'] if user else current_app.config['DUMMY_HASH'], password)
    if not user or not valid:
        abort(401, 'Email or password is incorrect.')
    for attempt_id in attempt_ids:
        db().execute('DELETE FROM login_attempts WHERE rowid=?',(attempt_id,))
    token, csrf = secrets.token_urlsafe(48), secrets.token_urlsafe(32)
    db().execute('DELETE FROM sessions WHERE expires<?', (now,))
    db().execute('INSERT INTO sessions VALUES(?,?,?,?)', (digest(token),user['id'],csrf,now+8*3600))
    g.user = user
    audit('signed_in', 'user', user['id'])
    db().commit()
    response = jsonify(ok=True)
    response.set_cookie('hf_session',token,httponly=True,secure=current_app.config['SECURE_COOKIES'],samesite='Strict',max_age=8*3600,path='/')
    return response

@bp.get('/api/me')
def me():
    return jsonify(user=g.user, csrf=g.session['csrf'])

@bp.post('/api/logout')
def logout():
    db().execute('DELETE FROM sessions WHERE token=?', (g.session['token'],))
    db().commit()
    r = jsonify(ok=True)
    r.delete_cookie('hf_session', path='/')
    return r

@bp.post('/api/password')
def change_password():
    data = request.get_json()
    old = one('SELECT password FROM users WHERE id=?', (g.user['id'],))
    value = data.get('current_password', '')
    if not isinstance(value, str) or len(value)>128 or not check_password_hash(old['password'], value):
        abort(400, 'Current password is incorrect.')
    new = password_hash(data.get('new_password'))
    if data.get('new_password') == value:
        abort(400, 'Choose a different password.')
    db().execute('UPDATE users SET password=?,must_change=0 WHERE id=?', (new,g.user['id']))
    db().execute('DELETE FROM sessions WHERE user_id=?', (g.user['id'],))
    audit('password_changed','user',g.user['id'])
    db().commit()
    r = jsonify(ok=True)
    r.delete_cookie('hf_session',path='/')
    return r
