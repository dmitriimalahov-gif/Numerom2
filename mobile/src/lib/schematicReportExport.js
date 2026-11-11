/** Vector-only report graphics, built from the same presentation models as mobile. */
const {esc,p}=require('./savedReportExport');
const {nameSchemeVisuals}=require('./nameSchemeVisuals');
const {VEDIC_PLANETS,planetSeriesModel,solarWheelModel,periodTimelineModel}=require('./vedicVisuals');
const ink='#183b62',muted='#61758b',line='#d3dedb',blue='#eaf1f8',accent='#28705e';
const attrs=values=>Object.entries(values).map(([key,value])=>`${key}="${esc(value)}"`).join(' ');
const el=(tag,values,content='')=>`<${tag} ${attrs(values)}>${content}</${tag}>`;
const text=(x,y,value,options={})=>el('text',{x,y,fill:ink,'text-anchor':'middle',style:'font-size:12px',...options},esc(value));
const svg=(kind,label,width,height,body)=>el('svg',{xmlns:'http://www.w3.org/2000/svg',role:'img','aria-label':label,'data-scheme':kind,viewBox:`0 0 ${width} ${height}`,style:'width:100%;height:auto;display:block;overflow:visible'},`<title>${esc(label)}</title>${body}`);
const segment=(x1,y1,x2,y2,extra={})=>el('line',{x1,y1,x2,y2,stroke:line,'stroke-width':1.5,...extra});
const circle=(x,y,r,extra={})=>el('circle',{cx:x,cy:y,r,fill:blue,stroke:ink,'stroke-width':1.5,...extra});
function nameSchematicHtml(data,kind){
 const model=nameSchemeVisuals(data)[kind];
 if(!model)return p(!data.available?data.note:kind==='triangle'?data.triangleNote:data.humanNote);
 const nodes=new Map(model.nodes.map(n=>[n.id,n]));
 const links=model.edges.map(edge=>{const a=nodes.get(edge.from),b=nodes.get(edge.to);return a&&b?segment(a.x,a.y,b.x,b.y):'';}).join('');
 const letters=model.letters.map(l=>text(l.x,l.y,l.text)).join('');
 const cells=model.nodes.map(n=>el('g',{'data-node':n.id,'aria-label':`${n.title}: ${n.value}. ${n.formula}`},`<title>${esc(n.title+': '+n.value+'. '+n.formula)}</title>${circle(n.x,n.y,n.radius||17)}${text(n.x,n.y+5,n.value,{style:'font-size:18px;font-weight:600'})}${(n.labelLines||[]).map((value,i)=>text(n.x,n.labelY+i*14,value,{style:'font-size:11px'})).join('')}`)).join('');
 let html=`<figure class="report-figure">${svg(kind,kind==='triangle'?'Абракадабра имени — персональная схема':'Человек имени — персональная схема',model.width,model.height,links+letters+cells)}<figcaption>${esc(kind==='triangle'?'Каждая нижняя ячейка складывает два соседних числа верхнего ряда и сокращает сумму до одной цифры.':'Числа расположены по авторской схеме имени. Подробности каждой позиции приведены ниже.')}</figcaption></figure>`;
 const series=model.series;
 if(series){
 const ticks=series.ticks.map(t=>segment(24,t.y,series.width-16,t.y)+text(17,t.y+4,t.value,{'text-anchor':'end',style:'font-size:10px',fill:muted})).join('');
 const chart=series.kind==='distribution'?series.points.map(point=>el('rect',{x:point.x-9,y:point.y,width:18,height:Math.max(0,series.baseline-point.y),rx:3,fill:accent})).join(''):el('polyline',{points:series.points.map(v=>`${v.x},${v.y}`).join(' '),fill:'none',stroke:ink,'stroke-width':2});
 const points=series.points.map(point=>circle(point.x,point.y,3,{fill:accent,stroke:accent})+text(point.x,point.y-8,point.value,{style:'font-size:11px'})+text(point.x,series.baseline+19,point.label,{style:'font-size:11px'})).join('');
 html+=`<figure class="report-figure"><h3>${esc(series.title)}</h3>${svg(kind+'-chart',series.title,series.width,series.height,ticks+chart+points)}<figcaption>${esc(series.note)}</figcaption></figure>`;
 }
 if(kind==='human')html+=model.nodes.map(n=>`<article><h3>${esc(n.title)}: ${esc(n.value)}</h3>${p(n.formula)}${p(n.meaning)}</article>`).join('');
 return html;
}
function planetGraphHtml(days,key){
 const g=planetSeriesModel(days,key,{width:580,height:190});if(!g)return '';
 const grid=g.ticks.map(t=>segment(g.left,t.y,g.right,t.y)+text(g.left-9,t.y+4,t.value,{'text-anchor':'end',fill:muted,style:'font-size:10px'})).join('');
 const series=g.segments.map(s=>el('polyline',{points:s.points,fill:'none',stroke:g.planet.stroke||g.planet.color,'stroke-width':2})).join('');
 const points=g.points.map(v=>circle(v.x,v.y,days.length>30?1.7:3,{fill:g.planet.color,stroke:g.planet.stroke||g.planet.color,'data-date':v.date,'data-value':v.value})).join('');
 const dates=g.dateTicks.map(v=>text(v.x,g.bottom+23,v.label,{style:'font-size:10px','text-anchor':v.x===g.left?'start':v.x===g.right?'end':'middle'})).join('');
 return `<figure class="report-figure"><h3>${esc(g.planet.title)} · индекс 0–100</h3>${svg('planet-'+key,g.planet.title+' — маршрут по дням',g.width,g.height,grid+series+points+dates)}${g.missingDates.length?p('Нет показателей для дат: '+g.missingDates.join(', ')):''}</figure>`;
}
function routeChartsHtml(report){
 if(!report.days.some(d=>d.energies.length))return '';
 return `<section><h2>Планетарный маршрут · девять графиков</h2>${p('Даты на горизонтальной оси, персональный индекс на вертикальной. Значения совпадают с подробным разбором каждого дня.')}${VEDIC_PLANETS.map(planet=>planetGraphHtml(report.days,planet.key)).join('')}</section>`;
}
function solarSchematicHtml(day){
 const g=solarWheelModel(day);if(!g)return '';
 const bands=g.bands.map(b=>el('path',{d:b.path,fill:b.period==='day'?'#faf2da':'#e8edf6',stroke:'none'})).join('');
 const slices=g.segments.map(s=>el('g',{'data-hour':s.index,'aria-label':`${s.title} ${s.startLabel}–${s.endLabel}`},el('path',{d:s.path,fill:s.color,stroke:'white','stroke-width':1})+text(s.labelX,s.labelY+3,s.hour,{style:'font-size:10px',fill:s.planet==='shani'?'#ffffff':ink}))).join('');
 const markers=g.markers.map(m=>circle(m.x,m.y,2.5,{fill:ink,stroke:ink})+text(m.labelX,m.labelY,m.label,{style:'font-size:10px'})).join('');
 return `<figure class="report-figure solar-figure"><h3>Круг 24 планетарных часов</h3>${svg('solar-hours','24 планетарных часа от восхода до следующего восхода',g.width,g.height,bands+slices+markers+text(g.cx,g.cy-6,'Восход',{style:'font-size:12px'})+text(g.cx,g.cy+14,g.startLabel,{style:'font-size:18px;font-weight:600'}))}<figcaption>От ${esc(g.startLabel)} до ${esc(g.endLabel)} следующего дня. ${g.timeBasis==='elapsed'?'Размер сектора соответствует реальной продолжительности интервала с учётом перевода часов.':'Для сохранённого маршрута без смещения UTC сектора построены по местным часам.'} Часы пронумерованы от 1 до 24; расшифровка ниже.</figcaption></figure>`;
}
function periodSchematicHtml(day){
 const g=periodTimelineModel(day,{width:580});if(!g)return '';
 const rows=g.rows.map(row=>text(g.left,row.y-8,`${row.title} · ${row.startLabel}–${row.endLabel}`,{'text-anchor':'start',style:'font-size:12px'})+el('rect',{x:g.left,y:row.y,width:g.right-g.left,height:row.height,rx:4,fill:blue})+el('rect',{x:row.x,y:row.y,width:row.width,height:row.height,rx:4,fill:row.color,'data-period':row.id})).join('');
 const ticks=g.ticks.map(t=>text(t.x,g.height-5,t.label,{'text-anchor':t.x===g.left?'start':t.x===g.right?'end':'middle',style:'font-size:11px'})).join('');
 return `<figure class="report-figure"><h3>Периоды на шкале солнечного дня</h3>${svg('day-periods','Периоды от восхода '+g.startLabel+' до заката '+g.endLabel,g.width,g.height,rows+ticks)}${g.missingIds.length?p('Временные границы некоторых периодов отсутствуют в сохранённом результате.'):''}</figure>`;
}
const schematicStyles='.report-figure{margin:18px 0;break-inside:avoid-page;page-break-inside:avoid}.report-figure svg{background:#f7f9fc;border-radius:12px;print-color-adjust:exact;-webkit-print-color-adjust:exact}.report-figure figcaption{font-size:12px;line-height:1.5;color:#61758b;margin-top:8px}.solar-figure svg{max-width:340px;margin:auto}';
module.exports={nameSchematicHtml,routeChartsHtml,solarSchematicHtml,periodSchematicHtml,schematicStyles};
