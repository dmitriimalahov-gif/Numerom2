function schemeFixture(){
 const counts={1:3,2:5,3:0,4:1,5:0,6:0,7:0,8:1,9:1};
 const names={1:'Солнце',2:'Луна',3:'Юпитер',4:'Раху',5:'Меркурий',6:'Венера',7:'Кету',8:'Сатурн',9:'Марс'};
 return {version:1,birth_date:'10.01.1982',method:'Цифры даты и четыре дополнительных числа',note:'Серверное примечание',additional_numbers:[22,4,20,2],
  cells:[1,4,7,2,5,8,3,6,9].map(digit=>({digit,count:counts[digit],digits:String(digit).repeat(counts[digit]),title:names[digit],meaning:`Символическое значение ${names[digit]}`})),
  lines:[['row-0',[1,4,7],4,'Горизонталь 1-4-7'],['row-1',[2,5,8],6,'Горизонталь 2-5-8'],['row-2',[3,6,9],1,'Горизонталь 3-6-9'],['col-0',[1,2,3],8,'Вертикаль 1-2-3'],['col-1',[4,5,6],1,'Вертикаль 4-5-6'],['col-2',[7,8,9],2,'Вертикаль 7-8-9'],['diag-0',[1,5,9],4,'Диагональ 1-5-9'],['diag-1',[3,5,7],0,'Диагональ 3-5-7']].map(([key,digits,value,title])=>({key,digits,value,title,meaning:`Смысл линии ${title}`}))};
}
module.exports={schemeFixture};
