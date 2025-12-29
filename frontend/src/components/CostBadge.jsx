import React from 'react';
import { Badge } from './ui/badge';
import { Coins } from 'lucide-react';

/**
 * Компонент для отображения стоимости в баллах
 * @param {number} cost - Стоимость в баллах
 * @param {number} balance - Текущий баланс пользователя (опционально)
 * @param {string} variant - Вариант отображения: 'inline', 'prominent', 'default'
 */
const CostBadge = ({ cost, balance, variant = 'default' }) => {
  const hasEnough = balance !== undefined ? balance >= cost : true;

  // Inline вариант - компактный, для использования внутри текста
  if (variant === 'inline') {
    return (
      <span className={`inline-flex items-center ${hasEnough ? 'text-green-400' : 'text-red-400'}`}>
        <Coins className="w-3 h-3 mr-1" />
        {cost} б.
      </span>
    );
  }

  // Prominent вариант - большой и заметный
  if (variant === 'prominent') {
    return (
      <div className={`flex items-center justify-center gap-2 p-3 rounded-xl border-2 ${
        hasEnough 
          ? 'bg-green-500/20 border-green-500/40 text-green-400' 
          : 'bg-red-500/20 border-red-500/40 text-red-400'
      }`}>
        <Coins className="w-5 h-5" />
        <span className="text-lg font-semibold">
          Стоимость: {cost} баллов
        </span>
        {balance !== undefined && (
          <span className="text-sm opacity-75">
            (баланс: {balance})
          </span>
        )}
      </div>
    );
  }

  // Default вариант - обычный Badge
  return (
    <Badge 
      variant="secondary" 
      className={`${
        hasEnough 
          ? 'bg-green-500/20 text-green-400 border-green-500/40' 
          : 'bg-red-500/20 text-red-400 border-red-500/40'
      }`}
    >
      <Coins className="w-3 h-3 mr-1" />
      {cost} баллов
      {balance !== undefined && ` (баланс: ${balance})`}
    </Badge>
  );
};

export default CostBadge;

