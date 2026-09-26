"""Create fictional demonstration accounts in a new, explicitly selected data directory."""
import getpass
import json
import os
from pathlib import Path
from werkzeug.security import generate_password_hash
from hf import create_app
from hf.db import db, one

if __name__ == '__main__':
    if not os.environ.get('HF_DATA_DIR'):
        raise SystemExit('Set HF_DATA_DIR to a new demo directory first. See START-HERE.html.')
    app=create_app()
    with app.app_context():
        if one('SELECT id FROM users LIMIT 1') or one('SELECT id FROM courses LIMIT 1'):
            raise SystemExit('Demo setup requires an empty data directory; nothing changed.')
        password=getpass.getpass('Choose demo passphrase (14–128 characters): ')
        if not 14<=len(password)<=128 or password!=getpass.getpass('Repeat passphrase: '):
            raise SystemExit('Passphrases must match and contain 14–128 characters.')
        hashed=generate_password_hash(password,method='scrypt')
        for name,email,role in [('Demo Administrator','admin@demo.invalid','admin'),('Demo Learner','learner@demo.invalid','learner'),('Demo Assessor','assessor@demo.invalid','assessor'),('Demo IQA','iqa@demo.invalid','iqa')]:
            db().execute('INSERT INTO users(name,email,password,role,must_change) VALUES(?,?,?,?,0)',(name,email,hashed,role))
        db().execute("INSERT INTO courses VALUES(1,'VRQ Level 2 — selected barbering units (DEMO)','Fictional demonstration. Draft centre criteria, not approved assessment content.')")
        for u in json.loads((Path(__file__).parent/'hf/units.json').read_text()):
            db().execute('INSERT INTO units(course_id,ref,title,aim,criteria) VALUES(1,?,?,?,?)',(u['ref'],u['title'],u['aim'],json.dumps(u['criteria'])))
        db().execute("INSERT INTO courses VALUES(2,'City & Guilds Level 2 Apprenticeship — content pending','Add confirmed qualification units before assessment.')")
        db().execute("INSERT INTO courses VALUES(3,'VTCT Barbering — content pending','Empty course area as requested.')")
        db().execute('INSERT INTO enrolments VALUES(2,1)')
        db().execute('INSERT INTO portfolios(learner_id,unit_id) SELECT 2,id FROM units WHERE course_id=1')
        db().execute('INSERT INTO assignments VALUES(3,2)')
        db().execute('INSERT INTO assignments VALUES(4,2)')
        db().commit()
        print('Fictional demo ready. Accounts: admin@demo.invalid, learner@demo.invalid, assessor@demo.invalid, iqa@demo.invalid. Use the passphrase you chose. Never use demo accounts for real learner records.')
