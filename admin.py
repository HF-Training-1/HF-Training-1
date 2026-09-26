import json
import sqlite3
from urllib.parse import urlsplit
from flask import Blueprint, abort, g, jsonify, request
from .auth import number, password_hash, require, text
from .db import db, one, rows, audit

bp=Blueprint('admin',__name__)

@bp.get('/api/admin')
@require('admin')
def overview():
    return jsonify(users=rows('SELECT id,name,email,role,active,must_change FROM users ORDER BY role,name'),
        courses=rows('SELECT * FROM courses'),units=rows('SELECT * FROM units'),
        assignments=rows('SELECT * FROM assignments'),enrolments=rows('SELECT * FROM enrolments'),
        audit=rows('''SELECT a.*,u.name FROM audit a LEFT JOIN users u ON a.actor=u.id ORDER BY a.id DESC LIMIT 100'''))

@bp.post('/api/admin/users')
@require('admin')
def create_user():
    d=request.get_json()
    role=text(d,'role',20)
    if role not in ('admin','assessor','iqa','learner'):
        abort(400,'Invalid role.')
    email=text(d,'email',254).lower()
    if '@' not in email or ' ' in email:
        abort(400,'Invalid email address.')
    hashed=password_hash(d.get('password'))
    try:
        cur=db().execute('INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)',
            (text(d,'name',100),email,hashed,role))
    except sqlite3.IntegrityError:
        abort(409,'This email already has an account.')
    audit('user_created','user',cur.lastrowid,role)
    db().commit()
    return jsonify(id=cur.lastrowid),201

@bp.post('/api/admin/users/<int:uid>')
@require('admin')
def user_action(uid):
    d=request.get_json()
    u=one('SELECT * FROM users WHERE id=?',(uid,))
    if not u:
        abort(404)
    if uid==g.user['id']:
        abort(400,'Use My account for your password. You cannot disable your own account.')
    action=text(d,'action',30)
    if action=='password':
        db().execute('UPDATE users SET password=?,must_change=1 WHERE id=?',(password_hash(d.get('password')),uid))
    elif action in ('disable','enable'):
        db().execute('UPDATE users SET active=? WHERE id=?',(int(action=='enable'),uid))
    else:
        abort(400,'Invalid action.')
    db().execute('DELETE FROM sessions WHERE user_id=?',(uid,))
    audit('user_'+action,'user',uid)
    db().commit()
    return jsonify(ok=True)

@bp.post('/api/admin/assignments')
@require('admin')
def assign():
    d=request.get_json()
    sid,lid=number(d,'staff_id'),number(d,'learner_id')
    if not one("SELECT id FROM users WHERE id=? AND role IN ('assessor','iqa') AND active=1",(sid,)) or not one("SELECT id FROM users WHERE id=? AND role='learner' AND active=1",(lid,)):
        abort(400,'Choose an active assessor or IQA and an active learner.')
    if d.get('remove') is True:
        db().execute('DELETE FROM assignments WHERE staff_id=? AND learner_id=?',(sid,lid))
        action='staff_unassigned'
    else:
        db().execute('INSERT OR IGNORE INTO assignments VALUES(?,?)',(sid,lid))
        action='staff_assigned'
    audit(action,'learner',lid,str(sid))
    db().commit()
    return jsonify(ok=True)

@bp.post('/api/admin/courses')
@require('admin')
def course():
    d=request.get_json()
    cur=db().execute('INSERT INTO courses(title,description) VALUES(?,?)',(text(d,'title',200),text(d,'description',4000)))
    audit('course_created','course',cur.lastrowid)
    db().commit()
    return jsonify(id=cur.lastrowid),201

@bp.post('/api/admin/units')
@require('admin')
def unit():
    d=request.get_json()
    cid=number(d,'course_id')
    if not one('SELECT id FROM courses WHERE id=?',(cid,)):
        abort(404,'Course not found.')
    criteria=[s.strip() for s in text(d,'criteria',10000).splitlines() if s.strip()]
    if not 1<=len(criteria)<=100:
        abort(400,'Provide between 1 and 100 criteria, one per line.')
    args=(cid,text(d,'ref',80),text(d,'title',200),text(d,'aim',2000),json.dumps(criteria))
    uid=d.get('id')
    if uid:
        uid=number(d,'id')
        old=one('SELECT * FROM units WHERE id=?',(uid,))
        if not old or old['course_id']!=cid:
            abort(400,'Course cannot change for an existing unit.')
        if one('SELECT id FROM portfolios WHERE unit_id=?',(uid,)):
            abort(409,'Units are locked after enrolment. Create a new course version to change the criteria.')
        db().execute('UPDATE units SET course_id=?,ref=?,title=?,aim=?,criteria=? WHERE id=?',args+(uid,))
    else:
        cur=db().execute('INSERT INTO units(course_id,ref,title,aim,criteria) VALUES(?,?,?,?,?)',args)
        uid=cur.lastrowid
        db().execute('INSERT INTO portfolios(learner_id,unit_id) SELECT learner_id,? FROM enrolments WHERE course_id=?',(uid,cid))
    audit('unit_saved','unit',uid)
    db().commit()
    return jsonify(id=uid)

@bp.post('/api/admin/enrolments')
@require('admin')
def enrol():
    d=request.get_json()
    lid,cid=number(d,'learner_id'),number(d,'course_id')
    if not one("SELECT id FROM users WHERE id=? AND role='learner' AND active=1",(lid,)) or not one('SELECT id FROM courses WHERE id=?',(cid,)):
        abort(400,'Choose an active learner and course.')
    if one('SELECT 1 FROM enrolments WHERE learner_id=? AND course_id=?',(lid,cid)):
        return jsonify(ok=True)
    db().execute('INSERT INTO enrolments VALUES(?,?)',(lid,cid))
    db().execute('INSERT OR IGNORE INTO portfolios(learner_id,unit_id) SELECT ?,id FROM units WHERE course_id=?',(lid,cid))
    audit('enrolled','learner',lid,str(cid))
    db().commit()
    return jsonify(ok=True)

@bp.post('/api/admin/resources')
@require('admin')
def resource():
    d=request.get_json()
    cid=number(d,'course_id')
    if not one('SELECT id FROM courses WHERE id=?',(cid,)):
        abort(404)
    url=text(d,'url',2000,False)
    try:
        parsed=urlsplit(url)
    except ValueError:
        abort(400,'Enter a valid HTTPS address.')
    if url and (parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password):
        abort(400,'Resource links must be HTTPS web addresses.')
    cur=db().execute('INSERT INTO resources(course_id,title,body,url) VALUES(?,?,?,?)',
        (cid,text(d,'title',200),text(d,'body'),url))
    audit('resource_created','resource',cur.lastrowid)
    db().commit()
    return jsonify(ok=True),201
