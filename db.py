import sqlite3
from flask import current_app, g

SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
 password TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('admin','assessor','iqa','learner')),
 active INTEGER NOT NULL DEFAULT 1, must_change INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS sessions (
 token TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), csrf TEXT NOT NULL, expires INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS login_attempts (subject TEXT NOT NULL, at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS assignments (
 staff_id INTEGER NOT NULL REFERENCES users(id), learner_id INTEGER NOT NULL REFERENCES users(id),
 PRIMARY KEY(staff_id,learner_id)
);
CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS units (
 id INTEGER PRIMARY KEY, course_id INTEGER NOT NULL REFERENCES courses(id), ref TEXT NOT NULL,
 title TEXT NOT NULL, aim TEXT NOT NULL, criteria TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS enrolments (
 learner_id INTEGER NOT NULL REFERENCES users(id), course_id INTEGER NOT NULL REFERENCES courses(id),
 PRIMARY KEY(learner_id,course_id)
);
CREATE TABLE IF NOT EXISTS portfolios (
 id INTEGER PRIMARY KEY, learner_id INTEGER NOT NULL REFERENCES users(id), unit_id INTEGER NOT NULL REFERENCES units(id),
 status TEXT NOT NULL DEFAULT 'draft', version INTEGER NOT NULL DEFAULT 0, fields TEXT NOT NULL DEFAULT '{}',
 updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS evidence (
 id INTEGER PRIMARY KEY, portfolio_id INTEGER NOT NULL REFERENCES portfolios(id), filename TEXT NOT NULL,
 stored TEXT UNIQUE NOT NULL, sha256 TEXT NOT NULL, size INTEGER NOT NULL, created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS decisions (
 id INTEGER PRIMARY KEY, portfolio_id INTEGER NOT NULL REFERENCES portfolios(id), actor INTEGER NOT NULL REFERENCES users(id),
 kind TEXT NOT NULL, outcome TEXT NOT NULL, feedback TEXT NOT NULL, version INTEGER NOT NULL,
 checks TEXT NOT NULL DEFAULT '[]',
 snapshot TEXT NOT NULL, created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS attendance (
 id INTEGER PRIMARY KEY, learner_id INTEGER NOT NULL REFERENCES users(id), day TEXT NOT NULL, status TEXT NOT NULL,
 minutes INTEGER NOT NULL, note TEXT NOT NULL, actor INTEGER NOT NULL REFERENCES users(id), UNIQUE(learner_id,day)
);
CREATE TABLE IF NOT EXISTS hours (
 id INTEGER PRIMARY KEY, learner_id INTEGER NOT NULL REFERENCES users(id), day TEXT NOT NULL, minutes INTEGER NOT NULL,
 category TEXT NOT NULL DEFAULT 'academy', course_id INTEGER REFERENCES courses(id),
 activity TEXT NOT NULL, reflection TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
 reviewer INTEGER REFERENCES users(id), feedback TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS reviews (
 id INTEGER PRIMARY KEY, learner_id INTEGER NOT NULL REFERENCES users(id), review_date TEXT NOT NULL, next_date TEXT NOT NULL,
 strengths TEXT NOT NULL, actions TEXT NOT NULL, actor INTEGER NOT NULL REFERENCES users(id),
 acknowledged TEXT, created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS resources (
 id INTEGER PRIMARY KEY, course_id INTEGER NOT NULL REFERENCES courses(id), title TEXT NOT NULL,
 body TEXT NOT NULL, url TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS exams (
 id INTEGER PRIMARY KEY, learner_id INTEGER NOT NULL REFERENCES users(id), unit_id INTEGER NOT NULL REFERENCES units(id),
 day TEXT NOT NULL, outcome TEXT NOT NULL, reference TEXT NOT NULL, actor INTEGER NOT NULL REFERENCES users(id),
 created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS audit (
 id INTEGER PRIMARY KEY, actor INTEGER REFERENCES users(id), action TEXT NOT NULL,
 entity TEXT NOT NULL, entity_id INTEGER, detail TEXT NOT NULL DEFAULT '', created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
'''

def db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'], timeout=15)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db

def rows(sql, args=()):
    return [dict(r) for r in db().execute(sql, args).fetchall()]

def one(sql, args=()):
    r = db().execute(sql, args).fetchone()
    return dict(r) if r else None

def audit(action, entity, entity_id=None, detail=''):
    db().execute('INSERT INTO audit(actor,action,entity,entity_id,detail) VALUES(?,?,?,?,?)',
                 (g.user['id'] if getattr(g, 'user', None) else None, action, entity, entity_id, detail))

def init_db(app):
    with app.app_context():
        db().executescript(SCHEMA)
        db().commit()
    @app.teardown_appcontext
    def close(_error):
        conn = g.pop('db', None)
        if conn:
            conn.close()
