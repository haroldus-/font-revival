/* Local scripts and fonts also work when the gallery is opened from disk. */
const tiles=[...document.querySelectorAll('.icon-tile')];
const search=document.getElementById('icon-search');
const filters=[...document.querySelectorAll('.filters input[type=checkbox]')];
const more=document.getElementById('show-more');
const reset=document.getElementById('reset-filters');
const size=document.getElementById('icon-size');
const groups=['collection','type','section'];
const countLabel=n=>`${n.toLocaleString('en')} ${n===1?'icon':'icons'}`;
const entries=tiles.map(tile=>({tile,search:tile.dataset.search.toLowerCase(),collection:[tile.dataset.collection],type:[tile.dataset.type],section:tile.dataset.section.split(' ')}));
let limit=96,matches=entries;
const params=new URLSearchParams(location.search);
search.value=params.get('q')||'';
for(const input of filters)input.checked=params.getAll(input.name).includes(input.value);
for(const input of filters)if(input.checked){const panel=input.closest('details');if(panel)panel.open=true;}
if(params.has('size'))size.value=String(Math.max(48,Math.min(144,Number(params.get('size'))||80)));
limit=Math.max(96,Math.min(tiles.length,Number(params.get('limit'))||96));
function setSize(){
  document.documentElement.style.setProperty('--icon-size',`${size.value}px`);
  document.getElementById('size-output').value=size.value;
}
function saveState(){
  const url=new URL(location.href);url.search='';
  if(search.value.trim())url.searchParams.set('q',search.value.trim());
  for(const input of filters)if(input.checked)url.searchParams.append(input.name,input.value);
  if(size.value!=='80')url.searchParams.set('size',size.value);
  if(limit>96)url.searchParams.set('limit',limit);
  // Some local-file hosts restrict history; filtering still works there.
  try{history.replaceState(null,'',url);}catch{}
}
function showResults(){
  const shown=new Set(matches.slice(0,limit).map(entry=>entry.tile));
  for(const tile of tiles)tile.hidden=!shown.has(tile);
  document.getElementById('result-count').textContent=matches.length>limit?`Showing ${Math.min(limit,matches.length)} of ${countLabel(matches.length)}`:countLabel(matches.length);
  document.getElementById('empty').hidden=matches.length!==0;
  more.hidden=matches.length<=limit;
  more.textContent=`Show ${Math.min(96,matches.length-limit)} more icons`;
}
function filterResults(persist=true){
  const words=search.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const selected=Object.fromEntries(groups.map(group=>[group,filters.filter(input=>input.name===group&&input.checked).map(input=>input.value)]));
  const textMatches=entries.filter(entry=>words.every(word=>entry.search.includes(word)));
  const inGroup=(entry,group)=>!selected[group].length||selected[group].some(value=>entry[group].includes(value));
  matches=textMatches.filter(entry=>groups.every(group=>inGroup(entry,group)));
  // Counts reflect the other groups; choices within a group are alternatives.
  for(const group of groups){
    const candidates=textMatches.filter(entry=>groups.every(other=>other===group||inGroup(entry,other)));
    for(const input of filters.filter(input=>input.name===group)){
      const count=candidates.filter(entry=>entry[group].includes(input.value)).length;
      input.closest('label').querySelector('small').textContent=count.toLocaleString('en');
    }
  }
  reset.hidden=!search.value&&!filters.some(input=>input.checked);
  for(const panel of document.querySelectorAll('.filters details')){
    const inputs=[...panel.querySelectorAll('input[type=checkbox]')];
    const count=inputs.filter(input=>input.checked).length;
    const name=inputs[0]?.name==='collection'?'Collection':'Specimen sections';
    panel.querySelector('summary').textContent=name+(count?` · ${count} selected`:'');
  }
  showResults();if(persist)saveState();
}
search.addEventListener('input',()=>{limit=96;filterResults();});
for(const input of filters)input.addEventListener('change',()=>{limit=96;filterResults();});
reset.addEventListener('click',()=>{search.value='';for(const input of filters)input.checked=false;limit=96;filterResults();});
more.addEventListener('click',()=>{const next=matches[limit]?.tile;limit+=96;showResults();saveState();next?.focus({preventScroll:true});});
size.addEventListener('input',()=>{setSize();saveState();});
document.getElementById('section-search').addEventListener('input',event=>{
  const value=event.target.value.trim().toLowerCase();
  for(const label of document.querySelectorAll('.section-options label'))label.hidden=!label.querySelector('span').textContent.toLowerCase().includes(value);
});
setSize();filterResults(false);
// Preserve links to icons from the former single-page catalogue.
const oldTarget=tiles.find(tile=>tile.dataset.id===location.hash.slice(1));
if(oldTarget)location.replace(oldTarget.href);

const artwork=tiles.map(tile=>tile.querySelector('.grid-icon'));
const hero=document.querySelector('.hero-art');
const toggle=document.querySelector('.hero-animation-toggle');
const reducedMotion=matchMedia('(prefers-reduced-motion: reduce)');
const faces=[hero.querySelector('.hero-face')];
let step=0,currentFace=0,timer,paused=false;
if(artwork.length){const next=faces[0].cloneNode(true);next.classList.add('is-hidden');hero.append(next);faces.push(next);}
async function rotateIcon(){
  const nextStep=step+1,index=Math.floor(nextStep/2)%artwork.length;
  const drawing=artwork[index].cloneNode(true);
  await document.fonts.load(`80px ${drawing.style.fontFamily}`,drawing.textContent);
  if(paused||reducedMotion.matches||document.hidden)return;
  step=nextStep;const next=1-currentFace;
  faces[next].replaceChildren(drawing);faces[next].style.color=step%2?'var(--red)':'var(--ink)';
  faces[next].classList.remove('is-hidden');faces[currentFace].classList.add('is-hidden');currentFace=next;
}
function updateRotation(){
  clearInterval(timer);toggle.hidden=reducedMotion.matches||!artwork.length;
  toggle.textContent=paused?'Play animation':'Pause animation';
  if(artwork.length&&!paused&&!reducedMotion.matches&&!document.hidden)timer=setInterval(rotateIcon,7000);
}
toggle.addEventListener('click',()=>{paused=!paused;updateRotation();});
reducedMotion.addEventListener('change',updateRotation);
document.addEventListener('visibilitychange',updateRotation);
document.fonts.ready.then(()=>{
  if(document.fonts.check('36px "erebus-1894"')&&document.fonts.check('36px "hades-1894"'))document.querySelector('.eyebrow').classList.add('is-layered');
});
updateRotation();
