import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ArrowUpRight, Check, FileDown, FileText, Headphones, RefreshCw, ShieldCheck } from 'lucide-react';
import { positionParagraphs, fullReportCatalog, fullReportOrder, fullReportHtml, fullReportSchemesHtml, fullReportStatus, validBirthDate, checkoutUrl } from '@numerom/full-report';
import { api } from '../../services/api';
import { useAuth } from '../../components/AuthContext';
import FullReportDiagram from './FullReportDiagram';
import FullReportAudio from './FullReportAudio';
import FullReportVideo from './FullReportVideo';
import ReportProfilePreview from './ReportProfilePreview';
import ReportPreparing from './ReportPreparing';
import './full-report.css';

const terminal = status => ['paid', 'failed', 'expired', 'cancelled'].includes(status);
const price = value => new Intl.NumberFormat('ru-RU', { style: 'currency', currency: value.currency || 'eur' }).format(value.amount_total / 100);
const toDate = value => /^\d{4}-\d{2}-\d{2}$/.test(value) ? value.split('-').reverse().join('.') : value;
const inputDate = value => /^\d{2}\.\d{2}\.\d{4}$/.test(value || '') ? value.split('.').reverse().join('-') : '';
const today = () => { const value = new Date(); return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`; };
const pendingKey = id => `numerom.full-report.pending.${id}`;
function readAttempt(key) { try { const value = JSON.parse(localStorage.getItem(key) || 'null'); return value && /^[0-9a-f-]{36}$/i.test(value.request_id) && validBirthDate(value.birth_date) ? value : null; } catch { return null; } }
function requestId() {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID();
  if (!window.crypto?.getRandomValues) throw new Error('Откройте NumerOM по защищённой ссылке HTTPS, чтобы перейти к оплате.');
  const bytes = window.crypto.getRandomValues(new Uint8Array(16)); bytes[6] = (bytes[6] & 15) | 64; bytes[8] = (bytes[8] & 63) | 128;
  return Array.from(bytes, (byte, i) => `${[4, 6, 8, 10].includes(i) ? '-' : ''}${byte.toString(16).padStart(2, '0')}`).join('');
}

function Report({ order, archived = false }) {
  const [printDocument, setPrintDocument] = useState(null), [exportError, setExportError] = useState('');
  const report = order.report;
  if (!report) return null;
  function exportPdf(build = fullReportHtml) { try { setPrintDocument({ html: build(order), revision: Date.now() }); setExportError(''); } catch { setExportError('Не удалось подготовить PDF. Обновите отчёт и повторите.'); } }
  return <article className="fr-report">
    <header className="fr-report-header"><div><span className="fr-eyebrow">Ваш личный отчёт</span><h2>{report.title}</h2><p>{order.person && <>{order.person} · </>}Дата рождения: <strong>{report.birth_date}</strong> · Расчёт на {report.as_of_date}</p></div><div className="fr-export"><button className="fr-button" onClick={() => exportPdf()}><FileDown size={18} aria-hidden="true" /> Сохранить PDF</button>
      <button className="fr-button secondary" onClick={() => exportPdf(fullReportSchemesHtml)}><FileDown size={18} aria-hidden="true" /> Краткий отчёт: схемы и графики</button></div></header>
    {exportError && <p className="fr-error" role="alert">{exportError}</p>}
    {printDocument && <iframe key={printDocument.revision} className="fr-print-frame" title="PDF полного разбора" srcDoc={printDocument.html} onLoad={event => { event.target.contentWindow?.focus(); event.target.contentWindow?.print(); }} />}
    <div className="fr-summary">{report.summary.map((text, index) => <p key={index}>{text}</p>)}
      {report.highlights?.map(group => <div key={group.id}><h3>{group.title}</h3><ul>{group.items.map((item, index) => <li key={index}>{item.text}<br/><small>Основание в расчёте: {item.basis}</small></li>)}</ul></div>)}</div>
    {order.report_status === 'preparing' && (order.analysis_status === 'review'
      ? <p className="fr-analysis-notice" role="status">Подготовка смыслового разбора остановилась. Повторите её кнопкой ниже; новая оплата не нужна.</p>
      : <ReportPreparing birthDate={report.birth_date} message="Смысловой разбор по вашим расчётам готовится в локальной нейросети. Числа уже доступны." />)}
    {!archived && <><FullReportVideo orderId={order.order_id} birthDate={report.birth_date} /><FullReportAudio key={`${order.order_id}-${order.revision || 1}`} orderId={order.order_id} /></>}
    <nav className="fr-contents" aria-label="Содержание отчёта">{report.sections.map(section => <a key={section.id} href={`#full-report-${section.id}`}>{section.title}</a>)}</nav>
    <div className="fr-sections">{report.sections.map((section, index) => <section className="fr-section" id={`full-report-${section.id}`} key={section.id}>
      <div className="fr-section-heading"><span>{String(index + 1).padStart(2, '0')}</span><h2>{section.title}</h2></div>
      <div className="fr-section-body">{section.paragraphs.map((paragraph, paragraphIndex) => <p key={paragraphIndex}>{paragraph}</p>)}</div>
      {!!section.values?.length && <dl className="fr-values">{section.values.map((value, valueIndex) => <div key={valueIndex}><dt>{value.label}</dt><dd><strong>{value.value}</strong>{positionParagraphs(section, valueIndex).map((paragraph, index) => <p key={index}>{paragraph}</p>)}</dd></div>)}</dl>}
      <FullReportDiagram report={report} section={section} />
      {(section.method || section.steps?.length > 0) && <details className="fr-method"><summary>Как получен этот результат</summary>{section.method && <p>{section.method}</p>}{!!section.steps?.length && <ol>{section.steps.map((step, stepIndex) => <li key={stepIndex}>{step}</li>)}</ol>}</details>}
    </section>)}</div>
    {!!report.excluded?.length && <section className="fr-excluded"><h2>Для дополнительных расчётов понадобятся данные</h2><p>Эти разделы требуют дополнительных данных. Заполните профиль, чтобы дополнить оплаченный разбор без повторной оплаты.</p><ul>{report.excluded.map((item, index) => <li key={index}><strong>{item.title}</strong><span>{item.reason}</span></li>)}</ul></section>}
  </article>;
}

function Workspace({ user }) {
  const [params, setParams] = useSearchParams();
  const key = pendingKey(user.id);
  const initial = useRef(readAttempt(key));
  const [attempt, setAttempt] = useState(initial.current), [birthDate, setBirthDate] = useState(inputDate(initial.current?.birth_date || user.birth_date)), [catalog, setCatalog] = useState(null), [orders, setOrders] = useState([]), [order, setOrder] = useState(null), [error, setError] = useState(''), [busy, setBusy] = useState(false), [loading, setLoading] = useState(true), [revision, setRevision] = useState(0);
  const [useProfile, setUseProfile] = useState(initial.current ? !!initial.current.use_profile : true), [preview, setPreview] = useState(null), [archive, setArchive] = useState(null);
  const active = useRef(true), inFlight = useRef(false);
  const selectedId = params.get('order_id') || attempt?.order_id || order?.order_id || '';
  const selectedBoundary=useRef(selectedId);selectedBoundary.current=selectedId;
  // A report picked from «Мои полные разборы» opens at the top of the page once it has loaded.
  const scrollAfterLoad = useRef('');
  useEffect(() => { active.current = true; return () => { active.current = false; }; }, []);
  const remember = useCallback(value => {
    if (value) localStorage.setItem(key, JSON.stringify(value)); else localStorage.removeItem(key);
    setAttempt(value);
  }, [key]);
  const accept = useCallback(value => {
    const next = fullReportOrder(value); setOrder(next);
    setOrders(current => [next, ...current.filter(item => item.order_id !== next.order_id)]);
    const saved = readAttempt(key);
    if (terminal(next.status) && saved?.order_id === next.order_id) { try { remember(null); } catch {} }
    return next;
  }, [key, remember]);
  useEffect(() => {
    const controller = new AbortController(); let current = true;
    setLoading(true); setError('');
    Promise.allSettled([api.request('/full-reports/catalog', { signal: controller.signal }).then(fullReportCatalog), api.request('/full-reports/history', { signal: controller.signal })]).then(([catalogResult, historyResult]) => {
      if (!current) return;
      if (catalogResult.status === 'fulfilled') setCatalog(catalogResult.value); else setError(catalogResult.reason.message);
      if (historyResult.status === 'fulfilled') { try { setOrders(historyResult.value.orders.map(fullReportOrder)); } catch { setError('Не удалось загрузить историю разборов.'); } }
      else setError(historyResult.reason.message);
      setLoading(false);
    });
    return () => { current = false; controller.abort(); };
  }, [revision]);
  useEffect(() => {
    setOrder(null); if (!selectedId) return undefined;
    const controller = new AbortController(); let current = true, timer, count = 0;
    async function poll() {
      try {
        const value = await api.request(`/full-reports/${encodeURIComponent(selectedId)}`, { signal: controller.signal });
        if (!current) return;
        const next = accept(value);
        if (scrollAfterLoad.current === selectedId) { scrollAfterLoad.current = ''; requestAnimationFrame(() => window.scrollTo({ top: 0, behavior: window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })); }
        if (next.status === 'paid' && next.report_status === 'preparing') timer = setTimeout(poll, 30000);
        else if ((!terminal(next.status) || (next.status === 'paid' && !next.report)) && count++ < 30) timer = setTimeout(poll, 4000);
      } catch (failure) { if (current) { setError(failure.message); timer = setTimeout(poll, 30000); } }
    }
    void poll(); return () => { current = false; clearTimeout(timer); controller.abort(); };
  }, [selectedId, revision, accept]);
  function select(id) { setError(''); setArchive(null); scrollAfterLoad.current = id; setParams({ order_id: id }); }
  async function purchase(event) {
    event.preventDefault(); if (inFlight.current || !canPay) return;
    const date = attempt?.birth_date || toDate(birthDate);
    if (!validBirthDate(date)) { setError('Введите существующую дату рождения.'); return; }
    inFlight.current = true; setBusy(true); setError('');
    try {
      if ((attempt?.profile_stale && (!preview || preview.birth_date!==date)) || (!attempt && useProfile && date === user.birth_date && (!preview?.profile_fingerprint || preview.birth_date!==date))) throw new Error('Дождитесь проверки состава разбора или отключите данные профиля.');
      const pending = (attempt?.profile_stale ? {...attempt,profile_stale:false,use_profile:preview.use_profile,profile_fingerprint:preview.profile_fingerprint} : attempt) || { request_id: requestId(), birth_date: date, use_profile: useProfile && date === user.birth_date, profile_fingerprint: useProfile && date === user.birth_date ? preview.profile_fingerprint : null };
      // The same id survives an ambiguous network reply: retrying cannot buy a second report.
      remember(pending);
      const response = await api.request('/full-reports/checkout', { method: 'POST', body: { birth_date: pending.birth_date, request_id: pending.request_id, client: 'web', use_profile: !!pending.use_profile, profile_fingerprint: pending.profile_fingerprint || null } });
      if (!active.current) return;
      const next = accept(response);
      remember(terminal(next.status) ? null : { ...pending, order_id: next.order_id });
      select(next.order_id);
      if (next.url && !terminal(next.status)) window.location.assign(checkoutUrl(next.url));
    } catch (failure) { if (active.current) {
      setError(failure.message);
      try { if(failure.code==='full_report_profile_changed'){const saved=readAttempt(key);if(saved)remember({...saved,profile_stale:true});}
      if(failure.code==='full_report_attempt_frozen'&&failure.orderId){const saved=readAttempt(key);if(saved)remember({...saved,order_id:failure.orderId,profile_stale:false});select(failure.orderId);}
      } catch(recovery){setError(recovery.message);}
    } }
    finally { inFlight.current = false; if (active.current) setBusy(false); }
  }
  async function cancel() {
    if (!order || inFlight.current) return;
    inFlight.current = true; setBusy(true); setError('');
    try { const value = await api.request(`/full-reports/${encodeURIComponent(order.order_id)}/cancel`, { method: 'POST', body: {} }); if (active.current) accept(value); }
    catch (failure) { if (active.current) setError(failure.message); }
    finally { inFlight.current = false; if (active.current) setBusy(false); }
  }
  async function extend() {
    if (!order || !preview?.use_profile || preview.birth_date!==order.birth_date || inFlight.current) return;
    const selected=order.order_id;
    inFlight.current=true;setBusy(true);setError('');
    try { const next=await api.request(`/full-reports/${order.order_id}/extend-profile`,{method:'POST',body:{profile_fingerprint:preview.profile_fingerprint,expected_revision:order.revision||1}});if(active.current&&selectedBoundary.current===selected){if(next.is_archived)setArchive(fullReportOrder(next));else{accept(next);setArchive(null);setRevision(value=>value+1);}} }
    catch(failure){if(active.current)setError(failure.message);}
    finally{inFlight.current=false;if(active.current)setBusy(false);}
  }
  async function openRevision(number) {
    if(!order||inFlight.current)return;const selected=order.order_id;inFlight.current=true;setBusy(true);setError('');
    try{const next=fullReportOrder(await api.request(`/full-reports/${order.order_id}/revisions/${number}`));if(active.current&&selectedBoundary.current===selected)setArchive(next);}
    catch(failure){if(active.current)setError(failure.message);}
    finally{inFlight.current=false;if(active.current)setBusy(false);}
  }
  const canPay = catalog?.enabled && catalog.clients.includes('web');
  return <div className="fr-page">
    <header className="fr-heading"><div><span className="fr-eyebrow">Отдельная услуга NumerOM</span><h1>Ваши числа.<br />Один полный разбор.</h1><p>Персональные числа, взаимосвязи и циклы — с объяснениями, авторскими схемами, озвучкой и персональным видео. Сохраните результаты в одном отчёте.</p></div><div className="fr-emblem" aria-hidden="true"><span>01—09</span><FileText size={43} strokeWidth={1.2} /><small>ВАША ИСТОРИЯ В ЧИСЛАХ</small></div></header>
    <div className="fr-offer-grid"><section className="fr-includes"><h2>Что входит в разбор</h2><ul>{(catalog?.includes || ['Все расчёты проекта, которым достаточно даты рождения', 'Объяснения ваших результатов и способов расчёта', 'Схемы и графики в отчёте', 'Персональная озвучка, MP4 и сохранение в PDF']).map((item, index) => <li key={index}><Check size={18} aria-hidden="true" />{typeof item === 'string' ? item : item?.title}</li>)}</ul><div className="fr-offer-note"><Headphones size={19} aria-hidden="true" /><p>Читайте, слушайте и возвращайтесь к разбору из своего кабинета.</p></div></section>
      <section className="fr-purchase"><span className="fr-eyebrow">Один разбор · одна дата рождения</span><div className="fr-price">{catalog ? price(catalog) : '6,66 €'}</div><p>Разовый платёж через Stripe. Баллы не списываются. Подписки нет.</p>
        {catalog?.mode === 'test' && <p className="fr-test" role="status">Тестовый режим Stripe. Это проверка оплаты, реальные деньги не списываются.</p>}
        <form onSubmit={purchase}><label htmlFor="full-report-birth-date">Дата рождения<input id="full-report-birth-date" type="date" required value={birthDate} min="1900-01-01" max={today()} disabled={busy || !!attempt} onChange={event => setBirthDate(event.target.value)} /></label>{(!attempt || attempt.profile_stale) && order?.status!=='paid' && <ReportProfilePreview user={user} birth={toDate(birthDate)} useProfile={useProfile} onUseProfile={setUseProfile} onPreview={setPreview} disabled={busy}/>}<button className="fr-button" disabled={busy || !canPay || !!attempt?.order_id || (attempt?.profile_stale && !preview) || (!attempt && useProfile && toDate(birthDate) === user.birth_date && !preview)}>{busy ? 'Проверяем заказ…' : attempt && !attempt.order_id ? 'Продолжить начатую оплату' : catalog ? `Получить разбор за ${price(catalog)}` : 'Загружаем стоимость…'}<ArrowUpRight size={18} aria-hidden="true" /></button></form>
        {attempt && <p className="fr-pending-note">У вас есть начатая попытка оплаты{attempt.birth_date ? ` для ${attempt.birth_date}` : ''}. Сначала проверьте её статус: повторная покупка не требуется.{attempt.order_id && <button className="fr-text-button" onClick={() => select(attempt.order_id)}>К начатой оплате</button>}</p>}
        {catalog && !canPay && <p role="status">{catalog.message || 'Оплата пока недоступна. Ваши готовые отчёты остаются в истории.'}</p>}
        <span className="fr-security"><ShieldCheck size={16} aria-hidden="true" /> Готовый отчёт открывается после подтверждения оплаты</span>
      </section></div>
    {!attempt && order?.status==='paid' && <ReportProfilePreview user={user} birth={order.birth_date} useProfile={useProfile} onUseProfile={setUseProfile} onPreview={setPreview} disabled={busy}/>}
    {order?.status==='paid' && preview?.use_profile && preview.profile_fingerprint!==order.profile_fingerprint && <div className="fr-profile-upgrade"><p>Добавьте текущие данные профиля в этот оплаченный разбор. Предыдущая версия сохранится; текст, аудио и видео новой версии подготовятся заново.</p><button className="fr-button" disabled={busy} onClick={extend}>Дополнить разбор без доплаты</button></div>}
    {error && <div className="fr-notice fr-error" role="alert"><p>{error}</p><button className="fr-button secondary" disabled={busy} onClick={() => setRevision(value => value + 1)}>Проверить снова</button></div>}
    {loading && <ReportPreparing birthDate={user.birth_date} message="Загружаем услугу и ваши отчёты." />}
    {order?.status === 'paid' && !order.report && <ReportPreparing birthDate={order.birth_date} message={order.message || 'Оплата подтверждена. Отчёт готовится; повторная оплата не нужна.'} />}
    {order && <section className="fr-order" aria-label="Статус заказа"><div><span className="fr-eyebrow">Разбор для {order.person ? `${order.person}, ` : ''}{order.birth_date}</span><h2>{fullReportStatus(order.status, order.report_status)}</h2><p>{price(order)}{order.mode === 'test' ? ' · Тестовая оплата' : ''}</p></div><div className="fr-order-actions"><button className="fr-button secondary" disabled={busy} onClick={() => setRevision(value => value + 1)}><RefreshCw size={16} aria-hidden="true" /> Проверить статус</button>{!terminal(order.status) && <><button className="fr-button" disabled={busy || !order.url} onClick={() => { const url = checkoutUrl(order.url); if (url) window.location.assign(url); else setError('Ссылка оплаты пока недоступна. Проверьте статус заказа.'); }}>Перейти к оплате</button><button className="fr-text-button" disabled={busy} onClick={cancel}>Отменить эту попытку</button></>}</div></section>}
    {!!order?.previous_revisions?.length && <div className="fr-revisions"><h3>Версии разбора</h3><button className="fr-text-button" onClick={()=>setArchive(null)}>Текущая версия {order.revision || 1}</button>{order.previous_revisions.map(item=><button key={item.revision} className="fr-text-button" disabled={busy} onClick={()=>openRevision(item.revision)}>Версия {item.revision}</button>)}{archive&&<p>Открыта сохранённая версия {archive.revision}. Аудио и видео доступны в текущей версии.</p>}</div>}
    {order?.status === 'paid' && (archive?.report || order.report) && <Report key={`${order.order_id}-${archive?.revision || order.revision || 1}`} order={archive||order} archived={!!archive} />}
    <section className="fr-history"><h2>Мои полные разборы</h2>{!orders.length ? <p>После первой покупки отчёт сохранится здесь. Доступен только в вашем аккаунте.</p> : <ul>{orders.map(item => <li key={item.order_id}><button onClick={() => select(item.order_id)} aria-current={selectedId === item.order_id ? 'true' : undefined}><FileText size={20} aria-hidden="true" /><span><strong>{item.person ? `${item.person} · ${item.birth_date}` : item.birth_date}</strong><small>{fullReportStatus(item.status, item.report_status)}{item.mode === 'test' ? ' · Тестовый' : ''}</small></span><span>{price(item)}</span></button></li>)}</ul>}</section>
  </div>;
}

export default function FullReportPage() {
  const { user } = useAuth();
  return user ? <Workspace key={user.id} user={user} /> : <p>Войдите в аккаунт, чтобы получить персональный разбор.</p>;
}
