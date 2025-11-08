import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Checkbox } from './ui/checkbox';
import { useAuth } from './AuthContext';
import { Globe, Download, Palette, FileText, CheckSquare } from 'lucide-react';
import { getBackendUrl } from '../utils/backendUrl';

const ReportExport = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [theme, setTheme] = useState('default');
  const [includeVedic, setIncludeVedic] = useState(true);
  const [includeCharts, setIncludeCharts] = useState(true);
  const [availableCalculations, setAvailableCalculations] = useState({});
  const [selectedCalculations, setSelectedCalculations] = useState([]);
  const [loadingCalculations, setLoadingCalculations] = useState(true);
  const [previewMode, setPreviewMode] = useState(false);
  const [htmlPreview, setHtmlPreview] = useState('');

  const backendUrl = getBackendUrl();

  // Загрузка доступных расчётов
  useEffect(() => {
    const fetchAvailableCalculations = async () => {
      try {
        const response = await fetch(`${backendUrl}/api/reports/available-calculations`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });

        if (response.ok) {
          const data = await response.json();
          setAvailableCalculations(data.available_calculations);
          
          // По умолчанию выбираем все доступные расчёты
          const defaultSelected = Object.keys(data.available_calculations)
            .filter(key => data.available_calculations[key].available);
          setSelectedCalculations(defaultSelected);
        } else {
          console.error('Failed to fetch available calculations');
        }
      } catch (error) {
        console.error('Error fetching available calculations:', error);
      } finally {
        setLoadingCalculations(false);
      }
    };

    fetchAvailableCalculations();
  }, [backendUrl]);

  const handleCalculationToggle = (calculationId) => {
    setSelectedCalculations(prev => {
      if (prev.includes(calculationId)) {
        return prev.filter(id => id !== calculationId);
      } else {
        return [...prev, calculationId];
      }
    });
  };

  const openHtmlReport = async (mode = 'open') => {
    if (!user) return;
    setLoading(true);
    setError('');

    try {
      const res = await fetch(`${backendUrl}/api/reports/html/numerology`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          selected_calculations: selectedCalculations,
          // Для совместимости со старой системой
          include_vedic: includeVedic,
          include_charts: includeCharts,
          include_compatibility: false,
          partner_birth_date: null,
          theme
        })
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        console.error('Report generation error:', res.status, err);
        
        if (res.status === 402) {
          throw new Error('Недостаточно кредитов для генерации отчёта');
        } else if (res.status === 404) {
          throw new Error('Пользователь не найден');
        } else if (res.status === 500) {
          throw new Error('Внутренняя ошибка сервера при генерации отчёта');
        } else {
          throw new Error(err.detail || `Ошибка генерации HTML отчёта (код: ${res.status})`);
        }
      }

      const htmlText = await res.text();
      
      if (mode === 'open') {
        // Создаём новую страницу с HTML контентом напрямую
        const newWindow = window.open('', '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');
        if (newWindow) {
          newWindow.document.open();
          newWindow.document.write(htmlText);
          newWindow.document.close();
          newWindow.document.title = `NUMEROM - Отчёт для ${user.full_name || user.email}`;
        } else {
          // Fallback: скачивание файла если popup заблокирован
          console.warn('Popup заблокирован, переключаемся на скачивание');
          const blob = new Blob([htmlText], { type: 'text/html;charset=utf-8' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `numerom_report_${user.id}_${new Date().toISOString().split('T')[0]}.html`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          setTimeout(() => URL.revokeObjectURL(url), 1000);
        }
      } else {
        const blob = new Blob([htmlText], { type: 'text/html;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `numerom_report_${user.id}_${new Date().toISOString().split('T')[0]}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // Новая функция для встроенного просмотра HTML
  const previewHTML = async () => {
    setLoading(true);
    setError('');
    
    try {
      if (selectedCalculations.length === 0) {
        throw new Error('Выберите хотя бы один тип расчёта');
      }

      const res = await fetch(`${backendUrl}/api/reports/html/numerology`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          selected_calculations: selectedCalculations,
          include_vedic: includeVedic,
          include_charts: includeCharts,
          include_compatibility: false,
          partner_birth_date: null,
          theme
        })
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        console.error('Report generation error:', res.status, err);
        
        if (res.status === 402) {
          throw new Error('Недостаточно кредитов для генерации отчёта');
        } else if (res.status === 404) {
          throw new Error('Пользователь не найден');
        } else if (res.status === 500) {
          throw new Error('Внутренняя ошибка сервера при генерации отчёта');
        } else {
          throw new Error(err.detail || `Ошибка генерации HTML отчёта (код: ${res.status})`);
        }
      }

      const htmlText = await res.text();
      console.log('Получен HTML размером:', htmlText.length, 'символов');
      console.log('Первые 500 символов HTML:', htmlText.substring(0, 500));
      
      // Проверяем что HTML содержит основные данные
      if (htmlText.includes('DOCTYPE html') && htmlText.includes('NUMEROM')) {
        setHtmlPreview(htmlText);
        setPreviewMode(true);
        console.log('HTML отчёт загружен для просмотра');
      } else {
        throw new Error('Полученный HTML не содержит ожидаемых данных');
      }
      
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <Card className="w-full max-w-3xl mx-auto">
        <CardContent className="p-6 text-center text-muted-foreground">
          Войдите в аккаунт для экспорта отчётов
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="w-full max-w-3xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl flex items-center gap-2">
            <Globe className="w-6 h-6" />
            HTML Отчёт
          </CardTitle>
          <CardDescription>Сгенерируйте красивый HTML-отчёт в фирменной пастельной теме</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Выбор темы */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Тема отчёта</label>
            <div className="flex items-center gap-2">
              <Palette className="w-4 h-4 text-muted-foreground" />
              <select
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
                className="border rounded-md p-2 w-full max-w-xs"
              >
                <option value="default">Пастельная (по умолчанию)</option>
                <option value="dark">Тёмная</option>
              </select>
            </div>
          </div>

          {/* Выбор расчётов для включения в отчёт */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 mb-3">
              <CheckSquare className="w-5 h-5 text-blue-600" />
              <label className="text-lg font-semibold">Выберите расчёты для включения в отчёт</label>
            </div>
            
            {loadingCalculations ? (
              <div className="text-center py-4">Загрузка доступных расчётов...</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Object.entries(availableCalculations).map(([id, calc]) => (
                  <div
                    key={id}
                    className={`p-3 border rounded-lg ${
                      calc.available ? 'border-gray-200 bg-white' : 'border-gray-100 bg-gray-50'
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      <Checkbox
                        id={id}
                        checked={selectedCalculations.includes(id)}
                        onCheckedChange={() => handleCalculationToggle(id)}
                        disabled={!calc.available}
                      />
                      <div className="flex-1 min-w-0">
                        <label
                          htmlFor={id}
                          className={`text-sm font-medium cursor-pointer ${
                            calc.available ? 'text-gray-900' : 'text-gray-500'
                          }`}
                        >
                          <span className="mr-2">{calc.icon}</span>
                          {calc.name}
                        </label>
                        <p className={`text-xs mt-1 ${
                          calc.available ? 'text-gray-600' : 'text-gray-400'
                        }`}>
                          {calc.description}
                        </p>
                        {!calc.available && (
                          <p className="text-xs text-orange-600 mt-1">
                            Недоступно - заполните соответствующие данные в профиле
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {selectedCalculations.length === 0 && !loadingCalculations && (
              <Alert>
                <AlertDescription>
                  Выберите хотя бы один расчёт для включения в отчёт
                </AlertDescription>
              </Alert>
            )}
          </div>

          {error && (
            <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>
          )}

          <div className="flex flex-col sm:flex-row gap-3">
            <Button
              onClick={previewHTML}
              disabled={loading || selectedCalculations.length === 0 || (!user.is_premium && (user.credits_remaining || 0) <= 0)}
              className="flex-1 bg-blue-600 hover:bg-blue-700"
            >
              {loading ? 'Генерируем…' : (
                <>
                  <Globe className="w-4 h-4 mr-2" />
                  Просмотр отчёта
                </>
              )}
            </Button>
            <Button
              onClick={() => openHtmlReport('open')}
              disabled={loading || selectedCalculations.length === 0 || (!user.is_premium && (user.credits_remaining || 0) <= 0)}
              variant="outline"
              className="flex-1"
            >
              {loading ? 'Генерируем…' : (
                <>
                  <FileText className="w-4 h-4 mr-2" />
                  Новая вкладка
                </>
              )}
            </Button>
            <Button
              onClick={() => openHtmlReport('download')}
              variant="outline"
              disabled={loading || selectedCalculations.length === 0 || (!user.is_premium && (user.credits_remaining || 0) <= 0)}
              className="flex-1"
            >
              <Download className="w-4 h-4 mr-2" />
              Скачать .html
            </Button>
          </div>

          {selectedCalculations.length > 0 && (
            <div className="text-sm text-gray-600 bg-blue-50 p-3 rounded-lg">
              <strong>Выбрано разделов:</strong> {selectedCalculations.length} из {Object.keys(availableCalculations).length}
              <br />
              <strong>Включаемые разделы:</strong> {
                selectedCalculations
                  .map(id => availableCalculations[id]?.name)
                  .filter(Boolean)
                  .join(', ')
              }
            </div>
          )}
        </CardContent>
      </Card>

      {!user.is_premium && (
        <Card>
          <CardContent className="p-4 text-sm text-amber-700 bg-amber-50 rounded-lg">
            Экспорт отчёта списывает 1 кредит у непремиум-пользователей
          </CardContent>
        </Card>
      )}

      {/* Модальное окно встроенного просмотра HTML */}
      {previewMode && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-6xl h-[90vh] flex flex-col">
            <div className="flex justify-between items-center p-4 border-b">
              <h3 className="text-lg font-semibold">Предварительный просмотр отчёта</h3>
              <div className="flex space-x-2">
                <Button
                  onClick={() => {
                    const newWindow = window.open('', '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');
                    if (newWindow) {
                      newWindow.document.open();
                      newWindow.document.write(htmlPreview);
                      newWindow.document.close();
                      newWindow.document.title = `NUMEROM - Отчёт для ${user.full_name || user.email}`;
                    }
                  }}
                  size="sm"
                  variant="outline"
                >
                  <FileText className="w-4 h-4 mr-1" />
                  Открыть в новой вкладке
                </Button>
                <Button
                  onClick={() => {
                    const blob = new Blob([htmlPreview], { type: 'text/html;charset=utf-8' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `numerom_report_${user.id}_${new Date().toISOString().split('T')[0]}.html`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    setTimeout(() => URL.revokeObjectURL(url), 1000);
                  }}
                  size="sm"
                  variant="outline"
                >
                  <Download className="w-4 h-4 mr-1" />
                  Скачать
                </Button>
                <Button
                  onClick={() => {
                    setPreviewMode(false);
                    setHtmlPreview('');
                  }}
                  size="sm"
                  variant="outline"
                >
                  ✕ Закрыть
                </Button>
              </div>
            </div>
            <div className="flex-1 overflow-hidden">
              {htmlPreview && htmlPreview.length > 0 ? (
                <iframe
                  srcDoc={htmlPreview}
                  className="w-full h-full border-0"
                  title="Предварительный просмотр отчёта"
                  sandbox="allow-scripts allow-same-origin"
                  onLoad={() => console.log('Iframe загружен успешно')}
                  onError={(e) => console.error('Ошибка загрузки iframe:', e)}
                />
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <p className="text-gray-500">HTML контент пуст</p>
                    <p className="text-sm text-gray-400">Размер: {htmlPreview.length} символов</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportExport;