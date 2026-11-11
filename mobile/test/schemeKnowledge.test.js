const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const {schemeCatalog,filterSchemes,adjacentScheme}=require('../src/lib/schemeKnowledge');
const entry=(id,title)=>({id,title,summary:'Описание',meaning:'Смысл',focus:'Фокус',group:'Группа',reading:[{label:'Шаг',text:'Душа, Солнце'}],narration:{id:`scheme-${id.toLowerCase()}`,text:'Разбор схемы'},sources:[]});
const material={method:{text:'Общий метод'},entries:[entry('A','Квадрат'),entry('B','Расчёт числа') ]};
test('scheme catalog requires exactly one meaningful explanation and voice per original artwork',()=>{
 assert.equal(schemeCatalog(material,['A','B']),material);
 assert.throws(()=>schemeCatalog(material,['A','C']));
 assert.throws(()=>schemeCatalog({...material,entries:[material.entries[0],material.entries[0]]},['A','B']));
 assert.throws(()=>schemeCatalog({...material,entries:[{...material.entries[0],reading:[]}]},['A']));
 assert.throws(()=>schemeCatalog({...material,entries:[{...material.entries[0],narration:{id:'scheme-a',text:''}}]},['A']));
});
test('search combines complete explanation text, Russian case and ё without losing category scope',()=>{
 const values=[entry('A','Расчёт души'),{...entry('B','Солнце'),group:'Планеты'}];
 assert.deepEqual(filterSchemes(values,'','РАСЧЕТ душа').map(x=>x.id),['A']);
 assert.equal(filterSchemes(values,'Группа','солнце').length,1);
 assert.equal(filterSchemes(values,'Группа','несуществующее').length,0);
 assert.deepEqual(filterSchemes(values,'Планеты','').map(x=>x.id),['B']);
});
test('detail navigation stays within visible examples and never wraps to another group',()=>{
 assert.equal(adjacentScheme(material.entries,'A',-1),null);
 assert.equal(adjacentScheme(material.entries,'B',1),null);
 assert.equal(adjacentScheme(material.entries,'missing',1),null);
 assert.equal(adjacentScheme(material.entries,'A',1).id,'B');
});
test('published teaching catalog covers every mobile illustration with a distinct narration',()=>{
 const raw=require('../../packages/scheme-knowledge/ru.json');
 const source=fs.readFileSync(path.resolve(__dirname,'../src/lib/illustrations.ts'),'utf8');
 const ids=[...source.matchAll(/id:"([A-Za-z0-9]+)"/g)].map(match=>match[1]);
 const catalog=schemeCatalog(raw,ids);assert.equal(catalog.entries.length,29);
 assert.match(catalog.entries.find(item=>item.id==='HSU').title,/Венер/);
});
