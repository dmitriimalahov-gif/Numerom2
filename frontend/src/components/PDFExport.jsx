import React, { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { useAuth } from './AuthContext';
import { FileText, Download, AlertCircle } from 'lucide-react';
import { getBackendUrl } from '../utils/backendUrl';

const PDFExport = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { user } = useAuth();

  const generatePDF = async (includeVedic = true, includeCharts = true, includeCompatibility = false, partnerBirthDate = null) => {
    if (!user) return;

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${getBackendUrl()}/api/reports/pdf/numerology`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          include_vedic: includeVedic,
          include_charts: includeCharts,
          include_compatibility: includeCompatibility,
          partner_birth_date: partnerBirthDate
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка генерации PDF');
      }

      // Скачиваем файл
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `numerom_report_${user.id}_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardContent className="p-6">
          <p className="text-center text-gray-600">
            Войдите в аккаунт для экспорта отчетов в PDF
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Заголовок */}
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl text-center flex items-center justify-center gap-2">
            <FileText className="w-6 h-6" />
            PDF Экспорт отчетов
          </CardTitle>
          <CardDescription className="text-center">
            Скачайте полные отчеты с вашими нумерологическими расчетами
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Кредиты */}
      {!user.is_premium && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-amber-700 bg-amber-50 p-3 rounded-lg">
              <AlertCircle className="w-5 h-5" />
              <div className="text-sm">
                <strong>Осталось кредитов: {user.credits_remaining || 0}</strong>
                <p>Экспорт PDF также требует 1 кредит</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Ошибка */}
      {error && (
        <Card>
          <CardContent className="p-4">
            <div className="text-red-600 text-center">
              <AlertCircle className="w-6 h-6 mx-auto mb-2" />
              <p>{error}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Варианты PDF */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Полный отчет */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">📋 Полный нумерологический отчет</CardTitle>
            <CardDescription>
              Включает все ваши расчеты, квадрат Пифагора, ведическую нумерологию и графики
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 mb-4 text-sm text-gray-600">
              <div>✅ Личные числа (жизненный путь, судьба, душа)</div>
              <div>✅ Улучшенный квадрат Пифагора</div>
              <div>✅ Ведическая нумерология</div>
              <div>✅ Планетарные графики энергий</div>
              <div>✅ Рекомендации и интерпретации</div>
            </div>
            <Button
              onClick={() => generatePDF(true, true, false)}
              disabled={loading || (!user.is_premium && user.credits_remaining <= 0)}
              className="w-full"
            >
              {loading ? (
                <div className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Генерируем PDF...
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Download className="w-4 h-4" />
                  Скачать полный отчет
                </div>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Базовый отчет */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">📄 Базовый отчет</CardTitle>
            <CardDescription>
              Основные нумерологические расчеты без дополнительных графиков
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 mb-4 text-sm text-gray-600">
              <div>✅ Личные числа</div>
              <div>✅ Квадрат Пифагора</div>
              <div>✅ Основные рекомендации</div>
              <div>❌ Ведические расчеты</div>
              <div>❌ Планетарные графики</div>
            </div>
            <Button
              onClick={() => generatePDF(false, false, false)}
              disabled={loading || (!user.is_premium && user.credits_remaining <= 0)}
              variant="outline"
              className="w-full"
            >
              {loading ? (
                <div className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                  Генерируем PDF...
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Download className="w-4 h-4" />
                  Скачать базовый отчет
                </div>
              )}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Информация о PDF */}
      <Card>
        <CardContent className="p-4">
          <div className="text-sm text-gray-600 space-y-2">
            <div><strong>📋 Формат:</strong> PDF с профессиональным дизайном</div>
            <div><strong>📝 Содержание:</strong> Полные расчеты с интерпретациями на русском языке</div>
            <div><strong>🎨 Оформление:</strong> Брендированный дизайн NUMEROM с цветными диаграммами</div>
            <div><strong>📱 Совместимость:</strong> Оптимизирован для просмотра на всех устройствах</div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PDFExport;