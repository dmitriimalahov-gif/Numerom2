const sections=[
 {title:'Моё пространство',items:[{id:'home',label:'Главная',path:'/home',icon:'grid-outline'}]},
 {title:'Расчёты',items:[
  {id:'full-report',label:'Полный разбор',path:'/full-report',icon:'document-text-outline'},
  {id:'numbers',label:'Личные числа',path:'/numbers',icon:'sparkles-outline'},
  {id:'relationships',label:'Совместимость',path:'/relationships',icon:'people-outline'},
  {id:'number-tools',label:'Имя, адрес и автомобиль',path:'/number-tools',icon:'calculator-outline'},
  {id:'vedic-time',label:'Время и планетарный маршрут',path:'/vedic-time',icon:'planet-outline'},
  {id:'assessment',label:'Самонаблюдение',path:'/assessment',icon:'compass-outline'},
 ]},
 {title:'Обучение',items:[
  {id:'learning',label:'Уроки и практика',path:'/learning',icon:'book-outline'},
  {id:'library',label:'Авторские схемы',path:'/library',icon:'shapes-outline'},
  {id:'audio-guide',label:'Аудиогид',path:'/audio-guide',icon:'headset-outline'},
 ]},
 {title:'Для бизнеса',items:[{id:'business',label:'Бизнес · сотрудники и команды',path:'/business',icon:'briefcase-outline'}]},
 {title:'Мой аккаунт',items:[
  {id:'consultations',label:'Консультации',path:'/consultations',icon:'chatbubbles-outline'},
  {id:'top-up',label:'Пополнить баллы',path:'/top-up',icon:'add-circle-outline'},
  {id:'credits',label:'История баллов',path:'/credits',icon:'receipt-outline'},
  {id:'profile',label:'Профиль и вход',path:'/profile',icon:'person-outline'},
 ]},
];
const guest=[{title:'Знакомство с NumerOM',items:[
 {id:'welcome',label:'Войти или зарегистрироваться',path:'/',icon:'log-in-outline'},
 {id:'guide',label:'Авторские схемы',path:'/guide',icon:'shapes-outline'},
 {id:'guest-audio-guide',label:'Аудиогид',path:'/audio-guide',icon:'headset-outline'},
 {id:'forgot-password',label:'Восстановить пароль',path:'/forgot-password',icon:'key-outline'},
]}];
const admin={title:'Управление',items:[{id:'admin',label:'Кабинет администратора',path:'/admin',icon:'settings-outline'}]};
function navigationSections({signedIn,isAdmin=false}){
 const visible=signedIn?[...sections,...(isAdmin?[admin]:[])]:guest;
 return visible.map(section=>({...section,items:section.items.map(item=>({...item}))}));
}
function pathOnly(pathname){return (typeof pathname==='string'?pathname.split(/[?#]/,1)[0]:'/').replace(/\/+$/,'')||'/';}
function activeSection(pathname,signedIn){
 const path=pathOnly(pathname);
 if(path.startsWith('/lesson/'))return '/learning';
 if(path==='/payment-result')return '/top-up';
 if(path==='/guide')return signedIn?'/library':'/guide';
 if(path==='/reset-password')return '/forgot-password';
 return path;
}
const titles=Object.fromEntries([...sections,...guest,admin].flatMap(section=>section.items.map(item=>[item.path,item.label])));
const parents={'/relationships':'/numbers','/number-tools':'/numbers','/vedic-time':'/numbers','/assessment':'/numbers','/audio-guide':'/learning','/consultations':'/profile','/top-up':'/profile','/credits':'/profile','/admin':'/profile','/payment-result':'/top-up','/forgot-password':'/','/reset-password':'/'};
function screenNavigation(pathname,signedIn){
 const path=pathOnly(pathname);
 if(path.startsWith('/lesson/'))return {title:'Обучение',parent:'/learning'};
 if(path==='/guide')return {title:'Авторские схемы',parent:signedIn?'/library':'/'};
 if(path==='/audio-guide'&&!signedIn)return {title:'Аудиогид',parent:null};
 if(path==='/payment-result')return {title:'Результат оплаты',parent:'/top-up'};
 if(path==='/reset-password')return {title:'Новый пароль',parent:'/'};
 if(path==='/telegram')return {title:'Вход через Telegram',parent:'/'};
 if(path==='/daily-email')return {title:'Утренние письма',parent:'/'};
 return {title:path==='/'?'Добро пожаловать':titles[path]||'NumerOM',parent:parents[path]||null};
}
module.exports={navigationSections,activeSection,screenNavigation};
