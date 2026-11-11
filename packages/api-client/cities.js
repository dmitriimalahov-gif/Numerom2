// One request lifecycle for web and native autocomplete. No persistence of queries.
function createCitySearch({request,delay=300}) {
 let state={items:[],busy:false,error:''},listeners=new Set(),epoch=0,timer,abort;
 const emit=patch=>{state={...state,...patch};listeners.forEach(fn=>fn());};
 function clear(){epoch++;clearTimeout(timer);abort?.abort();emit({items:[],busy:false,error:''});}
 function search(value){
  clear();const query=value.trim();if(query.length<2||query.length>80)return;
  const version=epoch;emit({busy:true});
  timer=setTimeout(async()=>{abort=new AbortController();try{
   const result=await request('/geography/cities?q='+encodeURIComponent(query),{signal:abort.signal});
   if(version!==epoch)return;
   const items=(Array.isArray(result?.items)?result.items:[]).filter(item=>item&&/^\d{1,12}$/.test(item.id)&&['name','country','region','label'].every(key=>typeof item[key]==='string'&&item[key].length<=300)).slice(0,12);
   emit({items,busy:false});
  }catch(error){if(version===epoch)emit({items:[],busy:false,error:'Поиск городов недоступен. Введите город, регион и страну вручную.'});}},delay);
 }
 return {search,clear,dispose:clear,getSnapshot:()=>state,subscribe:fn=>{listeners.add(fn);return()=>listeners.delete(fn);}};
}
module.exports={createCitySearch};
