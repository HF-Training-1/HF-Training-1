import {state,$,api,esc,label,badge,date,title,field,area,select,table,formData,bindForm,toast,wireButtons} from './ui.js';

export async function renderAdmin(refresh){
 const d=await api('/api/admin');state.admin=d;
 const learners=d.users.filter(u=>u.role==='learner'&&u.active),staff=d.users.filter(u=>['assessor','iqa'].includes(u.role)&&u.active);
 const learnerSelect=()=>select('learner_id','Learner',learners.map(u=>[u.id,u.name]));
 const courseSelect=()=>select('course_id','Course',d.courses.map(c=>[c.id,c.title]));
 const unitForm=(unit=null)=>`<form id="unit-form">${unit?`<input type="hidden" name="id" value="${unit.id}">`:''}${courseSelect()}<div class="form-grid">${field('ref','Unit reference','text',unit?.ref||'')}${field('title','Unit title','text',unit?.title||'')}</div>${area('aim','Unit aim',unit?.aim||'')}${area('criteria','Assessment criteria — one per line',unit?JSON.parse(unit.criteria).join('\n'):'')}<button class="primary">Save unit</button></form>`;
 $('#content').innerHTML=title('Administration','Manage access, programmes and the records behind your academy.')+`
 <div class="notice warning">Before enrolling learners, check the draft units against your current qualification handbook. Unit outlines lock after enrolment to protect existing evidence.</div>
 <details open><summary>People & access</summary><div class="grid-two"><form id="user-form"><h3>Create a test account</h3><div class="form-grid">${field('name','Fictional name')}${field('email','Fictional email address','email')}${select('role','Role',[['learner','Learner'],['assessor','Tutor / assessor'],['iqa','IQA'],['admin','Administrator']])}${field('password','Temporary passphrase (14–128 characters)','password')}</div><p class="small">Use fictional details and a test-only passphrase. This account exists only in this browser; it is not a secure or shared login.</p><button class="primary">Create account</button></form><form id="assignment-form"><h3>Assign staff to a learner</h3>${select('staff_id','Staff member',staff.map(u=>[u.id,u.name+' · '+label(u.role)]))}${learnerSelect()}<button>Assign staff</button></form></div>
 ${table(['Name / email','Role','Access','Actions'],d.users.map(u=>`<tr><td><strong>${esc(u.name)}</strong><br>${esc(u.email)}</td><td>${esc(label(u.role))}</td><td>${u.active?'Active':'Disabled'}${u.must_change?'<br><span class="small">Password change required</span>':''}</td><td>${u.id!==state.user.id?`<button data-user="${u.id}" data-action="${u.active?'disable':'enable'}">${u.active?'Disable':'Enable'}</button> <button data-user="${u.id}" data-action="password">Reset password</button>`:'Your account'}</td></tr>`).join(''))}
 <h3>Staff assignments</h3>${table(['Staff','Learner','Action'],d.assignments.map(a=>`<tr><td>${esc(d.users.find(u=>u.id===a.staff_id)?.name)}</td><td>${esc(d.users.find(u=>u.id===a.learner_id)?.name)}</td><td><button data-unassign="${a.staff_id}" data-learner="${a.learner_id}">Remove access</button></td></tr>`).join(''))}</details>
 <details><summary>Courses & enrolment</summary><div class="grid-two"><form id="course-form"><h3>Create a course</h3>${field('title','Course title')}${area('description','Programme description')}<button class="primary">Create course</button></form><form id="enrolment-form"><h3>Enrol a learner</h3>${learnerSelect()}${courseSelect()}<button class="primary">Enrol learner</button></form></div>${table(['Learner','Course'],d.enrolments.map(e=>`<tr><td>${esc(d.users.find(u=>u.id===e.learner_id)?.name)}</td><td>${esc(d.courses.find(c=>c.id===e.course_id)?.title)}</td></tr>`).join(''))}</details>
 <details><summary>Unit builder</summary><div id="unit-editor">${unitForm()}</div><h3>Existing units</h3>${table(['Reference','Title','Course','Edit'],d.units.map(u=>`<tr><td>${esc(u.ref)}</td><td>${esc(u.title)}</td><td>${esc(d.courses.find(c=>c.id===u.course_id)?.title)}</td><td><button data-edit-unit="${u.id}">Edit outline</button></td></tr>`).join(''))}</details>
 <details><summary>Add a learning resource</summary><form id="resource-form">${courseSelect()}${field('title','Resource title')}${area('body','Instructions or learning notes')}${field('url','Optional HTTPS link','url','',false)}<button class="primary">Publish to enrolled learners</button></form></details>
 <details><summary>Activity history — latest 100 events</summary>${table(['When (UTC)','Person','Action','Record','Detail'],d.audit.map(a=>`<tr><td>${esc(a.created)}</td><td>${esc(a.name||'Server operator')}</td><td>${esc(label(a.action))}</td><td>${esc(a.entity)} #${a.entity_id??'—'}</td><td>${esc(a.detail)}</td></tr>`).join(''))}</details>`;
 const bindUnit=()=>bindForm('unit-form',async form=>{await api('/api/admin/units','POST',formData(form));toast('Unit saved.');await refresh();});
 bindUnit();
 for(const [name,path,msg] of [['user','users','Account created.'],['assignment','assignments','Staff assigned.'],['course','courses','Course created.'],['enrolment','enrolments','Learner enrolled.'],['resource','resources','Resource published.']]){
  bindForm(`${name}-form`,async form=>{await api(`/api/admin/${path}`,'POST',formData(form));toast(msg);await refresh();});
 }
 wireButtons('[data-user]',async b=>{
  const data={action:b.dataset.action};
  if(data.action==='password'){
   // Passwords must use a masked field rather than a visible browser prompt.
   const {modal}=await import('./ui.js');
   modal('Reset temporary password',`<form id="reset-form">${field('password','New temporary passphrase (14–128 characters)','password')}<button class="primary">Reset password</button></form>`);
   bindForm('reset-form',async form=>{await api(`/api/admin/users/${b.dataset.user}`,'POST',{...formData(form),action:'password'});$('#modal').close();toast('Password reset. Existing sessions revoked.');await refresh();});return;
  }
  if(!confirm(`${label(data.action)} this account?`))return;
  await api(`/api/admin/users/${b.dataset.user}`,'POST',data);toast('Account updated.');await refresh();
 });
 wireButtons('[data-unassign]',async b=>{await api('/api/admin/assignments','POST',{staff_id:b.dataset.unassign,learner_id:b.dataset.learner,remove:true});toast('Staff access removed.');await refresh();});
 wireButtons('[data-edit-unit]',async b=>{const u=d.units.find(u=>u.id===Number(b.dataset.editUnit));$('#unit-editor').innerHTML=unitForm(u);$('#unit-form [name=course_id]').value=u.course_id;bindUnit();$('#unit-editor').scrollIntoView({behavior:'smooth'});});
}
