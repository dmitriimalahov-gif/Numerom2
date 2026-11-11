const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const ts=require('typescript');

function deferred() {
  let resolve;
  const promise=new Promise(done=>{resolve=done;});
  return {promise,resolve};
}
const settle=()=>new Promise(resolve=>setImmediate(resolve));

// Load the real native component; only its platform and hook dependencies are replaced.
// Calling the same handler twice also covers taps before React has rendered pending state.
function voice(t,{buffering=false,playing=false}={}) {
  const mode=deferred(),calls={mode:0,play:0,pause:0,focus:0,rates:[],chosen:[],awake:[],background:[]};
  const effects=[],cleanups=[];
  const player={play:()=>{calls.play++;},pause:()=>{calls.pause++;},seekTo:async()=>{},
    setPlaybackRate:(rate,quality)=>{calls.rates.push([rate,quality,player.shouldCorrectPitch]);}};
  const deps={
    react:{useCallback:fn=>fn,useEffect:effect=>effects.push(effect),
      useRef:current=>({current}),useState:initial=>[initial,()=>{}]},
    'react/jsx-runtime':{jsx:(type,props)=>({type,props})},
    'expo-audio':{
      setAudioModeAsync:options=>{calls.mode++;calls.background.push(options.shouldPlayInBackground);return mode.promise;},
      useAudioPlayer:()=>player,
      useAudioPlayerStatus:()=>({playing,isBuffering:buffering,didJustFinish:false,
        currentTime:0,duration:42,playbackState:'ready'}),
    },
    '../../lib/numberAudio':{numberAudio:{1:1}},
    '../../lib/numberKnowledge':{numberKnowledge:()=>({audio:{seconds:42}})},
    '../../lib/audioFocus':{takeAudioFocus:()=>{calls.focus++;},releaseAudioFocus(){}},
    '../../lib/wakeLock':{holdScreen:()=>{calls.awake.push(true);},releaseScreen:()=>{calls.awake.push(false);}},
    '../../lib/usePlaybackRate':{usePlaybackRate:()=>[1.5,value=>{calls.chosen.push(value);}]},
    '../numbers/VoiceControls':{VoiceControls:()=>{}},
  };
  const filename=path.resolve(__dirname,'../src/components/audio/AudioTrack.tsx');
  const mod={exports:{}};
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(filename,'utf8'),{
    compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX},
  }).outputText,{exports:mod.exports,require:name=>{
    assert.ok(name in deps,`Unexpected dependency: ${name}`);
    return deps[name];
  },setTimeout,clearTimeout});
  const controls=mod.exports.AudioTrack({digit:1,source:1,seconds:42}).props;
  for(const effect of effects){const cleanup=effect();if(cleanup)cleanups.push(cleanup);}
  t.after(()=>{for(const cleanup of cleanups)cleanup();});
  return {toggle:controls.onToggle,mode,calls,controls};
}

test('native narration plays at the shared speed with pitch kept and offers the speed choice',t=>{
  const item=voice(t);
  assert.deepEqual(item.calls.rates,[[1.5,'high',true]]);
  assert.equal(item.controls.rate,1.5);
  item.controls.onRate(2);
  assert.deepEqual(item.calls.chosen,[2]);
});

test('native narration can be paused while buffering before playing becomes true',async t=>{
  const item=voice(t,{buffering:true});
  item.toggle();
  item.mode.resolve();await settle();
  assert.equal(item.calls.play,1);
  assert.equal(item.calls.focus,1);
  item.toggle();await settle();
  assert.equal(item.calls.pause,1);
  assert.equal(item.calls.play,1,'a buffering tap must not start playback again');
  assert.equal(item.calls.mode,1);
});

test('a second tap cancels pending audio setup before it can play or take focus',async t=>{
  const item=voice(t);
  item.toggle();item.toggle();
  item.mode.resolve();await settle();
  assert.equal(item.calls.mode,1,'the second tap must cancel instead of creating another request');
  assert.equal(item.calls.pause,1);
  assert.equal(item.calls.play,0);
  assert.equal(item.calls.focus,0);
  item.toggle();await settle();
  assert.equal(item.calls.play,1,'an explicit later tap must still be able to play');
});

test('narration keeps playing in the background and keeps the screen on only while it plays',async t=>{
  const item=voice(t,{playing:true});
  assert.deepEqual(item.calls.awake,[true]);
  item.toggle();item.mode.resolve();await settle();
  const idle=voice(t);
  assert.deepEqual(idle.calls.awake,[false]);
  idle.toggle();idle.mode.resolve();await settle();
  assert.deepEqual(idle.calls.background,[true],'the recording must go on with the phone locked');
});

test('the native narration has no screen-focus or app-state stop',()=>{
  const code=fs.readFileSync(path.resolve(__dirname,'../src/components/audio/AudioTrack.tsx'),'utf8');
  assert.doesNotMatch(code,/useFocusEffect|AppState/);
});
