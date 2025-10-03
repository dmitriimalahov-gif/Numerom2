import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Menu, Calculator, Hash } from 'lucide-react';
import PersonalNumbers from './PersonalNumbers';
import PythagoreanSquare from './PythagoreanSquare';

const NumerologyDashboard = ({ fullScreen = false, onBack }) => {
  const [activeTab, setActiveTab] = useState('square');

  const FloatingMenu = () => (
    <div className="fixed top-4 left-4 z-50">
      <Button 
        onClick={() => {
          if (onBack) {
            onBack();
          } else {
            // Fallback для совместимости
            window.location.reload();
          }
        }}
        className="bg-white/90 backdrop-blur-sm text-gray-700 hover:bg-white shadow-lg border"
      >
        <Menu className="w-4 h-4 mr-2" />
        Назад
      </Button>
    </div>
  );

  const TabNavigation = () => (
    <div className="flex gap-2 mb-6">
      <Button
        variant={activeTab === 'square' ? 'default' : 'outline'}
        onClick={() => setActiveTab('square')}
        className={`flex-1 ${activeTab === 'square' ? 'numerology-gradient' : ''}`}
      >
        <Hash className="w-4 h-4 mr-2" />
        Квадрат с Энергиями
      </Button>
      <Button
        variant={activeTab === 'personal' ? 'default' : 'outline'}
        onClick={() => setActiveTab('personal')}
        className={`flex-1 ${activeTab === 'personal' ? 'numerology-gradient' : ''}`}
      >
        <Calculator className="w-4 h-4 mr-2" />
        Персональные числа
      </Button>
    </div>
  );

  return (
    <div className={`${fullScreen ? 'min-h-[calc(100vh-4rem)] py-3' : ''}`}>
      {fullScreen && <FloatingMenu />}
      
      <div className="max-w-6xl mx-auto">
        {fullScreen && (
          <Card className="numerology-gradient mb-6">
            <CardHeader className="text-white">
              <CardTitle className="text-3xl text-center">Нумерологический Анализ</CardTitle>
              <p className="text-white/90 text-center">
                Квадрат Пифагора интегрирован с планетарными энергиями для полного анализа
              </p>
            </CardHeader>
          </Card>
        )}

        {fullScreen && <TabNavigation />}

        {activeTab === 'square' && <PythagoreanSquare fullScreen={false} />}
        {activeTab === 'personal' && <PersonalNumbers fullScreen={false} onBack={onBack} />}
      </div>
    </div>
  );
};

export default NumerologyDashboard;