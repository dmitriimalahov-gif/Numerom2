'use strict';
// Presentation of saved report fields only. No numerology arithmetic lives here.
const LAYOUT=[1,4,7,2,5,8,3,6,9];
const DIRECTIONS=[['row-0',[1,4,7],'Гор.'],['row-1',[2,5,8],'Гор.'],['row-2',[3,6,9],'Гор.'],['col-0',[1,2,3],'Верт.'],['col-1',[4,5,6],'Верт.'],['col-2',[7,8,9],'Верт.'],['diag-0',[1,5,9],'Диаг.'],['diag-1',[3,5,7],'Диаг.']];
const KINDS=new Set(['personal','square','lines','sequence','tasks','individual','series','period','bars','triangle','human']);
const HUMAN_ORDER=['head','handLeft','handRight','soul','mindNumber','destinyNumber','bottomDigit'];
// Same positions and links as mobile/src/lib/nameSchemeVisuals.js and the web
// author grid: mind is bottom-left on screen, destiny bottom-right.
const HUMAN_POINTS={head:[150,42],handLeft:[50,146],handRight:[250,146],soul:[150,146],mindNumber:[50,260],destinyNumber:[250,260],bottomDigit:[150,260]};
const HUMAN_LINKS=[['head','soul'],['handLeft','soul'],['soul','handRight'],['soul','mindNumber'],['soul','bottomDigit'],['soul','destinyNumber']];
const trianglePoint=(row,column)=>[20+(32+(row+column)*48)*1.3,64+(64+row*46)*1.3];
const humanPoint=id=>HUMAN_POINTS[id].map((value,index)=>value*1.8+(index===0?50:90));
const finite=v=>typeof v==='number'&&Number.isFinite(v)&&Math.abs(v)<=100000;
const string=v=>typeof v==='string';
const rows=v=>Array.isArray(v)?v:[];
const record=v=>v&&typeof v==='object'&&!Array.isArray(v)?v:{};
const value=v=>v===null||finite(v)||string(v)&&v.length<=160;
const clean=v=>string(v)?v:'';
const text=(v,max=240)=>string(v)&&v.length<=max;
const entry=(id,label,number,detail='')=>({id,label,value:number,detail});
const base=(section,kind,entries,height,subtitle)=>({version:1,kind,title:clean(section.title),subtitle,width:640,height,entries});
function storedCells(report,vedic){
 if(!vedic){
  const cells=rows(report.raw?.scheme?.cells);
  if(cells.length!==9)return null;
  return LAYOUT.map(digit=>{const c=cells.find(c=>c?.digit===digit);return c?{digit,count:c.count,digits:c.digits,label:clean(c.title)}:null;});
 }
 const matrix=report.raw?.vedic?.yantra?.yantra_matrix;
 if(!Array.isArray(matrix)||matrix.length!==3||!matrix.every(r=>Array.isArray(r)&&r.length===3))return null;
 const values=rows(rows(report.sections).find(s=>s.id==='vedic-yantra')?.values);
 return LAYOUT.map((digit,index)=>{const digits=matrix[Math.floor(index/3)][index%3],v=values.find(v=>v?.digit===digit);return {digit,count:v?.value??(string(digits)?digits.length:undefined),digits,label:clean(v?.label).replace(/^\d\s*·\s*/,'')};});
}
function storedDirections(report,vedic){
 if(!vedic){
  const lines=rows(report.raw?.scheme?.lines);
  if(lines.length!==8)return null;
  return DIRECTIONS.map(([id,digits,label])=>{const line=lines.find(l=>l?.key===id);return line?{id,label:label+' '+digits.join('–'),digits:[...digits],value:line.value}:null;});
 }
 const sums=report.raw?.vedic?.yantra?.yantra_sums;if(!sums)return null;
 return DIRECTIONS.map(([id,digits,label],index)=>({id,label:label+' '+digits.join('–'),digits:[...digits],value:index<3?sums.horizontal?.[index]:index<6?sums.vertical?.[index-3]:sums.diagonal?.[index-6]}));
}

function sectionDiagram(report,section){
 if(!report||!section||!Array.isArray(section.values))return null;
 const raw=record(report.raw),values=section.values,entries=values.map((v,i)=>entry(clean(v?.key)||String(i),clean(v?.label),v?.value));
 let diagram;
 if(['personal','square','lines','vedic-yantra','vedic-lines'].includes(section.id)){
  const vedic=section.id.startsWith('vedic-'),cells=storedCells(report,vedic),directions=storedDirections(report,vedic);
  if(!cells||cells.some(c=>!c)||!directions||directions.some(d=>!d))return null;
  const kind=section.id==='personal'?'personal':section.id.endsWith('lines')?'lines':'square';
  diagram={...base(section,kind,entries,kind==='personal'?800:kind==='lines'?790:610,
   vedic?'Только цифры даты · линия = число планет в её ячейках':'Квадрат с дополнительными числами · линии считают количество'),cells,directions,vedic};
  if(kind==='personal'&&!['soul','mind','destiny','helping_mind','ruling','life_path','problem'].every(k=>entries.some(e=>e.id===k)))return null;
 }else if(section.id==='fractal'){
  if(!['digit1','digit2','digit3','digit4'].every(k=>finite(raw.fractal?.[k])))return null;
  diagram=base(section,'sequence',values.map((v,i)=>entry('digit'+(i+1),v.label,raw.fractal['digit'+(i+1)])),450,'Четыре позиции фрактала в сохранённом расчёте');
 }else if(section.id==='tasks'){
  if(!raw.tasks)return null;
  const items=[1,2,3,4].map(i=>{const p=raw.tasks['period'+i];return p?entry('problem'+i,'Задача '+i,raw.tasks['problem'+i],i===3?'На протяжении жизни':p.end===null?'От '+p.start+' лет':p.start+'–'+p.end+' лет'):null;});
  if(items.some(i=>!i))return null;
  diagram=base(section,'tasks',items,580,'Четыре задачи и границы соответствующих периодов');
 }else if(section.id==='individual'){
  const keys=['chig','chim','chid','chpg','chpm','chpd'];if(!keys.every(k=>finite(raw.individual?.[k]?.value)))return null;
  diagram=base(section,'individual',keys.map(k=>entry(k,clean(values.find(v=>v.key===k)?.label),raw.individual[k].value)),470,'Год → месяц → день · под каждым числом его задача');
 }else if(section.id==='cycles'){
  const years=rows(raw.cycles?.years).map(y=>({age:y.age,year:y.year,value:y.chlg}));if(!years.length)return null;
  diagram={...base(section,'series',entries,500,'Все 100 личных годов; возрастные границы взяты из расчёта'),years,periods:rows(raw.cycles?.periods).map(p=>({index:p.index,start:p.startAge,end:p.endAge}))};
 }else if(/^cycle-period-\d+$/.test(section.id)){
  const period=rows(raw.cycles?.periods).find(p=>'cycle-period-'+p.index===section.id);if(!period)return null;
  const keys=[['shadow','Тень'],['peak','Вершина'],['challenge','Вызов'],['transition','Переход']];
  diagram={...base(section,'period',keys.map(([k,label])=>entry(k,label,period[k]??null)),460,'Узлы периода и последовательность личных годов'),bounds:{start:period.startAge,end:period.endAge},years:rows(period.years).map(y=>({age:y.age,year:y.year,value:y.chlg}))};
 }else if(section.id==='vedic-numbers'){
  if(!raw.vedic?.numbers)return null;
  diagram=base(section,'sequence',entries,300,'Три числа отдельного ведического метода');
 }else if(section.id==='planets'){
  if(!raw.planets?.strength)return null;
  diagram=base(section,'bars',entries,Math.max(420,120+entries.length*56),'Семь планет · значения сохранённого планетарного расчёта');
 }else if(section.id==='profile-abracadabra'){
  const scheme=record(raw.profile?.name_schemes),levels=rows(scheme.rows),letters=rows(scheme.firstNine);
  if(levels.length!==9||letters.length!==9||!letters.every(v=>typeof v==='string'&&/^[A-Z]$/.test(v))||values.length!==45)return null;
  const cells=[];let index=0;
  for(let row=0;row<9;row++){
   if(!Array.isArray(levels[row])||levels[row].length!==9-row)return null;
   for(let column=0;column<9-row;column++){
    const stored=values[index++];if(stored?.row!==row||stored?.column!==column||stored.value!==levels[row][column])return null;
    cells.push({...entry('triangle-'+row+'-'+column,clean(stored.label),stored.value),row,column,...(row===0?{letter:letters[column]}:{})});
   }
  }
  diagram=base(section,'triangle',cells,690,'Девять исходных букв · все 45 сохранённых ячеек авторского треугольника');
 }else if(section.id==='profile-human'){
  const human=record(raw.profile?.name_schemes?.human);
  if(values.length!==HUMAN_ORDER.length||!HUMAN_ORDER.every((key,index)=>values[index]?.key===key&&values[index].value===human[key]))return null;
  diagram=base(section,'human',entries,720,'Позиции человечка имени: голова, руки, центр и три нижние опоры');
 }else return null;
 try{validate(diagram);return JSON.parse(JSON.stringify(diagram));}catch{return null;}
}

function validate(d){
 const fail=()=>{throw Error('Некорректная схема сохранённого отчёта');};
 if(!d||d.version!==1||!KINDS.has(d.kind)||!text(d.title)||!text(d.subtitle)||d.width!==640||!Number.isInteger(d.height)||d.height<250||d.height>1000||!Array.isArray(d.entries)||d.entries.length>120)fail();
 if(!d.entries.every(e=>e&&text(e.id,80)&&text(e.label,160)&&value(e.value)&&(e.detail===undefined||text(e.detail,160))))fail();
 if(['personal','square','lines'].includes(d.kind)){
  if(!Array.isArray(d.cells)||d.cells.length!==9||!d.cells.every((c,i)=>c&&c.digit===LAYOUT[i]&&Number.isInteger(c.count)&&c.count>=0&&c.count<=64&&c.digits===String(c.digit).repeat(c.count)&&text(c.label,160)))fail();
  if(!Array.isArray(d.directions)||d.directions.length!==8||!d.directions.every((v,i)=>v&&v.id===DIRECTIONS[i][0]&&Array.isArray(v.digits)&&v.digits.join(',')===DIRECTIONS[i][1].join(',')&&text(v.label,120)&&finite(v.value)&&v.value>=0))fail();
  if(typeof d.vedic!=='boolean')fail();
 }
 if(d.years!==undefined&&(!Array.isArray(d.years)||d.years.length>120||!d.years.every(y=>y&&Number.isInteger(y.age)&&Number.isInteger(y.year)&&finite(y.value))))fail();
 if(d.periods!==undefined&&(!Array.isArray(d.periods)||d.periods.length>120||!d.periods.every(p=>p&&Number.isInteger(p.index)&&finite(p.start)&&finite(p.end))))fail();
 if(d.bounds!==undefined&&(!finite(d.bounds?.start)||!finite(d.bounds?.end)))fail();
 if(d.kind==='personal'&&(d.entries.length<7||d.entries.length>9)||d.kind==='tasks'&&d.entries.length!==4||d.kind==='individual'&&d.entries.length!==6||d.kind==='period'&&(d.entries.length!==4||!d.years?.length)||d.kind==='series'&&!d.years?.length)fail();
 if(d.kind==='triangle'){
  if(d.height!==690||d.entries.length!==45)fail();
  let index=0;for(let row=0;row<9;row++)for(let column=0;column<9-row;column++){
   const e=d.entries[index++];if(e.id!=='triangle-'+row+'-'+column||e.row!==row||e.column!==column||!Number.isInteger(e.value)||e.value<1||e.value>9||(row===0?!/^[A-Z]$/.test(e.letter):e.letter!==undefined))fail();
  }
 }
 if(d.kind==='human'&&(d.height!==720||d.entries.length!==7||!HUMAN_ORDER.every((key,i)=>d.entries[i]?.id===key&&Number.isInteger(d.entries[i].value)&&d.entries[i].value>=1&&d.entries[i].value<=9)))fail();
 return d;
}
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const color={ink:'#183B62',muted:'#61758B',line:'#CEDDD8',pale:'#EDF6F2',green:'#D0E9DF',accent:'#267568',blue:'#356FA5'};
function label(x,y,value,size=24,fill=color.ink,anchor='middle',weight=400,extra=''){
 return `<text x="${x}" y="${y}" text-anchor="${anchor}" font-family="Arial, sans-serif" font-size="${size}" font-weight="${weight}" fill="${fill}" ${extra}>${esc(value)}</text>`;
}
function rect(x,y,w,h,fill=color.pale,stroke='none',r=18){return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${fill}" stroke="${stroke}" stroke-width="2"/>`;}
function line(x1,y1,x2,y2,fill=color.line,width=3,extra=''){return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${fill}" stroke-width="${width}" stroke-linecap="round" ${extra}/>`;}
function arrow(x1,y1,x2,y2){return line(x1,y1,x2,y2)+`<path d="M${x2-8} ${y2-6} L${x2} ${y2} L${x2-8} ${y2+6}" fill="none" stroke="${color.line}" stroke-width="3"/>`;}
function titleLines(value,length=42){const words=String(value).split(/\s+/),out=[''];for(const word of words){const i=out.length-1;if(out[i]&&(out[i]+' '+word).length>length)out.push(word);else out[i]+=(out[i]?' ':'')+word;}return out;}
function wrapped(x,y,value,width=160,size=23){const lines=titleLines(value,Math.max(8,Math.floor(width/(size*.55))));return lines.map((t,i)=>label(x,y+i*(size+5),t,size)).join('');}
function cell(x,y,w,h,c,active){
 const digits=c.digits||'—',size=Math.max(4,Math.min(42,(w-16)/(Math.max(1,digits.length)*.68)));
 return `<g data-cell="${c.digit}" data-count="${c.count}">${rect(x,y,w,h,active?color.green:color.pale,active?color.accent:'none')}${label(x+12,y+24,c.digit,18,color.muted,'start')}${label(x+w/2,y+h*.55,digits,size,color.ink,'middle',600)}${label(x+w/2,y+h-13,'кол-во '+c.count,18,color.muted)}</g>`;
}
function square(d,activeIndex,personal=false){
 let out='';const step=personal?110:150,x=personal?174:70,y=104,w=step-12,h=personal?100:126;
 const active=d.kind==='lines'&&Number.isInteger(activeIndex)&&activeIndex>=0&&activeIndex<8?d.directions[activeIndex]:null;
 const position=digit=>{const index=LAYOUT.indexOf(digit);return [x+(index%3)*step+w/2,y+Math.floor(index/3)*(h+12)+h/2];};
 d.cells.forEach((c,i)=>{out+=cell(x+(i%3)*step,y+Math.floor(i/3)*(h+12),w,h,c,!!active?.digits.includes(c.digit)||d.kind==='square'&&i===activeIndex);});
 if(d.kind==='lines')d.directions.forEach((direction,i)=>{const [a,b]=[position(direction.digits[0]),position(direction.digits[2])];out+=`<g data-direction="${esc(direction.id)}" data-active="${i===activeIndex}">${line(a[0],a[1],b[0],b[1],i===activeIndex?color.accent:color.blue,i===activeIndex?7:2,`opacity="${i===activeIndex?.85:.13}"`)}</g>`;});
 if(personal){
  const byId=Object.fromEntries(d.entries.map(e=>[e.id,e]));
  const pfill=key=>d.entries[activeIndex]?.id===key?color.green:color.pale;
  [['soul','Ч/Д'],['mind','Ч/У'],['destiny','Ч/С']].forEach(([key,name],i)=>{const yy=y+i*(h+12);out+=`<g data-node="${key}">${rect(12,yy,146,h,pfill(key))}${label(42,yy+40,name,25,color.ink,'middle',600)}${label(114,yy+65,byId[key].value,39)}</g>`;});
  d.directions.slice(0,3).forEach((v,i)=>{const yy=y+i*(h+12);out+=rect(512,yy,112,h)+label(568,yy+30,'Σ ряда',18,color.muted)+label(568,yy+67,v.value,36);});
  d.directions.slice(3,6).forEach((v,i)=>{out+=label(x+i*step+w/2,478,'Σ '+v.value,31);});
  out+=label(90,459,'3–5–7',18,color.muted)+label(90,492,d.directions[7].value,29)+label(568,459,'1–5–9',18,color.muted)+label(568,492,d.directions[6].value,29);
  // Ч/М is the wisdom number: it needs the name, so it is shown only when the report holds one.
  [['helping_mind','Ч/У*'],[byId.wisdom?'wisdom':null,'Ч/М'],['ruling','П/Ч']].forEach(([key,name],i)=>{const xx=12+i*208;out+=`<g data-node="${key||'wisdom-unavailable'}">${rect(xx,518,200,98,pfill(key))}${label(xx+100,550,name,25,color.ink,'middle',600)}${label(xx+100,589,key?byId[key].value:'Нужно имя',key?34:22)}</g>`;});
  [['life_path','Жизненный путь'],['problem','Общая задача']].forEach(([key,name],i)=>{const xx=12+i*314;out+=`<g data-node="${key}">${rect(xx,640,306,102,pfill(key))}${label(xx+153,674,name,25)}${label(xx+153,716,byId[key].value,38)}</g>`;});
  out+=label(320,781,byId.wisdom?'Ч/М — число мудрости: число судьбы + полное число имени':'Ч/М не вычисляется только по дате рождения',20,color.muted);
 }else{
  d.directions.slice(0,3).forEach((v,i)=>{out+=label(568,y+i*(h+12)+68,'Σ '+v.value,29);});
  d.directions.slice(3,6).forEach((v,i)=>{out+=label(x+i*step+w/2,552,'Σ '+v.value,29);});
  if(d.kind==='square')out+=label(320,594,'Позиции: 1–4–7 / 2–5–8 / 3–6–9',22,color.muted);
  else d.directions.forEach((v,i)=>{const xx=12+(i%2)*314,yy=580+Math.floor(i/2)*48;out+=`<g data-legend="${esc(v.id)}">${rect(xx,yy,306,42,i===activeIndex?color.green:color.pale)}${label(xx+153,yy+29,v.label+' = '+v.value,23,i===activeIndex?color.accent:color.ink,'middle',i===activeIndex?700:400)}</g>`;});
 }
 return out;
}
function node(x,y,w,h,e,active){return `<g data-node="${esc(e.id)}">${rect(x,y,w,h,active?color.green:color.pale,active?color.accent:'none')}${wrapped(x+w/2,y+31,e.label,w-20,23)}${label(x+w/2,y+h-24,e.value===null?'—':e.value,46,color.ink,'middle',600)}</g>`;}
function sequence(d,active){const cols=d.entries.length===3?3:2,w=cols===3?192:290,h=140,gap=22;return d.entries.map((e,i)=>{const x=12+(i%cols)*(w+gap),y=104+Math.floor(i/cols)*(h+36);return node(x,y,w,h,e,i===active)+(i%cols<cols-1&&i<d.entries.length-1?arrow(x+w+3,y+h/2,x+w+gap-3,y+h/2):'');}).join('');}
function individual(d,active){let out='';d.entries.forEach((e,i)=>{const x=12+(i%3)*210,y=108+Math.floor(i/3)*190;out+=node(x,y,196,140,e,i===active);if(i<3)out+=line(x+98,y+145,x+98,y+184);if(i<2)out+=arrow(x+198,y+70,x+208,y+70);});return out;}
function tasks(d,active){return d.entries.map((e,i)=>{const y=108+i*114;return `<g data-node="${esc(e.id)}">${rect(12,y,612,98,i===active?color.green:color.pale)}${label(64,y+65,e.value,44,color.ink,'middle',600)}${label(120,y+35,e.label,25,color.ink,'start',600)}${label(120,y+73,e.detail,25,color.muted,'start')}${line(414,y+52,590,y+52,color.blue,4)}${line(414,y+40,414,y+64,color.blue,3)}${e.detail.startsWith('От')||i===2?arrow(582,y+52,608,y+52):line(590,y+40,590,y+64,color.blue,3)}</g>`;}).join('');}
function bars(d,active){const max=Math.max(1,...d.entries.map(e=>finite(e.value)?e.value:0));return d.entries.map((e,i)=>{const y=112+i*56,v=finite(e.value)?e.value:0;return `<g data-node="${esc(e.id)}">${label(18,y+23,e.label,25,color.ink,'start')}${rect(216,y,330,32,color.pale,'none',8)}${rect(216,y,330*Math.max(0,v)/max,32,i===active?color.accent:color.blue,'none',8)}${label(594,y+25,e.value,28,color.ink,'middle',600)}</g>`;}).join('');}
function triangle(d,active){
 let out='';const chosen=d.entries[active]?.id;
 d.entries.forEach(e=>{if(e.row>0){const point=trianglePoint(e.row,e.column);for(const column of [e.column,e.column+1]){
  const parent=trianglePoint(e.row-1,column),selected=e.id===chosen;
  out+=line(parent[0],parent[1],point[0],point[1],selected?color.accent:color.line,selected?4:2,`data-link-target="${e.id}" data-active="${selected}"`);
 }}});
 d.entries.forEach((e,i)=>{const [x,y]=trianglePoint(e.row,e.column),selected=i===active;
  if(e.row===0)out+=label(x,98,e.letter,22,color.muted);
  out+=`<g data-node="${e.id}" data-row="${e.row}" data-column="${e.column}"><title>${esc(e.label)}</title><circle cx="${x}" cy="${y}" r="23.4" fill="${selected?color.green:color.pale}" stroke="${selected?color.accent:color.line}" stroke-width="${selected?3:1.5}"/>${label(x,y+10,e.value,30,color.ink,'middle',600)}</g>`;
 });return out;
}
function human(d,active){
 let out='';const chosen=d.entries[active]?.id;
 HUMAN_LINKS.forEach(([a,b])=>{const from=humanPoint(a),to=humanPoint(b),selected=a===chosen||b===chosen;
  out+=line(from[0],from[1],to[0],to[1],selected?color.accent:color.line,selected?5:3,`data-link-target="${b}" data-active="${selected}"`);
 });
 d.entries.forEach((e,i)=>{const [x,y]=humanPoint(e.id),selected=i===active;
  out+=`<g data-node="${e.id}"><circle cx="${x}" cy="${y}" r="43.2" fill="${selected?color.green:color.pale}" stroke="${selected?color.accent:color.line}" stroke-width="${selected?3:2}"/>${label(x,y+14,e.value,44,color.ink,'middle',600)}${wrapped(x,y+76,e.label,174,24)}</g>`;
 });return out;
}
function series(d,active){
 const ys=d.years,max=Math.max(9,...ys.map(y=>y.value)),left=38,right=614,top=d.kind==='period'?300:130,bottom=d.kind==='period'?382:354;
 const px=i=>left+i*(right-left)/Math.max(1,ys.length-1),py=v=>bottom-v/max*(bottom-top);
 let out='';if(d.kind==='period'){
  d.entries.forEach((e,i)=>{const x=12+i*158;out+=node(x,104,142,142,e,i===active);if(i<3)out+=arrow(x+144,175,x+156,175);});
  out+=label(320,280,'Возраст '+d.bounds.start+'–'+d.bounds.end+' лет',24,color.muted);
 }else{
  [1,5,9].forEach(v=>{out+=line(left,py(v),right,py(v),color.line,1)+label(20,py(v)+6,v,19,color.muted);});
  (d.periods||[]).forEach((p,i)=>{const n=ys.findIndex(y=>y.age===p.start);if(n>=0){const x=px(n);out+=line(x,top-12,x,bottom+8,color.line,2,'stroke-dasharray="5 5"')+label(x,top-22,p.start,18,color.muted);}});
 }
 out+=line(left,bottom,right,bottom,color.line,2)+`<polyline data-series="${ys.length}" points="${ys.map((y,i)=>px(i).toFixed(2)+','+py(y.value).toFixed(2)).join(' ')}" fill="none" stroke="${color.blue}" stroke-width="3" stroke-linejoin="round"/>`;
 ys.forEach((y,i)=>{if(d.kind==='period'||i===0||i===ys.length-1||i%10===9)out+=label(px(i),bottom+28,y.age,20,color.muted);if(d.kind==='period')out+=label(px(i),bottom+54,y.year,17,color.muted)+label(px(i),py(y.value)-10,y.value,21);});
 if(d.kind==='series'&&Number.isInteger(active)&&active>=0&&active<ys.length){const y=ys[active];out+=`<circle data-active-year="${y.age}" cx="${px(active)}" cy="${py(y.value)}" r="7" fill="${color.accent}" stroke="#FFFFFF" stroke-width="3"/>`+label(320,392,y.age+' лет · '+y.year+' · число '+y.value,24,color.accent,'middle',600);}
 if(d.kind==='series')out+=label(320,420,'Возраст · каждое значение сохранено в таблице',23,color.muted)+label(320,466,'Границы периодов: '+(d.periods||[]).map(p=>p.start).join(' · '),20,color.muted);
 return out;
}
function diagramSvg(diagram,{activeIndex=-1,width,height}={}){
 const d=validate(diagram),active=Number.isInteger(activeIndex)?activeIndex:-1;
 if(width!==undefined&&(!finite(width)||width<1||width>8192)||height!==undefined&&(!finite(height)||height<1||height>8192))throw Error('Некорректный размер схемы');
 const dimensions=(width!==undefined?` width="${width}"`:'')+(height!==undefined?` height="${height}"`:'');
 let body=['personal','square','lines'].includes(d.kind)?square(d,active,d.kind==='personal'):d.kind==='sequence'?sequence(d,active):d.kind==='tasks'?tasks(d,active):d.kind==='individual'?individual(d,active):d.kind==='bars'?bars(d,active):d.kind==='triangle'?triangle(d,active):d.kind==='human'?human(d,active):series(d,active);
 const heading=titleLines(d.title,44).slice(0,2).map((v,i)=>label(320,34+i*29,v,26,color.ink,'middle',600)).join('');
 return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${d.width} ${d.height}"${dimensions} role="img" aria-label="${esc(d.title)}" preserveAspectRatio="xMidYMid meet"><title>${esc(d.title)}</title><desc>${esc(d.subtitle)}</desc>${rect(0,0,d.width,d.height,'#FFFFFF','none',0)}${heading}${body}</svg>`;
}
function diagramFocusBounds(diagram,activeIndex){
 const d=validate(diagram),index=activeIndex;
 if(!Number.isInteger(index)||index<0)return null;
 if(d.kind==='lines'&&index<8)return {x:52,y:88,width:572,height:482};
 if(d.kind==='square'&&index<9){const col=index%3,row=Math.floor(index/3);return {x:56+col*150,y:90+row*138,width:166,height:154};}
 if(d.kind==='tasks'&&index<4)return {x:0,y:96+index*114,width:640,height:122};
 if(d.kind==='triangle'&&index<45){const e=d.entries[index],[x,y]=trianglePoint(e.row,e.column);return {x:Math.max(0,Math.min(420,x-110)),y:e.row<2?70:Math.max(70,Math.min(510,y-115)),width:220,height:180};}
 if(d.kind==='human'&&index<7){const id=d.entries[index].id;if(id==='head')return {x:200,y:98,width:240,height:200};return {x:0,y:['handLeft','handRight','soul'].includes(id)?275:490,width:640,height:225};}
 if(d.kind==='personal'&&index<d.entries.length){
  const key=d.entries[index].id,row=['soul','mind','destiny'].indexOf(key);
  if(row>=0)return {x:0,y:92+row*112,width:640,height:124};
  if(key==='helping_mind')return {x:0,y:506,width:224,height:122};
  if(key==='ruling')return {x:416,y:506,width:224,height:122};
  if(key==='wisdom')return {x:208,y:506,width:224,height:122};
  if(key==='life_path')return {x:0,y:628,width:326,height:126};
  if(key==='problem')return {x:314,y:628,width:326,height:126};
 }
 return null;
}
module.exports={sectionDiagram,diagramSvg,diagramFocusBounds};
