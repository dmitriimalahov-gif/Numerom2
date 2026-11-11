const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {numberKnowledge,knowledgeNumbers}=require('../src/lib/numberKnowledge');
const {takeAudioFocus,releaseAudioFocus}=require('../src/lib/audioFocus');
const root=path.resolve(__dirname,'../../packages/number-knowledge');
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');

test('nine selected-voice recordings match their source, oral transcript and bytes',()=>{
  const manifest=JSON.parse(fs.readFileSync(path.join(root,'audio-manifest.json'),'utf8'));
  assert.equal(manifest.voice,'dima golos');
  assert.equal(manifest.provider,'omnivoice');
  assert.equal(manifest.profile,'af750ff3');
  assert.equal(manifest.tempo,1);
  assert.deepEqual(knowledgeNumbers,[1,2,3,4,5,6,7,8,9]);
  const hashes=new Set();
  for(const digit of knowledgeNumbers){
    const item=numberKnowledge(digit);
    assert.equal(item.audio.digit,digit);assert.equal(item.segments.length,3);
    assert.equal(sha(item.segments.join('\n\n')),item.audio.text_sha256);
    assert.equal(sha(item.audio.transcript),item.audio.speech_sha256);
    const bytes=fs.readFileSync(path.join(root,item.audio.path));
    assert.equal(sha(bytes),item.audio.sha256);assert.equal(bytes.length,item.audio.bytes);
    assert.ok(item.audio.seconds>20&&item.audio.seconds<90);
    assert.equal(bytes.subarray(4,8).toString(),'ftyp');hashes.add(item.audio.sha256);
  }
  assert.equal(hashes.size,9);
});
test('invalid values never silently play a different digit',()=>{
  for(const value of [0,10,11,22,33,null,undefined,'1',1.5,NaN])assert.equal(numberKnowledge(value),null);
});
test('changing narration stops the previous one and stale cleanup cannot steal focus',()=>{
  let firstStops=0,secondStops=0;
  const first=()=>{firstStops++;releaseAudioFocus(first);},second=()=>{secondStops++;releaseAudioFocus(second);};
  takeAudioFocus(first);takeAudioFocus(first);assert.equal(firstStops,0);
  takeAudioFocus(second);assert.equal(firstStops,1);
  releaseAudioFocus(first);takeAudioFocus(first);assert.equal(secondStops,1);
  releaseAudioFocus(first);
});
