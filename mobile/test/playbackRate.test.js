const {test}=require('node:test');
const assert=require('node:assert/strict');
const speed=require('../src/lib/playbackRate');

test('listening speeds are the agreed steps with Russian labels',()=>{
  assert.equal(speed.getPlaybackRate(),1.2);
  assert.deepEqual(speed.RATES,[1,1.1,1.2,1.5,1.7,2]);
  assert.deepEqual(speed.RATES.map(speed.rateLabel),['1×','1,1×','1,2×','1,5×','1,7×','2×']);
});

test('one speed is shared by every player and unknown values fall back to the project default',()=>{
  const heard=[];const stop=speed.subscribePlaybackRate(rate=>heard.push(rate));
  assert.equal(speed.setPlaybackRate(1.7),1.7);
  assert.equal(speed.getPlaybackRate(),1.7);
  assert.equal(speed.setPlaybackRate(3),1.2);
  assert.equal(speed.setPlaybackRate('1.5'),1.2);
  stop();speed.setPlaybackRate(2);
  assert.deepEqual(heard,[1.7,1.2,1.2]);
  speed.setPlaybackRate(1);
});

test('authored 1.1x video starts at its own tempo, with manual choice still available',()=>{
  assert.ok(speed.RATES.includes(1.1));
  assert.equal(speed.reportPlaybackRate(1.1,null,1.2),1.1);
  assert.equal(speed.reportPlaybackRate(1.1,1.5,1.2),1.5);
  assert.equal(speed.reportPlaybackRate(1,null,1.2),1.2);
});
