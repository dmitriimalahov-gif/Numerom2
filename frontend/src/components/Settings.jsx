import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Moon, Sun, Bell, Calendar, Globe, Lock, User, Database, Smartphone, Mail } from 'lucide-react';
import { Card } from './ui/card';
import { Label } from './ui/label';
import { useTheme } from '../hooks/useTheme';

const Settings = () => {
  const { theme, setTheme } = useOutletContext();
  const themeConfig = useTheme(theme);
  const [notifications, setNotifications] = useState(false);
  const [calendarSync, setCalendarSync] = useState(false);
  const [language, setLanguage] = useState('ru');
  const [privacy, setPrivacy] = useState('standard');
  const [profile, setProfile] = useState('public');
  const [dataBackup, setDataBackup] = useState(false);
  const [deviceSync, setDeviceSync] = useState(false);
  const [emailNotifications, setEmailNotifications] = useState(false);

  const SettingItem = ({ icon: Icon, title, description, children, badge }) => (
    <div className={`p-6 rounded-xl border ${themeConfig.card} transition-all ${themeConfig.shadowHover}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4 flex-1">
          <div className={`p-3 rounded-lg ${themeConfig.isDark ? 'bg-indigo-500/20' : 'bg-indigo-100'}`}>
            <Icon className={`h-6 w-6 ${themeConfig.accentText}`} />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-1">
              <h3 className={`text-lg font-semibold ${themeConfig.text}`}>{title}</h3>
              {badge && (
                <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${themeConfig.badgeWarning}`}>
                  {badge}
                </span>
              )}
            </div>
            <p className={`text-sm ${themeConfig.mutedText} mb-4`}>{description}</p>
            {children}
          </div>
        </div>
      </div>
    </div>
  );

  const Toggle = ({ checked, onChange, disabled }) => (
    <button
      onClick={() => !disabled && onChange(!checked)}
      disabled={disabled}
      className={`
        relative inline-flex h-6 w-11 items-center rounded-full transition-colors
        ${checked ? themeConfig.toggleActive : themeConfig.toggle}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
    >
      <span
        className={`
          inline-block h-4 w-4 transform rounded-full bg-white transition-transform
          ${checked ? 'translate-x-6' : 'translate-x-1'}
        `}
      />
    </button>
  );

  return (
    <div className={`min-h-screen ${themeConfig.bg} p-6`}>
      <div className="max-w-4xl mx-auto">
        {/* Заголовок */}
        <div className="mb-8">
          <h1 className={`text-3xl font-bold ${themeConfig.text} mb-2`}>Настройки</h1>
          <p className={themeConfig.mutedText}>Управление параметрами приложения и персонализация</p>
        </div>

        <div className="space-y-4">
          {/* Тема приложения */}
          <SettingItem
            icon={theme === 'dark' ? Moon : Sun}
            title="Тема приложения"
            description="Переключение между светлой и тёмной темой оформления"
          >
            <div className="flex items-center gap-4">
              <button
                onClick={() => setTheme('light')}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-lg border transition-all
                  ${theme === 'light' 
                    ? `${themeConfig.accent} text-white border-transparent` 
                    : `${themeConfig.card} ${themeConfig.text}`
                  }
                `}
              >
                <Sun className="h-4 w-4" />
                <span>Светлая</span>
              </button>
              <button
                onClick={() => setTheme('dark')}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-lg border transition-all
                  ${theme === 'dark' 
                    ? `${themeConfig.accent} text-white border-transparent` 
                    : `${themeConfig.card} ${themeConfig.text}`
                  }
                `}
              >
                <Moon className="h-4 w-4" />
                <span>Тёмная</span>
              </button>
            </div>
          </SettingItem>

          {/* Push-уведомления */}
          <SettingItem
            icon={Bell}
            title="Push-уведомления"
            description="Получайте уведомления о важных астрологических событиях и благоприятных часах"
            badge="Скоро"
          >
            <div className="flex items-center justify-between">
              <Label className={themeConfig.mutedText}>Включить уведомления</Label>
              <Toggle checked={notifications} onChange={setNotifications} disabled />
            </div>
          </SettingItem>

          {/* Синхронизация с календарём */}
          <SettingItem
            icon={Calendar}
            title="Синхронизация с календарём"
            description="Автоматически добавляйте благоприятные дни и планетарные часы в ваш календарь"
            badge="Скоро"
          >
            <div className="flex items-center justify-between">
              <Label className={themeConfig.mutedText}>Синхронизировать с Google Calendar</Label>
              <Toggle checked={calendarSync} onChange={setCalendarSync} disabled />
            </div>
          </SettingItem>

          {/* Язык интерфейса */}
          <SettingItem
            icon={Globe}
            title="Язык интерфейса"
            description="Выберите предпочитаемый язык для отображения интерфейса"
            badge="Скоро"
          >
            <div className="flex items-center gap-3">
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                disabled
                className={`
                  px-4 py-2 rounded-lg border ${themeConfig.input}
                  opacity-50 cursor-not-allowed
                `}
              >
                <option value="ru">Русский</option>
                <option value="en">English</option>
                <option value="hi">हिन्दी (Hindi)</option>
              </select>
            </div>
          </SettingItem>

          {/* Конфиденциальность */}
          <SettingItem
            icon={Lock}
            title="Конфиденциальность"
            description="Управление настройками приватности и безопасности ваших данных"
            badge="Скоро"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className={themeConfig.mutedText}>Уровень конфиденциальности</Label>
                <select
                  value={privacy}
                  onChange={(e) => setPrivacy(e.target.value)}
                  disabled
                  className={`
                    px-3 py-1.5 rounded-lg border ${themeConfig.input} text-sm
                    opacity-50 cursor-not-allowed
                  `}
                >
                  <option value="public">Публичный</option>
                  <option value="standard">Стандартный</option>
                  <option value="private">Приватный</option>
                </select>
              </div>
            </div>
          </SettingItem>

          {/* Профиль пользователя */}
          <SettingItem
            icon={User}
            title="Настройки профиля"
            description="Управление видимостью профиля и персональной информацией"
            badge="Скоро"
          >
            <div className="flex items-center justify-between">
              <Label className={themeConfig.mutedText}>Публичный профиль</Label>
              <Toggle 
                checked={profile === 'public'} 
                onChange={(val) => setProfile(val ? 'public' : 'private')} 
                disabled 
              />
            </div>
          </SettingItem>

          {/* Резервное копирование */}
          <SettingItem
            icon={Database}
            title="Резервное копирование данных"
            description="Автоматическое сохранение ваших расчётов и настроек в облако"
            badge="Скоро"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className={themeConfig.mutedText}>Автоматическое резервное копирование</Label>
                <Toggle checked={dataBackup} onChange={setDataBackup} disabled />
              </div>
              <button
                disabled
                className={`
                  px-4 py-2 rounded-lg border ${themeConfig.card} ${themeConfig.text}
                  opacity-50 cursor-not-allowed text-sm
                `}
              >
                Создать резервную копию сейчас
              </button>
            </div>
          </SettingItem>

          {/* Синхронизация между устройствами */}
          <SettingItem
            icon={Smartphone}
            title="Синхронизация между устройствами"
            description="Синхронизируйте настройки и данные между всеми вашими устройствами"
            badge="Скоро"
          >
            <div className="flex items-center justify-between">
              <Label className={themeConfig.mutedText}>Синхронизация включена</Label>
              <Toggle checked={deviceSync} onChange={setDeviceSync} disabled />
            </div>
          </SettingItem>

          {/* Email-уведомления */}
          <SettingItem
            icon={Mail}
            title="Email-уведомления"
            description="Получайте еженедельные отчёты и важные обновления на почту"
            badge="Скоро"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className={themeConfig.mutedText}>Еженедельный отчёт</Label>
                <Toggle checked={emailNotifications} onChange={setEmailNotifications} disabled />
              </div>
              <div className="flex items-center justify-between">
                <Label className={themeConfig.mutedText}>Важные обновления</Label>
                <Toggle checked={false} onChange={() => {}} disabled />
              </div>
            </div>
          </SettingItem>
        </div>

        {/* Информация о версии */}
        <div className={`mt-8 p-4 rounded-lg border ${themeConfig.card} text-center`}>
          <p className={`text-sm ${themeConfig.mutedText}`}>
            Версия приложения: <span className="font-semibold">1.0.0</span>
          </p>
          <p className={`text-xs ${themeConfig.mutedText} mt-1`}>
            © 2025 NumerOM. Все права защищены.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Settings;

