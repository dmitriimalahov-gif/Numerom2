const fail = () => { throw Error('Сервер вернул неполный расчёт. Обновите историю.'); };
const price = value => Number.isInteger(value) && value >= 0 && value <= 1000000;
function createPaidCalculationController({catalog,history,calculate,refreshBalance,makeId,isCurrent=()=>true,pendingStore,onInsufficientCredits=()=>{}}, {parseCatalog,parseReceipt,validateDraft,historyLimit=30}) {
  let state={catalog:null,history:[],result:null,loading:false,busy:false,error:'',balanceError:'',pending:null};
  let revision=0,loadVersion=0,locked=false,storageReady=!pendingStore,loadingOperation=null;
  const listeners=new Set();
  const publish=patch=>{if(!isCurrent())return;state={...state,...patch};listeners.forEach(fn=>fn());};
  const merge=rows=>Array.from(new Map([...rows,...state.history].map(row=>[row.id,row])).values()).sort((a,b)=>Date.parse(b.created_at)-Date.parse(a.created_at)).slice(0,historyLimit);
  async function balance() {
    try {await refreshBalance();publish({balanceError:''});}
    catch(error) {publish({balanceError:error.message || 'Не удалось обновить баланс'});}
  }
  // Recovery owns the same pending intent as send. Coalesce readers and keep
  // sends out until every recovery write has settled, including storage errors.
  function load() {
    if(loadingOperation)return loadingOperation;
    if(locked || !isCurrent())return Promise.resolve();
    loadingOperation=loadOnce().finally(()=>{loadingOperation=null;});
    return loadingOperation;
  }
  async function loadOnce() {
    const version=++loadVersion, before=revision;publish({loading:true,error:''});
    try {
      if(!storageReady){
        const pending=await pendingStore.get();
        if(pending && (!/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i.test(pending.request_id)||!price(pending.expected_cost)||validateDraft(pending)))throw Error('Не удалось прочитать предыдущую попытку.');
        if(!isCurrent()||version!==loadVersion)return;
        storageReady=true;if(pending)publish({pending});
      }
      const [prices,data]=await Promise.all([catalog(),history()]);
      const next=parseCatalog(prices);
      if(!Array.isArray(data?.calculations))fail();
      const rows=data.calculations.map(parseReceipt);
      if(!isCurrent() || version!==loadVersion)return;
      const recovered=state.pending && rows.find(row=>row.request_id===state.pending.request_id);
      if(recovered&&pendingStore)await pendingStore.set(null);
      publish({error:'',catalog:next,history:merge(rows),...(before===revision?{result:recovered || state.result || rows[0] || null}:{}),...(recovered?{pending:null}:{})});
      if(recovered)await balance();
    } catch(error) {if(version===loadVersion)publish({error:error.message || 'Не удалось загрузить историю'});}
    finally {if(version===loadVersion)publish({loading:false});}
  }
  async function send(body) {
    if(locked || !isCurrent())return;
    if(loadingOperation){publish({error:'Дождитесь обновления цен и истории.'});return;}
    locked=true;revision++;publish({busy:true,error:'',pending:body});
    try {
      if(pendingStore)await pendingStore.set(body);
      if(!isCurrent())return;
      const result=parseReceipt(await calculate(body));
      if(result.request_id!==body.request_id)fail();
      if(!isCurrent())return;
      if(pendingStore)await pendingStore.set(null);
      publish({result,history:merge([result]),pending:null});await balance();
    } catch(error) {
      let definite=[400,402,409,422].includes(error.status);
      if(definite&&pendingStore){try{await pendingStore.set(null);}catch{definite=false;}}
      publish({error:error.message || 'Не удалось получить результат',...(definite?{pending:null}:{})});
    } finally {locked=false;publish({busy:false});}
  }
  return {
    getSnapshot:()=>state,subscribe:fn=>{listeners.add(fn);return()=>listeners.delete(fn);},load,
    select:result=>{revision++;publish({result:parseReceipt(result)});},
    refreshBalance:balance,
    retry:async()=>{if(state.pending)await send(state.pending);},
    calculate:async(draft,available)=>{
      if(locked || !isCurrent())return;
      if(loadingOperation){publish({error:'Дождитесь обновления цен и истории.'});return;}
      if(!storageReady){publish({error:'Сначала загрузите сохранённые попытки.'});return;}
      if(state.pending){publish({error:'Сначала проверьте предыдущую попытку или обновите историю.'});return;}
      if(state.balanceError){publish({error:'Сначала обновите баланс.'});return;}
      const cost=state.catalog?.[draft.kind];
      if(!price(cost) || !Number.isFinite(available) || available<0){publish({error:'Проверьте стоимость и доступный баланс.'});return;}
      if(available<cost){
        publish({error:'Недостаточно баллов. Пополните баланс.'});
        onInsufficientCredits({balance:available,cost});
        return;
      }
      const validation=validateDraft(draft);
      if(validation){publish({error:validation});return;}
      const body=JSON.parse(JSON.stringify({...draft,request_id:makeId(),expected_cost:cost}));
      await send(body);
    },
  };
}
module.exports={createPaidCalculationController};
