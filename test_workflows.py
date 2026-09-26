import io
import json
import tempfile
import unittest
from pathlib import Path
from werkzeug.security import generate_password_hash
from hf import create_app
from hf.db import db

PASSWORD='A test passphrase for HF 2026!'

class Workflows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashed=generate_password_hash(PASSWORD,method='scrypt')

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        root=Path(self.temp.name)
        self.app=create_app({'TESTING':True,'DATABASE':str(root/'test.sqlite'),'UPLOADS':str(root/'uploads'),'SECURE_COOKIES':False})
        with self.app.app_context():
            for name,role in [('Owner','admin'),('Learner A','learner'),('Learner B','learner'),('Assessor','assessor'),('Quality','iqa')]:
                db().execute('INSERT INTO users(name,email,password,role,must_change) VALUES(?,?,?,?,0)',(name,name.replace(' ','').lower()+'@example.test',self.hashed,role))
            db().execute("INSERT INTO courses VALUES(1,'Barbering test course','Test only')")
            db().execute('INSERT INTO units VALUES(1,1,?,?,?,?)',('HF1','Consultation','Test aim',json.dumps(['Consult','Record'])))
            for lid in (2,3):
                db().execute('INSERT INTO enrolments VALUES(?,1)',(lid,))
                db().execute('INSERT INTO portfolios(learner_id,unit_id) VALUES(?,1)',(lid,))
            db().execute('INSERT INTO assignments VALUES(4,2)')
            db().execute('INSERT INTO assignments VALUES(5,2)')
            db().commit()

    def tearDown(self):
        self.temp.cleanup()

    def login(self,name):
        c=self.app.test_client()
        r=c.post('/api/login',json={'email':name+'@example.test','password':PASSWORD})
        self.assertEqual(r.status_code,200,r.json)
        csrf=c.get('/api/me').json['csrf']
        return c,{'X-CSRF-Token':csrf}

    def save_submit(self,c,h):
        r=c.post('/api/portfolio/1/save',headers=h,json={'version':0,'objectives':'Agree a service','service':'Consulted and cut hair','went_well':'Client consultation','improve':'Work on sectioning','criteria':[0]})
        self.assertEqual(r.status_code,200,r.json)
        r=c.post('/api/portfolio/1/submit',headers=h,json={'version':1})
        self.assertEqual(r.status_code,200,r.json)

    def test_anonymous_and_csrf(self):
        c=self.app.test_client()
        self.assertEqual(c.get('/api/learners').status_code,401)
        c,h=self.login('learnera')
        self.assertEqual(c.post('/api/logout',json={}).status_code,403)
        self.assertEqual(c.post('/api/logout',headers=h,json={}).status_code,200)
        self.assertEqual(c.get('/api/me').status_code,401)

    def test_learner_and_staff_isolation(self):
        for name in ('learnera','assessor','quality'):
            c,h=self.login(name)
            self.assertEqual(c.get('/api/learners/2').status_code,200)
            self.assertEqual(c.get('/api/learners/3').status_code,403)
            self.assertEqual(c.get('/api/portfolio/2').status_code,403)
            self.assertEqual(c.get('/api/admin').status_code,403)
            self.assertEqual(c.post('/api/admin/users',headers=h,json={}).status_code,403)

    def test_full_assessment_and_iqa_history(self):
        c,h=self.login('learnera');self.save_submit(c,h)
        self.assertEqual(c.post('/api/portfolio/1/save',headers=h,json={'version':2}).status_code,409)
        self.assertEqual(c.post('/api/portfolio/1/decision',headers=h,json={}).status_code,403)
        assessor,ah=self.login('assessor')
        r=assessor.post('/api/portfolio/1/decision',headers=ah,json={'version':2,'kind':'assessment','outcome':'assessed','checks':[0],'feedback':'Observed safe, accurate work.'})
        self.assertEqual(r.status_code,200,r.json)
        iqa,ih=self.login('quality')
        r=iqa.post('/api/portfolio/1/decision',headers=ih,json={'version':3,'kind':'iqa','outcome':'verified','feedback':'Sample supports the decision.'})
        self.assertEqual(r.status_code,200,r.json)
        self.assertEqual(r.json['status'],'verified')
        self.assertEqual(len(r.json['decisions']),3)
        self.assertEqual(c.get('/api/portfolio/1').json['status'],'verified')

    def test_independent_iqa(self):
        c,h=self.login('learnera');self.save_submit(c,h)
        a,ah=self.login('owner')
        self.assertEqual(a.post('/api/portfolio/1/decision',headers=ah,json={'version':2,'kind':'assessment','outcome':'assessed','checks':[0],'feedback':'Meets outline.'}).status_code,200)
        self.assertEqual(a.post('/api/portfolio/1/decision',headers=ah,json={'version':3,'kind':'iqa','outcome':'verified','feedback':'Same assessor'}).status_code,403)

    def test_return_and_resubmit(self):
        c,h=self.login('learnera');self.save_submit(c,h)
        a,ah=self.login('assessor')
        r=a.post('/api/portfolio/1/decision',headers=ah,json={'version':2,'kind':'assessment','outcome':'returned','feedback':'Explain aftercare.'})
        self.assertEqual(r.status_code,200,r.json)
        r=c.post('/api/portfolio/1/save',headers=h,json={'version':3,'objectives':'Consult','service':'Cut','went_well':'Outline','improve':'Aftercare','aftercare':'Daily maintenance'})
        self.assertEqual(r.status_code,200,r.json)
        self.assertEqual(c.post('/api/portfolio/1/submit',headers=h,json={'version':4}).status_code,200)
        self.assertEqual(len(c.get('/api/portfolio/1').json['decisions']),3)

    def test_stale_version_and_required_fields(self):
        c,h=self.login('learnera')
        self.assertEqual(c.post('/api/portfolio/1/save',headers=h,json={'version':99}).status_code,409)
        self.assertEqual(c.post('/api/portfolio/1/submit',headers=h,json={'version':0}).status_code,400)
        self.assertEqual(c.post('/api/portfolio/1/save',headers=h,json={'version':0,'criteria':[100]}).status_code,400)

    def test_real_private_file_download(self):
        c,h=self.login('learnera')
        payload=b'%PDF-1.4\nTest attachment only\n%%EOF'
        r=c.post('/api/portfolio/1/files',headers=h,data={'version':'0','file':(io.BytesIO(payload),'worksheet.pdf')})
        self.assertEqual(r.status_code,201,r.json)
        fid=r.json['evidence'][0]['id']
        r=c.get('/api/files/'+str(fid))
        self.assertEqual(r.data,payload)
        self.assertIn('attachment',r.headers['Content-Disposition'])
        r.close()
        other,oh=self.login('learnerb')
        self.assertEqual(other.get('/api/files/'+str(fid)).status_code,403)
        self.assertEqual(self.app.test_client().get('/api/files/'+str(fid)).status_code,401)
        self.assertEqual(c.post('/api/portfolio/1/files',headers=h,data={'version':'1','file':(io.BytesIO(b'<script>bad</script>'),'bad.pdf')}).status_code,400)

    def test_admin_setup_and_enrolment(self):
        a,h=self.login('owner')
        r=a.post('/api/admin/users',headers=h,json={'name':'New learner','email':'new@example.test','role':'learner','password':PASSWORD})
        self.assertEqual(r.status_code,201,r.json)
        lid=r.json['id']
        self.assertEqual(a.post('/api/admin/enrolments',headers=h,json={'learner_id':lid,'course_id':1}).status_code,200)
        self.assertEqual(len(a.get('/api/learners/'+str(lid)).json['units']),1)
        self.assertEqual(a.post('/api/admin/assignments',headers=h,json={'staff_id':4,'learner_id':lid}).status_code,200)
        self.assertEqual(a.post('/api/admin/units',headers=h,json={'id':1,'course_id':1,'ref':'X','title':'X','aim':'X','criteria':'New requirement'}).status_code,409)

    def test_disable_revokes_session_and_reset_forces_change(self):
        c,h=self.login('learnera');a,ah=self.login('owner')
        self.assertEqual(a.post('/api/admin/users/2',headers=ah,json={'action':'disable'}).status_code,200)
        self.assertEqual(c.get('/api/me').status_code,401)
        self.assertEqual(a.post('/api/admin/users/1',headers=ah,json={'action':'disable'}).status_code,400)
        a.post('/api/admin/users/2',headers=ah,json={'action':'enable'})
        a.post('/api/admin/users/2',headers=ah,json={'action':'password','password':PASSWORD})
        c,h=self.login('learnera')
        self.assertEqual(c.get('/api/learners').status_code,403)
        self.assertEqual(c.post('/api/password',headers=h,json={'current_password':PASSWORD,'new_password':PASSWORD+'new'}).status_code,200)
        self.assertEqual(c.get('/api/me').status_code,401)

    def test_attendance_and_hours(self):
        c,h=self.login('learnera');a,ah=self.login('assessor')
        self.assertEqual(c.post('/api/learners/2/attendance',headers=h,json={}).status_code,403)
        self.assertEqual(a.post('/api/learners/2/attendance',headers=ah,json={'day':'2026-09-01','status':'present','minutes':360}).status_code,200)
        self.assertEqual(a.post('/api/learners/2/attendance',headers=ah,json={'day':'2026-09-01','status':'absent','minutes':360}).status_code,400)
        self.assertEqual(c.post('/api/learners/2/hours',headers=h,json={'day':'2026-09-01','minutes':60,'activity':'Scissor control','reflection':'Improved sectioning'}).status_code,201)
        self.assertEqual(c.post('/api/hours/1/review',headers=h,json={}).status_code,403)
        self.assertEqual(a.post('/api/hours/1/review',headers=ah,json={'status':'approved','feedback':'Relevant supervised learning'}).status_code,200)
        self.assertEqual(a.post('/api/hours/1/review',headers=ah,json={'status':'rejected','feedback':'Changed'}).status_code,409)

    def test_review_and_resource(self):
        c,h=self.login('learnera');a,ah=self.login('owner')
        self.assertEqual(a.post('/api/learners/2/reviews',headers=ah,json={'review_date':'2026-09-01','next_date':'2026-10-01','strengths':'Client care','actions':'Improve sectioning by next month'}).status_code,201)
        self.assertEqual(c.post('/api/reviews/1/acknowledge',headers=h,json={}).status_code,200)
        self.assertEqual(c.post('/api/reviews/1/acknowledge',headers=h,json={}).status_code,409)
        self.assertEqual(a.post('/api/admin/resources',headers=ah,json={'course_id':1,'title':'Unsafe URL','body':'Test','url':'javascript:alert(1)'}).status_code,400)
        self.assertEqual(a.post('/api/admin/resources',headers=ah,json={'course_id':1,'title':'Consultation','body':'Use open questions','url':'https://example.org/lesson'}).status_code,201)
        self.assertEqual(len(c.get('/api/learners/2').json['resources']),1)

    def test_rate_limit_and_headers(self):
        c=self.app.test_client()
        for _ in range(10):
            r=c.post('/api/login',json={'email':'missing@example.test','password':'wrong'})
            self.assertEqual(r.status_code,401)
        self.assertEqual(c.post('/api/login',json={'email':'missing@example.test','password':'wrong'}).status_code,429)
        response=c.get('/')
        self.assertIn("script-src 'self'",response.headers['Content-Security-Policy'])
        response.close()

    def test_repeated_services_and_assessor_checks(self):
        c,h=self.login('learnera')
        self.assertEqual(c.post('/api/portfolio/1/new-record',headers=h,json={}).status_code,409)
        r=c.post('/api/portfolio/1/save',headers=h,json={'version':0,'objectives':'Cut','service':'Short cut','went_well':'Balance','improve':'Timing','ranges':{'length':['Short'],'texture':['Curly']},'criteria':[0]})
        self.assertEqual(r.status_code,200,r.json)
        self.assertEqual(r.json['fields']['ranges']['length'],['Short'])
        c.post('/api/portfolio/1/submit',headers=h,json={'version':1})
        a,ah=self.login('assessor')
        d={'version':2,'kind':'assessment','outcome':'assessed','feedback':'Consultation observed','checks':[]}
        self.assertEqual(a.post('/api/portfolio/1/decision',headers=ah,json=d).status_code,400)
        d['checks']=[0]
        r=a.post('/api/portfolio/1/decision',headers=ah,json=d)
        self.assertEqual(r.status_code,200,r.json)
        self.assertEqual(json.loads(r.json['decisions'][0]['checks']),[0])
        r=c.post('/api/portfolio/1/new-record',headers=h,json={})
        self.assertEqual(r.status_code,201,r.json)
        self.assertEqual(c.get('/api/portfolio/'+str(r.json['id'])).json['fields'],{})
        self.assertEqual(c.get('/api/portfolio/1').json['status'],'assessed')

    def test_course_boundaries_exams_and_empty_courses(self):
        a,ah=self.login('owner');c,h=self.login('learnera');b,bh=self.login('learnerb')
        r=a.post('/api/admin/courses',headers=ah,json={'title':'VTCT pending','description':'Empty course area'})
        cid=r.json['id']
        self.assertEqual(a.post('/api/admin/enrolments',headers=ah,json={'learner_id':2,'course_id':cid}).status_code,200)
        self.assertEqual(len(c.get('/api/learners/2').json['courses']),2)
        self.assertEqual(len(b.get('/api/learners/3').json['courses']),1)
        exam={'unit_id':1,'day':'2026-09-01','outcome':'pass','reference':'Fictional result 001'}
        self.assertEqual(c.post('/api/learners/2/exams',headers=h,json=exam).status_code,403)
        self.assertEqual(a.post('/api/learners/2/exams',headers=ah,json=exam).status_code,201)
        self.assertEqual(c.get('/api/learners/2').json['exams'][0]['outcome'],'pass')
        self.assertEqual(b.get('/api/learners/2/export').status_code,403)
        self.assertEqual(c.get('/api/learners/2/export').status_code,200)
        self.assertEqual(a.post('/api/admin/enrolments',headers=ah,json={'learner_id':2,'course_id':1}).status_code,200)
        self.assertEqual(len(c.get('/api/learners/2').json['units']),1)
        self.assertEqual(b.post('/api/learners/3/hours',headers=bh,json={'day':'2026-09-01','minutes':60,'activity':'Shadowing','reflection':'Learned sectioning','category':'placement','course_id':cid}).status_code,403)

    def test_range_validation_and_separate_hours(self):
        c,h=self.login('learnera')
        self.assertEqual(c.post('/api/portfolio/1/save',headers=h,json={'version':0,'ranges':{'length':['Invented']}}).status_code,400)
        self.assertEqual(c.post('/api/learners/2/hours',headers=h,json={'day':'2026-09-01','minutes':360,'activity':'Shadowing','reflection':'Observed consultations','category':'placement','course_id':1}).status_code,201)
        self.assertEqual(c.get('/api/learners/2').json['hours'][0]['category'],'placement')

if __name__=='__main__':
    unittest.main()
