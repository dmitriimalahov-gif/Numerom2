import React, { useState } from 'react';
import { Button } from './ui/button';
import { Calculator, TrendingUp, HelpCircle, Calendar, GraduationCap, User } from 'lucide-react';
import VedicNumerologyCalculator from './VedicNumerologyCalculator';
import WeeklyPlanetChart from './WeeklyPlanetChart';
import NumerologyQuiz from './NumerologyQuiz';
import SelfDiscoveryPlatform from './SelfDiscoveryPlatform';

const MainCalculator = () => {
  const [activeTab, setActiveTab] = useState('platform');

  const tabs = [
    { id: 'platform', label: 'Академия самопознания', icon: GraduationCap, component: SelfDiscoveryPlatform },
    { id: 'vedic', label: 'Ведическая нумерология', icon: Calculator, component: VedicNumerologyCalculator },
    { id: 'weekly', label: 'График планет на неделю', icon: TrendingUp, component: WeeklyPlanetChart },
    { id: 'quiz', label: 'Обучающий квиз', icon: HelpCircle, component: NumerologyQuiz }
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component;

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(to bottom right, #F7FEE7, #ECFCCB, #D9F99D)' }}>
      <div className="container mx-auto py-8 px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center items-center gap-4 mb-4">
            <div className="relative">
              <div 
                className="w-16 h-16 rounded-full border-4 flex items-center justify-center bg-white shadow-lg"
                style={{ borderColor: '#32CD32' }}
              >
                <span className="text-2xl font-bold" style={{ color: '#32CD32' }}>N</span>
              </div>
              <div 
                className="absolute -top-1 -right-1 w-6 h-6 rounded-full"
                style={{ backgroundColor: '#228B22' }}
              ></div>
            </div>
            <h1 
              className="text-4xl font-bold"
              style={{ 
                background: 'linear-gradient(to right, #228B22, #32CD32)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}
            >
              NUMEROM
            </h1>
          </div>
          <p className="text-lg" style={{ color: '#228B22' }}>
            Numbers Reveal - Платформа самопознания через ведическую нумерологию
          </p>
        </div>

        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col lg:flex-row gap-6">
            
            {/* Navigation Sidebar */}
            <div className="lg:w-80 space-y-3">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <Button
                    key={tab.id}
                    variant={activeTab === tab.id ? "default" : "outline"}
                    className={`w-full justify-start text-left p-4 h-auto ${
                      activeTab === tab.id 
                        ? 'text-white' 
                        : 'border-lime-300 hover:bg-lime-50 text-lime-800'
                    }`}
                    style={activeTab === tab.id ? {
                      background: 'linear-gradient(to right, #228B22, #32CD32)'
                    } : {}}
                    onClick={() => setActiveTab(tab.id)}
                  >
                    <Icon className="w-5 h-5 mr-3" />
                    <div>
                      <div className="font-semibold text-sm">{tab.label}</div>
                      {tab.id === 'platform' && (
                        <div className="text-xs opacity-80">Пошаговое обучение</div>
                      )}
                      {tab.id === 'vedic' && (
                        <div className="text-xs opacity-80">Основные расчеты</div>
                      )}
                      {tab.id === 'weekly' && (
                        <div className="text-xs opacity-80">Планетные циклы</div>
                      )}
                      {tab.id === 'quiz' && (
                        <div className="text-xs opacity-80">Проверка знаний</div>
                      )}
                    </div>
                  </Button>
                );
              })}
            </div>

            {/* Main Content */}
            <div className="flex-1">
              {ActiveComponent && <ActiveComponent />}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MainCalculator;