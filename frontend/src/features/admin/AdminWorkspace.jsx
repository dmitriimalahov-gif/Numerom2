import React, { lazy, Suspense, useEffect, useState } from 'react';
import { Link, NavLink, useParams } from 'react-router-dom';
import { BookOpen, CalendarDays, ChevronRight, LayoutDashboard, MailCheck, Settings, ShieldCheck, Users } from 'lucide-react';
import { useAuth } from '../../components/AuthContext';
import { api } from '../../services/api';
import UsersPanel from './UsersPanel';
import './admin.css';

const AdminPanel = lazy(() => import('../../components/AdminPanel'));
const AdminPanelV2 = lazy(() => import('../../components/AdminPanelV2'));
const sections = [
  { id: '', title: 'Обзор', icon: LayoutDashboard, description: 'Пользователи, обучение и работа платформы.' },
  { id: 'users', title: 'Пользователи и доступ', icon: Users, description: 'Профили, роли, доступ к платформе и баланс кредитов.' },
  { id: 'learning', title: 'Уроки и материалы', icon: BookOpen, description: 'Содержание занятий, файлы и проверка ответов учеников.' },
  { id: 'consultations', title: 'Консультации', icon: CalendarDays, description: 'Личные консультации, материалы и назначения ученикам.' },
  { id: 'settings', title: 'Настройки платформы', icon: Settings, description: 'Стоимость услуг и правила начисления баллов.' },
];

export function AdminNotice({ children, error = false, onRetry }) {
  return <div className={`nm-admin-notice${error ? ' is-error' : ''}`} role={error ? 'alert' : 'status'}><p>{children}</p>{onRetry && <button type="button" className="nm-admin-button secondary" onClick={onRetry}>Повторить</button>}</div>;
}

function Overview() {
  const [state, setState] = useState({ loading: true });
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let current = true;
    const controller = new AbortController();
    setState({ loading: true });
    api.request('/admin/manage/overview', { signal: controller.signal }).then(data => {
      if (current) setState({ data });
    }).catch(error => { if (current) setState({ error: error.message }); });
    return () => { current = false; controller.abort(); };
  }, [revision]);
  return <>
    {state.loading ? <AdminNotice>Загружаем данные платформы…</AdminNotice> : state.error ? <AdminNotice error onRetry={() => setRevision(value => value + 1)}>{state.error}</AdminNotice> : <dl className="nm-admin-overview">
      {[
        ['users_total', 'Пользователи'], ['admins_total', 'Администраторы'], ['users_disabled', 'Доступ закрыт'], ['lessons_total', 'Уроки'], ['consultations_total', 'Консультации'],
      ].map(([key, label]) => <div key={key}><dt>{label}</dt><dd>{Number.isFinite(state.data?.[key]) ? state.data[key].toLocaleString('ru-RU') : '—'}</dd></div>)}
    </dl>}
    <RecoveryStatus />
    <div className="nm-admin-section-links">{sections.slice(1).map(({ id, title, icon: Icon, description }) => <Link to={`/dashboard/admin/${id}`} key={id}><Icon aria-hidden="true" size={23} /><div><h2>{title}</h2><p>{description}</p></div><ChevronRight aria-hidden="true" size={19} /></Link>)}</div>
  </>;
}

function RecoveryStatus() {
  const [state, setState] = useState({ loading: true });
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let current = true;
    const controller = new AbortController();
    setState({ loading: true });
    api.request('/admin/manage/recovery-status', { signal: controller.signal }).then(data => {
      if (current) setState(typeof data.configured === 'boolean' ? { configured: data.configured } : { error: true });
    }).catch(() => { if (current) setState({ error: true }); });
    return () => { current = false; controller.abort(); };
  }, [revision]);
  return <section className="nm-admin-recovery" aria-label="Восстановление пароля">
    <MailCheck size={23} aria-hidden="true" />
    <div><h2>Восстановление пароля</h2>
      {state.loading ? <p role="status">Проверяем настройки почты…</p> : state.error ? <><p role="alert">Не удалось проверить настройки отправки писем.</p><button type="button" className="nm-admin-button secondary" onClick={() => setRevision(value => value + 1)}>Проверить ещё раз</button></> : <>
        <p>{state.configured ? 'Отправка писем настроена. Пользователи могут запросить ссылку для восстановления на странице входа.' : 'Отправка писем не настроена. Восстановление пароля по почте пока недоступно; требуется настройка почты на сервере.'}</p>
        <span className={`nm-admin-badge${state.configured ? '' : ' is-disabled'}`}>{state.configured ? 'Почта настроена' : 'Почта не настроена'}</span>
      </>}
    </div>
  </section>;
}


function AuthorizedWorkspace({ actor }) {
  const { '*': rest = '' } = useParams();
  const id = rest.split('/')[0];
  const section = sections.find(item => item.id === id);
  return <div className="nm-admin-workspace">
    <header className="nm-admin-header"><div><p className="nm-admin-context"><ShieldCheck aria-hidden="true" size={17} /> Управление NumerOM</p><h1>{section?.title || 'Раздел не найден'}</h1><p>{section?.description || 'Выберите раздел управления в меню.'}</p></div><span className="nm-admin-role">{actor.is_super_admin ? 'Суперадминистратор' : 'Администратор'}</span></header>
    <div className="nm-admin-layout"><nav className="nm-admin-nav" aria-label="Управление платформой">{sections.map(({ id: sectionId, title, icon: Icon }) => <NavLink key={sectionId} end={sectionId === ''} to={`/dashboard/admin${sectionId ? `/${sectionId}` : ''}`}><Icon aria-hidden="true" size={19} /><span>{title}</span></NavLink>)}</nav>
      <section className="nm-admin-content" aria-label={section?.title || 'Управление'}><Suspense fallback={<AdminNotice>Открываем раздел…</AdminNotice>}>
        {id === '' && <Overview />}
        {id === 'users' && <UsersPanel actor={actor} />}
        {id === 'learning' && <div className="nm-admin-legacy"><AdminPanelV2 embedded /></div>}
        {id === 'consultations' && <div className="nm-admin-legacy"><AdminPanel embedded selectedSection="consultations" /></div>}
        {id === 'settings' && <div className="nm-admin-legacy"><AdminPanel embedded selectedSection="settings" /></div>}
        {!section && <Link className="nm-admin-button" to="/dashboard/admin">Вернуться к обзору</Link>}
      </Suspense></section></div>
  </div>;
}

export default function AdminWorkspace() {
  const { user, loading } = useAuth();
  if (loading) return <div className="nm-admin-workspace"><AdminNotice>Проверяем доступ…</AdminNotice></div>;
  if (!user || user.is_disabled || !(user.is_admin || user.is_super_admin)) return <section className="nm-admin-workspace nm-admin-denied"><ShieldCheck size={30} aria-hidden="true" /><h1>Доступ ограничен</h1><p>Этот раздел доступен администраторам NumerOM.</p><Link className="nm-admin-button secondary" to="/dashboard/home">Вернуться в кабинет</Link></section>;
  return <AuthorizedWorkspace key={user.id} actor={user} />;
}
