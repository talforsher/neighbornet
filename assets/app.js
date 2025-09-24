
function $(q,el=document){return el.querySelector(q)}
function $all(q,el=document){return Array.from(el.querySelectorAll(q))}
function normalize(s){return (s||'').toLowerCase()}
function filterCards(){
  const q = normalize($('#q').value);
  const cat = normalize($('#cat').value);
  $all('.card').forEach(c=>{
    const text = c.dataset.search;
    const categories = c.dataset.categories || '';
    const okQ = !q || text.includes(q);
    const okC = !cat || categories.includes(cat);
    c.style.display = (okQ && okC) ? '' : 'none';
  });
}
$('#q').addEventListener('input', filterCards);
$('#cat').addEventListener('change', filterCards);
