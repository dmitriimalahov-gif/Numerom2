const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const ts=require('typescript');
const {JSDOM}=require('jsdom');

// The web players with a real DOM; media playback itself is stubbed (jsdom cannot decode audio or video).
function load(){
  const dom=new JSDOM('<!doctype html><body><main id="screen"></main></body>');
  const {window}=dom,media=window.HTMLMediaElement.prototype,calls={awake:new Set(),navigate:[]};
  const playing=new WeakSet();
  Object.defineProperty(media,'paused',{configurable:true,get(){return !playing.has(this);}});
  media.play=function(){playing.add(this);this.dispatchEvent(new window.Event('play'));return Promise.resolve();};
  media.pause=function(){if(!playing.has(this))return;playing.delete(this);this.dispatchEvent(new window.Event('pause'));};
  media.load=function(){};
  const modules={
    './playbackRate':require('../src/lib/playbackRate'),
    './wakeLock':{holdScreen:tag=>calls.awake.add(tag),releaseScreen:tag=>calls.awake.delete(tag)},
    'expo-router':{router:{dismissTo:href=>calls.navigate.push(href)}},
  };
  const run=file=>{
    const mod={exports:{}};
    vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.resolve(__dirname,'../src/lib',file),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,
      {exports:mod.exports,require:name=>{assert.ok(name in modules,`Unexpected dependency: ${name}`);return modules[name];},
        document:window.document,navigator:window.navigator,setTimeout,clearTimeout});
    return mod.exports;
  };
  modules['./nowPlaying.web']=run('nowPlaying.web.ts');
  const dock=run('videoDock.web.ts');
  const fire=(node,type)=>node.dispatchEvent(new window.Event(type));
  return {window,document:window.document,calls,nowPlaying:modules['./nowPlaying.web'].nowPlaying,dock,fire};
}
const track={id:'/voice/1.m4a',source:'/voice/1.m4a?sig=1',title:'Глава 1',href:'/full-report',seconds:60};

test('narration goes on after its screen is left and keeps the screen on while it plays',async()=>{
  const {document,calls,nowPlaying,fire}=load();
  const leave=nowPlaying.show(track.id);
  await nowPlaying.play(track);
  const audio=document.querySelector('audio');
  fire(audio,'playing');
  assert.equal(nowPlaying.get().playing,true);
  assert.ok(calls.awake.has('narration'));
  leave();
  assert.equal(nowPlaying.visible(track.id),false,'the mini player takes over');
  assert.equal(nowPlaying.get().playing,true,'leaving the screen must not stop the recording');
  assert.equal(audio.paused,false);
  nowPlaying.pause();
  assert.equal(calls.awake.has('narration'),false,'a paused recording lets the phone sleep');
  nowPlaying.close();
  assert.equal(nowPlaying.get(),null);
});

test('a cancelled load does not show a playback error',async()=>{
  const {window,nowPlaying}=load();
  window.HTMLMediaElement.prototype.play=function(){return new Promise((_,reject)=>setTimeout(()=>reject(new Error('AbortError')),5));};
  const started=nowPlaying.play(track);
  assert.equal(nowPlaying.get().busy,true);
  nowPlaying.pause();
  await started;
  assert.equal(nowPlaying.get().error,'');
  assert.equal(nowPlaying.get().busy,false);
});

test('a playing video moves into the floating window and returns to its screen without restarting',()=>{
  const {document,calls,dock,fire}=load();
  const screen=document.getElementById('screen');
  const video=dock.createVideo('/video.mp4?sig=1','Видеоразбор');
  screen.append(video);
  void video.play();fire(video,'playing');
  assert.equal(calls.awake.size,1,'the screen stays on while the video plays');
  dock.videoDock.leave({id:'/video.mp4',element:video,title:'Видеоразбор',href:'/full-report'});
  const frame=document.querySelector('[aria-label="Видео в отдельном окне"]');
  assert.ok(frame.contains(video));
  assert.equal(frame.style.display,'block');
  assert.equal(video.paused,false);
  frame.querySelector('button').click();
  assert.deepEqual(calls.navigate,['/full-report']);
  assert.equal(dock.videoDock.take('/other.mp4'),null);
  assert.equal(dock.videoDock.take('/video.mp4'),video);
  assert.equal(frame.style.display,'none');
});

test('a paused video stays on its screen and another recording closes the floating window',()=>{
  const {document,dock,nowPlaying}=load();
  const screen=document.getElementById('screen');
  const paused=dock.createVideo('/a.mp4','A');screen.append(paused);
  dock.videoDock.leave({id:'/a.mp4',element:paused,title:'A',href:'/a'});
  assert.ok(screen.contains(paused));
  const video=dock.createVideo('/b.mp4','B');screen.append(video);void video.play();
  dock.videoDock.leave({id:'/b.mp4',element:video,title:'B',href:'/b'});
  assert.equal(dock.videoDock.docked('/b.mp4'),true);
  void nowPlaying.play(track);
  assert.equal(dock.videoDock.docked('/b.mp4'),false);
  assert.equal(video.paused,true,'only one sound plays at a time');
  assert.equal(document.contains(video),false);
});

test('the screen lock is taken while something plays and taken again when the page comes back',async()=>{
  const dom=new JSDOM('<!doctype html><body></body>');
  let visibility='visible';const events=[];
  Object.defineProperty(dom.window.document,'visibilityState',{configurable:true,get:()=>visibility});
  const navigator={wakeLock:{request:async()=>{events.push('take');const listeners=[];
    return {release:async()=>{events.push('release');listeners.forEach(fn=>fn());},addEventListener:(_,fn)=>listeners.push(fn)};}}};
  const mod={exports:{}};
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.resolve(__dirname,'../src/lib/wakeLock.web.ts'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,
    {exports:mod.exports,document:dom.window.document,navigator});
  const {holdScreen,releaseScreen}=mod.exports,tick=()=>new Promise(resolve=>setImmediate(resolve));
  holdScreen('narration');await tick();
  holdScreen('video-1');await tick();
  assert.deepEqual(events,['take'],'one lock serves every player');
  releaseScreen('narration');await tick();
  assert.deepEqual(events,['take'],'the lock stays while the video still plays');
  visibility='hidden';dom.window.document.dispatchEvent(new dom.window.Event('visibilitychange'));await tick();
  visibility='visible';dom.window.document.dispatchEvent(new dom.window.Event('visibilitychange'));await tick();
  assert.deepEqual(events,['take','release','take']);
  releaseScreen('video-1');await tick();
  assert.deepEqual(events,['take','release','take','release']);
});
