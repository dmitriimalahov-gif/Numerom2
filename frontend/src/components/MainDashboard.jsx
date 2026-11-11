import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { ArrowDown, ArrowUpRight, BookOpen, Check, ChevronRight, Compass, Heart, Grid3X3, FileText } from 'lucide-react';
import { Button } from './ui/button';
import { useAuth } from './AuthContext';
import AuthModal from './AuthModal';
import { Brand } from './NumeromIdentity';
import NumerologyIllustrations, { Illustration } from './NumerologyIllustrations';

const features = [
  { icon: FileText, tone: 'green', title: 'Полный разбор · 6,66 €', text: 'Расчёты по дате рождения, объяснения, схемы и персональная озвучка в одном отчёте. Отдельная разовая оплата.', action: 'Открыть полный разбор' },
  { icon: Grid3X3, tone: 'blue', title: 'Ваша карта чисел', text: 'Персональные числа, квадрат Пифагора и нумерология имени в одном пространстве.', action: 'Перейти к расчётам' },
  { icon: Heart, tone: 'rose', title: 'Лучше понимать друг друга', text: 'Исследуйте совместимость по датам рождения и особенности ваших отношений.', action: 'Изучить совместимость' },
  { icon: Compass, tone: 'green', title: 'Ритм вашего дня', text: 'Планетарные маршруты, ведические времена и графики энергий для вашей практики.', action: 'Посмотреть инструменты' },
];

const plans = [
  { name: 'Стартовый', price: '0,99', credits: '10 кредитов', description: 'Познакомиться с расчётами', items: ['Персональные числа', 'Квадрат Пифагора', 'Отчёты', 'Месяц доступа'] },
  { name: 'Базовый', price: '9,99', credits: '150 кредитов', description: 'Для регулярной практики', items: ['Все расчёты', 'Графики энергий', 'Совместимость', 'Месяц доступа'], featured: true },
  { name: 'Профессиональный', price: '66,60', credits: '1 000 кредитов', description: 'Для глубокого изучения', items: ['Все расчёты', 'Групповая совместимость', 'Методические материалы', 'Год доступа'] },
];

const MainDashboard = () => {
  const { user, loading, isInitialized } = useAuth();
  const [authMode, setAuthMode] = useState('login');
  const [showAuthModal, setShowAuthModal] = useState(false);
  useEffect(() => { document.documentElement.classList.remove('dark'); }, []);

  const openAuth = (mode = 'register') => {
    setAuthMode(mode);
    setShowAuthModal(true);
  };
  if (loading && !isInitialized && !user) {
    return <div className="nm-loading" role="status"><Brand /><span>Открываем NumerOM…</span></div>;
  }
  if (user) return <Navigate to="/dashboard" replace />;

  return (
    <div className="nm-landing">
      <a className="nm-skip-link" href="#main-content">Перейти к содержимому</a>
      <header className="nm-site-header">
        <div className="nm-container nm-header-inner">
          <a href="#" aria-label="NumerOM — главная"><Brand /></a>
          <nav className="nm-site-nav" aria-label="Основная навигация">
            <a href="#possibilities">Возможности</a><a href="#learning">Обучение</a><a href="#plans">Тарифы</a>
          </nav>
          <Button variant="outline" onClick={() => openAuth('login')}>Войти в кабинет <ArrowUpRight aria-hidden="true" /></Button>
        </div>
      </header>
      <main id="main-content">
        <section className="nm-container nm-hero">
          <div className="nm-hero-copy">
            <span className="nm-topic"><span /> Пространство самопознания</span>
            <h1>У каждого числа<br />есть своя история.<br />Откройте вашу.</h1>
            <p>Знакомьтесь с собой через нумерологию. Персональные расчёты, обучение и осознанная практика — в вашем ритме.</p>
            <div className="nm-hero-actions">
              <Button size="lg" onClick={() => openAuth()}>Создать свою карту <ArrowUpRight aria-hidden="true" /></Button>
              <a href="#possibilities" className="nm-text-link">Как это работает <ArrowDown size={16} aria-hidden="true" /></a>
            </div>
            <div className="nm-hero-note"><Grid3X3 size={16} aria-hidden="true" /><span>Начните с вашей даты рождения</span></div>
          </div>
          <div className="nm-hero-visual">
            <div className="nm-hero-matrix"><div className="nm-matrix-label">В основе — ваша уникальность</div><Illustration name="KVADRAT" alt="Квадрат NumerOM: числа от 1 до 9" loading="eager" /><div className="nm-matrix-footer"><span>Дата рождения</span><span>Характер</span><span>Потенциал</span></div></div>
            <div className="nm-orbit-caption"><span className="nm-small-star" aria-hidden="true">✳</span><div><strong>Разные грани одного «я»</strong><span>Девять чисел. Пространство для открытий.</span></div></div>
          </div>
        </section>
        <div className="nm-container nm-intro-line"><span>Знакомьтесь с собой</span><span>Замечайте взаимосвязи</span><span>Учитесь новому</span></div>
        <section id="possibilities" className="nm-container nm-section">
          <div className="nm-section-heading"><div><span className="nm-section-label">Возможности NumerOM</span><h2>Больше способов<br />узнать себя</h2></div><p>От первого расчёта до собственной практики.<br />Выберите то, что интересно вам сейчас.</p></div>
          <div className="nm-feature-grid">
            {features.map(({ icon: Icon, tone, title, text, action }) => (
              <article className={`nm-feature nm-tone-${tone}`} key={title}>
                <span className="nm-feature-icon"><Icon size={25} strokeWidth={1.5} aria-hidden="true" /></span>
                <h3>{title}</h3><p>{text}</p>
                <button className="nm-text-link" onClick={() => openAuth()}>{action}<ArrowUpRight size={17} aria-hidden="true" /></button>
              </article>
            ))}
          </div>
        </section>
        <section id="learning" className="nm-container nm-learning-section">
          <div className="nm-learning-art" aria-hidden="true"><Illustration name="SU" alt="" /><span className="nm-art-note">Пример учебной схемы NumerOM</span></div>
          <div className="nm-learning-copy"><span className="nm-section-label"><BookOpen size={16} aria-hidden="true" /> Обучение и практика</span><h2>Знания, к которым<br />хочется возвращаться</h2><p>Изучайте нумерологию последовательно: теория, примеры, задания и тесты. Сохраняйте материалы и возвращайтесь к ним в удобное время.</p><Button onClick={() => openAuth()}>Открыть обучение <ChevronRight aria-hidden="true" /></Button></div>
        </section>
        <div className="nm-container nm-section"><NumerologyIllustrations embedded /></div>
        <section className="nm-container nm-section nm-start-section" aria-labelledby="start-title">
          <div><span className="nm-section-label">Просто начать</span><h2 id="start-title">Ваш первый шаг<br />к новым открытиям</h2></div>
          <ol className="nm-steps">
            <li><span>1</span><div><h3>Создайте профиль</h3><p>Укажите имя и дату рождения для персональных расчётов.</p></div></li>
            <li><span>2</span><div><h3>Исследуйте свою карту</h3><p>Познакомьтесь с числами и их нумерологическими трактовками.</p></div></li>
            <li><span>3</span><div><h3>Продолжайте в своём темпе</h3><p>Выбирайте уроки, инструменты и консультации по вашим интересам.</p></div></li>
          </ol>
        </section>
        <section id="plans" className="nm-plans-section">
          <div className="nm-container nm-section">
            <div className="nm-section-heading"><div><span className="nm-section-label">Доступ к платформе</span><h2>Выберите свой ритм</h2></div><p>Кредиты используются для расчётов.<br />Баланс и история всегда доступны в кабинете.</p></div>
            <div className="nm-plans-grid">{plans.map(plan => <article key={plan.name} className={`nm-plan ${plan.featured ? 'nm-plan-featured' : ''}`}>
              <div className="nm-plan-title"><h3>{plan.name}</h3>{plan.featured && <span>Для практики</span>}</div><p>{plan.description}</p>
              <div className="nm-price">{plan.price}<span>€</span></div><span className="nm-credits-label">{plan.credits}</span>
              <ul>{plan.items.map(item => <li key={item}><Check size={16} aria-hidden="true" />{item}</li>)}</ul>
              <Button variant={plan.featured ? 'default' : 'outline'} onClick={() => openAuth()} className="w-full">Начать с этого пакета</Button>
            </article>)}</div>
          </div>
        </section>
      </main>
      <footer className="nm-container nm-footer"><Brand /><p>Нумерология для самопознания и личной практики.</p><span>© {new Date().getFullYear()} NumerOM</span></footer>
      <AuthModal initialMode={authMode} isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />
    </div>
  );
};
export default MainDashboard;
