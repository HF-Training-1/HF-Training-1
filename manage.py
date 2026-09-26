"""Local operator tools. No default credentials; never upload the instance directory."""
import argparse
import getpass
import json
from pathlib import Path
from werkzeug.security import generate_password_hash
from hf import create_app
from hf.db import db, one

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['init','admin','reset-password','serve'])
    args=parser.parse_args()
    app=create_app()
    with app.app_context():
        if args.command=='init':
            if one('SELECT id FROM courses LIMIT 1'):
                print('Courses already exist; no changes made.')
                return
            c=db().execute('INSERT INTO courses(title,description) VALUES(?,?)',
                ('VRQ Level 2 — selected barbering units (3002)','Five academy-selected units. Exact award and complete assessment mapping require centre confirmation. Weekly plan: 18 placement hours and 6 academy hours; duration agreed per learner.'))
            units=json.loads((Path(__file__).parent/'hf'/'units.json').read_text())
            for u in units:
                db().execute('INSERT INTO units(course_id,ref,title,aim,criteria) VALUES(?,?,?,?,?)',
                    (c.lastrowid,u['ref'],u['title'],u['aim'],json.dumps(u['criteria'])))
            for title in ('City & Guilds Level 2 Barbering Apprenticeship — content pending','VTCT Barbering — content pending'):
                db().execute('INSERT INTO courses(title,description) VALUES(?,?)',(title,'Course area ready. Add confirmed units and criteria before assessment.'))
            db().commit()
            print('VRQ draft and separate apprenticeship / VTCT course areas created.')
        elif args.command in ('admin','reset-password'):
            email=input('Account email: ').strip().lower()
            if '@' not in email or len(email)>254 or ' ' in email:
                raise SystemExit('Enter a valid email.')
            existing=one('SELECT id FROM users WHERE email=?',(email,))
            if args.command=='admin' and existing:
                raise SystemExit('Account already exists; use reset-password if needed.')
            if args.command=='reset-password' and not existing:
                raise SystemExit('Account not found.')
            name=input('Administrator name: ').strip() if args.command=='admin' else ''
            if args.command=='admin' and not name:
                raise SystemExit('Name required.')
            password=getpass.getpass('New passphrase (14–128 characters): ')
            if not 14<=len(password)<=128 or password!=getpass.getpass('Repeat passphrase: '):
                raise SystemExit('Passwords must match and contain 14–128 characters.')
            hashed=generate_password_hash(password,method='scrypt')
            if existing:
                uid=existing['id']
                db().execute('UPDATE users SET password=?,must_change=1 WHERE id=?',(hashed,uid))
                db().execute('DELETE FROM sessions WHERE user_id=?',(uid,))
            else:
                uid=db().execute("INSERT INTO users(name,email,password,role,must_change) VALUES(?,?,?,'admin',0)",(name,email,hashed)).lastrowid
            db().execute('INSERT INTO audit(action,entity,entity_id,detail) VALUES(?,?,?,?)',
                ('operator_'+args.command,'user',uid,'Server operator command'))
            db().commit()
            print('Account updated. No password has been printed or saved in source files.')
        else:
            if app.config['SECURE_COOKIES']:
                print('For local HTTP testing set HF_LOCAL_HTTP=1 first. Live hosting requires HTTPS.')
            app.run(host='127.0.0.1',port=8000,debug=False)

if __name__=='__main__':
    main()
