import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Headphones, RefreshCw } from 'lucide-react';
import { api } from '../../services/api';
import { getBackendUrl } from '../../utils/backendUrl';

function trustedAudioUrl(value) {
  if (!value) return '';
  const url = new URL(value);
  if (url.origin !== new URL(getBackendUrl()).origin || url.username || url.password || url.search || url.hash || !url.pathname.startsWith('/api/student/narration-media/')) throw new Error('Адрес аудиозаписи недоступен. Обновите озвучку.');
  return url.href;
}

function AudioWorkspace({ orderId }) {
  const [items, setItems] = useState([]), [selected, setSelected] = useState(''), [error, setError] = useState(''), [busy, setBusy] = useState(false), [dropped, setDropped] = useState(false);
  const [continuous, setContinuous] = useState(true), [autoPlay, setAutoPlay] = useState(false);
  const player = useRef(null), epoch = useRef(0), timer = useRef(null), snapshot = useRef([]), links = useRef(new Map()), reloadRef = useRef(null);
  const path = `/full-reports/${encodeURIComponent(orderId)}/narration`;
  const reload = useCallback(async () => {
    const version = ++epoch.current;
    let failed = false;
    clearTimeout(timer.current);
    setBusy(true); setError(''); setDropped(false);
    try {
      const response = await api.request(path);
      if (version !== epoch.current) return;
      if (!Array.isArray(response.items)) throw new Error('Не удалось загрузить список записей.');
      const clips = response.items.map(item => {
        const url = trustedAudioUrl(item.url), saved = links.current.get(item.hash || item.id);
        if (url && saved?.until > Date.now() && new URL(saved.url).origin === new URL(url).origin) return { ...item, url: saved.url };
        if (url) links.current.set(item.hash || item.id, { url, until: Date.now() + 25 * 60 * 1000 });
        return { ...item, url };
      });
      if (version === epoch.current) { snapshot.current = clips; setItems(clips); setSelected(value => clips.some(item => item.id === value) ? value : clips[0]?.id || ''); }
    } catch (failure) {
      failed = true;
      // A dropped connection or a busy server during polling is temporary; anything else (a foreign record address) is shown.
      if (version === epoch.current) { if (failure?.status >= 500 || ['network', 'timeout'].includes(failure?.code)) setDropped(true); else setError(failure.message); }
    }
    finally { if (version === epoch.current) { setBusy(false); timer.current = setTimeout(() => { if (!document.hidden) void reloadRef.current?.(); }, !failed && snapshot.current.length && snapshot.current.every(item => item.status === 'ready') ? 25 * 60 * 1000 : 30000); } }
  }, [path]);
  reloadRef.current = reload;
  useEffect(() => {
    epoch.current++; clearTimeout(timer.current); player.current?.pause();
    snapshot.current = []; links.current.clear(); setItems([]); setSelected(''); setAutoPlay(false); setError('');
    void reload();
    return () => { epoch.current++; clearTimeout(timer.current); player.current?.pause(); };
  }, [reload]);
  useEffect(() => {
    const onHidden = () => { if (document.hidden) { player.current?.pause(); setAutoPlay(false); clearTimeout(timer.current); } else void reload(); };
    const onPlay = event => { if (event.target !== player.current) { player.current?.pause(); setAutoPlay(false); } };
    document.addEventListener('visibilitychange', onHidden); document.addEventListener('play', onPlay, true);
    return () => { document.removeEventListener('visibilitychange', onHidden); document.removeEventListener('play', onPlay, true); };
  }, [reload]);
  const active = items.find(item => item.id === selected);
  async function prepare() {
    const version = epoch.current;
    setBusy(true); setError('');
    try {
      if (active?.status === 'review') await api.request(`/full-reports/${encodeURIComponent(orderId)}/video`, { method: 'POST', body: {} });
      else if (active && active.status !== 'ready') await api.request(`${path}/${encodeURIComponent(active.id)}/access`, { method: 'POST', body: {} });
      if (version === epoch.current) await reload();
    } catch (failure) { if (version === epoch.current) setError(failure.message); }
    finally { if (version === epoch.current) setBusy(false); }
  }
  return <section className="fr-audio" aria-label="Озвучка персонального разбора">
    <h2><Headphones size={21} aria-hidden="true" /> Ваш разбор — голосом</h2>
    <p>Каждая запись относится к результатам этой даты рождения. Выберите главу для прослушивания.</p>
    {!!items.length && <label>Глава<select value={selected} onChange={event => { player.current?.pause(); setAutoPlay(false); setSelected(event.target.value); setError(''); }}>{items.map(item => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label>}
    {active?.status === 'ready' && active.url ? <audio ref={player} key={active.url} controls autoPlay={autoPlay} preload="none" src={active.url} aria-label={active.title} onEnded={() => { const next = items.findIndex(item => item.id === selected) + 1; if (continuous && next < items.length) { setAutoPlay(true); setSelected(items[next].id); } }} onError={() => setError('Запись не загрузилась. Обновите озвучку и повторите воспроизведение.')} /> : <p role="status">{busy ? 'Подготавливаем аудиоверсию…' : active?.status === 'review' ? 'Запись не прошла подготовку. Можно повторить без новой оплаты.' : active ? 'Аудиозапись ещё готовится. Текст разбора уже доступен ниже.' : 'Озвучка готовится: голос записывает главы вашего разбора. Готовые главы появятся здесь сами. Страницу можно закрыть — когда будет готово всё, придёт письмо.'}</p>}
    {items.length > 1 && <label className="fr-continuous"><input type="checkbox" checked={continuous} onChange={event => setContinuous(event.target.checked)} /> Слушать готовые главы подряд</label>}
    {active?.text && <details><summary>Текст этой записи</summary><p className="fr-transcript">{active.text}</p></details>}
    {error && <p role="alert" className="fr-error">{error}</p>}
    {dropped && !error && <p className="fr-note">Связь ненадолго прервалась — проверим озвучку снова автоматически.</p>}
    <button className="fr-button secondary" type="button" onClick={prepare} disabled={busy}><RefreshCw size={16} aria-hidden="true" /> {active?.status === 'review' ? 'Повторить подготовку озвучки' : active?.status === 'missing' ? 'Подготовить озвучку' : 'Обновить озвучку'}</button>
  </section>;
}

export default function FullReportAudio({ orderId }) {
  return <AudioWorkspace key={orderId} orderId={orderId} />;
}
