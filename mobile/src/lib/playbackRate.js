// One listening speed for every voice and video player; the choice carries over to the next track.
const RATES = [1, 1.2, 1.5, 1.7, 2];
let rate = 1;
const listeners = new Set();

function validRate(value) {
  return RATES.includes(value) ? value : 1;
}
function getPlaybackRate() {
  return rate;
}
function setPlaybackRate(value) {
  rate = validRate(value);
  listeners.forEach(listener => listener(rate));
  return rate;
}
function subscribePlaybackRate(listener) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}
function rateLabel(value) {
  return String(validRate(value)).replace('.', ',') + '×';
}
module.exports = {RATES, validRate, getPlaybackRate, setPlaybackRate, subscribePlaybackRate, rateLabel};
