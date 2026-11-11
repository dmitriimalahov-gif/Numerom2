import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowUpRight, BookOpen, CalendarDays, ChevronRight, Compass, FileText, Grid3X3, Heart, Plus, RefreshCw, UserRound, Wallet } from 'lucide-react';
import { Button } from './ui/button';
import { useAuth } from './AuthContext';
import PaymentModal from './PaymentModal';
import { getBackendUrl } from '../utils/backendUrl';
import { Illustration } from './NumerologyIllustrations';

const tools = [
  { to: 'numerology-design', icon: Grid3X3, tone: 'blue', title: 'Карта чисел', text: 'Персональные числа и квадрат Пифагора' },
  { to: 'compatibility', icon: Heart, tone: 'rose', title: 'Совместимость', text: 'Исследуйте ваши отношения через числа' },
  { to: 'planetary-route', icon: Compass, tone: 'green', title: 'Планетарный маршрут', text: 'Энергии и рекомендации на каждый день' },
];

const HomeContent = () => {
  const { user } = useAuth();
  const [paymentOpen, setPaymentOpen] = useState(false);
  const [pointsBreakdown, setPointsBreakdown] = useState(null);
  const [pointsStatus, setPointsStatus] = useState('loading');
  const loadPoints = useCallback(async (signal) => {
    setPointsStatus('loading');
    try {
      const response = await fetch(`${getBackendUrl()}/api/user/points-breakdown`, { signal, headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
      if (!response.ok) throw new Error('Points unavailable');
      const data = await response.json();
      if (!signal?.aborted) { setPointsBreakdown(data); setPointsStatus('ready'); }
    } catch (error) {
      if (!signal?.aborted) setPointsStatus('error');
    }
  }, []);
  useEffect(() => {
    if (!user) return;
    const controller = new AbortController();
    loadPoints(controller.signal);
    return () => controller.abort();
  }, [user, loadPoints]);

  const firstName = (user?.full_name || user?.name || '').trim().split(' ')[0];
  const dateLabel = new Date().toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', weekday: 'long' });
  const breakdown = [
    ['Заработано в обучении', 'earned_points'], ['Приобретено', 'purchased_points'],
    ['Начислено администратором', 'admin_points'], ['За проверку заданий', 'exercise_review_points'],
  ];

  return (
    <div className="nm-home">
      <div className="nm-home-heading"><div><span className="nm-section-label">Ваш личный кабинет</span><h1>{firstName ? `Здравствуйте, ${firstName}` : 'Добро пожаловать'}</h1><p>Немного времени для себя и новых открытий.</p></div><span className="nm-date"><CalendarDays size={16} aria-hidden="true" />{dateLabel}</span></div>
      <section className="nm-welcome-panel" aria-labelledby="welcome-title">
        <div><span className="nm-topic"><span /> Самопознание начинается с интереса</span><h2 id="welcome-title">Ваша история<br />на языке чисел</h2><p>{user?.birth_date ? 'Вернитесь к своей карте: знакомые числа могут открыть новые стороны вашей личности.' : 'Добавьте дату рождения в профиль, чтобы начать знакомство со своей картой чисел.'}</p><Button asChild size="lg"><Link to={user?.birth_date ? '/dashboard/numerology-design' : '/dashboard/personal-data'}>{user?.birth_date ? 'Открыть мою карту' : 'Заполнить профиль'}<ArrowUpRight aria-hidden="true" /></Link></Button></div>
        <div className="nm-welcome-art"><Illustration name="KVADRAT" alt="Квадрат NumerOM: девять базовых чисел" /></div>
      </section>
      <section aria-labelledby="tools-title"><div className="nm-row-heading"><h2 id="tools-title">Что исследуем сегодня?</h2><span>Инструменты для вашей практики</span></div><div className="nm-quick-tools">{tools.map(({ to, icon: Icon, tone, title, text }) => <Link key={to} to={`/dashboard/${to}`} className={`nm-tool-card nm-tone-${tone}`}><span className="nm-feature-icon"><Icon size={23} strokeWidth={1.6} aria-hidden="true" /></span><ArrowUpRight className="nm-tool-arrow" size={18} aria-hidden="true" /><h3>{title}</h3><p>{text}</p></Link>)}</div></section>
      <div className="nm-home-columns">
        <div className="nm-home-main-column">
          <section className="nm-panel nm-learning-panel" aria-labelledby="learning-title"><div className="nm-row-heading"><span className="nm-section-label"><BookOpen size={17} aria-hidden="true" /> Учиться и практиковаться</span></div><h2 id="learning-title">Каждое открытие начинается<br />с нового знания</h2><p>Уроки, задания и тесты помогут разобраться в нумерологии шаг за шагом.</p><Button asChild><Link to="/dashboard/learning-v2">Перейти к обучению<ChevronRight aria-hidden="true" /></Link></Button><Link className="nm-resource-link" to="/dashboard/visual-guide"><Grid3X3 size={18} aria-hidden="true" /><span>Схемы и примеры<small>Наглядные иллюстрации NumerOM</small></span><ChevronRight size={17} aria-hidden="true" /></Link><Link className="nm-resource-link" to="/dashboard/materials"><FileText size={18} aria-hidden="true" /><span>Библиотека материалов<small>Материалы к урокам в одном месте</small></span><ChevronRight size={17} aria-hidden="true" /></Link></section>
          <section className="nm-panel nm-profile-panel" aria-labelledby="profile-title"><div className="nm-row-heading"><h2 id="profile-title">Мой профиль</h2><Link to="/dashboard/personal-data" className="nm-text-link">Изменить<ArrowUpRight size={15} aria-hidden="true" /></Link></div><dl className="nm-profile-data"><div><dt><UserRound size={15} aria-hidden="true" />Имя</dt><dd>{user?.full_name || user?.name || 'Не указано'}</dd></div><div><dt><CalendarDays size={15} aria-hidden="true" />Дата рождения</dt><dd>{user?.birth_date || 'Добавьте дату рождения'}</dd></div></dl><p className="nm-profile-email">{user?.email}</p></section>
        </div>
        <section className="nm-panel nm-wallet-panel" aria-labelledby="wallet-title"><div className="nm-row-heading"><h2 id="wallet-title">Ваш баланс</h2><Wallet size={20} aria-hidden="true" /></div><div className="nm-wallet-value">{user?.credits_remaining ?? '—'}<span>баллов</span></div><p>Используйте баллы для расчётов и изучения своих чисел.</p><Button variant="outline" className="w-full" onClick={() => setPaymentOpen(true)}><Plus aria-hidden="true" />Пополнить баланс</Button><div className="nm-points-breakdown" aria-live="polite">{pointsStatus === 'loading' ? <p role="status">Загружаем детализацию…</p> : pointsStatus === 'error' ? <div className="nm-inline-error"><p>Детализация пока недоступна.</p><button className="nm-text-link" onClick={() => loadPoints()}><RefreshCw size={14} aria-hidden="true" />Повторить</button></div> : <dl>{breakdown.map(([label, key]) => <div key={key}><dt>{label}</dt><dd>{pointsBreakdown?.[key] ?? '—'}</dd></div>)}</dl>}</div><Link to="/dashboard/credit-history" className="nm-text-link">История баллов<ChevronRight size={16} aria-hidden="true" /></Link><div className="nm-account-status"><span>{user?.is_premium ? 'Premium-подписка' : 'Базовый аккаунт'}</span>{user?.subscription_expires_at && <small>До {new Date(user.subscription_expires_at).toLocaleDateString('ru-RU')}</small>}</div></section>
      </div>
      <PaymentModal isOpen={paymentOpen} onClose={() => setPaymentOpen(false)} />
    </div>
  );
};
export default HomeContent;
