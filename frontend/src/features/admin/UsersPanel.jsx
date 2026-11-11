import React, { useEffect, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, Search, ShieldCheck, UserRound } from 'lucide-react';
import { api } from '../../services/api';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../../components/ui/dialog';

const userName = user => user.full_name || user.name || user.email || 'Без имени';
const formatNumber = value => Number.isFinite(value) ? value.toLocaleString('ru-RU') : '—';
const formatDate = value => value && !Number.isNaN(new Date(value).getTime()) ? new Date(value).toLocaleDateString('ru-RU') : '—';
const detailPath = id => `/admin/manage/users/${encodeURIComponent(id)}`;
const roleName = user => user.is_super_admin ? 'Суперадминистратор' : user.is_admin ? 'Администратор' : 'Ученик';

function Notice({ error, children, retry }) {
  return <div className={`nm-admin-notice${error ? ' is-error' : ''}`} role={error ? 'alert' : 'status'}><p>{children}</p>{retry && <button type="button" className="nm-admin-button secondary" onClick={retry}>Повторить</button>}</div>;
}

function UserEditor({ id, actor, onUpdated, onBusy }) {
  const [state, setState] = useState({ loading: true });
  const [revision, setRevision] = useState(0);
  const [amount, setAmount] = useState('');
  const [creditReason, setCreditReason] = useState('');
  const [accessReason, setAccessReason] = useState('');
  const [access, setAccess] = useState({ is_admin: false, is_disabled: false });
  const [confirmation, setConfirmation] = useState(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [mutationError, setMutationError] = useState('');
  const [historyError, setHistoryError] = useState('');
  const busy = useRef(false);
  const current = useRef(true);
  const needsReload = useRef(false);

  useEffect(() => {
    current.current = true;
    const controller = new AbortController();
    setState({ loading: true }); setHistoryError('');
    api.request(detailPath(id), { signal: controller.signal }).then(data => {
      if (!controller.signal.aborted) {
        setState({ data });
        setAccess({ is_admin: Boolean(data.user.is_admin), is_disabled: Boolean(data.user.is_disabled) });
        needsReload.current = false;
      }
    }).catch(error => { if (!controller.signal.aborted) setState({ error: error.message }); });
    return () => { current.current = false; controller.abort(); };
  }, [id, revision]);

  const change = async () => {
    if (busy.current || !confirmation || needsReload.current) return;
    busy.current = true; setSaving(true); onBusy(true); setMutationError(''); setMessage('');
    try {
      const result = await api.request(`${detailPath(id)}/${confirmation.kind}`, { method: 'PATCH', body: confirmation.body });
      if (!current.current) return;
      setState(previous => ({ data: { ...previous.data, user: result.user } }));
      setAccess({ is_admin: Boolean(result.user.is_admin), is_disabled: Boolean(result.user.is_disabled) });
      onUpdated(result.user);
      setConfirmation(null);
      if (confirmation.kind === 'credits') { setAmount(''); setCreditReason(''); setMessage('Кредиты обновлены'); }
      else { setAccessReason(''); setMessage('Доступ обновлён'); }
      // Reload the audit trail from its source after a successful mutation.
      try {
        const fresh = await api.request(detailPath(id));
        if (current.current) { setState({ data: fresh }); setAccess({ is_admin: Boolean(fresh.user.is_admin), is_disabled: Boolean(fresh.user.is_disabled) }); onUpdated(fresh.user); setHistoryError(''); }
      } catch { if (current.current) setHistoryError('Изменение сохранено, но история не обновилась.'); }
    } catch (error) {
      if (!current.current) return;
      if (error.status === 409) {
        setConfirmation(null);
        needsReload.current = true;
        setMutationError('Данные изменились. Загружаем актуальные значения; проверьте изменение ещё раз.');
        try {
          const fresh = await api.request(detailPath(id));
          if (current.current) {
            setState({ data: fresh }); setAccess({ is_admin: Boolean(fresh.user.is_admin), is_disabled: Boolean(fresh.user.is_disabled) }); onUpdated(fresh.user);
            needsReload.current = false;
            setMutationError('Данные обновлены. Проверьте новый баланс и подтвердите изменение ещё раз.');
          }
        } catch {
          if (current.current) { setState({ error: 'Не удалось обновить данные. Повторите загрузку перед изменением.' }); }
        }
      } else { setMutationError(error.message); }
    } finally {
      busy.current = false;
      if (current.current) { setSaving(false); onBusy(false); }
    }
  };

  if (state.loading) return <Notice>Загружаем профиль…</Notice>;
  if (state.error) return <Notice error retry={() => setRevision(value => value + 1)}>{state.error}</Notice>;
  const user = state.data.user;
  const isSelf = String(actor.id) === String(user.id);
  const canEditAccess = !isSelf && !user.is_super_admin && (actor.is_super_admin || !user.is_admin);
  const canEditCredits = actor.is_super_admin || (!user.is_super_admin && (!user.is_admin || isSelf));
  const delta = Number(amount);
  const balance = user.credits_remaining;
  const after = balance + delta;
  const validCredit = amount.trim() !== '' && Number.isInteger(delta) && delta !== 0 && Math.abs(delta) <= 1000000 && Number.isInteger(balance) && after >= 0 && after <= 1000000 && creditReason.trim().length >= 1;
  const accessChanged = access.is_admin !== Boolean(user.is_admin) || access.is_disabled !== Boolean(user.is_disabled);
  const history = Array.isArray(state.data.admin_history) ? [...state.data.admin_history].reverse() : [];

  return <div className="nm-admin-user-editor">
    <div className="nm-admin-user-summary"><div className="nm-admin-avatar"><UserRound size={25} aria-hidden="true" /></div><div><strong>{userName(user)}</strong><span>{user.email}</span></div><span className={`nm-admin-badge${user.is_disabled ? ' is-disabled' : ''}`}>{user.is_disabled ? 'Доступ закрыт' : roleName(user)}</span></div>
    <dl className="nm-admin-user-facts"><div><dt>Кредиты</dt><dd data-testid="current-balance">{formatNumber(balance)}</dd></div><div><dt>Регистрация</dt><dd>{formatDate(user.created_at)}</dd></div></dl>
    {message && <Notice>{message}</Notice>}{mutationError && <Notice error>{mutationError}</Notice>}
    {confirmation ? <section className="nm-admin-confirm" aria-label="Подтверждение изменения">
      <h3>{confirmation.kind === 'credits' ? 'Проверьте изменение кредитов' : 'Проверьте изменение доступа'}</h3>
      {confirmation.kind === 'credits' ? <dl className="nm-admin-credit-preview"><div><dt>Было</dt><dd>{formatNumber(confirmation.body.expected_balance)}</dd></div><div><dt>Изменение</dt><dd>{confirmation.body.amount > 0 ? '+' : ''}{formatNumber(confirmation.body.amount)}</dd></div><div><dt>Станет</dt><dd>{formatNumber(confirmation.body.expected_balance + confirmation.body.amount)}</dd></div></dl> : <ul>{'is_admin' in confirmation.body && <li>Роль: {user.is_admin ? 'Администратор' : 'Ученик'} → {confirmation.body.is_admin ? 'Администратор' : 'Ученик'}</li>}{'is_disabled' in confirmation.body && <li>Доступ: {user.is_disabled ? 'закрыт' : 'открыт'} → {confirmation.body.is_disabled ? 'закрыт' : 'открыт'}</li>}</ul>}
      <p>Причина: {confirmation.body.reason}</p><div className="nm-admin-actions"><button type="button" className="nm-admin-button" disabled={saving} onClick={change}>{saving ? 'Сохраняем…' : confirmation.kind === 'credits' ? confirmation.body.amount > 0 ? 'Подтвердить начисление' : 'Подтвердить списание' : 'Подтвердить доступ'}</button><button type="button" className="nm-admin-button secondary" disabled={saving} onClick={() => setConfirmation(null)}>Вернуться к изменению</button></div>
    </section> : <>
      <form className="nm-admin-editor-section" onSubmit={event => { event.preventDefault(); if (validCredit && canEditCredits) { setMutationError(''); setMessage(''); setConfirmation({ kind: 'credits', body: { amount: delta, expected_balance: balance, reason: creditReason.trim() } }); } }}>
        <h3>Кредиты</h3><p>Положительное число начисляет кредиты, отрицательное — списывает.</p>
        {!canEditCredits ? <p className="nm-admin-hint">Изменять баланс этого администратора может суперадминистратор.</p> : <fieldset disabled={saving}><div className="nm-admin-form-grid"><div><label htmlFor="admin-credit-amount">Изменение баланса</label><input id="admin-credit-amount" type="number" min="-1000000" max="1000000" step="1" placeholder="Например, 100 или −50" value={amount} onChange={event => setAmount(event.target.value)} /></div><div><label htmlFor="admin-credit-reason">Причина изменения</label><input id="admin-credit-reason" minLength="1" maxLength="500" required value={creditReason} onChange={event => setCreditReason(event.target.value)} placeholder="Например, возврат за консультацию" /></div></div>
        {amount && Number.isInteger(delta) && <p className="nm-admin-hint">Баланс после изменения: <strong>{formatNumber(after)}</strong></p>}{amount && (after < 0 || after > 1000000) && <p className="nm-admin-field-error">Итоговый баланс должен быть от 0 до 1 000 000.</p>}<button className="nm-admin-button" disabled={!validCredit} type="submit">Проверить изменение</button></fieldset>}
      </form>
      <form className="nm-admin-editor-section" onSubmit={event => { event.preventDefault(); if (!canEditAccess || !accessChanged || accessReason.trim().length < 1) return; const body = { reason: accessReason.trim() }; if (actor.is_super_admin && access.is_admin !== Boolean(user.is_admin)) body.is_admin = access.is_admin; if (access.is_disabled !== Boolean(user.is_disabled)) body.is_disabled = access.is_disabled; setMutationError(''); setMessage(''); setConfirmation({ kind: 'access', body }); }}>
        <h3>Доступ к платформе</h3>{!canEditAccess ? <p className="nm-admin-hint">{isSelf ? 'Собственные права доступа здесь изменить нельзя.' : 'Изменение доступа для этого администратора недоступно.'}</p> : <fieldset disabled={saving}><div className="nm-admin-access-options">{actor.is_super_admin && <label><input type="checkbox" checked={access.is_admin} onChange={event => setAccess(previous => ({ ...previous, is_admin: event.target.checked }))} /><span>Права администратора<small>Доступ к управлению пользователями и содержимым</small></span></label>}<label><input type="checkbox" checked={access.is_disabled} onChange={event => setAccess(previous => ({ ...previous, is_disabled: event.target.checked }))} /><span>Закрыть доступ к платформе<small>Пользователь не сможет войти в свой кабинет</small></span></label></div><label htmlFor="admin-access-reason">Причина изменения доступа</label><input id="admin-access-reason" required minLength="1" maxLength="500" value={accessReason} onChange={event => setAccessReason(event.target.value)} /><button type="submit" className="nm-admin-button secondary" disabled={!accessChanged || accessReason.trim().length < 1}>Проверить доступ</button></fieldset>}</form>
    </>}
    <section className="nm-admin-editor-section"><h3>История изменений</h3>{historyError && <Notice error retry={() => setRevision(value => value + 1)}>{historyError}</Notice>}{!history.length ? <p className="nm-admin-hint">Изменений доступа и кредитов пока нет.</p> : <ol className="nm-admin-history">{history.map((entry, index) => <li key={entry.id || index}><div><strong>{entry.action === 'credits' || entry.action?.includes('credit') ? 'Кредиты' : 'Доступ'}</strong><time dateTime={entry.created_at}>{formatDate(entry.created_at)}</time></div><p>{entry.reason || 'Причина не указана'}</p>{entry.after?.credits_remaining !== undefined && <span>{formatNumber(entry.before?.credits_remaining)} → {formatNumber(entry.after.credits_remaining)}</span>}</li>)}</ol>}</section>
  </div>;
}

export default function UsersPanel({ actor }) {
  const [search, setSearch] = useState('');
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const [state, setState] = useState({ loading: true });
  const [revision, setRevision] = useState(0);
  const [selected, setSelected] = useState(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let current = true;
    const controller = new AbortController();
    setState({ loading: true });
    const params = new URLSearchParams({ q: query, page: String(page), page_size: '20' });
    api.request(`/admin/manage/users?${params}`, { signal: controller.signal }).then(data => { if (current) setState({ data }); }).catch(error => { if (current) setState({ error: error.message }); });
    return () => { current = false; controller.abort(); };
  }, [query, page, revision]);
  const updateUser = user => setState(previous => previous.data ? { data: { ...previous.data, users: previous.data.users.map(item => item.id === user.id ? user : item) } } : previous);
  const users = state.data?.users || [];
  const total = state.data?.total;
  return <>
    <form className="nm-admin-search" role="search" onSubmit={event => { event.preventDefault(); setQuery(search.trim()); setPage(1); }}><label htmlFor="admin-user-search">Найти пользователя</label><div><Search size={19} aria-hidden="true" /><input id="admin-user-search" type="search" maxLength="200" autoComplete="off" value={search} onChange={event => setSearch(event.target.value)} placeholder="Имя или электронная почта" /><button className="nm-admin-button" type="submit">Найти</button></div></form>
    {state.loading ? <Notice>Загружаем пользователей…</Notice> : state.error ? <Notice error retry={() => setRevision(value => value + 1)}>{state.error}</Notice> : <>
      <div className="nm-admin-list-heading"><h2>{query ? 'Результаты поиска' : 'Все пользователи'}</h2><span>{formatNumber(total)}</span></div>
      {!users.length ? <div className="nm-admin-empty"><UsersEmpty /><h3>{query ? 'Пользователи не найдены' : 'Пользователей пока нет'}</h3><p>{query ? 'Проверьте имя или адрес электронной почты.' : 'Здесь появятся зарегистрированные пользователи платформы.'}</p>{query && <button type="button" className="nm-admin-button secondary" onClick={() => { setSearch(''); setQuery(''); setPage(1); }}>Сбросить поиск</button>}</div> : <div className="nm-admin-table-wrap"><table className="nm-admin-table"><thead><tr><th>Пользователь</th><th>Доступ</th><th>Кредиты</th><th><span className="sr-only">Действия</span></th></tr></thead><tbody>{users.map(user => <tr key={user.id}><td><strong>{userName(user)}</strong><span className="nm-admin-user-email">{user.email}</span></td><td><span className={`nm-admin-badge${user.is_disabled ? ' is-disabled' : ''}`}>{user.is_disabled ? 'Доступ закрыт' : roleName(user)}</span></td><td data-label="Кредиты">{formatNumber(user.credits_remaining)}</td><td><button className="nm-admin-open-user" type="button" onClick={() => setSelected(user.id)}>Открыть <span className="sr-only">{userName(user)}</span><ChevronRight size={17} aria-hidden="true" /></button></td></tr>)}</tbody></table></div>}
      {Number.isFinite(total) && total > 20 && <nav className="nm-admin-pagination" aria-label="Страницы пользователей"><button type="button" className="nm-admin-button secondary" disabled={page === 1} onClick={() => setPage(value => value - 1)}><ChevronLeft size={16} /> Назад</button><span>Страница {page} из {Math.ceil(total / 20)}</span><button type="button" className="nm-admin-button secondary" disabled={page * 20 >= total} onClick={() => setPage(value => value + 1)}>Далее <ChevronRight size={16} /></button></nav>}
    </>}
    <Dialog open={selected !== null} onOpenChange={open => { if (!open && !busy) setSelected(null); }}><DialogContent className="nm-admin-user-dialog" onEscapeKeyDown={event => { if (busy) event.preventDefault(); }} onInteractOutside={event => { if (busy) event.preventDefault(); }}><DialogHeader><DialogTitle>Карточка пользователя</DialogTitle><DialogDescription>Профиль, доступ и баланс кредитов.</DialogDescription></DialogHeader>{selected !== null && <UserEditor key={selected} id={selected} actor={actor} onUpdated={updateUser} onBusy={setBusy} />}</DialogContent></Dialog>
  </>;
}
function UsersEmpty() { return <ShieldCheck size={28} aria-hidden="true" />; }
