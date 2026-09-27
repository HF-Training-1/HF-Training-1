import {demoRequest} from './demo-store.js';
export const state={user:null,csrf:'',learners:[],lid:null,data:null,page:'dashboard',admin:null};
export const $=(s)=>document.querySelector(s);
export const esc=(value)=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const label=(s)=>String(s).replaceAll('_',' ').replace(/^./,c=>c.toUpperCase());
export const badge=(s)=>`<span class="badge ${esc(s)}">${esc(label(s))}</span>`;
export const date=(s)=>s?new Intl.DateTimeFormat('en-GB',{day:'numeric',month:'short',year:'numeric'}).format(new Date(s.slice(0,10)+'T12:00:00')):'—';
export const today=()=>new Intl.DateTimeFormat('en-CA').format(new Date());
export const field=(name,title,type='text',value='',required=true)=>`<label>${esc(title)}<input name="${name}" type="${type}" value="${esc(value)}" ${required?'required':''}></label>`;
export const area=(name,title,value='',required=true)=>`<label>${esc(title)}<textarea name="${name}" ${required?'required':''} maxlength="10000">${esc(value)}</textarea></label>`;
export const select=(name,title,options)=>`<label>${esc(title)}<select name="${name}" required>${options.map(o=>`<option value="${esc(o[0])}">${esc(o[1])}</option>`).join('')}</select></label>`;
export const formData=(f)=>Object.fromEntries(new FormData(f));
export const empty=(s)=>`<div class="empty">${esc(s)}</div>`;
export const title=(heading,subtitle)=>`<div class="page-title"><div><h1>${esc(heading)}</h1><p>${esc(subtitle)}</p></div></div>`;
export const table=(heads,body)=>`<div class="table-scroll"><table><thead><tr>${heads.map(h=>`<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${body||`<tr><td colspan="${heads.length}">No records yet.</td></tr>`}</tbody></table></div>`;
let toastTimer;
export function toast(message){$('#toast').textContent=message;$('#toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').hidden=true,6500);}
export const api=demoRequest;

export function bindForm(id,handler){
 const form=document.getElementById(id);if(!form)return;
 form.addEventListener('submit',async event=>{event.preventDefault();const buttons=[...form.querySelectorAll('button')];buttons.forEach(b=>b.disabled=true);
  try{await handler(form,event.submitter);}catch(error){toast(error.message);}finally{buttons.forEach(b=>b.disabled=false);}
 });
}
export function modal(heading,html){$('#modal-title').textContent=heading;$('#modal-body').innerHTML=html;if(!$('#modal').open)$('#modal').showModal();}
export function wireButtons(selector,handler){document.querySelectorAll(selector).forEach(b=>b.addEventListener('click',async()=>{b.disabled=true;try{await handler(b);}catch(e){toast(e.message);}finally{b.disabled=false;}}));}
