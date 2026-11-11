const {test}=require('node:test');const assert=require('node:assert/strict');
const {paymentCatalog,stripeCheckout,paymentReceipt,paymentMessage}=require('..');
const order_id='a'.repeat(64),session_id='cs_test_123';
test('checkout only opens exact Stripe HTTPS origin',()=>{
 const good={url:'https://checkout.stripe.com/c/pay/cs_test_123',order_id,session_id,mode:'test',state:'pending'};assert.deepEqual(stripeCheckout(good),good);
 for(const url of ['javascript:alert(1)','https://checkout.stripe.com.evil.test/','https://evil.test/','http://checkout.stripe.com/','https://user@checkout.stripe.com/'])assert.throws(()=>stripeCheckout({...good,url}));
});
test('client cannot infer a successful payment from return parameters',()=>{
 for(const bad of [{success:true},{payment_status:'paid'},{status:'paid',credits:100},null])assert.throws(()=>paymentReceipt(bad));
 const receipt={order_id,status:'paid',payment_status:'paid',mode:'test',credits:10,amount_total:99,currency:'eur'};
 assert.match(paymentMessage(receipt),/Рабочий баланс не изменён/);
 assert.match(paymentMessage({...receipt,mode:'live'}),/Начислено 10/);
 assert.match(paymentMessage({...receipt,status:'processing',payment_status:'unpaid'}),/Не оплачивайте повторно/);
});
test('prices and credit amounts come from a validated server catalog',()=>{
 const data={enabled:true,mode:'test',clients:['mobile'],balance:0,test_balance:0,packages:[{id:'one_time',title:'Пакет',credits:10,amount_total:99,currency:'eur',recurring:false,access_days:30,consultation:false}]};
 assert.equal(paymentCatalog(data).packages[0].credits,10);
 for(const change of [{amount_total:NaN},{credits:-1},{currency:'usd'},{recurring:true}])assert.throws(()=>paymentCatalog({...data,packages:[{...data.packages[0],...change}]}));
 for(const change of [{clients:null},{clients:['evil']},{balance:null},{test_balance:-1}])assert.throws(()=>paymentCatalog({...data,...change}));
});
