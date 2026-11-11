// «Отчёт готовится»: the birth date's digits drop into a row, fly into the cells of the Pythagorean square,
// then its rows, columns and diagonals are traced and the cycle starts again. A pure function of time:
// the app (react-native-svg) and the site (DOM SVG) draw the same shapes. Decoration only — the saved
// report, not this animation, holds the calculation (extra square numbers are not drawn here).
'use strict';
const WIDTH=320,HEIGHT=300,CYCLE=10;
const LAYOUT=[1,4,7,2,5,8,3,6,9];
const CELL={w:72,h:50,gap:8,x:(WIDTH-3*72-2*8)/2,y:104};
const DIRECTIONS=[[1,4,7],[2,5,8],[3,6,9],[1,2,3],[4,5,6],[7,8,9],[1,5,9],[3,5,7]];
const STAGES=['Читаем дату рождения','Раскладываем цифры по квадрату','Проводим линии и диагонали','Собираем ваш отчёт'];
const COLOR={navy:'#183B62',accent:'#267568',pale:'#EDF6F2',line:'#D3DFEA',white:'#FFFFFF',blue:'#356FA5'};
const clamp=v=>Math.max(0,Math.min(1,v));
const ease=v=>{const t=clamp(v);return t*t*(3-2*t);};
// A little overshoot so a digit lands with weight.
const pop=v=>{const t=clamp(v);return t<1?1-Math.pow(1-t,3)*Math.cos(t*Math.PI*1.4):1;};
const DEMO='14.07.1988';

function cellCenter(digit){
 const i=LAYOUT.indexOf(digit);
 return [CELL.x+(i%3)*(CELL.w+CELL.gap)+CELL.w/2,CELL.y+Math.floor(i/3)*(CELL.h+CELL.gap)+CELL.h/2];
}

function dateChars(birthDate){
 return /^\d{2}\.\d{2}\.\d{4}$/.test(String(birthDate||''))?String(birthDate).split(''):DEMO.split('');
}

/** Shapes of one moment: {kind:'rect'|'text'|'line', …} in a 320×300 view, plus the stage caption. */
function loadingFrame(seconds,birthDate,reduced=false){
 const t=reduced?7.9:((seconds%CYCLE)+CYCLE)%CYCLE,shapes=[];
 const fade=reduced?1:1-ease((t-9.2)/.8)*1;
 const chars=dateChars(birthDate);
 // Drifting faint digits keep the frame alive behind everything.
 if(!reduced)for(let i=0;i<9;i++){
  const x=(i*41+seconds*(6+(i%3)*3))%(WIDTH+40)-20,y=18+(i*67)%(HEIGHT-30)+6*Math.sin(seconds/1.7+i);
  shapes.push({kind:'text',x,y,text:String((i*4)%9+1),size:16+(i%3)*8,weight:700,color:COLOR.blue,opacity:.06});
 }
 // 1. The date, one digit after another.
 const step=26,left=WIDTH/2-(chars.length-1)*step/2,places=[];
 chars.forEach((ch,i)=>{
  const x=left+i*step,y=40,p=reduced?1:pop((t-.12*i)/.45);
  places.push([x,y]);
  if(ch==='.'){shapes.push({kind:'text',x,y:y+8,text:'.',size:20,weight:700,color:COLOR.navy,opacity:clamp(p)*fade});return;}
  shapes.push({kind:'rect',x:x-11,y:y-14-(1-p)*24,w:22,h:28,r:6,fill:COLOR.white,stroke:COLOR.line,opacity:clamp(p)*fade});
  shapes.push({kind:'text',x,y:y+6-(1-p)*24,text:ch,size:16,weight:700,color:COLOR.navy,opacity:clamp(p)*fade});
 });
 // 2. Every non-zero digit flies into its cell; a cell shows the digits that have landed.
 const flights=chars.map((ch,i)=>({digit:+ch,from:places[i],i})).filter(f=>f.digit>0&&!Number.isNaN(f.digit))
  .map((f,k)=>({...f,at:1.4+k*.32}));
 const landed={},cellTexts=[],flying=[];
 flights.forEach(f=>{if(t>=f.at+.55)landed[f.digit]=(landed[f.digit]||'')+f.digit;});
 LAYOUT.forEach((digit,i)=>{
  const [cx,cy]=cellCenter(digit),p=reduced?1:ease((t-1.1-i*.05)/.4),text=landed[digit]||'';
  const glow=reduced?0:clamp(1-(t-(flights.filter(f=>f.digit===digit).map(f=>f.at+.55).filter(a=>a<=t).pop()??-9))/.5);
  shapes.push({kind:'rect',x:cx-CELL.w/2,y:cy-CELL.h/2,w:CELL.w,h:CELL.h,r:10,fill:glow>0?COLOR.pale:COLOR.white,stroke:glow>0?COLOR.accent:COLOR.line,opacity:p*fade});
  // Cell digits are drawn after the lines, so a traced line never covers them.
  cellTexts.push({kind:'text',x:cx-CELL.w/2+8,y:cy-CELL.h/2+12,text:String(digit),size:9,weight:400,color:'#8A9BAD',anchor:'start',opacity:p*fade});
  cellTexts.push({kind:'text',x:cx,y:cy+7,text:text||'—',size:text.length>3?15:19,weight:700,color:text?COLOR.navy:'#B4C2D0',opacity:p*fade});
 });
 flights.forEach(f=>{
  const v=reduced?1:clamp((t-f.at)/.55);
  if(v<=0||v>=1)return;
  const [tx,ty]=cellCenter(f.digit),e=ease(v),x=f.from[0]+(tx-f.from[0])*e,y=f.from[1]+(ty-f.from[1])*e-34*Math.sin(Math.PI*e);
  flying.push({kind:'rect',x:x-10,y:y-13,w:20,h:26,r:6,fill:COLOR.accent,stroke:COLOR.accent,opacity:fade});
  flying.push({kind:'text',x,y:y+5,text:String(f.digit),size:14,weight:700,color:COLOR.white,opacity:fade});
 });
 // 3. Rows, columns and diagonals are traced one after another; the current one glows.
 DIRECTIONS.forEach((digits,i)=>{
  const start=4.9+i*.5,v=reduced?1:ease((t-start)/.38);
  if(v<=0)return;
  const [a,b]=[cellCenter(digits[0]),cellCenter(digits[2])],dx=b[0]-a[0],dy=b[1]-a[1],len=Math.hypot(dx,dy),ux=dx/len,uy=dy/len;
  const s=[a[0]-ux*30,a[1]-uy*22],e=[b[0]+ux*30,b[1]+uy*22],current=!reduced&&t>=start&&t<start+.5;
  shapes.push({kind:'line',x1:s[0],y1:s[1],x2:s[0]+(e[0]-s[0])*v,y2:s[1]+(e[1]-s[1])*v,width:current?4:2,color:current?COLOR.accent:COLOR.blue,opacity:(current?.95:.28)*fade});
 });
 shapes.push(...cellTexts,...flying);
 const stage=t<1.4?0:t<4.9?1:t<9?2:3;
 return {width:WIDTH,height:HEIGHT,shapes,stage,caption:STAGES[stage]};
}

module.exports={loadingFrame,LOADING_CYCLE:CYCLE,LOADING_STAGES:STAGES};
