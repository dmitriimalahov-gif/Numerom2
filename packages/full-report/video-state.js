'use strict';
const states = new Set(['waiting_analysis', 'waiting_audio', 'queued', 'rendering', 'ready', 'failed']);
function mediaUrl(value, origin) {
  let url;
  try { url = new URL(value); } catch { throw new Error('Ссылка на видео недоступна. Обновите видеоверсию.'); }
  if (url.protocol !== 'https:' || url.origin !== new URL(origin).origin || url.username || url.password || url.search || url.hash || !/^\/api\/student\/report-video\/[A-Za-z0-9._~-]+$/.test(url.pathname)) throw new Error('Адрес видео не подтверждён. Обновите видеоверсию.');
  return url.href;
}
function videoState(raw, origin) {
  if (!raw || !states.has(raw.status) || !Number.isSafeInteger(raw.audio_ready) || !Number.isSafeInteger(raw.audio_total) || raw.audio_ready < 0 || raw.audio_total < raw.audio_ready) throw new Error('Не удалось прочитать состояние видео. Попробуйте ещё раз.');
  const result = { ...raw, message: typeof raw.message === 'string' ? raw.message : '', chapters: [] };
  if (raw.progress !== undefined && (!Number.isFinite(raw.progress) || raw.progress < 0 || raw.progress > 100)) throw new Error('Не удалось прочитать состояние видео. Попробуйте ещё раз.');
  for (const key of ['seconds', 'bytes']) if (raw[key] !== undefined && (!Number.isFinite(raw[key]) || raw[key] < 0)) throw new Error('Не удалось прочитать параметры видео.');
  if (raw.status === 'ready') {
    if (!Number.isFinite(raw.expires_in) || raw.expires_in <= 0) throw new Error('Ссылка видео истекла. Обновите видеоверсию.');
    result.url = mediaUrl(raw.url, origin); result.download_url = mediaUrl(raw.download_url, origin);
  } else { delete result.url; delete result.download_url; }
  if (Array.isArray(raw.chapters)) result.chapters = raw.chapters.filter(item => item && typeof item.id === 'string' && typeof item.title === 'string' && Number.isFinite(item.start_seconds) && item.start_seconds >= 0 && Number.isFinite(item.duration_seconds) && item.duration_seconds > 0);
  if(raw.encoded_speed!==undefined && ![1,1.1,1.2].includes(raw.encoded_speed))throw new Error('Скорость видео не подтверждена.');
  if(raw.width!==undefined && (!Number.isSafeInteger(raw.width)||raw.width<1||raw.width>4096))throw new Error('Размер видео не подтверждён.');
  if(raw.height!==undefined && (!Number.isSafeInteger(raw.height)||raw.height<1||raw.height>4096))throw new Error('Размер видео не подтверждён.');
  return result;
}
function retainVideo(previous, next, now = Date.now()) {
  if (next.status !== 'ready') return { ...next, link_until: 0 };
  const sameOrigin = previous?.url && new URL(previous.url).origin === new URL(next.url).origin;
  const sameMedia = ['encoded_speed','seconds','bytes','width','height'].every(key => previous?.[key] === next[key]);
  if (previous?.status === 'ready' && previous.link_until > now && sameOrigin && sameMedia) return { ...next, url: previous.url, download_url: previous.download_url, link_until: previous.link_until };
  return { ...next, link_until: now + Math.max(1, next.expires_in - Math.min(30, next.expires_in / 4)) * 1000 };
}
function videoPollDelay(value, now = Date.now()) {
  return value?.status === 'ready' ? Math.max(1000, value.link_until - now) : ['waiting_analysis', 'waiting_audio', 'queued', 'rendering'].includes(value?.status) ? 30000 : null;
}
module.exports = { mediaUrl, videoState, retainVideo, videoPollDelay };
