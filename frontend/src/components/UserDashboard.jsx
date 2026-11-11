import React, { useState, useEffect } from 'react';
import { Link, NavLink, useNavigate, useLocation, Outlet } from 'react-router-dom';
import { Button } from './ui/button';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from './ui/sheet';
import { LayoutDashboard, Calculator, Heart, HelpCircle, BarChart3, BookOpen, FileText, Settings, Grid3X3, Clock, MapPin, LogOut, Wallet, Menu, UserRound, Video, ChevronRight, Plus } from 'lucide-react';
import { useAuth } from './AuthContext';
import PaymentModal from './PaymentModal';
import { getBackendUrl } from '../utils/backendUrl';
import { Brand } from './NumeromIdentity';

const navigationGroups = [
  { label: 'Моё пространство', items: [
    { id: 'home', label: 'Обзор', icon: LayoutDashboard },
    { id: 'personal-data', label: 'Мой профиль', icon: UserRound },
  ] },
  { label: 'Исследовать себя', items: [
    { id: 'numerology-design', label: 'Карта чисел', icon: Calculator },
    { id: 'full-report', label: 'Полный разбор · 6,66 €', icon: FileText },
    { id: 'name-numerology', label: 'Нумерология имени', icon: UserRound },
    { id: 'compatibility', label: 'Совместимость', icon: Heart },
    { id: 'vedic-time', label: 'Ведические времена', icon: Clock },
    { id: 'planetary-route', label: 'Планетарный маршрут', icon: MapPin },
    { id: 'quiz', label: 'Тест личности', icon: HelpCircle },
  ] },
  { label: 'Знания и практика', items: [
    { id: 'learning-v2', label: 'Обучение', icon: BookOpen },
    { id: 'materials', label: 'Библиотека материалов', icon: FileText },
    { id: 'visual-guide', label: 'Схемы и примеры', icon: Grid3X3 },
    { id: 'consultations', label: 'Мои консультации', icon: Video },
    { id: 'comprehensive-report', label: 'Комплексный отчёт', icon: BarChart3 },
    { id: 'report-export', label: 'Скачать отчёты', icon: FileText },
  ] },
  { label: 'Аккаунт', items: [
    { id: 'credit-history', label: 'История баллов', icon: Wallet },
    { id: 'settings', label: 'Настройки', icon: Settings },
  ] },
];

const UserDashboard = () => {
  const { user, logout, loading, isAuthenticated, isInitialized } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [paymentOpen, setPaymentOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [hasNewConsultations, setHasNewConsultations] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light');

  useEffect(() => {
    localStorage.setItem('theme', theme);
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  useEffect(() => {
    if (isInitialized && !isAuthenticated) navigate('/', { replace: true });
  }, [isInitialized, isAuthenticated, navigate]);

  useEffect(() => { setMenuOpen(false); }, [location.pathname]);

  // Проверка наличия новых консультаций
  useEffect(() => {
    if (!isAuthenticated || !user) return;

    const checkNewConsultations = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;

        const backendUrl = getBackendUrl();
        const response = await fetch(`${backendUrl}/api/user/consultations`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const consultations = await response.json();
          // Проверяем, есть ли консультации, которые были обновлены за последние 7 дней
          const sevenDaysAgo = new Date();
          sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
          
          const hasNew = consultations.some(consultation => {
            if (consultation.updated_at) {
              const updatedDate = new Date(consultation.updated_at);
              return updatedDate > sevenDaysAgo;
            }
            if (consultation.created_at) {
              const createdDate = new Date(consultation.created_at);
              return createdDate > sevenDaysAgo;
            }
            return false;
          });

          setHasNewConsultations(hasNew);
        }
      } catch (error) {
        console.error('Error checking consultations:', error);
      }
    };

    checkNewConsultations();
    // Проверяем каждые 5 минут
    const interval = setInterval(checkNewConsultations, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [isAuthenticated, user]);


  if (loading || !isInitialized) return <div className="nm-loading" role="status"><Brand /><span>Загружаем ваш профиль…</span></div>;
  if (!isAuthenticated || !user) return null;

  const groups = (user.is_super_admin || user.is_admin)
    ? [...navigationGroups, { label: 'Управление', items: [
      { id: 'admin', label: 'Админ-панель', icon: Grid3X3 },
    ] }]
    : navigationGroups;
  const activeSection = location.pathname.split('/')[2] || 'home';
  const activeItem = groups.flatMap(group => group.items).find(item => item.id === activeSection);
  const name = user.full_name || user.name || 'Ваш профиль';
  const initials = name.split(' ').filter(Boolean).slice(0, 2).map(part => part[0]).join('').toUpperCase();

  const renderNavigation = () => <nav className="nm-navigation" aria-label="Разделы кабинета">
    {groups.map(group => <div className="nm-nav-group" key={group.label}>
      <p>{group.label}</p>
      {group.items.map(({ id, label, icon: Icon }) => <NavLink key={id} to={`/dashboard/${id}`} className={({ isActive }) => `nm-nav-item ${isActive ? 'is-active' : ''}`} onClick={() => { setMenuOpen(false); if (id === 'consultations') setHasNewConsultations(false); }}>
        <Icon size={18} strokeWidth={1.7} aria-hidden="true" /><span>{label}</span>
        {id === 'consultations' && hasNewConsultations && <span className="nm-unread-dot" aria-label="Есть новые консультации" />}
      </NavLink>)}
    </div>)}
  </nav>;

  const profile = <div className="nm-sidebar-profile"><Link to="/dashboard/personal-data" className="nm-profile-link" onClick={() => setMenuOpen(false)}><span className="nm-avatar">{initials}</span><span><strong>{name}</strong><small>{user.is_premium ? 'Premium' : 'Личный кабинет'}</small></span></Link><button className="nm-icon-button" onClick={logout} aria-label="Выйти из аккаунта" title="Выйти"><LogOut size={18} /></button></div>;

  return (
    <div className="nm-dashboard">
      <a className="nm-skip-link" href="#dashboard-content">Перейти к содержимому</a>
      <aside className="nm-sidebar"><Link to="/dashboard/home" className="nm-sidebar-brand" aria-label="NumerOM — обзор"><Brand /></Link>{renderNavigation()}{profile}</aside>
      <div className="nm-workspace">
        <header className="nm-workspace-header">
          <div className="nm-breadcrumb">
            <Sheet open={menuOpen} onOpenChange={setMenuOpen}>
              <SheetTrigger asChild><Button className="nm-menu-trigger" variant="ghost" size="icon" aria-label="Открыть меню"><Menu size={21} /></Button></SheetTrigger>
              <SheetContent side="left" className="nm-mobile-sheet">
                <SheetHeader className="sr-only"><SheetTitle>Разделы NumerOM</SheetTitle><SheetDescription>Перейдите к расчётам, обучению или настройкам профиля.</SheetDescription></SheetHeader>
                <Link to="/dashboard/home" className="nm-sidebar-brand" onClick={() => setMenuOpen(false)}><Brand /></Link>{renderNavigation()}{profile}
              </SheetContent>
            </Sheet>
            <span className="nm-breadcrumb-parent">Моё пространство</span><ChevronRight className="nm-breadcrumb-parent" size={15} aria-hidden="true" /><span>{activeItem?.label || 'Обзор'}</span>
          </div>
          <div className="nm-header-actions"><Link to="/dashboard/credit-history" className="nm-balance-link" aria-label={`Баланс: ${user.credits_remaining ?? 'нет данных'}. История баллов`}><Wallet size={17} aria-hidden="true" /><strong>{user.credits_remaining ?? '—'}</strong><span>баллов</span></Link><Button variant="outline" size="sm" onClick={() => setPaymentOpen(true)}><Plus aria-hidden="true" /><span>Пополнить</span></Button></div>
        </header>
        <main id="dashboard-content" className="nm-dashboard-content"><Outlet context={{ theme, setTheme }} /></main>
        <footer className="nm-workspace-footer"><span>NumerOM · Пространство самопознания</span><Link to="/dashboard/settings">Настройки</Link></footer>
      </div>
      <PaymentModal isOpen={paymentOpen} onClose={() => setPaymentOpen(false)} />
    </div>
  );
};
export default UserDashboard;
