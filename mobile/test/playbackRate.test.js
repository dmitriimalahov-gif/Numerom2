const {test}=require('node:test');
const assert=require('node:assert/strict');
const speed=require('../src/lib/playbackRate');

test('listening speeds are the agreed steps with Russian labels',()=>{
  assert.deepEqual(speed.RATES,[1,1.2,1.5,1.7,2]);
  assert.deepEqual(speed.RATES.map(speed.rateLabel),['1×','1,2×','1,5×','1,7×','2×']);
});

test('one speed is shared by every player and unknown values fall back to normal',()=>{
  const heard=[];const stop=speed.subscribePlaybackRate(rate=>heard.push(rate));
  assert.equal(speed.setPlaybackRate(1.7),1.7);
  assert.equal(speed.getPlaybackRate(),1.7);
  assert.equal(speed.setPlaybackRate(3),1);
  assert.equal(speed.setPlaybackRate('1.5'),1);
  stop();speed.setPlaybackRate(2);
  assert.deepEqual(heard,[1.7,1,1]);
  speed.setPlaybackRate(1);
});
