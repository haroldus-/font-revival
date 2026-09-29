document.getElementById('icon-size').addEventListener('input',event=>{
  document.body.style.setProperty('--icon-size',`${event.target.value}px`);
  document.getElementById('size-output').value=event.target.value;
});
document.getElementById('icon-color').addEventListener('input',event=>document.documentElement.style.setProperty('--icon-color',event.target.value));
// Reuse the referring grid's filters, size and loaded result count when present.
try{
  const previous=new URL(document.referrer),current=new URL(location.href);
  if(previous.protocol===current.protocol&&previous.host===current.host&&previous.pathname===new URL('../icons.html',current).pathname){
    previous.hash='collection';document.querySelector('.back-link a').href=previous.href;
  }
}catch{}
