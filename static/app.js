if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(()=>{});
const form=document.querySelector('#proposal-form');
if(form){
 document.querySelector('#preview-button').addEventListener('click',()=>{
  if(!form.reportValidity())return;
  document.querySelector('#preview-text').textContent=form.elements.title.value+'\n\n'+form.elements.body.value;
  document.querySelector('#preview-text').classList.add('pre');
  document.querySelector('#preview').hidden=false;
 });
 document.querySelector('#title-input').addEventListener('input',e=>{
  const words=e.target.value.toLocaleLowerCase('tr').split(/\s+/).filter(w=>w.length>3);
  const matches=[...document.querySelectorAll('#similar-topics a')].filter(a=>words.some(w=>a.textContent.toLocaleLowerCase('tr').includes(w)));
  document.querySelector('#similar-notice').textContent=matches.length?'Benzer başlıklar var: '+matches.slice(0,3).map(a=>a.textContent).join(' · '):'';
  document.querySelector('#preview').hidden=true;
 });
}
