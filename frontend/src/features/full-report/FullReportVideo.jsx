import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Download, Film, RefreshCw } from 'lucide-react';
import { api } from '../../services/api';
import { useAuth } from '../../components/AuthContext';
import { getBackendUrl } from '../../utils/backendUrl';
import { mediaUrl, videoState, retainVideo, videoPollDelay } from '../../../../packages/full-report/video-state';
import ReportPreparing from './ReportPreparing';

function VideoWorkspace({ orderId, birthDate }) {
  const [state, setState] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState('');
  const snapshot = useRef(null), mounted = useRef(false), epoch = useRef(0), inFlight = useRef(false), timer = useRef(null), controller = useRef(null), player = useRef(null), position = useRef(0), reloadRef = useRef(null);
  const ownerToken = useRef(localStorage.getItem('token'));
  const path = `/full-reports/${encodeURIComponent(orderId)}/video`;
  const reload = useCallback(async (prepare = false) => {
    if (inFlight.current || !mounted.current || ownerToken.current !== localStorage.getItem('token')) return;
    clearTimeout(timer.current); inFlight.current = true;
    const generation = ++epoch.current, token = localStorage.getItem('token');
    const requestController = new AbortController(); controller.current = requestController;
    const current = () => mounted.current && generation === epoch.current && token === localStorage.getItem('token');
    setBusy(true); setError('');
    try {
      const raw = await api.request(path, { ...(prepare ? { method: 'POST', body: {} } : {}), signal: requestController.signal });
      if (!current()) return;
      const next = retainVideo(snapshot.current, videoState(raw, getBackendUrl()));
      if (snapshot.current?.url !== next.url) position.current = player.current?.currentTime || position.current;
      snapshot.current = next; setState(next);
    } catch (failure) { if (current()) setError(failure.message); }
    finally {
      if (generation === epoch.current) inFlight.current = false;
      if (current()) {
        setBusy(false);
        const delay = videoPollDelay(snapshot.current);
        if (delay !== null) timer.current = setTimeout(() => { if (!document.hidden) void reloadRef.current(false); }, delay);
      }
    }
  }, [path]);
  reloadRef.current = reload;
  useEffect(() => {
    mounted.current = true; void reload();
    const visible = () => { if (document.hidden) { player.current?.pause(); clearTimeout(timer.current); } else void reloadRef.current(false); };
    const otherMedia = event => { if (event.target !== player.current) player.current?.pause(); };
    document.addEventListener('visibilitychange', visible); document.addEventListener('play', otherMedia, true);
    return () => { mounted.current = false; epoch.current++; inFlight.current = false; controller.current?.abort(); clearTimeout(timer.current); player.current?.pause(); document.removeEventListener('visibilitychange', visible); document.removeEventListener('play', otherMedia, true); };
  }, [reload]);
  function seek(seconds) { if (player.current) { player.current.currentTime = seconds; position.current = seconds; } }
  return <section className="fr-video" aria-label="Персональная видеоверсия">
    <div className="fr-video-heading"><Film size={22} aria-hidden="true" /><div><h2>Ваш разбор в видео</h2><p>Авторские схемы и персональная озвучка в одном MP4. Входит в покупку 6,66 €.</p></div></div>
    {state?.status === 'ready' && state.url ? <>
      <video ref={player} controls playsInline preload="metadata" src={state.url} onPlay={event => { if (ownerToken.current !== localStorage.getItem('token')) event.currentTarget.pause(); }} onTimeUpdate={event => { position.current = event.currentTarget.currentTime; }} onLoadedMetadata={event => { if (position.current > 0) event.currentTarget.currentTime = Math.min(position.current, event.currentTarget.duration || position.current); }} onError={() => setError('Не удалось открыть видео. Обновите ссылку и повторите воспроизведение.')} />
      <div className="fr-video-meta"><span>{state.seconds ? `${Math.ceil(state.seconds / 60)} мин` : 'MP4'}{state.bytes ? ` · ${(state.bytes / 1048576).toFixed(1)} МБ` : ''}</span><a className="fr-button" href={state.download_url} download rel="noreferrer" referrerPolicy="no-referrer" onClick={event => { try { if (ownerToken.current !== localStorage.getItem('token')) { event.preventDefault(); player.current?.pause(); return; } mediaUrl(state.download_url, getBackendUrl()); if (state.link_until <= Date.now()) { event.preventDefault(); void reload(true); } } catch (failure) { event.preventDefault(); setError(failure.message); } }}><Download size={17} aria-hidden="true" /> Скачать MP4</a></div>
      {!!state.chapters?.length && <details className="fr-video-chapters"><summary>Главы видео</summary>{state.chapters.map(chapter => <button type="button" className="fr-text-button" key={chapter.id} onClick={() => seek(chapter.start_seconds)}>{Math.floor(chapter.start_seconds / 60)}:{String(Math.floor(chapter.start_seconds % 60)).padStart(2, '0')} · {chapter.title}</button>)}</details>}
    </> : <div className="fr-video-status" role="status">{state && !['failed', 'waiting_analysis'].includes(state.status) && <ReportPreparing birthDate={birthDate} />}<strong>{state?.status === 'waiting_analysis' ? 'Готовим смысловой разбор' : state?.status === 'rendering' ? 'Собираем персональное видео' : state?.status === 'queued' ? 'Видео в очереди на подготовку' : state?.status === 'failed' ? (state.stage === 'analysis' ? 'Подготовку смыслового разбора нужно повторить' : state.stage === 'audio' ? 'Подготовку озвучки нужно повторить' : 'Подготовку видео нужно повторить') : 'Подготавливаем аудиоглавы для видео'}</strong><p>{state?.message || (busy ? 'Проверяем состояние видеоверсии…' : 'Видео появится здесь после подготовки всех персональных аудиоглав.')}</p>{state && state.status !== 'waiting_analysis' && state.stage !== 'analysis' && <p>Готово аудиоглав: {state.audio_ready} из {state.audio_total}</p>}{state?.progress !== undefined && <><progress value={state.progress} max="100" aria-label="Подготовка видео" /><span>{Math.round(state.progress)}%</span></>}</div>}
    {error && <p className="fr-error" role="alert">{error}</p>}
    <button type="button" className="fr-button secondary" disabled={busy} onClick={() => void reload(true)}><RefreshCw size={16} aria-hidden="true" />{busy ? 'Проверяем…' : state?.status === 'ready' ? 'Обновить ссылку на видео' : state?.status === 'failed' ? (state.stage === 'analysis' ? 'Повторить смысловой разбор' : state.stage === 'audio' ? 'Повторить подготовку озвучки' : 'Повторить подготовку видео') : 'Подготовить / проверить видео'}</button>
    <p className="fr-video-note">Дополнительная оплата и баллы не нужны. Можно закрыть страницу и вернуться позже.</p>
  </section>;
}

export default function FullReportVideo({ orderId, birthDate }) {
  const { user } = useAuth();
  return user ? <VideoWorkspace key={`${user.id}:${orderId}`} orderId={orderId} birthDate={birthDate} /> : null;
}
