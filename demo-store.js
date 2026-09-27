/* GITHUB PAGES DEMONSTRATION ONLY.
 * Everything, including role checks and demo logins, runs in the browser.
 * This is not secure authentication or a shared learner database.
 * Never use real student records or a password you use elsewhere.
 */
import {UNIT_OUTLINES} from './unit-outlines.js';

export const DEMO_PASSWORD='HF-Demo-2026!';
const scope=new URL('./',globalThis.location.href).pathname;
const DB_NAME='hf-training-pages-demo-v4:'+scope;
const SESSION=DB_NAME+':session';
const RANGES={length:['Short','Mid-length','Long'],texture:['Straight','Wavy','Curly','Coily'],technique:['Scissor-over-comb','Clipper-over-comb','Club cutting','Graduation','Layering','Fading','Tapering','Freehand'],facial_hair:['Moustache','Partial beard','Full beard']};
const FIELDS=['client_reference','service_date','objectives','analysis','tools','health_safety','communication','practical_range','service','time_taken','functional_skills','went_well','improve','aftercare'];
const now=()=>new Date().toISOString();
const fail=message=>{throw new Error(message);};
const clone=value=>structuredClone(value);
const publicUser=({password,...u})=>u;
const num=(v,min=1,max=2147483647)=>{const n=Number(v);if(v===''||v===null||typeof v==='boolean'||!Number.isInteger(n)||n<min||n>max)fail('Enter a valid number.');return n;};
const str=(d,k,required=true,max=10000)=>{const v=d[k]??'';if(typeof v!=='string'||v.length>max||(required&&!v.trim()))fail('Please complete '+k.replaceAll('_',' ')+'.');return v.trim();};
const day=(d,k)=>{const s=str(d,k);if(!/^\d{4}-\d{2}-\d{2}$/.test(s)||!Number.isFinite(Date.parse(s))||new Date(s).toISOString().slice(0,10)!==s)fail('Enter a valid date.');return s;};
const id=(table)=>Math.max(0,...table.map(x=>x.id))+1;
const safePassword=p=>{if(typeof p!=='string'||p.length<14||p.length>128)fail('For a new test account use a 14–128 character test passphrase. Do not reuse a real password.');return p;};
const hash=async s=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(s)))).map(b=>b.toString(16).padStart(2,'0')).join('');
let dbPromise;

async function seed(){
 const password=await hash(DEMO_PASSWORD);
 const users=[['Demo Administrator','admin','admin'],['Alex — VRQ demo learner','learner','learner'],['Demo Assessor','assessor','assessor'],['Demo IQA','iqa','iqa'],['Jordan — apprenticeship demo learner','apprentice','learner']].map(([name,email,role],i)=>({id:i+1,name,email:email+'@demo.invalid',role,password,active:1,must_change:0}));
 const courses=[{id:1,title:'VRQ Level 2 Barbering — selected 3002 units',description:'Units 202, 203, 204, 210 and 211. Centre draft checklists for testing; full qualification mapping still needs checking.'},{id:2,title:'City & Guilds Level 2 Barbering Apprenticeship',description:'Separate course area. Official units and criteria have not been added yet.'},{id:3,title:'VTCT Barbering',description:'Empty course area, ready for future content.'}];
 const units=UNIT_OUTLINES.map((u,i)=>({...u,id:i+1,course_id:1,criteria:JSON.stringify(u.criteria)}));
 const portfolios=units.map(u=>({id:u.id,learner_id:2,unit_id:u.id,status:'draft',version:0,fields:{},updated:now()}));
 return {schema:4,users,courses,units,portfolios,enrolments:[{learner_id:2,course_id:1},{learner_id:5,course_id:2}],assignments:[{staff_id:3,learner_id:2},{staff_id:4,learner_id:2},{staff_id:3,learner_id:5},{staff_id:4,learner_id:5}],evidence:[],decisions:[],attendance:[],hours:[],reviews:[],exams:[],resources:[{id:1,course_id:1,title:'Try your first practical record',body:'Sign out, choose the Student demo, open E-portfolio and select a unit. Complete the service notes and reflection, tick the relevant ranges and submit. Then sign in as Assessor to record feedback. All details in this demonstration must be fictional.',url:''}],audit:[]};
}

async function database(){
 if(!dbPromise)dbPromise=new Promise((resolve,reject)=>{
  if(!globalThis.indexedDB){reject(new Error('This browser does not allow local demo storage. Use a normal Chrome window, not a restricted or private session.'));return;}
  const r=indexedDB.open(DB_NAME,1);
  r.onupgradeneeded=()=>r.result.createObjectStore('demo');
  r.onsuccess=()=>{r.result.onversionchange=()=>r.result.close();resolve(r.result);};
  r.onerror=()=>reject(new Error('Could not open demo storage. Check Chrome site-storage settings.'));
 });
 return dbPromise;
}

async function transact(handler,write){
 const db=await database(),initial=await seed();
 return new Promise((resolve,reject)=>{
  const tx=db.transaction('demo','readwrite'),store=tx.objectStore('demo');
  let result,error;
  const get=store.get('state');
  get.onsuccess=()=>{
   try{const data=get.result||initial;result=handler(data);if(write||!get.result)store.put(data,'state');}
   catch(e){error=e;tx.abort();}
  };
  tx.oncomplete=()=>resolve(clone(result));
  tx.onabort=()=>reject(error||new Error('Demo changes could not be saved. Your browser storage may be full.'));
  tx.onerror=()=>{error??=new Error('Could not save local demo data.');};
 });
}

export async function demoRequest(path,method='GET',body={}){
 let d=body??{};
 if(body instanceof FormData){
  const file=body.get('file');
  if(!file||typeof file.arrayBuffer!=='function'||file.size>5*1024*1024)fail('Choose a sample PDF, JPG or PNG under 5 MB.');
  const bytes=new Uint8Array(await file.arrayBuffer());
  const ext=file.name.split('.').pop().toLowerCase();
  const valid=(ext==='pdf'&&new TextDecoder().decode(bytes.slice(0,5))==='%PDF-')||(['jpg','jpeg'].includes(ext)&&bytes[0]===255&&bytes[1]===216&&bytes[2]===255)||(ext==='png'&&[137,80,78,71,13,10,26,10].every((b,i)=>bytes[i]===b));
  if(!valid)fail('Choose a valid sample PDF, JPG or PNG file.');
  d={version:body.get('version'),file:{filename:file.name.slice(0,180),size:file.size,blob:new Blob([bytes],{type:'application/octet-stream'})}};
 }else d=clone(d);
 if(path==='/api/login')d.passwordHash=await hash(String(d.password??''));
 if(path==='/api/admin/users'||(/^\/api\/admin\/users\/\d+$/.test(path)&&d.action==='password'))d.passwordHash=await hash(safePassword(d.password));
 if(path==='/api/password'){d.currentHash=await hash(String(d.current_password??''));d.newHash=await hash(safePassword(d.new_password));}
 const output=await transact(s=>route(s,path,method,d),method!=='GET');
 if(path==='/api/login')sessionStorage.setItem(SESSION,String(output.user_id));
 if(path==='/api/logout'||path==='/api/password')sessionStorage.removeItem(SESSION);
 return output;
}

function route(s,path,method,d){
 const find=(table,uid)=>s[table].find(x=>x.id===Number(uid))||fail('Record not found.');
 if(path==='/api/login'&&method==='POST'){
  const u=s.users.find(u=>u.email===str(d,'email').toLowerCase()&&u.active&&u.password===d.passwordHash);
  if(!u)fail('Demo login not recognised. Use a demo email and HF-Demo-2026!, or reset the demo if you changed it.');
  return {ok:true,user_id:u.id};
 }
 const u=s.users.find(u=>u.id===Number(sessionStorage.getItem(SESSION))&&u.active);
 if(!u)fail('Please sign in to the demo.');
 const require=(...roles)=>{if(!roles.includes(u.role))fail('That action belongs to a different demo role.');};
 const audit=(action,entity,entity_id,detail='')=>s.audit.push({id:id(s.audit),actor:u.id,name:u.name,action,entity,entity_id,detail,created:now()});
 const access=lid=>{const l=find('users',lid);if(l.role!=='learner')fail('Choose a learner.');if(u.role==='admin'||(u.role==='learner'&&u.id===l.id)||(['assessor','iqa'].includes(u.role)&&s.assignments.some(a=>a.staff_id===u.id&&a.learner_id===l.id)))return l;fail('This learner is not assigned to this demo account.');};
 const enrolled=(lid,cid)=>{if(!s.enrolments.some(e=>e.learner_id===lid&&e.course_id===cid))fail('The learner is not enrolled on this course.');};
 const portfolio=pid=>{const p=find('portfolios',pid);access(p.learner_id);enrolled(p.learner_id,find('units',p.unit_id).course_id);return p;};
 const detail=p=>({...p,unit:find('units',p.unit_id),range_options:RANGES,evidence:s.evidence.filter(e=>e.portfolio_id===p.id).map(({blob,...e})=>e),decisions:s.decisions.filter(x=>x.portfolio_id===p.id).slice().reverse().map(({snapshot,...x})=>({...x,name:find('users',x.actor).name}))});
 const editable=p=>{require('learner');if(p.learner_id!==u.id||!['draft','returned'].includes(p.status))fail('Submitted work is locked. Ask the assessor to return it.');};
 const version=p=>{if(num(d.version,0)!==p.version)fail('This record changed. Close and reopen it before editing.');};
 const checks=(value,unit)=>{if(!Array.isArray(value)||value.some(i=>!Number.isInteger(i)||i<0||i>=JSON.parse(unit.criteria).length))fail('Invalid criteria selection.');return [...new Set(value)];};
 const bump=p=>{p.version++;p.updated=now();};
 const recordDecision=(p,kind,outcome,feedback,ticks=[])=>s.decisions.push({id:id(s.decisions),portfolio_id:p.id,actor:u.id,kind,outcome,feedback,version:p.version,checks:JSON.stringify(ticks),created:now(),snapshot:{fields:clone(p.fields),evidence_ids:s.evidence.filter(e=>e.portfolio_id===p.id).map(e=>e.id)}});
 const makePortfolio=(lid,uid)=>{const p={id:id(s.portfolios),learner_id:lid,unit_id:uid,status:'draft',version:0,fields:{},updated:now()};s.portfolios.push(p);return p;};
 if(path==='/api/me')return {user:publicUser(u),csrf:'demo-only'};
 if(path==='/api/logout')return {ok:true};
 if(path==='/api/password'){
  if(u.password!==d.currentHash)fail('Current test password is incorrect.');
  if(d.currentHash===d.newHash)fail('Choose a different test password.');
  u.password=d.newHash;u.must_change=0;audit('test_password_changed','user',u.id);return {ok:true};
 }
 if(u.must_change)fail('Change your temporary test password in My account first.');
 if(path==='/api/learners')return s.users.filter(l=>l.role==='learner'&&l.active&&(u.role==='admin'||l.id===u.id||s.assignments.some(a=>a.staff_id===u.id&&a.learner_id===l.id))).map(publicUser);

 let match=path.match(/^\/api\/learners\/(\d+)(?:\/(\w+))?$/);
 if(match){
  const lid=Number(match[1]),action=match[2],l=access(lid);
  if(method==='GET'){
   const courses=s.courses.filter(c=>s.enrolments.some(e=>e.learner_id===lid&&e.course_id===c.id));
   const units=s.portfolios.filter(p=>p.learner_id===lid&&courses.some(c=>c.id===find('units',p.unit_id).course_id)).map(p=>{const unit=find('units',p.unit_id);return {...unit,id:p.id,unit_id:unit.id,status:p.status,version:p.version,updated:p.updated,course:find('courses',unit.course_id).title};});
   const forLearner=table=>s[table].filter(x=>x.learner_id===lid).slice().reverse();
   const result={learner:publicUser(l),courses,units,attendance:forLearner('attendance'),hours:forLearner('hours'),reviews:forLearner('reviews').map(r=>({...r,author:find('users',r.actor).name})),exams:forLearner('exams').map(e=>({...e,ref:find('units',e.unit_id).ref,title:find('units',e.unit_id).title})),resources:s.resources.filter(r=>courses.some(c=>c.id===r.course_id)).map(r=>({...r,course:find('courses',r.course_id).title}))};
   if(action==='export')return {...result,demo_only:true,note:'Local test records. Evidence metadata only; download sample attachments separately.',portfolios:units.map(x=>detail(portfolio(x.id)))};
   return result;
  }
  if(action==='attendance'){
   require('admin','assessor');const date=day(d,'day'),status=str(d,'status'),minutes=num(d.minutes,0,1440);
   if(!['present','late','absent','authorised'].includes(status)||(['absent','authorised'].includes(status)&&minutes!==0))fail('Absence must have 0 minutes; choose a valid status.');
   const existing=s.attendance.find(a=>a.learner_id===lid&&a.day===date),values={learner_id:lid,day:date,status,minutes,note:str(d,'note',false),actor:u.id};
   if(existing)Object.assign(existing,values);else s.attendance.push({id:id(s.attendance),...values});audit('attendance_recorded','learner',lid,date);return {ok:true};
  }
  if(action==='hours'){
   require('learner');const date=day(d,'day'),minutes=num(d.minutes,1,1440),category=str(d,'category'),cid=num(d.course_id);
   enrolled(lid,cid);if(date>new Date().toLocaleDateString('en-CA'))fail('Do not log future learning hours.');
   if(!['academy','placement','other'].includes(category))fail('Choose a learning category.');
   if(minutes+s.hours.filter(h=>h.learner_id===lid&&h.day===date&&h.status!=='rejected').reduce((n,h)=>n+h.minutes,0)>1440)fail('A day cannot contain more than 24 learning hours.');
   s.hours.push({id:id(s.hours),learner_id:lid,day:date,minutes,category,course_id:cid,activity:str(d,'activity'),reflection:str(d,'reflection'),status:'pending',feedback:'',reviewer:null});audit('hours_submitted','learner',lid);return {ok:true};
  }
  if(action==='reviews'){
   require('admin','assessor');const date=day(d,'review_date'),next=day(d,'next_date');if(next<=date)fail('Next review date must be later.');
   s.reviews.push({id:id(s.reviews),learner_id:lid,review_date:date,next_date:next,strengths:str(d,'strengths'),actions:str(d,'actions'),actor:u.id,acknowledged:null,created:now()});audit('review_created','learner',lid);return {ok:true};
  }
  if(action==='exams'){
   require('admin','assessor');const uid=num(d.unit_id),unit=find('units',uid);enrolled(lid,unit.course_id);const outcome=str(d,'outcome'),date=day(d,'day');
   if(!['pending','pass','fail'].includes(outcome))fail('Invalid exam outcome.');if(date>new Date().toLocaleDateString('en-CA'))fail('Results cannot be dated in the future.');
   s.exams.push({id:id(s.exams),learner_id:lid,unit_id:uid,day:date,outcome,reference:str(d,'reference'),actor:u.id});audit('exam_recorded','learner',lid);return {ok:true};
  }
 }
 match=path.match(/^\/api\/portfolio\/(\d+)(?:\/([\w-]+))?$/);
 if(match){
  const p=portfolio(Number(match[1])),action=match[2],unit=find('units',p.unit_id);
  if(method==='GET')return detail(p);
  if(action==='new-record'){
   require('learner','assessor','admin');if(s.portfolios.some(x=>x.learner_id===p.learner_id&&x.unit_id===p.unit_id&&['draft','returned'].includes(x.status)))fail('Finish the existing draft for this unit before starting another.');
   const next=makePortfolio(p.learner_id,p.unit_id);audit('service_record_created','portfolio',next.id);return {id:next.id};
  }
  version(p);
  if(action==='save'){
   editable(p);const fields=Object.fromEntries(FIELDS.map(k=>[k,str(d,k,false)]));fields.criteria=checks(d.criteria??[],unit);fields.ranges={};
   for(const [key,values] of Object.entries(d.ranges??{})){if(!RANGES[key]||!Array.isArray(values)||values.some(v=>!RANGES[key].includes(v)))fail('Invalid range selection.');fields.ranges[key]=[...new Set(values)];}
   p.fields=fields;bump(p);audit('draft_saved','portfolio',p.id);return detail(p);
  }
  if(action==='submit'){
   editable(p);if(!['objectives','service','went_well','improve'].every(k=>p.fields[k]?.trim()))fail('Complete objectives, service, what went well and next steps first.');
   p.status='submitted';bump(p);recordDecision(p,'submission','submitted','Submitted by demo learner');audit('submitted','portfolio',p.id);return detail(p);
  }
  if(action==='files'){
   editable(p);if(!d.file)fail('Choose a sample file.');if(s.evidence.filter(e=>e.portfolio_id===p.id).length>=20)fail('Maximum 20 sample files per record.');
   if(s.evidence.reduce((n,e)=>n+e.size,0)+d.file.size>30*1024*1024)fail('Demo storage limit is 30 MB of sample files.');
   s.evidence.push({id:id(s.evidence),portfolio_id:p.id,...d.file,created:now()});bump(p);audit('file_added','portfolio',p.id);return detail(p);
  }
  if(action==='decision'){
   const kind=str(d,'kind'),outcome=str(d,'outcome'),feedback=str(d,'feedback');let ticks=[];
   if(kind==='assessment'){
    require('admin','assessor');if(!['submitted','iqa_action','assessed'].includes(p.status)||!['assessed','returned'].includes(outcome)||(p.status==='assessed'&&outcome!=='returned'))fail('This assessment action is not available.');
    ticks=checks(d.checks??[],unit);if(outcome==='assessed'&&!ticks.length)fail('Tick the criteria demonstrated by this service.');
   }else if(kind==='iqa'){
    require('admin','iqa');if(p.status!=='assessed'||!['verified','iqa_action'].includes(outcome))fail('Only assessed work can be sampled.');
    const last=s.decisions.filter(x=>x.portfolio_id===p.id&&x.kind==='assessment').at(-1);if(!last||last.actor===u.id)fail('A different person must complete the IQA check.');
   }else fail('Invalid decision type.');
   recordDecision(p,kind,outcome,feedback,ticks);p.status=outcome;bump(p);audit(outcome,'portfolio',p.id);return detail(p);
  }
 }
 match=path.match(/^\/api\/files\/(\d+)$/);
 if(match){const e=find('evidence',match[1]);portfolio(e.portfolio_id);return {filename:e.filename,blob:e.blob};}
 match=path.match(/^\/api\/hours\/(\d+)\/review$/);
 if(match){require('admin','assessor');const h=find('hours',match[1]);access(h.learner_id);if(h.status!=='pending'||!['approved','rejected'].includes(d.status))fail('Only pending hours can be reviewed.');h.feedback=str(d,'feedback');h.status=d.status;h.reviewer=u.id;audit('hours_'+h.status,'hours',h.id);return {ok:true};}
 match=path.match(/^\/api\/reviews\/(\d+)\/acknowledge$/);
 if(match){require('learner');const r=find('reviews',match[1]);access(r.learner_id);if(r.acknowledged)fail('Already acknowledged.');r.acknowledged=now();audit('review_acknowledged','review',r.id);return {ok:true};}
 if(path.startsWith('/api/admin')){
  require('admin');
  if(path==='/api/admin'&&method==='GET')return {users:s.users.map(publicUser),courses:s.courses,units:s.units,assignments:s.assignments,enrolments:s.enrolments,audit:s.audit.slice(-100).reverse()};
  if(path==='/api/admin/users'){
   const email=str(d,'email').toLowerCase(),role=str(d,'role');if(!email.includes('@')||email.includes(' '))fail('Enter a valid fictional email.');if(s.users.some(x=>x.email===email))fail('This email is already in the demo.');if(!['admin','learner','assessor','iqa'].includes(role))fail('Choose a role.');
   const user={id:id(s.users),name:str(d,'name'),email,role,password:d.passwordHash,active:1,must_change:1};s.users.push(user);audit('demo_user_created','user',user.id);return {id:user.id};
  }
  match=path.match(/^\/api\/admin\/users\/(\d+)$/);
  if(match){const person=find('users',match[1]);if(person.id===u.id)fail('Use My account to change your own test password.');if(d.action==='password'){person.password=d.passwordHash;person.must_change=1;}else if(['disable','enable'].includes(d.action))person.active=Number(d.action==='enable');else fail('Unknown account action.');audit('user_'+d.action,'user',person.id);return {ok:true};}
  if(path==='/api/admin/assignments'){
   const staff=find('users',num(d.staff_id)),learner=find('users',num(d.learner_id));if(!['assessor','iqa'].includes(staff.role)||learner.role!=='learner'||!staff.active||!learner.active)fail('Choose active staff and learner accounts.');
   const same=a=>a.staff_id===staff.id&&a.learner_id===learner.id;if(d.remove)s.assignments=s.assignments.filter(a=>!same(a));else if(!s.assignments.some(same))s.assignments.push({staff_id:staff.id,learner_id:learner.id});audit(d.remove?'staff_unassigned':'staff_assigned','learner',learner.id);return {ok:true};
  }
  if(path==='/api/admin/courses'){const c={id:id(s.courses),title:str(d,'title'),description:str(d,'description')};s.courses.push(c);audit('course_created','course',c.id);return {id:c.id};}
  if(path==='/api/admin/units'){
   const cid=num(d.course_id);find('courses',cid);const list=str(d,'criteria').split('\n').map(v=>v.trim()).filter(Boolean);if(!list.length||list.length>100)fail('Use 1–100 criteria, one per line.');
   const values={course_id:cid,ref:str(d,'ref'),title:str(d,'title'),aim:str(d,'aim'),criteria:JSON.stringify(list)};let unit;
   if(d.id){unit=find('units',num(d.id));if(unit.course_id!==cid)fail('An existing unit cannot move courses.');if(s.portfolios.some(p=>p.unit_id===unit.id))fail('This unit is already enrolled. Create a new course version to change its outline.');Object.assign(unit,values);}
   else{unit={id:id(s.units),...values};s.units.push(unit);s.enrolments.filter(e=>e.course_id===cid).forEach(e=>makePortfolio(e.learner_id,unit.id));}audit('unit_saved','unit',unit.id);return {id:unit.id};
  }
  if(path==='/api/admin/enrolments'){
   const lid=num(d.learner_id),cid=num(d.course_id),learner=find('users',lid);find('courses',cid);if(learner.role!=='learner'||!learner.active)fail('Choose an active learner.');
   if(!s.enrolments.some(e=>e.learner_id===lid&&e.course_id===cid))s.enrolments.push({learner_id:lid,course_id:cid});s.units.filter(unit=>unit.course_id===cid).forEach(unit=>{if(!s.portfolios.some(p=>p.learner_id===lid&&p.unit_id===unit.id))makePortfolio(lid,unit.id);});audit('enrolled','learner',lid,String(cid));return {ok:true};
  }
  if(path==='/api/admin/resources'){
   const cid=num(d.course_id);find('courses',cid);const url=str(d,'url',false);if(url){let parsed;try{parsed=new URL(url);}catch{fail('Enter a valid HTTPS link.');}if(parsed.protocol!=='https:'||parsed.username||parsed.password)fail('Use an HTTPS link.');}
   s.resources.push({id:id(s.resources),course_id:cid,title:str(d,'title'),body:str(d,'body'),url});audit('resource_added','course',cid);return {ok:true};
  }
 }
 fail('This action is not available in this demo.');
}

export async function resetDemo(){
 const db=await database();
 await new Promise((resolve,reject)=>{const tx=db.transaction('demo','readwrite');tx.objectStore('demo').delete('state');tx.oncomplete=resolve;tx.onabort=()=>reject(new Error('Reset failed.'));});
 sessionStorage.removeItem(SESSION);
}

export function saveDownload(blob,filename){const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
