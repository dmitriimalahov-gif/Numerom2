const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {navigationSections, activeSection, screenNavigation} = require('../src/lib/mobileNavigation');

const userPaths = ['/home','/numbers','/full-report','/relationships','/number-tools','/vedic-time','/assessment',
  '/learning','/library','/audio-guide','/consultations','/top-up','/credits','/profile','/business'];
const items = options => navigationSections(options).flatMap(section => section.items);

function routeInventory(directory, prefix = []) {
  return fs.readdirSync(directory, {withFileTypes:true}).flatMap(entry => {
    const segments = entry.name.startsWith('(') ? prefix : [...prefix, entry.name];
    if (entry.isDirectory()) return routeInventory(path.join(directory,entry.name), segments);
    // +html.tsx and other '+' files are Expo document hooks, not screens.
    if (!entry.name.endsWith('.tsx') || entry.name === '_layout.tsx' || entry.name.startsWith('+')) return [];
    const parts = [...prefix, entry.name.slice(0,-4)].filter(part => part !== 'index');
    return ['/' + parts.join('/')];
  });
}

test('every user section is available directly from the menu, with no duplicate destinations', () => {
  const entries = items({signedIn:true,isAdmin:false});
  assert.deepEqual(entries.map(item=>item.path).sort(), [...userPaths].sort());
  assert.equal(new Set(entries.map(item=>item.id)).size, entries.length);
  assert.equal(new Set(entries.map(item=>item.path)).size, entries.length);
  for (const section of navigationSections({signedIn:true})) {
    assert.ok(section.title.trim(), 'section has an accessible heading');
    for (const item of section.items) {
      assert.ok(item.label.trim(), 'each destination has a text label');
      assert.ok(item.icon, 'icons supplement the text label');
      assert.equal(activeSection(item.path, true), item.path, `${item.path} is selected when open`);
    }
  }
});

test('guest and administrator menus do not expose privileged links after sign-out or lock', () => {
  const ordinary = items({signedIn:true,isAdmin:false}).map(item=>item.path);
  const admin = items({signedIn:true,isAdmin:true}).map(item=>item.path);
  assert.deepEqual(admin.filter(route=>!ordinary.includes(route)), ['/admin']);
  const expected = ['/','/guide','/audio-guide','/forgot-password'].sort();
  assert.deepEqual(items({signedIn:false,isAdmin:false}).map(item=>item.path).sort(), expected);
  assert.deepEqual(items({signedIn:false,isAdmin:true}).map(item=>item.path).sort(), expected,
    'a stale admin flag cannot reveal account sections when not signed in');
});

test('every existing Expo route has a menu destination or an explicit contextual parent', () => {
  const routes = routeInventory(path.resolve(__dirname,'../src/app'));
  const destinations = new Set([
    ...items({signedIn:true,isAdmin:true}), ...items({signedIn:false}),
  ].map(item=>item.path));
  const contextual = new Map([
    ['/lesson/[id]', '/learning'], ['/payment-result', '/top-up'], ['/reset-password', '/'], ['/daily-email', '/'], ['/telegram', '/'],
  ]);
  for (const route of routes) {
    assert.ok(destinations.has(route) || contextual.has(route), `Unreachable route needs a menu or parent: ${route}`);
    if (contextual.has(route)) {
      const current = route.replace('[id]','lesson-example');
      assert.equal(screenNavigation(current, route !== '/reset-password').parent, contextual.get(route), current);
    }
  }
  for (const destination of destinations) assert.ok(routes.includes(destination), `Menu points to missing page: ${destination}`);
});

test('nested lesson and payment returns retain the correct menu selection and fallback', () => {
  for (const [route, selected, parent] of [
    ['/lesson/intro-1','/learning','/learning'],
    ['/payment-result','/top-up','/top-up'],
    ['/guide','/library','/library'],
  ]) {
    assert.equal(activeSection(route,true),selected,route);
    assert.equal(screenNavigation(route,true).parent,parent,route);
    assert.ok(screenNavigation(route,true).title.trim(),route);
  }
  assert.equal(activeSection('/guide',false),'/guide');
  assert.equal(screenNavigation('/guide',false).parent,'/');
});

test('direct visits always have a safe parent outside the five main sections', () => {
  for (const route of ['/home','/numbers','/learning','/library','/profile']) {
    assert.equal(screenNavigation(route,true).parent,null,route);
  }
  const parents = {
    '/relationships':'/numbers','/number-tools':'/numbers','/vedic-time':'/numbers','/assessment':'/numbers',
    '/top-up':'/profile','/credits':'/profile','/admin':'/profile','/consultations':'/profile','/audio-guide':'/learning',
  };
  for (const [route,parent] of Object.entries(parents)) {
    assert.equal(screenNavigation(route,true).parent,parent,route);
    assert.notEqual(parent,route,'fallback cannot loop to its own page');
  }
  for (const route of ['/forgot-password','/reset-password']) assert.equal(screenNavigation(route,false).parent,'/',route);
});

async function navigationScreen({pathname='/home',status='signedIn',user={id:'student',full_name:'Synthetic Student',credits_remaining:12},reducedMotion=true}={}) {
  const {JSDOM}=require('jsdom');
  const dom=new JSDOM('<div id="root"></div>',{url:'https://example.org/',pretendToBeVisual:true});
  const previous=new Map();
  for (const key of ['window','document','HTMLElement','Element','Node','ShadowRoot','ResizeObserver','navigator','getComputedStyle','requestAnimationFrame','cancelAnimationFrame','IS_REACT_ACT_ENVIRONMENT']) previous.set(key,Object.getOwnPropertyDescriptor(global,key));
  for (const [key,value] of Object.entries({window:dom.window,document:dom.window.document,HTMLElement:dom.window.HTMLElement,
    Element:dom.window.Element,Node:dom.window.Node,ShadowRoot:dom.window.ShadowRoot,ResizeObserver:class{observe(){}unobserve(){}disconnect(){}},navigator:dom.window.navigator,getComputedStyle:dom.window.getComputedStyle,
    requestAnimationFrame:dom.window.requestAnimationFrame.bind(dom.window),cancelAnimationFrame:dom.window.cancelAnimationFrame.bind(dom.window),IS_REACT_ACT_ENVIRONMENT:true})) {
    Object.defineProperty(global,key,{value,writable:true,configurable:true});
  }
  dom.window.ResizeObserver=global.ResizeObserver;
  Object.defineProperty(dom.window,'innerWidth',{value:320,configurable:true});
  const React=require('react'),{act}=React,{createRoot}=require('react-dom/client');
  // Use the real web Modal/Pressable: Escape, focus trapping and tabindex are
  // platform behavior that a DOM wrapper would not exercise.
  const native=require('react-native-web');
  let snapshot={status,user},currentPath=pathname,backAvailable=false,mounts=0;
  const appListeners=new Set(),calls=[];
  const router={navigate:value=>calls.push(['navigate',value]),replace:value=>calls.push(['replace',value]),
    back:()=>calls.push(['back']),canGoBack:()=>backAvailable};
  const deps={
    react:React,'react/jsx-runtime':require('react/jsx-runtime'),
    'react-native':{...native,useWindowDimensions:()=>({width:320,height:640,scale:1,fontScale:1}),
      AppState:{addEventListener:(_event,fn)=>{appListeners.add(fn);return {remove:()=>appListeners.delete(fn)};}},
      AccessibilityInfo:{addEventListener:()=>({remove(){}}),isReduceMotionEnabled:async()=>reducedMotion,setAccessibilityFocus(){}}},
    'react-native-safe-area-context':{SafeAreaView:native.View,useSafeAreaInsets:()=>({top:0,left:0,right:0,bottom:0})},
    'expo-router':{router,usePathname:()=>currentPath},'@expo/vector-icons':{Ionicons:()=>null},
    './Brand':{Brand:()=>React.createElement('span',null,'NumerOM logo')},
    './NavigationChromeContext':{NavigationChromeContext:React.createContext(false)},
    '../lib/telegram':{telegramApp:()=>null},
    '../lib/session':{useSession:()=>snapshot},'../lib/mobileNavigation':require('../src/lib/mobileNavigation'),
    '../lib/theme':{colors:{background:'#fff',surface:'#fff',line:'#ddd',navy:'#123',muted:'#456',accent:'#357',ink:'#123',blue:'#def'}},
  };
  const ts=require('typescript'),vm=require('node:vm'),mod={exports:{}};
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.resolve(__dirname,'../src/components/AppNavigation.tsx'),'utf8'),{
    compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX},
  }).outputText,{exports:mod.exports,require:name=>{assert.ok(name in deps,name);return deps[name];},document:dom.window.document,window:dom.window,setTimeout,clearTimeout});
  function Child(){React.useEffect(()=>{mounts++;},[]);return React.createElement('button',{'data-testid':'content-button'},'Screen content');}
  const root=createRoot(document.getElementById('root'));
  const render=()=>root.render(React.createElement(mod.exports.AppNavigation,null,React.createElement(Child)));
  await act(async()=>render());
  return {
    dom,calls,get mounts(){return mounts;},get text(){return document.body.textContent;},
    get visible(){return document.querySelector('[aria-label="Открыть меню разделов"]').getAttribute('aria-expanded')==='true';},
    async press(label){const node=document.querySelector(`[aria-label="${label}"]`);assert.ok(node,label);await act(async()=>{node.focus();node.click();});},
    async update(next){if('pathname' in next)currentPath=next.pathname;if('status' in next||'user' in next)snapshot={...snapshot,...next};await act(async()=>render());},
    async event(type,value){await act(async()=>{
      if(type==='app')for(const listener of appListeners)listener(value);
      if(type==='visibility'){Object.defineProperty(document,'hidden',{value,configurable:true});document.dispatchEvent(new dom.window.Event('visibilitychange'));}
      if(type==='escape')document.dispatchEvent(new dom.window.KeyboardEvent('keyup',{key:'Escape',bubbles:true}));
    });},
    async tryBackgroundFocus(){await act(async()=>document.querySelector('[data-testid="content-button"]').focus());},
    async finishAnimation(){await act(async()=>{
      const portal=[...document.body.children].find(node=>node!==document.getElementById('root'));
      assert.ok(portal?.firstElementChild,'real modal animation is present');
      portal.firstElementChild.dispatchEvent(new dom.window.Event('animationend',{bubbles:true}));
    });},
    canGoBack(value){backAvailable=value;},
    async close(){await act(async()=>root.unmount());dom.window.close();for(const [key,descriptor] of previous){if(descriptor)Object.defineProperty(global,key,descriptor);else delete global[key];}},
  };
}

test('drawer keeps web focus inside, closes on Escape and restores its named trigger',async()=>{
  const screen=await navigationScreen();try{
    await screen.press('Открыть меню разделов');assert.equal(screen.visible,true);
    assert.equal(document.activeElement.getAttribute('aria-label'),'Закрыть меню');
    assert.equal(document.querySelector('[aria-label="Главная"]').getAttribute('aria-current'),'page');
    assert.ok(document.querySelector('[data-testid="content-button"]').closest('[aria-hidden="true"]'),'screen content is hidden from web assistive technology while modal is open');
    const unnamed=[...document.querySelectorAll('[tabindex="0"]')].filter(node=>!node.textContent.trim()&&!node.getAttribute('aria-label')&&!['none','presentation'].includes(node.getAttribute('role')));
    assert.equal(unnamed.length,0,'the backdrop must not be an invisible keyboard stop: '+unnamed.map(node=>node.outerHTML).join(' '));
    await screen.tryBackgroundFocus();
    assert.notEqual(document.activeElement.getAttribute('data-testid'),'content-button','focus cannot escape the open drawer');
    assert.ok(document.activeElement.getAttribute('aria-label'),'focus trapping must land on a named menu control, not the backdrop');
    await screen.event('escape');assert.equal(screen.visible,false);
    assert.equal(document.activeElement.getAttribute('aria-label'),'Открыть меню разделов');
    assert.equal(screen.mounts,1,'opening the menu preserves the current screen and drafts');
  }finally{await screen.close();}
});

test('route and account changes close the drawer and remove stale administrator identity',async()=>{
  const screen=await navigationScreen({user:{id:'admin-one',full_name:'Private Admin Name',is_admin:true,credits_remaining:25}});try{
    await screen.press('Открыть меню разделов');assert.equal(screen.visible,true);assert.match(screen.text,/Кабинет администратора/);
    await screen.update({pathname:'/numbers'});assert.equal(screen.visible,false);
    await screen.press('Открыть меню разделов');
    await screen.update({status:'signedOut'});assert.equal(screen.visible,false);
    assert.doesNotMatch(screen.text,/Private Admin Name|Кабинет администратора/);
    await screen.press('Открыть меню разделов');
    assert.match(screen.text,/Войти или зарегистрироваться/);assert.doesNotMatch(screen.text,/Private Admin Name|Кабинет администратора/);
    await screen.update({status:'signedIn',user:{id:'student-two',full_name:'Second Student'}});assert.equal(screen.visible,false);
    await screen.press('Открыть меню разделов');assert.match(screen.text,/Second Student/);assert.doesNotMatch(screen.text,/Private Admin Name|Кабинет администратора/);
  }finally{await screen.close();}
});

test('background and hidden browser document dismiss the drawer without navigating',async()=>{
  const screen=await navigationScreen();try{
    await screen.press('Открыть меню разделов');assert.equal(screen.visible,true);await screen.event('app','background');assert.equal(screen.visible,false);
    await screen.press('Открыть меню разделов');assert.equal(screen.visible,true);await screen.event('visibility',true);assert.equal(screen.visible,false);
    assert.deepEqual(screen.calls,[]);assert.equal(screen.mounts,1);
  }finally{await screen.close();}
});

test('an account change removes private links and identity before the closing fade finishes',async()=>{
  const screen=await navigationScreen({reducedMotion:false,user:{id:'admin-one',full_name:'Private Admin Name',is_admin:true,credits_remaining:25}});try{
    await screen.press('Открыть меню разделов');await screen.finishAnimation();
    assert.equal(screen.visible,true);assert.match(screen.text,/Private Admin Name|Кабинет администратора/);
    await screen.update({status:'signedOut'});
    assert.equal(screen.visible,false);
    assert.ok(document.querySelector('[aria-modal="true"]'),'real Modal still exists during its closing animation');
    assert.doesNotMatch(screen.text,/Private Admin Name|Кабинет администратора/);
    await screen.finishAnimation();assert.equal(document.querySelector('[aria-modal="true"]'),null);
  }finally{await screen.close();}
});

test('contextual back uses history when present and a real parent for direct visits',async()=>{
  const screen=await navigationScreen({pathname:'/lesson/intro-1'});try{
    await screen.press('Назад');assert.deepEqual(screen.calls.pop(),['replace','/learning']);
    screen.canGoBack(true);await screen.press('Назад');assert.deepEqual(screen.calls.pop(),['back']);
    await screen.press('Открыть меню разделов');await screen.press('Уроки и практика');
    assert.equal(screen.visible,false);assert.deepEqual(screen.calls.pop(),['navigate','/learning']);
    await screen.update({pathname:'/learning'});await screen.press('Открыть меню разделов');await screen.press('Уроки и практика');
    assert.equal(screen.visible,false);assert.deepEqual(screen.calls,[],'the selected section closes without duplicating a history entry');
    assert.equal(screen.mounts,1);
  }finally{await screen.close();}
});
