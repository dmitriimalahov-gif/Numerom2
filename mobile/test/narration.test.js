const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const ts=require('typescript');

function provider(){
 let value,loader,now=0,memo,depsBefore,timer,interval,contextValue;
 const requests=[];const api={request:async(...args)=>{requests.push(args);return value;}};
 const resource={data:null,loading:false,error:null,reload:()=>{}};
 const deps={
  react:{createContext:()=>({Provider:'Provider'}),useContext:()=>contextValue,useCallback:fn=>fn,useState:initial=>[initial,()=>{}],useRef:initial=>({current:initial}),
   useEffect:fn=>fn(),useMemo:(fn,deps)=>{if(!depsBefore||deps.some((item,i)=>item!==depsBefore[i])){memo=fn();depsBefore=deps;}return memo;}},
  'react/jsx-runtime':{jsx:(type,props)=>({type,props}),jsxs:(type,props)=>({type,props})},'react-native':{Text:'Text',View:'View'},
  '../../lib/session':{backendUrl:'https://audio.example.org',useSession:()=>({api})},
  '../../lib/useResource':{useResource:fn=>{loader=fn;return resource;}},
  '../ui':{Button:'Button',Notice:'Notice',s:{}},'./AudioTrack':{AudioTrack:'AudioTrack'},
 };
 const filename=path.resolve(__dirname,'../src/components/audio/Narration.tsx'),mod={exports:{}};
 vm.runInNewContext(ts.transpileModule(fs.readFileSync(filename,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,
  {exports:mod.exports,require:name=>{assert.ok(name in deps,`Unexpected dependency ${name}`);return deps[name];},URL,Date:{now:()=>now},setInterval:(fn,ms)=>{timer=fn;interval=ms;return 1;},clearInterval(){}});
 return {render:(path='/narration/project')=>mod.exports.NarrationProvider({path,children:null}),clip:(context,id)=>{contextValue=context;return mod.exports.NarrationClip({id});},available:(context,id)=>{contextValue=context;return mod.exports.AvailableNarration({id,fallback:'bundled'});},requests,load:()=>loader(),set:valueIn=>{value=valueIn;},time:value=>{now=value;},resource,get interval(){return interval;}};
}
const item=(url='first',hash='a')=>({id:'soul',section:'numbers',title:'Число души',text:'Текст',status:'ready',hash,seconds:30,url:`https://audio.example.org/api/student/narration-media/${url}`});

test('polling keeps the current playback URL stable until its renewal window',async()=>{
 const p=provider();p.render();p.set({items:[item()]});const first=(await p.load())[0];
 p.time(30000);p.set({items:[item('next')]});assert.equal((await p.load())[0].url,first.url);
 p.time(25*60*1000);assert.match((await p.load())[0].url,/next$/);
});
test('updated text or a different lesson cannot inherit the previous audio URL',async()=>{
 const p=provider();p.render('/narration/lesson/one');p.set({items:[item()]});await p.load();
 p.set({items:[item('changed','b')]});assert.match((await p.load())[0].url,/changed$/);
 p.render('/narration/lesson/two');p.set({items:[item('second-lesson')]});assert.match((await p.load())[0].url,/second-lesson$/);
});
test('pending recordings refresh automatically without rapid polling of completed libraries',()=>{
 const p=provider();p.resource.data=[{...item(),status:'preparing'}];p.render();assert.equal(p.interval,30000);
 p.resource.data=[item()];p.render();assert.equal(p.interval,25*60*1000);
});
test('full report polls after initial analysis 503 and missing clips instead of waiting 25 minutes',()=>{
 const p=provider();p.resource.data=null;p.resource.error='503';p.render('/full-reports/owned/narration');assert.equal(p.interval,30000);
 p.resource.error=null;p.resource.data=[];p.render('/full-reports/owned/narration');assert.equal(p.interval,30000);
 p.resource.data=[{...item(),status:'missing'}];p.render('/full-reports/owned/narration');assert.equal(p.interval,30000);
 p.resource.data=[item()];p.render('/full-reports/owned/narration');assert.equal(p.interval,25*60*1000);
});
test('failed paid report clip requests only current owned report retry',async()=>{
 const p=provider(),clip={...item(),id:'full-report-summary',status:'review'};let refreshed=0;
 const tree=p.clip({items:[clip],path:'/full-reports/owned/narration',refresh:async()=>{refreshed++;}},clip.id);
 function find(node){if(!node)return;if(Array.isArray(node)){for(const child of node){const value=find(child);if(value)return value;}}else{if(node.type==='Button')return node;return find(node.props?.children);}}
 const button=find(tree);assert.equal(button.props.title,'Повторить подготовку озвучки');button.props.onPress();await new Promise(resolve=>setImmediate(resolve));
 assert.equal(p.requests[0][0],'/full-reports/owned/video');assert.equal(p.requests[0][1].method,'POST');assert.equal(Object.keys(p.requests[0][1].body).length,0);assert.equal(refreshed,1);
});
test('narration rejects an unexpected host or non-media path before it reaches the player',async()=>{
 const p=provider();p.render();
 for(const url of ['https://other.example.org/api/student/narration-media/a','http://audio.example.org/api/student/narration-media/a','https://audio.example.org/private/a']){
  p.set({items:[{...item(),url}]});await assert.rejects(p.load(),/Адрес записи недоступен/);
 }
});

const flatten=node=>node==null||node===false?[]:typeof node==='string'?[node]:Array.isArray(node)?node.flatMap(flatten):[node.type,...flatten(node.props?.children),...(node.props?.message?[node.props.message]:[])];
test('a paid report whose voice is still recorded says so, and a dropped poll is not shown as a failure',()=>{
 const p=provider(),base={items:[],loading:false,refresh:async()=>{},path:`/full-reports/${'a'.repeat(64)}/narration`,guest:false};
 const preparing=flatten(p.clip({...base,error:'',dropped:false},'full-report-summary')).join(' ');
 assert.match(preparing,/Озвучка готовится: голос записывает главы вашего разбора/);assert.doesNotMatch(preparing,/Notice/);
 const dropped=flatten(p.clip({...base,error:'Не удалось связаться с NumerOM. Проверьте соединение или попробуйте позже.',dropped:true},'full-report-summary')).join(' ');
 assert.match(dropped,/Связь ненадолго прервалась/);assert.doesNotMatch(dropped,/Notice|Не удалось связаться/);
 // A real problem (a record address from elsewhere) is still an error, and lessons keep their usual notice.
 assert.match(flatten(p.clip({...base,error:'Адрес записи недоступен.',dropped:false},'full-report-summary')).join(' '),/Notice Адрес записи недоступен/);
 assert.match(flatten(p.clip({...base,path:'/narration/project',error:'Не удалось связаться',dropped:true},'soul')).join(' '),/Notice/);
});


test('ready legacy audio refreshes while its consultation replacement is recording',()=>{
 const p=provider();p.resource.data=[{...item(),replacement_pending:true}];p.render();assert.equal(p.interval,30000);
 p.resource.data=[item()];p.render();assert.equal(p.interval,25*60*1000);
});
test('bundled audio is replaced only by a ready available server recording',()=>{
 const p=provider();
 for(const context of [null,{items:[]},{items:[{...item(),status:'preparing'}]},{items:[{...item(),url:undefined}]}]){
  assert.equal(p.available(context,'soul').props.children,'bundled');
 }
 const selected=p.available({items:[item()]},'soul');assert.equal(selected.type.name,'NarrationClip');assert.equal(selected.props.id,'soul');
});
