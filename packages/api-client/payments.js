/** Payment states are server receipts, never inferred from a return URL. */
const ids=new Set(['one_time','monthly','annual','master_consultation']);
function paymentCatalog(value) {
 if(!value || !Array.isArray(value.packages) || typeof value.enabled!=='boolean' || !['test','live'].includes(value.mode) || !Array.isArray(value.clients) || value.clients.some(c=>!['mobile','web'].includes(c)) || !Number.isFinite(value.balance) || value.balance<0 || !Number.isFinite(value.test_balance) || value.test_balance<0)throw Error('Не удалось загрузить пакеты');
 const seen=new Set();
 for(const p of value.packages) {
  if(!ids.has(p.id) || seen.has(p.id) || typeof p.title!=='string' || !Number.isSafeInteger(p.credits) || p.credits<=0 || !Number.isSafeInteger(p.amount_total) || p.amount_total<=0 || p.currency!=='eur' || p.recurring!==false || !Number.isSafeInteger(p.access_days) || p.access_days<0 || typeof p.consultation!=='boolean')throw Error('Некорректная стоимость пакета');
  seen.add(p.id);
 }
 return value;
}
function stripeCheckout(value) {
 let url;try{url=new URL(value?.url);}catch{throw Error('Не удалось открыть оплату');}
 if(url.protocol!=='https:' || url.hostname!=='checkout.stripe.com' || url.username || url.password || url.port || !/^cs_(?:test_|live_)?[A-Za-z0-9]+$/.test(value.session_id) || !/^[a-f0-9]{64}$/.test(value.order_id) || !['test','live'].includes(value.mode) || !['creating','pending','processing','paid','failed','expired'].includes(value.state))throw Error('Некорректная ссылка Stripe');
 return value;
}
function paymentReceipt(value) {
 if(!value || !['creating','pending','processing','paid','failed','expired'].includes(value.status) || !['test','live'].includes(value.mode) || !Number.isSafeInteger(value.credits) || value.credits<=0 || !Number.isSafeInteger(value.amount_total) || value.amount_total<=0 || value.currency!=='eur' || !/^[a-f0-9]{64}$/.test(value.order_id) || (value.status==='paid' && value.payment_status!=='paid'))throw Error('Подтверждение оплаты пока не получено');
 return value;
}
function paymentMessage(receipt) {
 const r=paymentReceipt(receipt);
 if(r.status==='paid')return r.mode==='test' ? 'Тестовая оплата подтверждена. Рабочий баланс не изменён.' : `Оплата подтверждена. Начислено ${r.credits} баллов.`;
 if(r.status==='expired')return 'Срок оплаты истёк. Можно выбрать пакет заново.';
 if(r.status==='failed')return 'Stripe не подтвердил оплату. Проверьте платёж перед новой попыткой.';
 return 'Ожидаем подтверждение Stripe. Не оплачивайте повторно — проверьте статус чуть позже.';
}
module.exports={paymentCatalog,stripeCheckout,paymentReceipt,paymentMessage};
