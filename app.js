import {state,$,api,esc,label,field,title,formData,bindForm,toast} from './ui.js';
import {renderLearning} from './learning.js';
import {renderAdmin} from './admin.js';
import {DEMO_PASSWORD,resetDemo,saveDownload} from './demo-store.js';

const navigation=[['dashboard','01','Overview'],['portfolio','02','E-portfolio'],['assessment','03','Assessment & IQA'],['attendance','04','Attendance'],['hours','05','Learning hours'],['reviews','06','Progress reviews'],['exams','07','Exam results'],['resources','08','Resources'],['admin','09','Administration'],['account','10','My account']];
$('#close-modal').addEventListener('click',()=>$('#modal').close());
$('#logout').addEventListener('click',async()=>{try{await api('/api/logout','POST',{});location.reload();}catch(e){toast(e.message);}});
bindForm('login-form',async form=>{
 $('#login-error').textContent='';
 try{await api('/api/login','POST',formData(form));form.reset();await boot();}catch(e){$('#login-error').textContent=e.message;}
});

document.querySelectorAll('[data-demo-role]').forEach(button=>button.addEventListener('click',()=>{
 $('#login-form [name=email]').value=button.dataset.demoRole+'@demo.invalid';
 $('#login-form [name=password]').value=DEMO_PASSWORD;
 $('#login-form').requestSubmit();
}));
$('#reset-demo').addEventListener('click',async()=>{
 if(!confirm('Reset this GitHub demo in this browser? This permanently removes its test records and sample files. Your old HF app data is not touched.'))return;
 try{await resetDemo();location.reload();}catch(e){toast(e.message);}
});
document.addEventListener('click',async event=>{
 const link=event.target.closest('[data-file],[data-export]');if(!link)return;event.preventDefault();
 try{
  if(link.dataset.file){const f=await api(`/api/files/${link.dataset.file}`);saveDownload(f.blob,f.filename);}
  else{const records=await api(`/api/learners/${link.dataset.export}/export`);saveDownload(new Blob([JSON.stringify(records,null,2)],{type:'application/json'}),`HF-demo-learner-${link.dataset.export}.json`);}
 }catch(e){toast(e.message);}
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
  $('#content').innerHTML=title('My demo account','Test account settings in this browser only.')+`<section class="notice warning">This is a public demonstration, not secure account hosting. Never enter a real password. Reset demo restores the public test logins and deletes local test records.</section><section class="card">${state.user.must_change?'<p class="notice">Replace your temporary test password before continuing.</p>':''}<form id="password-form">${field('current_password','Current test password','password')}${field('new_password','New test passphrase (14–128 characters)','password')}<button class="primary">Change test password & sign out</button></form></section>`;
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

boot().catch(error=>{$('#workspace').hidden=true;$('#login').hidden=false;if(error.message!=='Please sign in to the demo.')$('#login-error').textContent=error.message;});
