type TelegramApp = {
 initData:string; ready:()=>void; expand:()=>void;
 setHeaderColor?:(color:string)=>void; setBackgroundColor?:(color:string)=>void;
 BackButton?:{show:()=>void;hide:()=>void;onClick:(cb:()=>void)=>void;offClick:(cb:()=>void)=>void};
 openInvoice:(url:string,callback:(status:string)=>void)=>void;
};
declare global { interface Window {Telegram?:{WebApp?:TelegramApp}} }

export function telegramApp():TelegramApp|null {
 if(typeof window==='undefined')return null;
 const app=window.Telegram?.WebApp;
 return app?.initData?app:null;
}

export function telegramContext():boolean {
 if(typeof window==='undefined')return false;
 try{return !!telegramApp()||window.location.pathname.includes('/telegram')||window.location.hash.includes('tgWebAppData=')||window.sessionStorage.getItem('numerom.telegram.context')==='1';}catch{return false;}
}
let sdk:Promise<TelegramApp>|null=null;
export function loadTelegram():Promise<TelegramApp>{
 const existing=telegramApp();if(existing)return Promise.resolve(existing);
 if(typeof window==='undefined')return Promise.reject(Error('Откройте приложение в Telegram.'));
 if(sdk)return sdk;
 sdk=new Promise<TelegramApp>((resolve,reject)=>{
  const script=document.createElement('script');script.src='https://telegram.org/js/telegram-web-app.js';script.async=true;
  const timer=setTimeout(()=>{script.remove();sdk=null;reject(Error('Telegram не ответил. Откройте приложение из меню бота.'));},10000);
  script.onload=()=>{clearTimeout(timer);const app=telegramApp();if(app){try{window.sessionStorage.setItem('numerom.telegram.context','1');}catch{}resolve(app);}else{sdk=null;reject(Error('Откройте NumerOM кнопкой в меню Telegram-бота.'));}};
  script.onerror=()=>{clearTimeout(timer);sdk=null;reject(Error('Не удалось подключить Telegram. Повторите попытку.'));};
  document.head.appendChild(script);
 });
 return sdk;
}

const sections=new Set(['home','numbers','full-report','relationships','number-tools','vedic-time','assessment','learning','library','audio-guide','consultations','business','top-up','credits','profile','admin']);
export function telegramSection(value:unknown){return typeof value==='string'&&sections.has(value)?'/'+value:'/home';}
export function openStarsInvoice(url:string):Promise<string>{
 const app=telegramApp();if(!app)return Promise.reject(Error('Оплата доступна внутри Telegram.'));
 const parsed=new URL(url);if(parsed.protocol!=='https:'||parsed.hostname!=='t.me'||parsed.port||parsed.username||parsed.password||!parsed.pathname.startsWith('/$'))throw Error('Некорректная ссылка оплаты.');
 return new Promise((resolve,reject)=>{try{app.openInvoice(url,resolve);}catch{reject(Error('Не удалось открыть оплату в Telegram.'));}});
}
