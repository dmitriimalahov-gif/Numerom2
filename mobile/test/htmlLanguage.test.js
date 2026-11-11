const test=require('node:test'),assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs'),vm=require('node:vm');
const {JSDOM}=require('jsdom'),React=require('react'),{renderToStaticMarkup}=require('react-dom/server'),ts=require('typescript');
const project=path.resolve(__dirname,'..');
function config(){const mod={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(project,'app.config.ts'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports:mod.exports,module:mod,process:{env:{APP_VARIANT:'development',EXPO_PUBLIC_API_URL:'http://127.0.0.1:18006'}}});return mod.exports.default;}
function assertLanguage(html){const dom=new JSDOM(html),doc=dom.window.document;try{assert.equal(doc.documentElement.lang,'ru');assert.equal(doc.documentElement.getAttribute('translate'),'no');assert.equal(doc.querySelector('meta[name="google"]')?.content,'notranslate');assert.ok(doc.querySelector('meta[name="viewport"]'));assert.ok(doc.querySelector('style#expo-reset'));assert.equal(doc.querySelectorAll('style#expo-reset').length,1);}finally{dom.window.close();}}
test('SPA uses the real Expo HTML template with Russian language and preserves root reset and script injection',async()=>{
 const exp=config();assert.equal(exp.web.output,'single');assert.equal(exp.web.lang,'ru');
 const {createTemplateHtmlFromExpoConfigAsync}=require('../node_modules/expo/node_modules/@expo/cli/build/src/start/server/webTemplate');
 const html=await createTemplateHtmlFromExpoConfigAsync(project,{exp,scripts:['/qa-entry.js'],cssLinks:[]});assertLanguage(html);const doc=new JSDOM(html).window.document;
 assert.equal(doc.title,'NumerOM');assert.equal(doc.querySelector('script').getAttribute('src'),'/qa-entry.js');assert.ok(doc.querySelector('#root'));assert.match(doc.querySelector('#expo-reset').textContent,/overflow:\s*hidden/);assert.match(doc.querySelector('#expo-reset').textContent,/height:\s*100%/);assert.match(doc.querySelector('noscript').textContent,/включите JavaScript/);
});
test('static HTML keeps Expo server attributes, head nodes, body nodes and ScrollView reset',()=>{
 const mod={exports:{}},source=fs.readFileSync(path.join(project,'src/app/+html.tsx'),'utf8');
 const deps={'react/jsx-runtime':require('react/jsx-runtime'),'expo-router/html':{ScrollViewStyleReset:()=>React.createElement('style',{id:'expo-reset'},'#root,body,html{height:100%}body{overflow:hidden}'),useServerDocumentContext:()=>({htmlAttributes:{lang:'en','data-server':'yes'},bodyAttributes:{'data-body':'yes'},headNodes:React.createElement('meta',{name:'qa-head',content:'kept'}),bodyNodes:React.createElement('script',{id:'qa-server'})})}};
 vm.runInNewContext(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module:mod,exports:mod.exports,require:name=>{assert.ok(name in deps,name);return deps[name];}});
 const html=renderToStaticMarkup(React.createElement(mod.exports.default,null,React.createElement('div',{id:'root'},'NumerOM')));assertLanguage(html);const dom=new JSDOM(html);try{assert.equal(dom.window.document.documentElement.dataset.server,'yes');assert.equal(dom.window.document.body.dataset.body,'yes');assert.ok(dom.window.document.querySelector('meta[name="qa-head"]'));assert.ok(dom.window.document.querySelector('#qa-server'));assert.equal(dom.window.document.querySelector('#root').textContent,'NumerOM');}finally{dom.window.close();}
});
test('completed Expo export includes Russian untranslated HTML and a real bundle', {skip:!process.env.NUMEROM_HTML_EXPORT_DIR},()=>{
 const output=path.resolve(process.env.NUMEROM_HTML_EXPORT_DIR),html=fs.readFileSync(path.join(output,'index.html'),'utf8');assertLanguage(html);
 const dom=new JSDOM(html);try{const script=dom.window.document.querySelector('script[src]')?.getAttribute('src');assert.match(script,/\/_expo\/static\/js\/web\/entry-[a-f0-9]+\.js$/);const relative=script.slice(script.indexOf('_expo/'));assert.ok(fs.statSync(path.join(output,relative)).size>100000);assert.doesNotMatch(html,/%LANG_ISO_CODE%|%WEB_TITLE%/);}finally{dom.window.close();}
});
