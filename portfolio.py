import hashlib
import json
import secrets
from pathlib import Path
from flask import Blueprint, abort, current_app, g, jsonify, request, send_file
from werkzeug.utils import secure_filename
from .auth import learner_access, number, require, text
from .db import db, one, rows, audit

bp = Blueprint('portfolio', __name__)
RANGES = {'length': ['Short','Mid-length','Long'],
          'texture': ['Straight','Wavy','Curly','Coily'],
          'technique': ['Scissor-over-comb','Clipper-over-comb','Club cutting','Graduation','Layering','Fading','Tapering','Freehand'],
          'facial_hair': ['Moustache','Partial beard','Full beard']}

FIELDS = ('client_reference','service_date','objectives','analysis','tools','health_safety','communication',
          'practical_range','service','time_taken','functional_skills','went_well','improve','aftercare')

def load_portfolio(pid):
    p = one('SELECT * FROM portfolios WHERE id=?', (pid,))
    if not p:
        abort(404, 'Portfolio not found.')
    learner_access(p['learner_id'])
    if not one('SELECT 1 FROM enrolments e JOIN units u ON u.course_id=e.course_id WHERE e.learner_id=? AND u.id=?',(p['learner_id'],p['unit_id'])):
        abort(403,'No enrolment for this course.')
    p['fields'] = json.loads(p['fields'])
    p['evidence'] = rows('SELECT id,filename,size,sha256,created FROM evidence WHERE portfolio_id=?', (pid,))
    p['decisions'] = rows('''SELECT d.id,d.kind,d.outcome,d.feedback,d.checks,d.version,d.created,u.name
        FROM decisions d JOIN users u ON u.id=d.actor WHERE portfolio_id=? ORDER BY d.id DESC''', (pid,))
    p['range_options'] = RANGES
    p['unit'] = one('SELECT * FROM units WHERE id=?',(p['unit_id'],))
    return p

def check_version(p, data):
    if number(data,'version',0) != p['version']:
        abort(409, 'This record changed in another session. Reload before editing.')

def editable(p):
    if g.user['role'] != 'learner' or p['learner_id'] != g.user['id']:
        abort(403, 'Only the learner can edit their evidence.')
    if p['status'] not in ('draft', 'returned'):
        abort(409, 'Submitted work is locked. Ask your assessor to return it.')

@bp.get('/api/portfolio/<int:pid>')
def detail(pid):
    return jsonify(load_portfolio(pid))

@bp.post('/api/portfolio/<int:pid>/save')
@require('learner')
def save(pid):
    db().execute('BEGIN IMMEDIATE')
    p = load_portfolio(pid)
    editable(p)
    data = request.get_json()
    check_version(p, data)
    fields = {key: text(data,key,10000,False) for key in FIELDS}
    criteria = data.get('criteria', [])
    unit = one('SELECT criteria FROM units WHERE id=?', (p['unit_id'],))
    count = len(json.loads(unit['criteria']))
    if not isinstance(criteria,list) or any(type(i) is not int or i<0 or i>=count for i in criteria):
        abort(400, 'Invalid criteria checklist.')
    fields['criteria'] = sorted(set(criteria))
    selected=data.get('ranges',{})
    if not isinstance(selected,dict) or set(selected)-set(RANGES):
        abort(400,'Invalid practical ranges.')
    for key, values in selected.items():
        if not isinstance(values,list) or any(not isinstance(v,str) or v not in RANGES[key] for v in values):
            abort(400,'Invalid practical range selection.')
    fields['ranges']={key:sorted(set(values)) for key,values in selected.items()}
    db().execute('UPDATE portfolios SET fields=?,version=version+1,updated=CURRENT_TIMESTAMP WHERE id=?', (json.dumps(fields),pid))
    audit('draft_saved','portfolio',pid)
    db().commit()
    return jsonify(load_portfolio(pid))

@bp.post('/api/portfolio/<int:pid>/submit')
@require('learner')
def submit(pid):
    db().execute('BEGIN IMMEDIATE')
    p = load_portfolio(pid)
    editable(p)
    check_version(p, request.get_json())
    if not all(p['fields'].get(k,'').strip() for k in ('objectives','service','went_well','improve')):
        abort(400,'Complete service objectives, service carried out, what went well and your next steps first.')
    db().execute("UPDATE portfolios SET status='submitted',version=version+1,updated=CURRENT_TIMESTAMP WHERE id=?", (pid,))
    db().execute('INSERT INTO decisions(portfolio_id,actor,kind,outcome,feedback,version,snapshot) VALUES(?,?,?,?,?,?,?)',
        (pid,g.user['id'],'submission','submitted','Learner submitted for assessment',p['version']+1,json.dumps(p)))
    audit('submitted','portfolio',pid)
    db().commit()
    return jsonify(load_portfolio(pid))

@bp.post('/api/portfolio/<int:pid>/decision')
@require('assessor','iqa','admin')
def decision(pid):
    db().execute('BEGIN IMMEDIATE')
    p = load_portfolio(pid)
    data = request.get_json()
    check_version(p,data)
    kind = text(data,'kind',20)
    outcome = text(data,'outcome',30)
    feedback = text(data,'feedback')
    role = g.user['role']
    if kind == 'assessment' and role in ('assessor','admin'):
        if p['status'] not in ('submitted','iqa_action','assessed') or outcome not in ('assessed','returned'):
            abort(409, 'This assessment action is not available.')
        if p['status']=='assessed' and outcome!='returned':
            abort(409,'This work has already been assessed.')
    elif kind == 'iqa' and role in ('iqa','admin'):
        if p['status'] != 'assessed' or outcome not in ('verified','iqa_action'):
            abort(409, 'Only assessed work can be sampled by IQA.')
        last = one("SELECT actor FROM decisions WHERE portfolio_id=? AND kind='assessment' ORDER BY id DESC LIMIT 1", (pid,))
        if not last or last['actor'] == g.user['id']:
            abort(403, 'An independent IQA must sample this assessment.')
    else:
        abort(403, 'Your role cannot make this decision.')
    checks = data.get('checks', [])
    count = len(json.loads(p['unit']['criteria']))
    if not isinstance(checks,list) or any(type(i) is not int or i<0 or i>=count for i in checks):
        abort(400,'Invalid assessor criteria.')
    if kind=='assessment' and outcome=='assessed' and not checks:
        abort(400,'Select the criteria demonstrated in this assessment.')
    if kind=='iqa':
        checks=[]
    db().execute('INSERT INTO decisions(portfolio_id,actor,kind,outcome,feedback,version,snapshot,checks) VALUES(?,?,?,?,?,?,?,?)',
        (pid,g.user['id'],kind,outcome,feedback,p['version'],json.dumps(p),json.dumps(sorted(set(checks)))))
    db().execute('UPDATE portfolios SET status=?,version=version+1,updated=CURRENT_TIMESTAMP WHERE id=?', (outcome,pid))
    audit(outcome,'portfolio',pid)
    db().commit()
    return jsonify(load_portfolio(pid))

@bp.post('/api/portfolio/<int:pid>/files')
@require('learner')
def upload(pid):
    db().execute('BEGIN IMMEDIATE')
    p = load_portfolio(pid)
    editable(p)
    check_version(p,request.form)
    f = request.files.get('file')
    if not f:
        abort(400,'Select a file.')
    filename = secure_filename(f.filename or '')[:180]
    ext = Path(filename).suffix.lower()
    data = f.read(10*1024*1024+1)
    signatures = {'.pdf': data.startswith(b'%PDF-'),'.png':data.startswith(b'\x89PNG\r\n\x1a\n'),
                  '.jpg':data.startswith(b'\xff\xd8\xff'),'.jpeg':data.startswith(b'\xff\xd8\xff')}
    if len(data)>10*1024*1024 or not signatures.get(ext):
        abort(400,'Use a valid PDF, PNG or JPEG under 10 MB.')
    if len(p['evidence'])>=20:
        abort(400,'Maximum 20 attachments per unit in this version.')
    stored = secrets.token_hex(24)
    target = Path(current_app.config['UPLOADS'])/stored
    target.write_bytes(data)
    try:
        db().execute('INSERT INTO evidence(portfolio_id,filename,stored,sha256,size) VALUES(?,?,?,?,?)',
            (pid,filename,stored,hashlib.sha256(data).hexdigest(),len(data)))
        db().execute('UPDATE portfolios SET version=version+1,updated=CURRENT_TIMESTAMP WHERE id=?',(pid,))
        audit('evidence_uploaded','portfolio',pid)
        db().commit()
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return jsonify(load_portfolio(pid)),201

@bp.get('/api/files/<int:fid>')
def download(fid):
    f = one('SELECT * FROM evidence WHERE id=?', (fid,))
    if not f:
        abort(404)
    load_portfolio(f['portfolio_id'])
    return send_file(Path(current_app.config['UPLOADS'])/f['stored'],as_attachment=True,download_name=f['filename'],mimetype='application/octet-stream')

@bp.post('/api/portfolio/<int:pid>/new-record')
@require('learner','assessor','admin')
def new_record(pid):
    db().execute('BEGIN IMMEDIATE')
    p=load_portfolio(pid)
    if one("SELECT id FROM portfolios WHERE learner_id=? AND unit_id=? AND status IN ('draft','returned')",(p['learner_id'],p['unit_id'])):
        abort(409,'Finish the existing draft for this unit before adding another service.')
    cur=db().execute('INSERT INTO portfolios(learner_id,unit_id) VALUES(?,?)',(p['learner_id'],p['unit_id']))
    audit('service_record_created','portfolio',cur.lastrowid)
    db().commit()
    return jsonify(id=cur.lastrowid),201
