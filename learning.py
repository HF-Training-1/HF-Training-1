from datetime import date
from flask import Blueprint, abort, g, jsonify, request
from .auth import learner_access, require, number, text
from .db import db, one, rows, audit

bp = Blueprint('learning', __name__)

def valid_date(data,key):
    value = text(data,key,10)
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat()!=value:
            raise ValueError()
    except ValueError:
        abort(400,f'Invalid {key}.')
    return value

@bp.get('/api/learners')
def learners():
    if g.user['role']=='learner':
        result = rows("SELECT id,name,email FROM users WHERE id=?", (g.user['id'],))
    elif g.user['role']=='admin':
        result = rows("SELECT id,name,email FROM users WHERE role='learner' AND active=1 ORDER BY name")
    else:
        result = rows('''SELECT u.id,u.name,u.email FROM users u JOIN assignments a ON u.id=a.learner_id
                        WHERE a.staff_id=? AND u.active=1 ORDER BY u.name''',(g.user['id'],))
    return jsonify(result)

@bp.get('/api/learners/<int:lid>')
def learner(lid):
    who = learner_access(lid)
    units = rows('''SELECT p.id,p.status,p.version,p.updated,u.id unit_id,u.course_id,u.ref,u.title,u.aim,u.criteria,c.title course
        FROM portfolios p JOIN units u ON u.id=p.unit_id JOIN courses c ON c.id=u.course_id
        WHERE p.learner_id=? ORDER BY c.id,u.id''',(lid,))
    return jsonify(learner=who,units=units,
        courses=rows('SELECT c.* FROM courses c JOIN enrolments e ON e.course_id=c.id WHERE e.learner_id=?',(lid,)),
        exams=rows('SELECT e.*,u.ref,u.title FROM exams e JOIN units u ON e.unit_id=u.id WHERE e.learner_id=? ORDER BY e.id DESC',(lid,)),
        attendance=rows('SELECT * FROM attendance WHERE learner_id=? ORDER BY day DESC',(lid,)),
        hours=rows('SELECT * FROM hours WHERE learner_id=? ORDER BY day DESC,id DESC',(lid,)),
        reviews=rows('''SELECT r.*,u.name author FROM reviews r JOIN users u ON r.actor=u.id
                        WHERE learner_id=? ORDER BY review_date DESC,r.id DESC''',(lid,)),
        resources=rows('''SELECT r.*,c.title course FROM resources r JOIN courses c ON r.course_id=c.id
                    JOIN enrolments e ON e.course_id=r.course_id WHERE e.learner_id=? ORDER BY r.id DESC''',(lid,)))

@bp.post('/api/learners/<int:lid>/attendance')
@require('admin','assessor')
def attendance(lid):
    learner_access(lid)
    d = request.get_json()
    day = valid_date(d,'day')
    status = text(d,'status',20)
    minutes = number(d,'minutes',0,1440)
    if status not in ('present','late','absent','authorised') or (status in ('absent','authorised') and minutes!=0):
        abort(400,'Choose a valid attendance status. Absence must have zero minutes.')
    db().execute('''INSERT INTO attendance(learner_id,day,status,minutes,note,actor) VALUES(?,?,?,?,?,?)
        ON CONFLICT(learner_id,day) DO UPDATE SET status=excluded.status,minutes=excluded.minutes,
        note=excluded.note,actor=excluded.actor''',(lid,day,status,minutes,text(d,'note',2000,False),g.user['id']))
    audit('attendance_recorded','learner',lid,f'{day}: {status}, {minutes} minutes')
    db().commit()
    return jsonify(ok=True)

@bp.post('/api/learners/<int:lid>/hours')
@require('learner')
def hours(lid):
    learner_access(lid)
    d = request.get_json()
    day = valid_date(d,'day')
    if day>date.today().isoformat():
        abort(400,'Learning hours cannot be recorded in the future.')
    minutes = number(d,'minutes',1,1440)
    db().execute('BEGIN IMMEDIATE')
    existing = one("SELECT COALESCE(SUM(minutes),0) n FROM hours WHERE learner_id=? AND day=? AND status!='rejected'",(lid,day))['n']
    if existing+minutes>1440:
        abort(400,'Daily hours cannot exceed 24.')
    category=text(d,'category',30,False) or 'academy'
    if category not in ('academy','placement','other'):
        abort(400,'Invalid learning category.')
    cid=number(d,'course_id') if d.get('course_id') else None
    if cid and not one('SELECT 1 FROM enrolments WHERE learner_id=? AND course_id=?',(lid,cid)):
        abort(403,'Not enrolled on this course.')
    cur = db().execute('INSERT INTO hours(learner_id,day,minutes,activity,reflection,category,course_id) VALUES(?,?,?,?,?,?,?)',
        (lid,day,minutes,text(d,'activity',2000),text(d,'reflection',5000),category,cid))
    audit('hours_submitted','hours',cur.lastrowid)
    db().commit()
    return jsonify(ok=True),201

@bp.post('/api/hours/<int:hid>/review')
@require('admin','assessor')
def hours_review(hid):
    db().execute('BEGIN IMMEDIATE')
    h = one('SELECT * FROM hours WHERE id=?',(hid,))
    if not h:
        abort(404)
    learner_access(h['learner_id'])
    d = request.get_json()
    status = text(d,'status',20)
    if status not in ('approved','rejected') or h['status']!='pending':
        abort(409,'Only pending hours can be reviewed.')
    feedback = text(d,'feedback',2000)
    db().execute('UPDATE hours SET status=?,reviewer=?,feedback=? WHERE id=?',(status,g.user['id'],feedback,hid))
    audit('hours_'+status,'hours',hid)
    db().commit()
    return jsonify(ok=True)

@bp.post('/api/learners/<int:lid>/reviews')
@require('admin','assessor')
def review(lid):
    learner_access(lid)
    d = request.get_json()
    day, next_day = valid_date(d,'review_date'),valid_date(d,'next_date')
    if next_day<=day:
        abort(400,'Next review must be after this review.')
    cur=db().execute('INSERT INTO reviews(learner_id,review_date,next_date,strengths,actions,actor) VALUES(?,?,?,?,?,?)',
        (lid,day,next_day,text(d,'strengths'),text(d,'actions'),g.user['id']))
    audit('review_created','review',cur.lastrowid)
    db().commit()
    return jsonify(ok=True),201

@bp.post('/api/reviews/<int:rid>/acknowledge')
@require('learner')
def acknowledge(rid):
    r=one('SELECT * FROM reviews WHERE id=?',(rid,))
    if not r:
        abort(404)
    learner_access(r['learner_id'])
    if r['acknowledged']:
        abort(409,'Already acknowledged.')
    db().execute('UPDATE reviews SET acknowledged=CURRENT_TIMESTAMP WHERE id=?',(rid,))
    audit('review_acknowledged','review',rid)
    db().commit()
    return jsonify(ok=True)

@bp.post('/api/learners/<int:lid>/exams')
@require('admin','assessor')
def exam(lid):
    learner_access(lid)
    d=request.get_json()
    uid=number(d,'unit_id')
    if not one('SELECT 1 FROM units u JOIN enrolments e ON e.course_id=u.course_id WHERE u.id=? AND e.learner_id=?',(uid,lid)):
        abort(403,'The learner is not enrolled on this unit.')
    outcome=text(d,'outcome',30)
    if outcome not in ('pass','fail','pending'):
        abort(400,'Choose pass, fail or pending.')
    day=valid_date(d,'day')
    if day>date.today().isoformat():
        abort(400,'Exam results cannot be dated in the future.')
    cur=db().execute('INSERT INTO exams(learner_id,unit_id,day,outcome,reference,actor) VALUES(?,?,?,?,?,?)',
        (lid,uid,day,outcome,text(d,'reference',1000),g.user['id']))
    audit('exam_result_recorded','exam',cur.lastrowid)
    db().commit()
    return jsonify(ok=True),201

@bp.get('/api/learners/<int:lid>/export')
def export(lid):
    learner_access(lid)
    from .portfolio import load_portfolio
    payload=learner(lid).get_json()
    payload['portfolios']=[load_portfolio(p['id']) for p in payload['units']]
    response=jsonify(payload)
    response.headers['Content-Disposition']=f'attachment; filename=learner-{lid}-records.json'
    return response
