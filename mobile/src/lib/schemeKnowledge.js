/** Resolve teaching material by artwork ID, never by the position of an image. */
function schemeCatalog(value, assetIds) {
 const fail=()=>{throw new Error('Каталог авторских схем содержит неполный разбор.');};
 if(!value||!Array.isArray(value.entries)||!value.method||typeof value.method.text!=='string')fail();
 const ids=new Set(), voices=new Set();
 for(const entry of value.entries){
  if(!entry||!['id','title','summary','meaning','focus'].every(key=>typeof entry[key]==='string'&&entry[key].trim())||!Array.isArray(entry.reading)||!entry.reading.length||!entry.reading.every(step=>step&&typeof step.label==='string'&&step.label.trim()&&typeof step.text==='string'&&step.text.trim()))fail();
  if(ids.has(entry.id)||!entry.narration||typeof entry.narration.id!=='string'||!/^scheme-[a-z0-9-]+$/.test(entry.narration.id)||voices.has(entry.narration.id)||typeof entry.narration.text!=='string'||!entry.narration.text.trim())fail();
  ids.add(entry.id);voices.add(entry.narration.id);
 }
 if(assetIds&&(new Set(assetIds).size!==assetIds.length||assetIds.length!==ids.size||assetIds.some(id=>!ids.has(id))))fail();
 return value;
}
const normalize=value=>String(value||'').normalize('NFKC').toLocaleLowerCase('ru').replace(/ё/g,'е').replace(/[–—−]/g,'-').replace(/\s+/g,' ').trim();
function filterSchemes(entries,group,query){
 const tokens=normalize(query).split(' ').filter(Boolean);
 return entries.filter(entry=>(!group||entry.group===group)&&tokens.every(token=>normalize([entry.id,entry.title,entry.summary,entry.meaning,entry.focus,...entry.reading.map(step=>`${step.label} ${step.text}`)].join(' ')).includes(token)));
}
function adjacentScheme(entries,id,offset){
 const index=entries.findIndex(entry=>entry.id===id);
 return index<0?null:entries[index+offset]||null;
}
module.exports={schemeCatalog,filterSchemes,adjacentScheme};
