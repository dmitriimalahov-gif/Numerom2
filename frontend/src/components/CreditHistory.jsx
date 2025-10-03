import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import {
  History,
  TrendingDown,
  TrendingUp,
  Calculator,
  Clock,
  MapPin,
  Heart,
  HelpCircle,
  BookOpen,
  Video,
  FileText,
  Users,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ExternalLink
} from 'lucide-react';
import { useAuth } from './AuthContext';
import axios from 'axios';

const CreditHistory = ({ onNavigate }) => {
  const { user } = useAuth();
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [page, setPage] = useState(0);
  const [totalTransactions, setTotalTransactions] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
  const limit = 20;

  const categoryIcons = {
    'numerology': <Calculator className="w-4 h-4" />,
    'vedic': <Clock className="w-4 h-4" />,
    'learning': <Video className="w-4 h-4" />,
    'quiz': <HelpCircle className="w-4 h-4" />,
    'materials': <FileText className="w-4 h-4" />,
    'purchase': <TrendingUp className="w-4 h-4" />,
    'refund': <RefreshCw className="w-4 h-4" />
  };

  const categoryColors = {
    'numerology': 'bg-blue-100 text-blue-800',
    'vedic': 'bg-purple-100 text-purple-800',
    'learning': 'bg-green-100 text-green-800',
    'quiz': 'bg-orange-100 text-orange-800',
    'materials': 'bg-cyan-100 text-cyan-800',
    'purchase': 'bg-emerald-100 text-emerald-800',
    'refund': 'bg-yellow-100 text-yellow-800'
  };

  useEffect(() => {
    loadTransactions();
  }, [page]);

  const loadTransactions = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await axios.get(
        `${backendUrl}/api/user/credit-history?limit=${limit}&offset=${page * limit}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      const newTransactions = response.data.transactions;
      setTotalTransactions(response.data.total);
      
      if (page === 0) {
        setTransactions(newTransactions);
      } else {
        setTransactions(prev => [...prev, ...newTransactions]);
      }
      
      setHasMore(newTransactions.length === limit);
    } catch (error) {
      console.error('Error loading credit history:', error);
      setError(error.response?.data?.detail || 'Ошибка при загрузке истории транзакций');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getAmountDisplay = (transaction) => {
    const isCredit = transaction.transaction_type === 'credit';
    const amount = Math.abs(transaction.amount);
    return {
      sign: isCredit ? '+' : '-',
      color: isCredit ? 'text-green-600' : 'text-red-600',
      amount: amount
    };
  };

  const loadMore = () => {
    if (!loading && hasMore) {
      setPage(prev => prev + 1);
    }
  };

  const refresh = () => {
    setPage(0);
    loadTransactions();
  };

  // Маппинг типов расчетов на секции навигации
  const calculationTypeToSection = {
    'personal_numbers': 'numerology',
    'pythagorean_square': 'square',
    'numerology': 'numerology', // общая категория нумерологии
    'vedic': 'vedic-time',
    'compatibility': 'compatibility',
    'quiz': 'quiz',
    'learning': 'learning'
  };

  const handleTransactionClick = (transaction) => {
    // Проверяем, есть ли тип расчета в деталях транзакции
    const calculationType = transaction.details?.calculation_type || transaction.category;
    const section = calculationTypeToSection[calculationType];

    if (section && onNavigate) {
      onNavigate(section);
    }
  };

  if (loading && transactions.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 mx-auto mb-4 animate-spin" />
          <p>Загрузка истории транзакций...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <History className="w-6 h-6 text-blue-600" />
              <div>
                <CardTitle>История баллов</CardTitle>
                <CardDescription>
                  Вся история начисления и списания баллов
                </CardDescription>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={refresh} disabled={loading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Обновить
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert className="mb-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {transactions.length === 0 && !loading ? (
            <div className="text-center py-8">
              <History className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p className="text-gray-500">История транзакций пуста</p>
            </div>
          ) : (
            <div className="space-y-3">
              {/* Сводка */}
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Всего транзакций:</span>
                  <span className="font-medium">{totalTransactions}</span>
                </div>
                <div className="flex items-center justify-between text-sm mt-2">
                  <span className="text-gray-600">Текущий баланс:</span>
                  <span className="font-medium text-blue-600">{user?.credits_remaining || 0} баллов</span>
                </div>
              </div>

              {/* Список транзакций */}
              {transactions.map((transaction) => {
                const amountInfo = getAmountDisplay(transaction);
                const categoryIcon = categoryIcons[transaction.category] || <Calculator className="w-4 h-4" />;
                const categoryColor = categoryColors[transaction.category] || 'bg-gray-100 text-gray-800';
                const calculationType = transaction.details?.calculation_type || transaction.category;
                const isClickable = calculationTypeToSection[calculationType];

                return (
                  <div
                    key={transaction.id}
                    className={`flex items-center justify-between p-4 border rounded-lg transition-colors ${
                      isClickable ? 'hover:bg-blue-50 hover:border-blue-300 cursor-pointer' : 'hover:bg-gray-50'
                    }`}
                    onClick={() => isClickable && handleTransactionClick(transaction)}
                  >
                    <div className="flex items-center space-x-4">
                      <div className={`p-2 rounded-full ${categoryColor}`}>
                        {categoryIcon}
                      </div>
                      <div>
                        <h4 className="font-medium text-sm">{transaction.description}</h4>
                        <div className="flex items-center space-x-2 mt-1">
                          <Badge variant="secondary" className="text-xs">
                            {transaction.category}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            {formatDate(transaction.created_at)}
                          </span>
                        </div>
                        {transaction.details && Object.keys(transaction.details).length > 0 && (
                          <div className="text-xs text-gray-500 mt-1">
                            {transaction.details.lesson_title && (
                              <span>Урок: {transaction.details.lesson_title}</span>
                            )}
                            {transaction.details.material_title && (
                              <span>Материал: {transaction.details.material_title}</span>
                            )}
                            {transaction.details.calculation_type && (
                              <span>Тип: {transaction.details.calculation_type}</span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className={`font-bold text-lg ${amountInfo.color}`}>
                        {amountInfo.sign}{amountInfo.amount}
                      </div>
                      {isClickable && (
                        <ExternalLink className="w-4 h-4 text-blue-500" />
                      )}
                    </div>
                  </div>
                );
              })}

              {/* Кнопка "Загрузить еще" */}
              {hasMore && (
                <div className="text-center pt-4">
                  <Button 
                    variant="outline" 
                    onClick={loadMore} 
                    disabled={loading}
                    className="w-full"
                  >
                    {loading ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Загрузка...
                      </>
                    ) : (
                      <>
                        <ChevronDown className="w-4 h-4 mr-2" />
                        Загрузить еще
                      </>
                    )}
                  </Button>
                </div>
              )}

              {!hasMore && transactions.length > limit && (
                <div className="text-center pt-4 text-sm text-gray-500">
                  Показаны все транзакции
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default CreditHistory;