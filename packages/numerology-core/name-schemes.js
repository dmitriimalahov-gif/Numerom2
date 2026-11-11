// Same A–Z table and neighbour-sum triangle as ComprehensiveReport.jsx.
// Separate saved fields are required; a combined name is never split or guessed.
const groups=['AJS','BKT','CLU','DMV','ENW','FOX','GPY','HQZ','IR'];
const digit=ch=>groups.findIndex(group=>group.includes(ch))+1;
const reduce=n=>{let x=Math.abs(n);while(x>9)x=String(x).split('').reduce((sum,d)=>sum+Number(d),0);return x;};
function nameSchemes(parts,birthDate){
 if(!parts||typeof parts.name!=='string'||typeof parts.surname!=='string')return {available:false,note:'В сохранённом отчёте нет отдельных полей имени и фамилии. Для этих схем нужен новый личный расчёт с заполненным профилем.'};
 if([parts.name,parts.surname].some(v=>! /^[A-Za-z '\-’]*$/.test(v)))return {available:false,note:'Для этих авторских схем используются латинские буквы A–Z. Заполните имя и фамилию в поддерживаемом алфавите перед новым расчётом.'};
 const name=parts.name.toUpperCase().replace(/[^A-Z]/g,''),surname=parts.surname.toUpperCase().replace(/[^A-Z]/g,'');
 const firstNine=(name+surname).slice(0,9).split(''),rows=[];
 if(firstNine.length===9){rows.push(firstNine.map(digit));for(let i=1;i<9;i++)rows.push(rows[i-1].slice(0,-1).map((n,j)=>reduce(n+rows[i-1][j+1])));}
 let human=null;
 const m=/^(\d{2})\.(\d{2})\.(\d{4})$/.exec(birthDate||'');
 if(name.length>=4&&m){const ds=[...name].map(digit);human={head:ds[0],handLeft:ds[2],handRight:ds[1],soul:ds[3],mindNumber:reduce(Number(m[2])),destinyNumber:reduce(Number(m[1])+Number(m[2])+Number(m[3])),bottomDigit:ds.at(-1)};}
 return {available:true,name,surname,nameLetters:[...name].map(letter=>({letter,digit:digit(letter)})),surnameLetters:[...surname].map(letter=>({letter,digit:digit(letter)})),firstNine,rows,human,triangleNote:rows.length?'':'Для треугольника нужны не менее 9 латинских букв в имени и фамилии вместе.',humanNote:human?'':'Для человечка нужны не менее 4 латинских букв именно в имени.'};
}
module.exports={nameSchemes};
