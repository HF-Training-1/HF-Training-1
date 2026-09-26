import {state,$,api,esc,label,field,title,formData,bindForm,toast} from './ui.js';
import {renderLearning} from './learning.js';
import {renderAdmin} from './admin.js';

const navigation=[['dashboard','01','Overview'],['portfolio','02','E-portfolio'],['assessment','03','Assessment & IQA'],['attendance','04','Attendance'],['hours','05','Learning hours'],['reviews','06','Progress reviews'],['exams','07','Exam results'],['resources','08','Resources'],['admin','08','Administration'],['account','09','My account']];
$('#close-modal').addEventListener('click',()=>$('#modal').close());
$('#logout').addEventListener('click',async()=>{try{await api('/api/logout','POST',{});location.reload();}catch(e){toast(e.message);}});
bindForm('login-form',async form=>{
 $('#login-error').textContent='';
 try{await api('/api/login','POST',formData(form));form.reset();await boot();}catch(e){$('#login-error').textContent=e.message;}
});

async function boot(){
 const me=await api('/api/me');state.user=me.user;state.csrf=me.csrf;
 $('#login').hidden=true;$('#workspace').hidden=false;
 $('#identity').innerHTML=`<strong>${esc(state.user.name)}</strong> <span class="small">${esc(label(state.user.role))}</span>`;
 if(state.user.must_change)state.page='account';
 renderNav();await refresh();
}

function renderNav(){
 const nav=navigation.filter(([key])=>(key!=='admin'||state.user.role==='admin')&&(key!=='assessment'||state.user.role!=='learner')&&(!state.user.must_change||key==='account'));
 $('#nav').innerHTML=nav.map(([key,num,text])=>`<button data-page="${key}" class="${state.page===key?'active':''}" ${state.page===key?'aria-current="page"':''}><span>${num}</span>${text}</button>`).join('');
 $('#nav').querySelectorAll('button').forEach(b=>b.addEventListener('click',async()=>{state.page=b.dataset.page;renderNav();try{await refresh();}catch(e){toast(e.message);}}));
 $('#breadcrumb').textContent=navigation.find(n=>n[0]===state.page)?.[2]||'Learning workspace';
}

async function refresh(){
 if(state.page==='account'){
  $('#learner-picker').innerHTML='';
  $('#content').innerHTML=title('My account','Keep your sign-in details private.')+`<section class="card">${state.user.must_change?'<p class="notice">Please replace your temporary password before using the learning workspace.</p>':''}<form id="password-form">${field('current_password','Current password','password')}${field('new_password','New passphrase (14–128 characters)','password')}<button class="primary">Change password & sign out</button></form></section>`;
  $('#password-form [name=current_password]').autocomplete='current-password';$('#password-form [name=new_password]').autocomplete='new-password';
  bindForm('password-form',async form=>{await api('/api/password','POST',formData(form));location.reload();});return;
 }
 state.learners=await api('/api/learners');
 if(!state.learners.some(l=>l.id===state.lid))state.lid=state.learners[0]?.id??null;
 if(state.page==='admin'){$('#learner-picker').innerHTML='';await renderAdmin(refresh);return;}
 if(state.user.role!=='learner'&&state.learners.length){
  $('#learner-picker').innerHTML=`<div class="learner-selector"><label for="learner-select">LEARNER WORKSPACE</label><select id="learner-select">${state.learners.map(l=>`<option value="${l.id}" ${l.id===state.lid?'selected':''}>${esc(l.name)}</option>`).join('')}</select></div>`;
  $('#learner-select').addEventListener('change',async e=>{state.lid=Number(e.target.value);try{await refresh();}catch(err){toast(err.message);}});
 }else $('#learner-picker').innerHTML='';
 state.data=state.lid?await api(`/api/learners/${state.lid}`):null;
 renderLearning(refresh);
}

boot().catch(()=>{$('#workspace').hidden=true;$('#login').hidden=false;});
