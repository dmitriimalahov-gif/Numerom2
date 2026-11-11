// One narration at a time, including mounted but inactive tab screens.
let stopCurrent = null;
function takeAudioFocus(stop) {
  if (stopCurrent && stopCurrent !== stop) stopCurrent();
  stopCurrent = stop;
}
function releaseAudioFocus(stop) {
  if (stopCurrent === stop) stopCurrent = null;
}
module.exports = {takeAudioFocus, releaseAudioFocus};
