import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Alert, AlertDescription } from './ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import {
  BookOpen,
  Brain,
  Target,
  Calendar,
  BarChart3,
  PlayCircle,
  CheckCircle,
  Lock,
  Star,
  Trophy,
  Clock,
  FileText,
  Video,
  ChevronRight,
  ChevronLeft,
  Home,
  User,
  Calculator,
  Eye,
  Download,
  X,
  ExternalLink,
  Upload,
  Film,
  Maximize2,
  Minimize2,
  Image,
  FileSpreadsheet,
  RotateCw,
  RotateCcw,
  Zap,
  TrendingUp,
  Award,
  Flame,
  CheckCircle2,
  Lightbulb
} from 'lucide-react';
import { useAuth } from './AuthContext';
import { getBackendUrl } from '../utils/backendUrl';

// Компонент для плавного линейного графика попыток теста
const QuizAttemptsLineChart = ({ attempts, maxPossibleScore }) => {
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const [svgRef, setSvgRef] = useState(null);
  
  if (!attempts || attempts.length === 0) return null;
  
  const padding = { top: 30, right: 30, bottom: 70, left: 70 };
  const width = 800;
  const height = 350;
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  
  const maxScore = Math.max(...attempts.map(a => a.score || 0), maxPossibleScore || 100);
  const minScore = 0;
  const yRange = maxScore - minScore;
  
  // Создаем точки для графика
  const points = attempts.map((attempt, index) => {
    const x = (index / (attempts.length - 1 || 1)) * chartWidth + padding.left;
    const y = chartHeight - ((attempt.score || 0) - minScore) / yRange * chartHeight + padding.top;
    return { x, y, ...attempt, index, attemptNumber: index + 1 };
  });
  
  // Создаем плавную кривую
  const createSmoothPath = (points) => {
    if (!points || points.length === 0) return '';
    if (points.length === 1) {
      return `M ${points[0].x} ${points[0].y}`;
    }
    if (points.length === 2) {
      return `M ${points[0].x} ${points[0].y} L ${points[1].x} ${points[1].y}`;
    }
    
    let path = `M ${points[0].x} ${points[0].y}`;
    
    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[Math.max(0, i - 1)];
      const p1 = points[i];
      const p2 = points[i + 1];
      const p3 = points[Math.min(points.length - 1, i + 2)];
      
      const cp1x = p1.x + (p2.x - p0.x) / 6;
      const cp1y = p1.y + (p2.y - p0.y) / 6;
      const cp2x = p2.x - (p3.x - p1.x) / 6;
      const cp2y = p2.y - (p3.y - p1.y) / 6;
      
      path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.x} ${p2.y}`;
    }
    
    return path;
  };
  
  const pathData = createSmoothPath(points);
  // Проверяем, что pathData не пустой и начинается с M перед созданием areaPath
  const areaPath = pathData && pathData.trim().startsWith('M') && points.length > 0
    ? `${pathData} L ${points[points.length - 1].x} ${chartHeight + padding.top} L ${points[0].x} ${chartHeight + padding.top} Z`
    : '';
  
  // Сетка
  const gridLines = [];
  for (let i = 0; i <= 5; i++) {
    const y = padding.top + (chartHeight / 5) * i;
    gridLines.push(
      <line key={`grid-h-${i}`} x1={padding.left} y1={y} x2={width - padding.right} y2={y} stroke="#e5e7eb" strokeWidth="1" strokeDasharray="3 3" />
    );
  }
  
  for (let i = 0; i < points.length; i++) {
    const x = points[i].x;
    gridLines.push(
      <line key={`grid-v-${i}`} x1={x} y1={padding.top} x2={x} y2={chartHeight + padding.top} stroke="#f3f4f6" strokeWidth="1" strokeDasharray="2 2" />
    );
  }
  
  // Подписи оси Y
  const yLabels = [];
  for (let i = 0; i <= 5; i++) {
    const value = Math.round((maxScore / 5) * (5 - i));
    const y = padding.top + (chartHeight / 5) * i;
    yLabels.push(
      <text key={`y-label-${i}`} x={padding.left - 15} y={y + 4} textAnchor="end" className="text-xs fill-gray-600 font-medium">
        {value}
      </text>
    );
  }
  
  return (
    <div className="relative w-full" onMouseLeave={() => setHoveredIndex(null)}>
      <svg ref={setSvgRef} width="100%" height={height} viewBox={`0 0 ${width} ${height}`} className="overflow-visible" preserveAspectRatio="xMidYMid meet">
        {gridLines}
        <line x1={padding.left} y1={padding.top} x2={padding.left} y2={chartHeight + padding.top} stroke="#374151" strokeWidth="2" />
        <line x1={padding.left} y1={chartHeight + padding.top} x2={width - padding.right} y2={chartHeight + padding.top} stroke="#374151" strokeWidth="2" />
        {yLabels}
        
        {/* Область под графиком */}
        <path d={areaPath} fill="url(#gradientQuizArea)" opacity="0.3" />
        <defs>
          <linearGradient id="gradientQuizArea" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#10b981" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#10b981" stopOpacity="0.05" />
          </linearGradient>
        </defs>
        
        {/* Плавная линия */}
        <path d={pathData} fill="none" stroke="#10b981" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="drop-shadow-sm" />
        
        {/* Hover области */}
        {points.map((point, index) => (
          <rect key={`hover-area-${index}`} x={point.x - 20} y={padding.top} width="40" height={chartHeight} fill="transparent" className="cursor-pointer" onMouseEnter={() => setHoveredIndex(index)} />
        ))}
        
        {/* Точки данных */}
        {points.map((point) => (
          <g key={point.index}>
            <circle
              cx={point.x}
              cy={point.y}
              r={hoveredIndex === point.index ? 10 : 6}
              fill={point.passed ? "#10b981" : "#f59e0b"}
              stroke="white"
              strokeWidth={hoveredIndex === point.index ? "3" : "2"}
              className="cursor-pointer transition-all duration-200"
            />
            <text x={point.x} y={height - 20} textAnchor="middle" className="text-xs fill-gray-600 font-medium">
              #{point.attemptNumber}
            </text>
          </g>
        ))}
        
        {hoveredIndex !== null && (
          <line x1={points[hoveredIndex].x} y1={padding.top - 5} x2={points[hoveredIndex].x} y2={chartHeight + padding.top + 5} stroke="#10b981" strokeWidth="2" strokeDasharray="5 5" opacity="0.6" />
        )}
      </svg>
      
      {/* Tooltip */}
      {hoveredIndex !== null && svgRef && (() => {
        const point = points[hoveredIndex];
        const xPercent = (point.x / width);
        const yPercent = (point.y / height);
        
        return (
          <div
            className="absolute bg-gray-900 text-white text-sm rounded-lg px-4 py-3 shadow-2xl z-30 pointer-events-none border border-gray-700"
            style={{
              left: `${xPercent * 100}%`,
              top: `${yPercent * 100}%`,
              transform: 'translate(-50%, calc(-100% - 15px))',
              minWidth: '200px'
            }}
          >
            <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-full">
              <div className="w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
            </div>
            <div className="font-bold text-base mb-2 text-green-300">Попытка #{point.attemptNumber}</div>
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-gray-300">Балл:</span>
                <span className="font-bold text-white text-lg">{point.score} / {maxPossibleScore || 100}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-300">Процент:</span>
                <span className={`font-bold ${point.passed ? 'text-green-400' : 'text-orange-400'}`}>
                  {point.score_percentage || 0}%
                </span>
              </div>
              <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-700">
                <span className="text-gray-300">Статус:</span>
                <span className={`font-semibold ${point.passed ? 'text-green-400' : 'text-orange-400'}`}>
                  {point.passed ? '✅ Пройдено' : '❌ Не пройдено'}
                </span>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
};

// Компонент для плавного линейного графика активности с детализацией
// Принимает дополнительные данные из timeline для объединения в один график
const ActivityLineChart = ({ data, videoTimeline = null, theoryTimeline = null, challengeTimeline = null, quizTimeline = null, exerciseTimeline = null, section = 'lessons' }) => {
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const [svgRef, setSvgRef] = useState(null);
  
  // Объединяем данные из activity_chart и timeline
  const mergedData = useMemo(() => {
    // Создаем карту дат из основного графика
    const dateMap = new Map();
    if (data && data.length > 0) {
      data.forEach((item, index) => {
        // Сохраняем ВСЕ поля из activity_chart, включая theory_activity, video_activity, pdf_activity, lesson_presence
        // Извлекаем только примитивные значения, чтобы избежать попадания объектов в mergedData
        dateMap.set(item.date, { 
          date: item.date || '',
          day_name: item.day_name || '',
          originalIndex: index,
          // Явно сохраняем все поля активности (только примитивные значения)
          theory_activity: typeof item.theory_activity === 'number' ? item.theory_activity : 0,
          lesson_presence: typeof item.lesson_presence === 'number' ? item.lesson_presence : 0,
          video_activity: typeof item.video_activity === 'number' ? item.video_activity : 0,
          pdf_activity: typeof item.pdf_activity === 'number' ? item.pdf_activity : 0,
          activity: typeof item.activity === 'number' ? item.activity : 0,
          efficiency: typeof item.efficiency === 'number' ? item.efficiency : 0,
          study_time_minutes: typeof item.study_time_minutes === 'number' ? item.study_time_minutes : 0,
          file_views: typeof item.file_views === 'number' ? item.file_views : 0
        });
      });
    }
    
    // Объединяем данные из timeline
    const timelines = [
      { data: videoTimeline, key: 'video_minutes', label: 'video_timeline' },
      { data: theoryTimeline, key: 'theory_sessions', label: 'theory_timeline' },
      { data: challengeTimeline, key: 'challenge_updates', label: 'challenge_timeline', additionalKeys: ['completed_challenges'] },
      { data: quizTimeline, key: 'quiz_attempts', label: 'quiz_timeline', additionalKeys: ['passed_quizzes', 'avg_score'] },
      { data: exerciseTimeline, key: 'exercise_submissions', label: 'exercise_timeline', additionalKeys: ['reviewed_exercises', 'total_points'] }
    ];
    
    let maxIndex = data && data.length > 0 ? data.length : 0;
    
    timelines.forEach(timeline => {
      if (timeline.data && timeline.data.length > 0) {
        timeline.data.forEach((item, idx) => {
          // Проверяем, что item - это объект, а не примитив
          if (!item || typeof item !== 'object' || Array.isArray(item)) {
            return; // Пропускаем невалидные элементы
          }
          
          // Преобразуем дату из timeline в формат DD.MM или DD.MM HH:MM
          // Timeline может содержать date (DD.MM или YYYY-MM-DD), time (HH:00), timestamp (ISO), или datetime
          let itemDate = '';
          let itemTime = '';
          
          if (typeof item.date === 'string') {
            itemDate = item.date;
          } else if (typeof item.timestamp === 'string') {
            itemDate = item.timestamp;
          } else if (typeof item.datetime === 'string') {
            itemDate = item.datetime;
          }
          
          if (typeof item.time === 'string') {
            itemTime = item.time;
          } else if (typeof item.hour === 'string') {
            itemTime = item.hour;
          }
          
          let formattedDate = '';
          
          if (itemDate) {
            // Если дата уже в формате DD.MM, используем её как есть
            if (itemDate.match(/^\d{2}\.\d{2}$/)) {
              formattedDate = itemDate;
              // Если есть время, добавляем его
              if (itemTime) {
                formattedDate = `${itemDate} ${itemTime}`;
              }
            }
            // Если дата в формате YYYY-MM-DD, преобразуем в DD.MM
            else if (itemDate.includes('-') && itemDate.length >= 10) {
              const [year, month, day] = itemDate.split('-');
              formattedDate = `${day}.${month}`;
              // Если есть время, добавляем его
              if (itemTime) {
                formattedDate = `${day}.${month} ${itemTime}`;
              }
            } else if (itemDate.includes('T')) {
              // Если дата в формате ISO (YYYY-MM-DDTHH:MM:SS)
              const datePart = itemDate.split('T')[0];
              const [year, month, day] = datePart.split('-');
              formattedDate = `${day}.${month}`;
              // Если есть время в ISO формате, извлекаем его
              const timePart = itemDate.split('T')[1];
              if (timePart) {
                const [hours, minutes] = timePart.split(':');
                formattedDate = `${day}.${month} ${hours}:${minutes}`;
              } else if (itemTime) {
                formattedDate = `${day}.${month} ${itemTime}`;
              }
            } else if (itemDate.includes(':')) {
              // Если это только время (HH:MM), используем текущую дату
              const now = new Date();
              const day = String(now.getDate()).padStart(2, '0');
              const month = String(now.getMonth() + 1).padStart(2, '0');
              formattedDate = `${day}.${month} ${itemDate}`;
            } else {
              formattedDate = itemDate;
              if (itemTime) {
                formattedDate = `${itemDate} ${itemTime}`;
              }
            }
          } else if (itemTime) {
            // Если есть только время, используем текущую дату
            const now = new Date();
            const day = String(now.getDate()).padStart(2, '0');
            const month = String(now.getMonth() + 1).padStart(2, '0');
            formattedDate = `${day}.${month} ${itemTime}`;
          }
          
          if (formattedDate) {
            // Извлекаем значения из timeline
            const timelineValue = typeof item[timeline.key] === 'number' ? item[timeline.key] : 0;
            const timelineEfficiency = typeof item.efficiency === 'number' ? item.efficiency : 0;
            
            // Извлекаем дополнительные ключи, если они есть
            const additionalData = {};
            if (timeline.additionalKeys) {
              timeline.additionalKeys.forEach(additionalKey => {
                const value = item[additionalKey];
                if (typeof value === 'number' || typeof value === 'string' || typeof value === 'boolean') {
                  additionalData[`${timeline.label}_${additionalKey}`] = value;
                }
              });
            }
            
            if (dateMap.has(formattedDate)) {
              const existing = dateMap.get(formattedDate);
              // Добавляем данные из timeline, но НЕ перезаписываем существующие данные из activity_chart
              if (!existing[`${timeline.label}_value`]) {
                existing[`${timeline.label}_value`] = timelineValue;
              }
              if (timelineEfficiency && !existing[`${timeline.label}_efficiency`]) {
                existing[`${timeline.label}_efficiency`] = timelineEfficiency;
              }
              // Добавляем дополнительные данные
              Object.keys(additionalData).forEach(key => {
                if (!existing[key]) {
                  existing[key] = additionalData[key];
                }
              });
            } else {
              // Создаем новую запись для этой даты
              dateMap.set(formattedDate, {
                date: formattedDate,
                day_name: item.time || item.hour || '',
                [`${timeline.label}_value`]: timelineValue,
                [`${timeline.label}_efficiency`]: timelineEfficiency,
                ...additionalData,
                activity: 0,
                theory_activity: 0,
                lesson_presence: 0,
                video_activity: 0,
                pdf_activity: 0,
                efficiency: timelineEfficiency,
                originalIndex: maxIndex + idx
              });
              maxIndex++;
            }
          }
        });
      }
    });
    
    // Если нет данных вообще, возвращаем пустой массив
    if (dateMap.size === 0) return [];
    
    // Преобразуем обратно в массив и сортируем по дате
    // Убеждаемся, что все значения примитивные (не объекты)
    const result = Array.from(dateMap.values()).map(item => {
      // Создаем новый объект только с примитивными значениями
      const cleanItem = {
        date: typeof item.date === 'string' ? item.date : '',
        day_name: typeof item.day_name === 'string' ? item.day_name : '',
        originalIndex: typeof item.originalIndex === 'number' ? item.originalIndex : 0,
        theory_activity: typeof item.theory_activity === 'number' ? item.theory_activity : 0,
        lesson_presence: typeof item.lesson_presence === 'number' ? item.lesson_presence : 0,
        video_activity: typeof item.video_activity === 'number' ? item.video_activity : 0,
        pdf_activity: typeof item.pdf_activity === 'number' ? item.pdf_activity : 0,
        activity: typeof item.activity === 'number' ? item.activity : 0,
        efficiency: typeof item.efficiency === 'number' ? item.efficiency : 0,
        study_time_minutes: typeof item.study_time_minutes === 'number' ? item.study_time_minutes : 0,
        file_views: typeof item.file_views === 'number' ? item.file_views : 0
      };
      
      // Добавляем значения из timeline, если они есть (только примитивные)
      Object.keys(item).forEach(key => {
        if (key.startsWith('video_timeline_') || key.startsWith('theory_timeline_') || 
            key.startsWith('challenge_timeline_') || key.startsWith('quiz_timeline_') ||
            key.startsWith('exercise_timeline_')) {
          const value = item[key];
          if (typeof value === 'number' || typeof value === 'string' || typeof value === 'boolean') {
            cleanItem[key] = value;
          }
        }
      });
      
      return cleanItem;
    }).sort((a, b) => {
      const dateA = a.originalIndex !== undefined ? a.originalIndex : 999;
      const dateB = b.originalIndex !== undefined ? b.originalIndex : 999;
      return dateA - dateB;
    });
    
    return result;
  }, [data, videoTimeline, theoryTimeline, challengeTimeline, quizTimeline, exerciseTimeline]);
  
  if (!mergedData || mergedData.length === 0) return null;
  
  // Логируем данные для отладки (только в development режиме)
  if (process.env.NODE_ENV === 'development') {
    console.log('📊 ActivityLineChart data:', JSON.stringify(data, null, 2));
    console.log('📊 ActivityLineChart mergedData:', JSON.stringify(mergedData, null, 2));
    console.log('📊 ActivityLineChart videoTimeline:', JSON.stringify(videoTimeline, null, 2));
    console.log('📊 ActivityLineChart theoryTimeline:', JSON.stringify(theoryTimeline, null, 2));
    console.log('📊 ActivityLineChart section:', section);
    
    // Детальное логирование каждого элемента mergedData
    mergedData.forEach((item, idx) => {
      console.log(`📊 mergedData[${idx}]:`, {
        date: item.date,
        theory_activity: item.theory_activity,
        lesson_presence: item.lesson_presence,
        video_activity: item.video_activity,
        pdf_activity: item.pdf_activity,
        activity: item.activity,
        efficiency: item.efficiency
      });
    });
  }
  
  const padding = { top: 50, right: 200, bottom: 70, left: 70 };
  const width = 1000;
  const height = 450;
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  
  // Определяем линии для разных типов активности в зависимости от раздела
  const activityLines = useMemo(() => {
    const baseLines = [];
    
    if (section === 'lessons') {
      baseLines.push(
        { key: 'theory_activity', label: 'Активность теории', color: '#8b5cf6', strokeWidth: 3, offset: 0 },
        { key: 'lesson_presence', label: 'Присутствие в уроке', color: '#3b82f6', strokeWidth: 3, offset: 0 },
        { key: 'video_activity', label: 'Просмотр видео', color: '#ef4444', strokeWidth: 3, offset: 0 },
        { key: 'pdf_activity', label: 'Просмотр PDF', color: '#10b981', strokeWidth: 3, offset: 0 },
        { key: 'activity', label: 'Общая активность', color: '#f59e0b', strokeWidth: 2, strokeDasharray: '5 5', offset: 0 },
        { key: 'efficiency', label: 'Эффективность (%)', color: '#06b6d4', strokeWidth: 4, isEfficiency: true, offset: 0 }
      );
      
      // Добавляем линии из timeline, если они есть
      if (videoTimeline && videoTimeline.length > 0) {
        baseLines.push({ key: 'video_timeline_value', label: 'Видео (детально)', color: '#dc2626', strokeWidth: 2.5, offset: 2 });
      }
      if (theoryTimeline && theoryTimeline.length > 0) {
        baseLines.push({ key: 'theory_timeline_value', label: 'Теория (детально)', color: '#9333ea', strokeWidth: 2.5, offset: -2 });
      }
    } else if (section === 'challenges') {
      baseLines.push(
        { key: 'challenge_timeline_value', label: 'Обновления челленджей', color: '#f59e0b', strokeWidth: 3, offset: 0 },
        { key: 'challenge_timeline_completed_challenges', label: 'Завершенные челленджи', color: '#10b981', strokeWidth: 3, offset: 2 },
        { key: 'challenge_timeline_efficiency', label: 'Эффективность (%)', color: '#06b6d4', strokeWidth: 4, isEfficiency: true, offset: 0 }
      );
    } else if (section === 'quizzes') {
      baseLines.push(
        { key: 'quiz_timeline_value', label: 'Попытки тестов', color: '#10b981', strokeWidth: 3, offset: 0 },
        { key: 'quiz_timeline_passed_quizzes', label: 'Пройденные тесты', color: '#22c55e', strokeWidth: 3, offset: 2 },
        { key: 'quiz_timeline_avg_score', label: 'Средний балл', color: '#8b5cf6', strokeWidth: 3, offset: -2 },
        { key: 'quiz_timeline_efficiency', label: 'Эффективность (%)', color: '#06b6d4', strokeWidth: 4, isEfficiency: true, offset: 0 }
      );
    } else if (section === 'exercises') {
      baseLines.push(
        { key: 'exercise_timeline_value', label: 'Отправленные упражнения', color: '#8b5cf6', strokeWidth: 3, offset: 0 },
        { key: 'exercise_timeline_reviewed_exercises', label: 'Проверенные упражнения', color: '#10b981', strokeWidth: 3, offset: 2 },
        { key: 'exercise_timeline_total_points', label: 'Баллы', color: '#f59e0b', strokeWidth: 3, offset: -2 },
        { key: 'exercise_timeline_efficiency', label: 'Эффективность (%)', color: '#06b6d4', strokeWidth: 4, isEfficiency: true, offset: 0 }
      );
    }
    
    return baseLines;
  }, [section, videoTimeline, theoryTimeline]);
  
  // Определяем максимальное значение для масштабирования
  // Для эффективности используем отдельную шкалу (0-100%)
  const maxActivity = useMemo(() => {
    const values = [];
    activityLines.forEach(line => {
      if (!line.isEfficiency) {
        mergedData.forEach(d => {
          const val = d[line.key] || 0;
          if (val > 0) values.push(val);
        });
      }
    });
    return Math.max(...values, 1);
  }, [mergedData, activityLines]);
  
  const minActivity = 0;
  const yRange = maxActivity - minActivity;
  
  // Создаем точки для каждой линии с учетом смещения для видимости пересекающихся линий
  const createPointsForLine = (lineKey, isEfficiency = false, offset = 0) => {
    return mergedData.map((day, index) => {
      const x = (index / (mergedData.length - 1 || 1)) * chartWidth + padding.left;
      // Явно проверяем наличие поля в данных
      const value = day[lineKey] !== undefined && day[lineKey] !== null ? (day[lineKey] || 0) : 0;
      let y;
      if (isEfficiency) {
        // Для эффективности используем шкалу 0-100%
        y = chartHeight - ((value / 100) * chartHeight) + padding.top;
      } else {
        // Для обычных линий: если yRange = 0, все точки будут внизу (y = chartHeight + padding.top)
        if (yRange === 0) {
          y = chartHeight + padding.top; // Внизу графика
        } else {
          y = chartHeight - ((value - minActivity) / yRange * chartHeight) + padding.top;
        }
        // Применяем смещение для видимости пересекающихся линий (в пикселях)
        y += offset;
      }
      return { x, y, value, ...day, index };
    });
  };
  
  const allPoints = activityLines.map(line => ({
    ...line,
    points: createPointsForLine(line.key, line.isEfficiency, line.offset || 0)
  }));
  
  // Создаем плавную кривую через точки (Catmull-Rom spline)
  const createSmoothPath = (points) => {
    if (points.length < 2) return '';
    if (points.length === 2) {
      return `M ${points[0].x} ${points[0].y} L ${points[1].x} ${points[1].y}`;
    }
    
    let path = `M ${points[0].x} ${points[0].y}`;
    
    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[Math.max(0, i - 1)];
      const p1 = points[i];
      const p2 = points[i + 1];
      const p3 = points[Math.min(points.length - 1, i + 2)];
      
      // Контрольные точки для плавной кривой
      const cp1x = p1.x + (p2.x - p0.x) / 6;
      const cp1y = p1.y + (p2.y - p0.y) / 6;
      const cp2x = p2.x - (p3.x - p1.x) / 6;
      const cp2y = p2.y - (p3.y - p1.y) / 6;
      
      path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.x} ${p2.y}`;
    }
    
    return path;
  };
  
  // Создаем плавные пути для всех линий
  const allPaths = allPoints.map(line => {
    const path = createSmoothPath(line.points);
    // Проверяем, есть ли данные для линии: либо есть значения > 0, либо поле присутствует в данных
    const hasNonZeroData = line.points.some(p => p.value > 0);
    const hasFieldInData = data.some(d => d[line.key] !== undefined && d[line.key] !== null);
    
    // Логируем для отладки линии теории
    if (line.key === 'theory_activity') {
      console.log('🔍 Theory line debug:', {
        key: line.key,
        points: line.points.map(p => ({ x: p.x, y: p.y, value: p.value })),
        path: path,
        hasNonZeroData,
        hasFieldInData,
        pathLength: path.length
      });
    }
    
    return {
      ...line,
      path: path,
      hasData: hasNonZeroData || hasFieldInData // Показываем линию, если есть данные (даже если все 0) или поле присутствует
    };
  }).filter(line => line.path); // Фильтруем только линии с валидным путем
  
  // Логируем все пути для отладки
  console.log('🔍 All paths:', allPaths.map(p => ({ key: p.key, hasData: p.hasData, pathLength: p.path.length })));
  
  // Сетка - горизонтальные линии
  const gridLines = [];
  for (let i = 0; i <= 5; i++) {
    const y = padding.top + (chartHeight / 5) * i;
    gridLines.push(
      <line
        key={`grid-h-${i}`}
        x1={padding.left}
        y1={y}
        x2={width - padding.right}
        y2={y}
        stroke="#e5e7eb"
        strokeWidth="1"
        strokeDasharray="3 3"
      />
    );
  }
  
  // Сетка - вертикальные линии (используем первую линию для позиций)
  const firstLinePoints = allPoints[0]?.points || [];
  for (let i = 0; i < firstLinePoints.length; i++) {
    const x = firstLinePoints[i].x;
    gridLines.push(
      <line
        key={`grid-v-${i}`}
        x1={x}
        y1={padding.top}
        x2={x}
        y2={chartHeight + padding.top}
        stroke="#f3f4f6"
        strokeWidth="1"
        strokeDasharray="2 2"
      />
    );
  }
  
  // Подписи оси Y (для активности)
  const yLabels = [];
  for (let i = 0; i <= 5; i++) {
    const value = Math.round((maxActivity / 5) * (5 - i));
    const y = padding.top + (chartHeight / 5) * i;
    yLabels.push(
      <text
        key={`y-label-${i}`}
        x={padding.left - 15}
        y={y + 4}
        textAnchor="end"
        className="text-xs fill-gray-600 font-medium"
      >
        {value}
      </text>
    );
  }
  
  // Подписи оси Y справа (для эффективности 0-100%)
  const yLabelsEfficiency = [];
  for (let i = 0; i <= 5; i++) {
    const value = Math.round((100 / 5) * (5 - i));
    const y = padding.top + (chartHeight / 5) * i;
    yLabelsEfficiency.push(
      <text
        key={`y-label-eff-${i}`}
        x={width - padding.right + 15}
        y={y + 4}
        textAnchor="start"
        className="text-xs fill-cyan-600 font-medium"
      >
        {value}%
      </text>
    );
  }
  
  const handlePointHover = (index) => {
    setHoveredIndex(index);
  };
  
  const handleMouseLeave = () => {
    setHoveredIndex(null);
  };
  
  return (
    <div className="relative w-full" onMouseLeave={handleMouseLeave}>
      <svg 
        ref={setSvgRef}
        width="100%" 
        height={height} 
        viewBox={`0 0 ${width} ${height}`} 
        className="overflow-visible"
        preserveAspectRatio="xMidYMid meet"
      >
        {/* Сетка */}
        {gridLines}
        
        {/* Оси */}
        <line
          x1={padding.left}
          y1={padding.top}
          x2={padding.left}
          y2={chartHeight + padding.top}
          stroke="#374151"
          strokeWidth="2"
        />
        <line
          x1={padding.left}
          y1={chartHeight + padding.top}
          x2={width - padding.right}
          y2={chartHeight + padding.top}
          stroke="#374151"
          strokeWidth="2"
        />
        
        {/* Подписи оси Y (активность) */}
        {yLabels}
        
        {/* Подписи оси Y справа (эффективность) */}
        {yLabelsEfficiency}
        
        {/* Рисуем все линии */}
        {allPaths.map((lineData, lineIndex) => {
          // Показываем все линии, которые имеют путь (даже если значения 0)
          // Для линий с нулевыми значениями используем меньшую прозрачность
          const hasNonZeroValues = lineData.points.some(p => p.value > 0);
          const hasFieldInData = data.some(d => d[lineData.key] !== undefined && d[lineData.key] !== null);
          
          // Логируем для отладки линии теории
          if (lineData.key === 'theory_activity') {
            console.log('🎨 Rendering theory line:', {
              key: lineData.key,
              path: lineData.path,
              color: lineData.color,
              hasNonZeroValues,
              hasFieldInData,
              opacity: hasNonZeroValues ? "1" : "0.3"
            });
          }
          
          // Показываем линию, если есть данные или поле присутствует
          // Для линии теории всегда показываем, даже если все значения 0
          if (!hasFieldInData && lineData.key !== 'activity' && lineData.key !== 'efficiency' && lineData.key !== 'theory_activity') {
            return null;
          }
          
          // Для линии теории всегда показываем с хорошей видимостью
          const lineOpacity = lineData.key === 'theory_activity' 
            ? (hasNonZeroValues ? "1" : "0.8")  // Для теории более видимая линия даже при нулевых значениях
            : (hasNonZeroValues ? "1" : "0.5");
          
          // Для линии теории увеличиваем толщину и добавляем свечение
          const strokeWidth = lineData.key === 'theory_activity' ? (hasNonZeroValues ? 3 : 2.5) : lineData.strokeWidth;
          
          return (
            <path
              key={lineData.key}
              d={lineData.path}
              fill="none"
              stroke={lineData.color}
              strokeWidth={strokeWidth}
              strokeDasharray={lineData.strokeDasharray}
              strokeLinecap="round"
              strokeLinejoin="round"
              className="drop-shadow-sm"
              opacity={lineOpacity}
              style={{
                filter: lineData.key === 'theory_activity' 
                  ? (hasNonZeroValues 
                      ? 'drop-shadow(0 0 3px rgba(139, 92, 246, 0.8))' 
                      : 'drop-shadow(0 0 2px rgba(139, 92, 246, 0.6))')
                  : undefined
              }}
            />
          );
        })}
        
        {/* Невидимая область для hover (используем первую линию) */}
        {firstLinePoints.map((point, index) => (
          <rect
            key={`hover-area-${index}`}
            x={point.x - 20}
            y={padding.top}
            width="40"
            height={chartHeight}
            fill="transparent"
            className="cursor-pointer"
            onMouseEnter={() => handlePointHover(index)}
          />
        ))}
        
        {/* Точки данных для всех линий */}
        {allPoints.map((lineData) => {
          // Показываем точки для всех линий, которые имеют данные (даже если значения 0)
          const hasFieldInData = data.some(d => d[lineData.key] !== undefined && d[lineData.key] !== null);
          if (!hasFieldInData && lineData.key !== 'activity' && lineData.key !== 'efficiency') {
            return null;
          }
          return (
            <g key={`points-${lineData.key}`}>
              {lineData.points.map((point) => {
                // Показываем точку только если значение > 0 (для нулевых значений не показываем точки)
                if (point.value === 0) {
                  return null;
                }
                return (
                  <circle
                    key={`${lineData.key}-${point.index}`}
                    cx={point.x}
                    cy={point.y}
                    r={hoveredIndex === point.index ? 6 : 4}
                    fill={lineData.color}
                    stroke="white"
                    strokeWidth={hoveredIndex === point.index ? "2" : "1"}
                    className="cursor-pointer transition-all duration-200"
                    opacity={hoveredIndex === point.index || hoveredIndex === null ? 1 : 0.5}
                  />
                );
              })}
            </g>
          );
        })}
        
        {/* Подписи дат (используем первую линию) */}
        {firstLinePoints.map((point) => (
          <text
            key={`date-${point.index}`}
            x={point.x}
            y={height - 20}
            textAnchor="middle"
            className="text-xs fill-gray-600 font-medium"
          >
            {point.date || ''}
          </text>
        ))}
        
        {/* Вертикальная линия при наведении */}
        {hoveredIndex !== null && firstLinePoints[hoveredIndex] && (
          <line
            x1={firstLinePoints[hoveredIndex].x}
            y1={padding.top - 5}
            x2={firstLinePoints[hoveredIndex].x}
            y2={chartHeight + padding.top + 5}
            stroke="#6b7280"
            strokeWidth="2"
            strokeDasharray="5 5"
            opacity="0.5"
          />
        )}
        
        {/* Легенда */}
        <g>
          {activityLines.map((line, index) => {
            // Проверяем, есть ли данные для этой линии
            const hasFieldInData = mergedData.some(d => d[line.key] !== undefined && d[line.key] !== null);
            const hasNonZeroData = mergedData.some(d => (d[line.key] || 0) > 0);
            
            // Показываем все линии в легенде, но с разной прозрачностью
            return (
              <g key={`legend-${line.key}`} opacity={hasNonZeroData ? "1" : hasFieldInData ? "0.6" : "0.4"}>
                <line
                  x1={width - padding.right + 20}
                  y1={padding.top + 20 + index * 25}
                  x2={width - padding.right + 60}
                  y2={padding.top + 20 + index * 25}
                  stroke={line.color}
                  strokeWidth={line.strokeWidth}
                  strokeDasharray={line.strokeDasharray}
                />
                <text
                  x={width - padding.right + 70}
                  y={padding.top + 24 + index * 25}
                  className="text-xs fill-gray-700 dark:fill-gray-300 font-medium"
                >
                  {line.label}
                </text>
              </g>
            );
          })}
        </g>
      </svg>
      
      {/* Tooltip с детальной информацией */}
      {hoveredIndex !== null && svgRef && firstLinePoints[hoveredIndex] && (() => {
        const dayData = mergedData[hoveredIndex];
        const point = firstLinePoints[hoveredIndex];
        
        // Логируем данные для отладки tooltip (только при первом hover)
        if (hoveredIndex === 0) {
          console.log('🔍 Tooltip dayData:', dayData);
          console.log('🔍 Tooltip values:', {
            theory_activity: dayData?.theory_activity,
            lesson_presence: dayData?.lesson_presence,
            video_activity: dayData?.video_activity,
            pdf_activity: dayData?.pdf_activity,
            activity: dayData?.activity,
            efficiency: dayData?.efficiency
          });
        }
        
        const xPercent = (point.x / width);
        const yPercent = Math.min((point.y / height), 0.5); // Показываем tooltip выше точки
        
        return (
          <div
            className="absolute bg-gray-900 text-white text-sm rounded-lg px-4 py-3 shadow-2xl z-30 pointer-events-none border border-gray-700"
            style={{
              left: `${xPercent * 100}%`,
              top: `${yPercent * 100}%`,
              transform: 'translate(-50%, calc(-100% - 15px))',
              minWidth: '220px'
            }}
          >
            <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-full">
              <div className="w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
            </div>
            <div className="font-bold text-base mb-3 text-blue-300 border-b border-gray-700 pb-2">
              📅 {dayData?.date || ''}
            </div>
            <div className="space-y-2">
              {/* Активность теории */}
              <div className="flex items-center justify-between p-2 bg-purple-900/20 rounded">
                <span className="text-gray-300 flex items-center">
                  <span className="w-3 h-3 rounded-full mr-2" style={{ backgroundColor: '#8b5cf6' }}></span>
                  📖 Активность теории:
                </span>
                <span className="font-bold text-purple-300">{dayData?.theory_activity || 0} сессий</span>
              </div>
              
              {/* Присутствие в уроке */}
              <div className="flex items-center justify-between p-2 bg-blue-900/20 rounded">
                <span className="text-gray-300 flex items-center">
                  <span className="w-3 h-3 rounded-full mr-2" style={{ backgroundColor: '#3b82f6' }}></span>
                  👁️ Присутствие в уроке:
                </span>
                <span className="font-bold text-blue-300">{dayData?.lesson_presence || 0} раз</span>
              </div>
              
              {/* Просмотр видео */}
              <div className="flex items-center justify-between p-2 bg-red-900/20 rounded">
                <span className="text-gray-300 flex items-center">
                  <span className="w-3 h-3 rounded-full mr-2" style={{ backgroundColor: '#ef4444' }}></span>
                  🎥 Просмотр видео:
                </span>
                <span className="font-bold text-red-300">
                  {dayData?.video_activity || 0} {dayData?.video_activity === 1 ? 'минута' : dayData?.video_activity > 1 && dayData?.video_activity < 5 ? 'минуты' : 'минут'}
                </span>
              </div>
              
              {/* Просмотр PDF */}
              <div className="flex items-center justify-between p-2 bg-green-900/20 rounded">
                <span className="text-gray-300 flex items-center">
                  <span className="w-3 h-3 rounded-full mr-2" style={{ backgroundColor: '#10b981' }}></span>
                  📄 Просмотр PDF:
                </span>
                <span className="font-bold text-green-300">
                  {dayData?.pdf_activity || 0} {dayData?.pdf_activity === 1 ? 'файл' : dayData?.pdf_activity > 1 && dayData?.pdf_activity < 5 ? 'файла' : 'файлов'}
                </span>
              </div>
              
              {/* Общая активность */}
              <div className="flex items-center justify-between pt-2 border-t border-gray-700 p-2 bg-orange-900/20 rounded mt-2">
                <span className="text-gray-300 flex items-center">
                  <span className="w-3 h-3 rounded-full mr-2 border-2" style={{ borderColor: '#f59e0b', backgroundColor: 'transparent' }}></span>
                  📊 Общая активность:
                </span>
                <span className="font-bold text-orange-400 text-lg">{dayData?.activity || 0} баллов</span>
              </div>
              
              {/* Эффективность */}
              {dayData?.efficiency !== undefined && (
                <div className="flex items-center justify-between pt-2 border-t border-gray-700 p-2 bg-cyan-900/20 rounded mt-2">
                  <span className="text-gray-300 flex items-center">
                    <span className="w-3 h-3 rounded-full mr-2" style={{ backgroundColor: '#06b6d4' }}></span>
                    ⚡ Эффективность:
                  </span>
                  <span className={`font-bold text-lg ${
                    dayData.efficiency >= 80 ? 'text-green-400' : 
                    dayData.efficiency >= 60 ? 'text-yellow-400' : 
                    dayData.efficiency >= 40 ? 'text-orange-400' : 
                    'text-red-400'
                  }`}>
                    {dayData?.efficiency || 0}%
                    {dayData.efficiency >= 80 && ' 🎉'}
                    {dayData.efficiency >= 60 && dayData.efficiency < 80 && ' 👍'}
                    {dayData.efficiency < 40 && ' ⚠️'}
                  </span>
                </div>
              )}
              
              {/* Время изучения */}
              {dayData?.study_time_minutes && (
                <div className="flex items-center justify-between pt-2 border-t border-gray-700 p-2 bg-indigo-900/20 rounded mt-2">
                  <span className="text-gray-300 flex items-center">
                    ⏱️ Время осознания:
                  </span>
                  <span className="font-bold text-indigo-300">
                    {dayData.study_time_minutes} {dayData.study_time_minutes === 1 ? 'минута' : dayData.study_time_minutes > 1 && dayData.study_time_minutes < 5 ? 'минуты' : 'минут'}
                  </span>
                </div>
              )}
              
              {/* Просмотры файлов */}
              {dayData?.file_views !== undefined && (
                <div className="flex items-center justify-between pt-2 border-t border-gray-700 p-2 bg-pink-900/20 rounded mt-2">
                  <span className="text-gray-300 flex items-center">
                    👀 Просмотры файлов:
                  </span>
                  <span className="font-bold text-pink-300">
                    {dayData.file_views || 0} {dayData.file_views === 1 ? 'просмотр' : dayData.file_views > 1 && dayData.file_views < 5 ? 'просмотра' : 'просмотров'}
                  </span>
                </div>
              )}
            </div>
          </div>
        );
      })()}
    </div>
  );
};

// Компонент для графика просмотра видео с временными метками
const VideoTimelineChart = ({ timelineData, period }) => {
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const [svgRef, setSvgRef] = useState(null);
  
  if (!timelineData || timelineData.length === 0) return null;
  
  const padding = { top: 50, right: 200, bottom: 100, left: 70 };
  const width = 1200;
  const height = 500;
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  
  // Определяем максимальное значение для масштабирования
  // Учитываем разные типы данных (video_minutes, theory_sessions, challenge_updates, quiz_attempts)
  // Используем rawValue для правильного масштабирования
  const maxValue = Math.max(
    ...timelineData.map(d => {
      const raw = d.video_minutes || d.theory_sessions || d.challenge_updates || d.quiz_attempts || 0;
      return raw; // Всегда используем реальное значение для масштабирования
    }), 
    1
  );
  const minValue = 0;
  const yRange = maxValue - minValue || 1; // Избегаем деления на ноль
  
  // Создаем точки для графика
  const points = timelineData.map((item, index) => {
    const x = (index / (timelineData.length - 1 || 1)) * chartWidth + padding.left;
    const rawValue = item.video_minutes || item.theory_sessions || item.challenge_updates || item.quiz_attempts || 0;
    // Используем rawValue для отображения, но проверяем is_watching для визуального отображения
    const value = rawValue; // Всегда показываем реальное значение
    const y = chartHeight - ((value - minValue) / yRange * chartHeight) + padding.top;
    
    // Извлекаем date и time из datetime или используем отдельные поля
    let dateStr = '';
    let timeStr = '';
    if (typeof item.datetime === 'string' && item.datetime) {
      try {
        const dt = new Date(item.datetime);
        if (!isNaN(dt.getTime())) {
          dateStr = dt.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
          timeStr = dt.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
        }
      } catch (e) {
        // Игнорируем ошибки парсинга даты
      }
    }
    if (!dateStr && typeof item.date === 'string') {
      dateStr = item.date;
    }
    if (!timeStr && typeof item.hour === 'string') {
      timeStr = item.hour;
    }
    
    // Извлекаем только примитивные значения, чтобы избежать попадания объектов в JSX
    return { 
      x, 
      y, 
      value: rawValue, 
      index,
      video_minutes: typeof item.video_minutes === 'number' ? item.video_minutes : 0,
      theory_sessions: typeof item.theory_sessions === 'number' ? item.theory_sessions : 0,
      challenge_updates: typeof item.challenge_updates === 'number' ? item.challenge_updates : 0,
      quiz_attempts: typeof item.quiz_attempts === 'number' ? item.quiz_attempts : 0,
      efficiency: typeof item.efficiency === 'number' ? item.efficiency : 0,
      is_watching: typeof item.is_watching === 'boolean' ? item.is_watching : false,
      date: dateStr,
      time: timeStr,
      hour: typeof item.hour === 'string' ? item.hour : '',
      datetime: typeof item.datetime === 'string' ? item.datetime : '',
      planetary_hour: typeof item.planetary_hour === 'string' ? item.planetary_hour : '',
      day_planet: typeof item.day_planet === 'string' ? item.day_planet : '',
      lesson_planet: typeof item.lesson_planet === 'string' ? item.lesson_planet : '',
      avg_score: typeof item.avg_score === 'number' ? item.avg_score : undefined,
      passed_quizzes: typeof item.passed_quizzes === 'number' ? item.passed_quizzes : undefined,
      completed_challenges: typeof item.completed_challenges === 'number' ? item.completed_challenges : undefined
    };
  });
  
  // Создаем плавную кривую
  const createSmoothPath = (points) => {
    if (!points || points.length === 0) return '';
    if (points.length === 1) {
      return `M ${points[0].x} ${points[0].y}`;
    }
    if (points.length === 2) {
      return `M ${points[0].x} ${points[0].y} L ${points[1].x} ${points[1].y}`;
    }
    
    let path = `M ${points[0].x} ${points[0].y}`;
    
    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[Math.max(0, i - 1)];
      const p1 = points[i];
      const p2 = points[i + 1];
      const p3 = points[Math.min(points.length - 1, i + 2)];
      
      const cp1x = p1.x + (p2.x - p0.x) / 6;
      const cp1y = p1.y + (p2.y - p0.y) / 6;
      const cp2x = p2.x - (p3.x - p1.x) / 6;
      const cp2y = p2.y - (p3.y - p1.y) / 6;
      
      path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.x} ${p2.y}`;
    }
    
    return path;
  };
  
  const pathData = createSmoothPath(points);
  // Проверяем, что pathData не пустой и начинается с M перед созданием areaPath
  const areaPath = pathData && pathData.trim().startsWith('M') && points.length > 0
    ? `${pathData} L ${points[points.length - 1].x} ${chartHeight + padding.top} L ${points[0].x} ${chartHeight + padding.top} Z`
    : '';
  
  // Сетка
  const gridLines = [];
  for (let i = 0; i <= 5; i++) {
    const y = padding.top + (chartHeight / 5) * i;
    gridLines.push(
      <line key={`grid-h-${i}`} x1={padding.left} y1={y} x2={width - padding.right} y2={y} stroke="#e5e7eb" strokeWidth="1" strokeDasharray="3 3" />
    );
  }
  
  // Подписи оси Y (активность)
  const yLabels = [];
  for (let i = 0; i <= 5; i++) {
    const value = Math.round((maxValue / 5) * (5 - i));
    const y = padding.top + (chartHeight / 5) * i;
    yLabels.push(
      <text key={`y-label-${i}`} x={padding.left - 15} y={y + 4} textAnchor="end" className="text-xs fill-gray-600 font-medium">
        {value}
      </text>
    );
  }
  
  // Подписи оси Y справа (эффективность 0-100%)
  const yLabelsEfficiency = [];
  for (let i = 0; i <= 5; i++) {
    const value = Math.round((100 / 5) * (5 - i));
    const y = padding.top + (chartHeight / 5) * i;
    yLabelsEfficiency.push(
      <text key={`y-label-eff-${i}`} x={width - padding.right + 15} y={y + 4} textAnchor="start" className="text-xs fill-cyan-600 font-medium">
        {value}%
      </text>
    );
  }
  
  // Подписи оси X (дата и время)
  const xLabels = [];
  const step = Math.max(1, Math.floor(timelineData.length / 10)); // Показываем примерно 10 меток
  for (let i = 0; i < timelineData.length; i += step) {
    const point = points[i];
    if (point) {
      xLabels.push(
        <text key={`x-label-${i}`} x={point.x} y={height - 40} textAnchor="middle" className="text-xs fill-gray-600 font-medium">
          {point.date}
        </text>
      );
      xLabels.push(
        <text key={`x-time-${i}`} x={point.x} y={height - 25} textAnchor="middle" className="text-xs fill-gray-500">
          {point.time}
        </text>
      );
    }
  }
  
  return (
    <div className="relative w-full" onMouseLeave={() => setHoveredIndex(null)}>
      <svg ref={setSvgRef} width="100%" height={height} viewBox={`0 0 ${width} ${height}`} className="overflow-visible" preserveAspectRatio="xMidYMid meet">
        {gridLines}
        <line x1={padding.left} y1={padding.top} x2={padding.left} y2={chartHeight + padding.top} stroke="#374151" strokeWidth="2" />
        <line x1={padding.left} y1={chartHeight + padding.top} x2={width - padding.right} y2={chartHeight + padding.top} stroke="#374151" strokeWidth="2" />
        {yLabels}
        {yLabelsEfficiency}
        {xLabels}
        
        <defs>
          <linearGradient id="gradientTimelineArea" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#ef4444" stopOpacity="0.5" />
            <stop offset="100%" stopColor="#ef4444" stopOpacity="0.05" />
          </linearGradient>
        </defs>
        
        {/* Область под графиком - только если pathData валидный */}
        {pathData && pathData.trim().startsWith('M') && (
          <path d={areaPath} fill="url(#gradientTimelineArea)" opacity="0.4" />
        )}
        
        {/* Плавная линия активности - только если pathData валидный */}
        {pathData && pathData.trim().startsWith('M') && (
          <path d={pathData} fill="none" stroke="#ef4444" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="drop-shadow-sm" />
        )}
        
        {/* Линия эффективности (если есть данные) - более яркая и заметная */}
        {timelineData.some(d => d.efficiency !== undefined && d.efficiency > 0) && (() => {
          const efficiencyPoints = timelineData.map((item, index) => {
            const x = (index / (timelineData.length - 1 || 1)) * chartWidth + padding.left;
            const efficiency = typeof item.efficiency === 'number' ? item.efficiency : 0;
            const y = chartHeight - ((efficiency / 100) * chartHeight) + padding.top;
            // Извлекаем только примитивные значения, чтобы избежать попадания объектов в JSX
            return { 
              x, 
              y, 
              efficiency, 
              index,
              date: typeof item.date === 'string' ? item.date : '',
              hour: typeof item.hour === 'string' ? item.hour : '',
              datetime: typeof item.datetime === 'string' ? item.datetime : '',
              planetary_hour: typeof item.planetary_hour === 'string' ? item.planetary_hour : '',
              day_planet: typeof item.day_planet === 'string' ? item.day_planet : '',
              lesson_planet: typeof item.lesson_planet === 'string' ? item.lesson_planet : ''
            };
          });
          
          const efficiencyPath = createSmoothPath(efficiencyPoints);
          
          // Проверяем, что путь не пустой
          if (!efficiencyPath) return null;
          
          // Градиент для линии эффективности
          return (
            <>
              <defs>
                <linearGradient id="efficiencyGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#06b6d4" stopOpacity="1" />
                  <stop offset="50%" stopColor="#3b82f6" stopOpacity="0.9" />
                  <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.8" />
                </linearGradient>
              </defs>
              <path 
                d={efficiencyPath} 
                fill="none" 
                stroke="url(#efficiencyGradient)" 
                strokeWidth="5" 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                className="drop-shadow-lg"
                opacity="1"
              />
            </>
          );
        })()}
        
        {/* Hover области */}
        {points.map((point, index) => (
          <rect key={`hover-area-${index}`} x={point.x - 15} y={padding.top} width="30" height={chartHeight} fill="transparent" className="cursor-pointer" onMouseEnter={() => setHoveredIndex(index)} />
        ))}
        
        {/* Точки данных активности */}
        {points.map((point) => (
          <circle
            key={point.index}
            cx={point.x}
            cy={point.y}
            r={hoveredIndex === point.index ? 8 : (point.is_watching ? 5 : 3)}
            fill={point.is_watching ? "#ef4444" : "#9ca3af"}
            stroke="white"
            strokeWidth={hoveredIndex === point.index ? "3" : "2"}
            className="cursor-pointer transition-all duration-200"
            opacity={hoveredIndex === point.index || hoveredIndex === null ? 1 : 0.5}
          />
        ))}
        
        {/* Точки эффективности (если есть данные) - с цветовой индикацией */}
        {timelineData.some(d => d.efficiency !== undefined && d.efficiency > 0) && timelineData.map((item, index) => {
          if (!item.efficiency || item.efficiency === 0) return null;
          const x = (index / (timelineData.length - 1 || 1)) * chartWidth + padding.left;
          const efficiency = item.efficiency || 0;
          const y = chartHeight - ((efficiency / 100) * chartHeight) + padding.top;
          
          // Цвет в зависимости от эффективности
          let pointColor = "#06b6d4"; // Голубой по умолчанию
          if (efficiency >= 80) {
            pointColor = "#10b981"; // Зеленый - отлично
          } else if (efficiency >= 60) {
            pointColor = "#f59e0b"; // Желтый - хорошо
          } else if (efficiency >= 40) {
            pointColor = "#ef4444"; // Красный - плохо
          }
          
          return (
            <circle
              key={`eff-${index}`}
              cx={x}
              cy={y}
              r={hoveredIndex === index ? 8 : (efficiency >= 80 ? 6 : 4)}
              fill={pointColor}
              stroke="white"
              strokeWidth={hoveredIndex === index ? "3" : "2"}
              className="cursor-pointer transition-all duration-200"
              opacity={hoveredIndex === index || hoveredIndex === null ? 1 : 0.7}
            />
          );
        })}
        
        {/* Вертикальная линия при наведении */}
        {hoveredIndex !== null && (
          <line x1={points[hoveredIndex].x} y1={padding.top - 5} x2={points[hoveredIndex].x} y2={chartHeight + padding.top + 5} stroke="#ef4444" strokeWidth="2" strokeDasharray="5 5" opacity="0.6" />
        )}
      </svg>
      
      {/* Tooltip */}
      {hoveredIndex !== null && svgRef && (() => {
        const point = points[hoveredIndex];
        const xPercent = (point.x / width);
        const yPercent = Math.min((point.y / height), 0.5);
        
        return (
          <div
            className="absolute bg-gray-900 text-white text-sm rounded-lg px-4 py-3 shadow-2xl z-30 pointer-events-none border border-gray-700"
            style={{
              left: `${xPercent * 100}%`,
              top: `${yPercent * 100}%`,
              transform: 'translate(-50%, calc(-100% - 15px))',
              minWidth: '200px'
            }}
          >
            <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-full">
              <div className="w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
            </div>
            <div className="font-bold text-base mb-2 text-red-300">{point.date} {point.time}</div>
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-gray-300">Статус:</span>
                <span className={`font-bold ${point.is_watching ? 'text-red-400' : 'text-gray-400'}`}>
                  {point.is_watching ? '▶️ Активность' : '⏸️ Нет активности'}
                </span>
              </div>
              {point.is_watching && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Значение:</span>
                  <span className="font-bold text-white">{point.video_minutes || point.theory_sessions || point.challenge_updates || point.quiz_attempts || 0} {point.video_minutes ? 'мин' : point.theory_sessions ? 'сессий' : point.challenge_updates ? 'обновлений' : 'попыток'}</span>
                </div>
              )}
              {point.efficiency !== undefined && point.efficiency > 0 && (
                <div className="flex items-center justify-between pt-2 border-t border-gray-700">
                  <span className="text-gray-300">Эффективность:</span>
                  <span className="font-bold text-cyan-400">{point.efficiency}%</span>
                </div>
              )}
              {point.avg_score !== undefined && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Средний балл:</span>
                  <span className="font-bold text-white">{point.avg_score}%</span>
                </div>
              )}
              {point.passed_quizzes !== undefined && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Пройдено:</span>
                  <span className="font-bold text-green-400">{point.passed_quizzes} / {point.quiz_attempts}</span>
                </div>
              )}
              {point.completed_challenges !== undefined && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Завершено:</span>
                  <span className="font-bold text-green-400">{point.completed_challenges}</span>
                </div>
              )}
              {point.planetary_hour && (
                <div className="flex items-center justify-between pt-2 border-t border-gray-700">
                  <span className="text-gray-300">Час планеты:</span>
                  <span className="font-bold text-yellow-400">{point.planetary_hour}</span>
                </div>
              )}
              {point.day_planet && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">День планеты:</span>
                  <span className="font-bold text-yellow-400">{point.day_planet}</span>
                </div>
              )}
              {point.lesson_planet && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Планета урока:</span>
                  <span className="font-bold text-yellow-400">{point.lesson_planet}</span>
                </div>
              )}
            </div>
          </div>
        );
      })()}
    </div>
  );
};

const LearningSystemV2 = () => {
  const { user, isAuthenticated, loading: authLoading, isInitialized } = useAuth();
  const navigate = useNavigate();
  const [lessons, setLessons] = useState([]);
  const [currentLesson, setCurrentLesson] = useState(null);
  const [currentSection, setCurrentSection] = useState('theory');
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [analyticsSection, setAnalyticsSection] = useState(null); // 'lessons', 'challenges', 'quizzes', 'exercises'
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [userLevel, setUserLevel] = useState(1);
  const [lessonsFilesStats, setLessonsFilesStats] = useState({}); // Статистика файлов для всех уроков
  const [dashboardStats, setDashboardStats] = useState(null); // Статистика дашборда
  const [analyticsStats, setAnalyticsStats] = useState(null); // Статистика для аналитики
  const [detailedAnalytics, setDetailedAnalytics] = useState(null); // Детальная аналитика
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [videoTimeline, setVideoTimeline] = useState(null); // Данные о просмотре видео
  const [theoryTimeline, setTheoryTimeline] = useState(null); // Данные об изучении теории
  const [challengeTimeline, setChallengeTimeline] = useState(null); // Данные о челленджах
  const [quizTimeline, setQuizTimeline] = useState(null); // Данные о тестах
  const [exerciseTimeline, setExerciseTimeline] = useState(null); // Данные об упражнениях
  const [timelinePeriod, setTimelinePeriod] = useState('day'); // Период для графиков: day (по умолчанию), week, month, quarter
  const [selectedStartDate, setSelectedStartDate] = useState(null); // Выбранная начальная дата для календаря
  const [selectedEndDate, setSelectedEndDate] = useState(null); // Выбранная конечная дата для календаря
  const [showCalendar, setShowCalendar] = useState(false); // Показывать ли календарь
  
  // Инициализация дат для одного дня (24:00) - сегодня по умолчанию
  useEffect(() => {
    const today = new Date();
    const startDate = new Date(today);
    startDate.setHours(0, 0, 0, 0);
    const endDate = new Date(today);
    endDate.setHours(23, 59, 59, 999);
    
    // Устанавливаем начальную и конечную дату для одного дня (сегодня)
    setSelectedStartDate(startDate);
    setSelectedEndDate(endDate);
  }, []);
  const [exerciseResponses, setExerciseResponses] = useState({});
  const [exerciseResponsesData, setExerciseResponsesData] = useState({}); // Полные данные ответов
  const [savingResponse, setSavingResponse] = useState({});
  const [lessonProgress, setLessonProgress] = useState(null);
  const [challengeProgress, setChallengeProgress] = useState(null);
  const [challengeNotes, setChallengeNotes] = useState({});
  const [savingChallengeNote, setSavingChallengeNote] = useState({});
  const [challengeHistory, setChallengeHistory] = useState([]); // История всех попыток челленджа
  const [quizHistory, setQuizHistory] = useState([]); // История всех попыток теста
  
  // Состояния для файлов
  const [lessonFiles, setLessonFiles] = useState({ theory: [], exercises: [], challenge: [], quiz: [] });
  const [viewingFile, setViewingFile] = useState(null);
  const [fileViewerOpen, setFileViewerOpen] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [imageRotation, setImageRotation] = useState(0); // Угол поворота изображения
  const [videoWatchStartTime, setVideoWatchStartTime] = useState(null);
  const [videoWatchInterval, setVideoWatchInterval] = useState(null);
  const [studentFilesStats, setStudentFilesStats] = useState(null);
  const [lessonFileMap, setLessonFileMap] = useState({});
  
  // Состояние для компактной навигации при прокрутке
  const [isScrolled, setIsScrolled] = useState(false);
  
  // Состояния для теста
  const [quizStarted, setQuizStarted] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [quizAnswers, setQuizAnswers] = useState({});
  const [quizCompleted, setQuizCompleted] = useState(false);
  const [quizScore, setQuizScore] = useState(0);
  
  // Состояния для отслеживания времени активности
  const [timeActivity, setTimeActivity] = useState({ total_minutes: 0, total_points: 0 });
  const [activityStartTime, setActivityStartTime] = useState(null);

  const backendUrl = getBackendUrl();

  useEffect(() => {
    if (!isInitialized || authLoading || !isAuthenticated) {
      return;
    }

    loadLessons();
    loadDashboardStats();
  }, [isInitialized, authLoading, isAuthenticated]);

  useEffect(() => {
    if (!isAuthenticated) {
      setLessons([]);
      setCurrentLesson(null);
      setDashboardStats(null);
      setLessonFiles({ theory: [], exercises: [], challenge: [], quiz: [] });
      setStudentFilesStats(null);
      setLoading(false);
    }
  }, [isAuthenticated]);

  // Загрузка аналитики для конкретной секции
  const loadAnalytics = async (section, period = null, startDate = null, endDate = null) => {
    try {
      setAnalyticsLoading(true);
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/');
        return;
      }

      // Загружаем общую статистику дашборда
      const statsResponse = await fetch(`${backendUrl}/api/student/dashboard-stats`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });

      if (statsResponse.status === 401) {
        localStorage.removeItem('token');
        navigate('/');
        return;
      }

      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        console.log('📊 Dashboard stats from backend:', statsData.stats);
        console.log('📊 Dashboard activity_chart:', JSON.stringify(statsData.stats?.activity_chart, null, 2));
        
        // Детальное логирование каждого элемента activity_chart
        if (statsData.stats?.activity_chart) {
          statsData.stats.activity_chart.forEach((item, idx) => {
            console.log(`📊 activity_chart[${idx}]:`, {
              date: item.date,
              theory_activity: item.theory_activity,
              lesson_presence: item.lesson_presence,
              video_activity: item.video_activity,
              pdf_activity: item.pdf_activity,
              activity: item.activity,
              efficiency: item.efficiency
            });
          });
        }
        
        setAnalyticsStats(statsData.stats);
      }

      // Загружаем детальную аналитику для секции с периодом и датами
      // Используем переданные параметры или текущие значения из state
      const currentPeriod = period || timelinePeriod;
      const currentStartDate = startDate || selectedStartDate;
      const currentEndDate = endDate || selectedEndDate;
      
      let analyticsUrl = `${backendUrl}/api/student/analytics/${section}?period=${currentPeriod}`;
      if (currentStartDate && currentEndDate) {
        // Используем локальную дату, чтобы избежать проблем с часовыми поясами
        const formatDate = (date) => {
          const year = date.getFullYear();
          const month = String(date.getMonth() + 1).padStart(2, '0');
          const day = String(date.getDate()).padStart(2, '0');
          return `${year}-${month}-${day}`;
        };
        analyticsUrl += `&start_date=${formatDate(currentStartDate)}&end_date=${formatDate(currentEndDate)}`;
      }
      
      const analyticsResponse = await fetch(analyticsUrl, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });

      if (analyticsResponse.status === 401) {
        localStorage.removeItem('token');
        navigate('/');
        return;
      }

      if (analyticsResponse.ok) {
        const analyticsData = await analyticsResponse.json();
        setDetailedAnalytics(analyticsData.analytics);
        // Если есть activity_chart в ответе, обновляем stats
        if (analyticsData.activity_chart) {
          console.log('📊 Analytics activity_chart from backend:', JSON.stringify(analyticsData.activity_chart, null, 2));
          console.log('📊 Period:', currentPeriod, 'StartDate:', currentStartDate, 'EndDate:', currentEndDate);
          console.log('📊 Activity chart length:', analyticsData.activity_chart.length);
          setAnalyticsStats(prev => ({
            ...prev,
            activity_chart: analyticsData.activity_chart
          }));
        }
      }
    } catch (error) {
      console.error('Error loading analytics:', error);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  // Загрузка данных о просмотре видео
  const loadVideoTimeline = async (period = 'week', startDate = null, endDate = null) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      // Функция для форматирования даты в локальном времени (избегаем проблем с UTC)
      const formatDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
      };
      
      let url = `${backendUrl}/api/student/analytics/video-timeline?period=${period}`;
      if (startDate && endDate) {
        url += `&start_date=${formatDate(startDate)}&end_date=${formatDate(endDate)}`;
        // Для периода 'day' добавляем параметры для детализации по часам
        if (period === 'day') {
          url += `&hourly=true`;
        }
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Video timeline data:', data);
        console.log('Video timeline array:', data.timeline || []);
        setVideoTimeline(data.timeline || []);
      } else {
        console.error('Video timeline response not ok:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Error loading video timeline:', error);
    }
  };

  // Загрузка данных об изучении теории
  const loadTheoryTimeline = async (period = 'week', startDate = null, endDate = null) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      // Функция для форматирования даты в локальном времени
      const formatDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
      };

      let url = `${backendUrl}/api/student/analytics/theory-timeline?period=${period}`;
      if (startDate && endDate) {
        url += `&start_date=${formatDate(startDate)}&end_date=${formatDate(endDate)}`;
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Theory timeline data:', data);
        console.log('Theory timeline array:', data.timeline || []);
        setTheoryTimeline(data.timeline || []);
      } else {
        console.error('Theory timeline response not ok:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Error loading theory timeline:', error);
    }
  };

  // Загрузка данных о челленджах
  const loadChallengeTimeline = async (period = 'week', startDate = null, endDate = null) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      // Функция для форматирования даты в локальном времени
      const formatDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
      };

      let url = `${backendUrl}/api/student/analytics/challenge-timeline?period=${period}`;
      if (startDate && endDate) {
        url += `&start_date=${formatDate(startDate)}&end_date=${formatDate(endDate)}`;
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setChallengeTimeline(data.timeline || []);
      }
    } catch (error) {
      console.error('Error loading challenge timeline:', error);
    }
  };

  // Загрузка данных о тестах
  const loadQuizTimeline = async (period = 'week', startDate = null, endDate = null) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      // Функция для форматирования даты в локальном времени
      const formatDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
      };

      let url = `${backendUrl}/api/student/analytics/quiz-timeline?period=${period}`;
      if (startDate && endDate) {
        url += `&start_date=${formatDate(startDate)}&end_date=${formatDate(endDate)}`;
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setQuizTimeline(data.timeline || []);
      }
    } catch (error) {
      console.error('Error loading quiz timeline:', error);
    }
  };

  // Загрузка данных об упражнениях
  const loadExerciseTimeline = async (period = 'week', startDate = null, endDate = null) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      // Функция для форматирования даты в локальном времени
      const formatDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
      };

      let url = `${backendUrl}/api/student/analytics/exercise-timeline?period=${period}`;
      if (startDate && endDate) {
        url += `&start_date=${formatDate(startDate)}&end_date=${formatDate(endDate)}`;
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setExerciseTimeline(data.timeline || []);
      }
    } catch (error) {
      console.error('Error loading exercise timeline:', error);
    }
  };

  // Обработчик изменения периода для графиков
  const handleTimelinePeriodChange = async (newPeriod) => {
    const today = new Date();
    let startDate = null;
    let endDate = today;
    
    if (newPeriod === 'day') {
      // Один день (24 часа) - сегодня
      startDate = new Date(today);
      startDate.setHours(0, 0, 0, 0);
      endDate = new Date(today);
      endDate.setHours(23, 59, 59, 999);
    } else if (newPeriod === 'week') {
      // Последняя неделя (сегодня - последний день)
      startDate = new Date(today);
      startDate.setDate(today.getDate() - 6); // 7 дней включая сегодня
    } else if (newPeriod === 'month') {
      // Последний месяц (сегодня - последний день)
      startDate = new Date(today);
      startDate.setMonth(today.getMonth() - 1);
    } else if (newPeriod === 'quarter') {
      // Последний квартал (сегодня - последний день)
      startDate = new Date(today);
      startDate.setMonth(today.getMonth() - 3);
    }
    
    // Обновляем состояние
    setTimelinePeriod(newPeriod);
    setSelectedStartDate(startDate);
    setSelectedEndDate(endDate);
    
    // Перезагружаем аналитику с новым периодом и датами, если она открыта
    // Передаем даты напрямую, чтобы избежать проблем с асинхронным обновлением state
    if (showAnalytics && analyticsSection) {
      console.log('🔄 Reloading analytics with period:', newPeriod, 'startDate:', startDate, 'endDate:', endDate);
      await loadAnalytics(analyticsSection, newPeriod, startDate, endDate);
    }
    
    // Загружаем данные для всех типов активности
    if (startDate && endDate) {
      loadVideoTimeline(newPeriod, startDate, endDate);
      loadTheoryTimeline(newPeriod, startDate, endDate);
      loadChallengeTimeline(newPeriod, startDate, endDate);
      loadQuizTimeline(newPeriod, startDate, endDate);
      loadExerciseTimeline(newPeriod, startDate, endDate);
    } else {
      loadVideoTimeline(newPeriod);
      loadTheoryTimeline(newPeriod);
      loadChallengeTimeline(newPeriod);
      loadQuizTimeline(newPeriod);
      loadExerciseTimeline(newPeriod);
    }
  };

  // Обработчик выбора диапазона дат
  const handleDateRangeSelect = (startDate, endDate) => {
    setSelectedStartDate(startDate);
    setSelectedEndDate(endDate);
    // Загружаем данные для всех типов активности с выбранным диапазоном дат
    loadVideoTimeline(timelinePeriod, startDate, endDate);
    loadTheoryTimeline(timelinePeriod, startDate, endDate);
    loadChallengeTimeline(timelinePeriod, startDate, endDate);
    loadQuizTimeline(timelinePeriod, startDate, endDate);
    loadExerciseTimeline(timelinePeriod, startDate, endDate);
  };

  // Обработчик клика на карточку статистики
  const handleStatsCardClick = async (section) => {
    console.log('=== STATS CARD CLICKED ===', section);
    setAnalyticsSection(section);
    setShowAnalytics(true);
    
    // Получаем текущий период и даты (по умолчанию 'day' с сегодняшним днем)
    const currentPeriod = timelinePeriod || 'day';
    let startDate = selectedStartDate;
    let endDate = selectedEndDate;
    
    // Если даты не установлены, устанавливаем их для одного дня (сегодня)
    if (!startDate || !endDate) {
      const today = new Date();
      startDate = new Date(today);
      startDate.setHours(0, 0, 0, 0);
      endDate = new Date(today);
      endDate.setHours(23, 59, 59, 999);
      setSelectedStartDate(startDate);
      setSelectedEndDate(endDate);
    }
    
    // Загружаем аналитику с текущим периодом и датами
    await loadAnalytics(section, currentPeriod, startDate, endDate);
    
    // Загружаем timeline данные с учетом выбранного периода и дат
    if (section === 'lessons') {
      loadVideoTimeline(currentPeriod, startDate, endDate);
      loadTheoryTimeline(currentPeriod, startDate, endDate);
    } else if (section === 'challenges') {
      loadChallengeTimeline(currentPeriod, startDate, endDate);
    } else if (section === 'quizzes') {
      loadQuizTimeline(currentPeriod, startDate, endDate);
    } else if (section === 'exercises') {
      loadExerciseTimeline(currentPeriod, startDate, endDate);
    }
  };

  const loadDashboardStats = async () => {
    try {
      console.log('Loading dashboard stats...');
      const response = await fetch(`${backendUrl}/api/student/dashboard-stats`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      console.log('Dashboard stats response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Dashboard stats data:', data);
        setDashboardStats(data.stats);
        console.log('Dashboard stats set successfully');
      } else {
        console.error('Dashboard stats response not ok:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Error loading dashboard stats:', error);
    }
  };

  const loadLessons = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No token available');
        return;
      }

      const response = await fetch(`${backendUrl}/api/learning-v2/lessons`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        if (response.status === 401) {
          console.error('Unauthorized - token may be invalid');
          localStorage.removeItem('token');
          return;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Загружаем прогресс для каждого урока
      const lessonsWithProgress = await Promise.all(
        data.lessons.map(async (lesson) => {
          try {
            const progressResponse = await fetch(
              `${backendUrl}/api/student/lesson-progress/${lesson.id}`,
              {
                headers: {
                  'Authorization': `Bearer ${localStorage.getItem('token')}`,
                  'Content-Type': 'application/json'
                }
              }
            );
            
            if (progressResponse.ok) {
              const progressData = await progressResponse.json();
              return {
                ...lesson,
                progress_data: progressData
              };
            }
            return lesson;
          } catch (error) {
            console.error(`Error loading progress for lesson ${lesson.id}:`, error);
            return lesson;
          }
        })
      );
      
      setLessons(lessonsWithProgress);
      setUserLevel(data.user_level);
      
      // Загружаем статистику файлов для всех уроков
      await loadAllLessonsFilesStats(lessonsWithProgress);
    } catch (error) {
      console.error('Error loading lessons:', error);
      setError('Ошибка загрузки уроков');
    } finally {
      setLoading(false);
    }
  };

  // Загрузка статистики файлов для всех уроков
  const loadAllLessonsFilesStats = async (lessons) => {
    try {
      const stats = {};
      
      // Загружаем файлы для каждого урока параллельно
      await Promise.all(
        lessons.map(async (lesson) => {
          try {
            const response = await fetch(
              `${backendUrl}/api/student/lesson-files/${lesson.id}`,
              {
                headers: {
                  'Authorization': `Bearer ${localStorage.getItem('token')}`,
                  'Content-Type': 'application/json'
                }
              }
            );
            
            if (response.ok) {
              const data = await response.json();
              const files = data.files || [];
              const videoCount = files.filter(f => f.mime_type?.startsWith('video/') || f.file_type === 'media').length;
              const documentCount = files.length - videoCount;
              
              stats[lesson.id] = { videoCount, documentCount };
            }
          } catch (err) {
            console.error(`Error loading files for lesson ${lesson.id}:`, err);
            stats[lesson.id] = { videoCount: 0, documentCount: 0 };
          }
        })
      );
      
      setLessonsFilesStats(stats);
    } catch (error) {
      console.error('Error loading lessons files stats:', error);
    }
  };

  // Загрузка ответов на упражнения для урока
  // Загрузка ответов на упражнения (как в челлендже - одним запросом)
  const loadExerciseResponses = async (lessonId) => {
    try {
      const response = await fetch(
        `${backendUrl}/api/student/exercise-responses/${lessonId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        const exerciseResponsesObj = data.exercise_responses || {};
        
        // Формируем объекты для состояния
        const responses = {};
        const responsesData = {};
        
        Object.keys(exerciseResponsesObj).forEach(exerciseId => {
          const responseData = exerciseResponsesObj[exerciseId];
          responses[exerciseId] = responseData.response_text || '';
          responsesData[exerciseId] = responseData;
        });
        
        setExerciseResponses(responses);
        setExerciseResponsesData(responsesData);
      }
    } catch (error) {
      console.error('Error loading exercise responses:', error);
    }
  };

  // Загрузка прогресса урока
  const loadLessonProgress = async (lessonId) => {
    try {
      const response = await fetch(
        `${backendUrl}/api/student/lesson-progress/${lessonId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setLessonProgress(data);
      }
    } catch (error) {
      console.error('Error loading lesson progress:', error);
    }
  };

  // Сохранение ответа на упражнение (как в челлендже)
  const saveExerciseResponse = async (lessonId, exerciseId, responseText) => {
    try {
      setSavingResponse(prev => ({ ...prev, [exerciseId]: true }));

      const response = await fetch(
        `${backendUrl}/api/student/exercise-response`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            lesson_id: lessonId,
            exercise_id: exerciseId,
            response_text: responseText
          })
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Обновляем локальное состояние
      setExerciseResponses(prev => ({
        ...prev,
        [exerciseId]: responseText
      }));

      // Перезагружаем ответы и прогресс (как в челлендже)
      await loadExerciseResponses(lessonId);
      await loadLessonProgress(lessonId);

      return data;
    } catch (error) {
      console.error('Error saving exercise response:', error);
      throw error;
    } finally {
      setSavingResponse(prev => ({ ...prev, [exerciseId]: false }));
    }
  };

  const startLesson = async (lesson) => {
    try {
      // Сначала загружаем прогресс, чтобы зафиксировать начало урока (если урок еще не начат)
      // Это создаст запись в базе данных с started_at
      await loadLessonProgress(lesson.id);
      
      const response = await fetch(`${backendUrl}/api/learning-v2/lessons/${lesson.id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setCurrentLesson(data.lesson);
      setCurrentSection('theory');
      
      // Загружаем ответы и прогресс для этого урока (обновляем после открытия)
      await loadExerciseResponses(lesson.id);
      await loadLessonProgress(lesson.id);
      
      // Загружаем прогресс челленджа и историю если есть
      if (data.lesson.challenge) {
        await loadChallengeProgress(lesson.id, data.lesson.challenge.id);
        await loadChallengeHistory(lesson.id, data.lesson.challenge.id);
      }
      
      // Загружаем историю тестов если есть
      if (data.lesson.quiz) {
        await loadQuizHistory(lesson.id);
      }
      
      // Загружаем статистику времени активности
      await loadTimeActivity(lesson.id);
      
      // Загружаем файлы урока
      await loadLessonFiles(lesson.id);
      
      // Загружаем статистику файлов студента
      await loadStudentFilesStats(lesson.id);
    } catch (error) {
      console.error('Error loading lesson:', error);
      setError('Ошибка загрузки урока');
    }
  };

  // Загрузка прогресса челленджа
  // Загрузка текущего прогресса челленджа
  const loadChallengeProgress = async (lessonId, challengeId) => {
    try {
      const response = await fetch(
        `${backendUrl}/api/student/challenge-progress/${lessonId}/${challengeId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setChallengeProgress(data);
        
        // Загружаем заметки в локальное состояние
        const notes = {};
        data.daily_notes.forEach(note => {
          notes[note.day] = note.note;
        });
        setChallengeNotes(notes);
      }
    } catch (error) {
      console.error('Error loading challenge progress:', error);
    }
  };

  // Загрузка истории всех попыток челленджа
  const loadChallengeHistory = async (lessonId, challengeId) => {
    try {
      const response = await fetch(
        `${backendUrl}/api/student/challenge-history/${lessonId}/${challengeId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setChallengeHistory(data.attempts || []);
      }
    } catch (error) {
      console.error('Error loading challenge history:', error);
    }
  };

  // Загрузка истории всех попыток теста
  const loadQuizHistory = async (lessonId) => {
    try {
      const response = await fetch(
        `${backendUrl}/api/student/quiz-attempts/${lessonId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        console.log('Quiz history loaded:', data);
        setQuizHistory(data.attempts || []);
        
        // Восстанавливаем состояние последней попытки теста
        if (data.attempts && data.attempts.length > 0) {
          const lastAttempt = data.attempts[0]; // Первая попытка - самая последняя (сортировка по убыванию)
          setQuizCompleted(true);
          setQuizScore(lastAttempt.score);
          console.log('Quiz state restored:', { score: lastAttempt.score, passed: lastAttempt.passed });
        }
      }
    } catch (error) {
      console.error('Error loading quiz history:', error);
    }
  };

  // Загрузка статистики времени активности
  const loadTimeActivity = async (lessonId) => {
    try {
      const response = await fetch(
        `${backendUrl}/api/student/time-activity/${lessonId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setTimeActivity({
          total_minutes: data.total_minutes || 0,
          total_points: data.total_points || 0
        });
        console.log('Time activity loaded:', data);
      }
    } catch (error) {
      console.error('Error loading time activity:', error);
    }
  };

  // Отправка времени активности на сервер
  const sendTimeActivity = async (lessonId, minutesSpent) => {
    try {
      const response = await fetch(
        `${backendUrl}/api/student/time-activity`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            lesson_id: lessonId,
            minutes_spent: minutesSpent
          })
        }
      );

      if (response.ok) {
        const data = await response.json();
        setTimeActivity({
          total_minutes: data.total_minutes,
          total_points: data.total_points
        });
        console.log('Time activity updated:', data);
      }
    } catch (error) {
      console.error('Error sending time activity:', error);
    }
  };

  // Загрузка файлов урока
  const loadLessonFiles = async (lessonId) => {
    try {
      const response = await fetch(
        `${backendUrl}/api/student/lesson-files/${lessonId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        const receipt = Array.isArray(data.files) ? data.files : [];
        
        const filesBySection = {
          theory: receipt.filter(f => f.section === 'theory'),
          exercises: receipt.filter(f => f.section === 'exercises'),
          challenge: receipt.filter(f => f.section === 'challenge'),
          quiz: receipt.filter(f => f.section === 'quiz')
        };

        const map = {};
        receipt.forEach(file => {
          if (file?.id) {
            map[file.id] = file;
          }
        });

        setLessonFiles(filesBySection);
        setLessonFileMap(map);
      } else if (response.status === 404) {
        setLessonFiles({ theory: [], exercises: [], challenge: [], quiz: [] });
        setLessonFileMap({});
      } else {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Error loading lesson files:', error);
      setLessonFiles({ theory: [], exercises: [], challenge: [], quiz: [] });
      setLessonFileMap({});
    }
  };

  // Загрузка статистики файлов студента
  const loadStudentFilesStats = async (lessonId) => {
    try {
      const response = await fetch(
        `${backendUrl}/api/student/my-files-stats/${lessonId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        // Убеждаемся, что files - это массив и все элементы имеют правильную структуру
        if (data && data.files && Array.isArray(data.files)) {
          const sanitizedFiles = data.files.map(file => ({
            file_id: file.file_id || file.id || '',
            file_name: file.file_name || file.original_name || '',
            mime_type: file.mime_type || '',
            section: file.section || '',
            views: typeof file.views === 'number' ? file.views : 0,
            downloads: typeof file.downloads === 'number' ? file.downloads : 0,
            video_stats: file.video_stats && typeof file.video_stats === 'object' ? {
              minutes_watched: typeof file.video_stats.minutes_watched === 'number' ? file.video_stats.minutes_watched : 0,
              points_earned: typeof file.video_stats.points_earned === 'number' ? file.video_stats.points_earned : 0
            } : null
          }));
          setStudentFilesStats({ ...data, files: sanitizedFiles });
        } else {
          setStudentFilesStats(data);
        }
      }
    } catch (error) {
      console.error('Error loading student files stats:', error);
    }
  };

  // Открытие файла на просмотр
  const handleViewFile = async (file) => {
    setViewingFile(file);
    setFileViewerOpen(true);
    
    // Отправляем событие просмотра
    try {
      await fetch(`${backendUrl}/api/student/file-analytics`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          file_id: file.id,
          lesson_id: currentLesson.id,
          action: 'view'
        })
      });
    } catch (error) {
      console.error('Error tracking file view:', error);
    }
  };

  // Закрытие просмотра файла
  const handleCloseFileViewer = () => {
    // Останавливаем трекинг видео
    if (videoWatchInterval) {
      clearInterval(videoWatchInterval);
      setVideoWatchInterval(null);
    }
    
    // Отправляем финальное время просмотра
    if (videoWatchStartTime && viewingFile?.mime_type?.startsWith('video/')) {
      const minutesWatched = Math.floor((Date.now() - videoWatchStartTime) / 60000);
      if (minutesWatched > 0) {
        sendVideoWatchTime(viewingFile.id, minutesWatched);
      }
    }
    
    setViewingFile(null);
    setFileViewerOpen(false);
    setIsFullscreen(false);
    setImageRotation(0);
    setVideoWatchStartTime(null);
  };

  // Отправка времени просмотра видео
  const sendVideoWatchTime = async (fileId, minutesWatched) => {
    try {
      await fetch(`${backendUrl}/api/student/video-watch-time`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          file_id: fileId,
          lesson_id: currentLesson.id,
          minutes_watched: minutesWatched
        })
      });
    } catch (error) {
      console.error('Error tracking video watch time:', error);
    }
  };

  // Скачивание файла
  const handleDownloadFile = async (file) => {
    try {
      // Отправляем событие скачивания
      try {
        await fetch(`${backendUrl}/api/student/file-analytics`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
            file_id: file.id,
            lesson_id: currentLesson.id,
            action: 'download'
          })
        });
      } catch (analyticsError) {
        console.error('Error tracking file download:', analyticsError);
      }
      
      // Скачиваем файл
      const response = await fetch(`${backendUrl}/api/download-file/${file.id}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Ошибка при скачивании файла');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = file.original_name;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading file:', error);
      alert('Ошибка при скачивании файла');
    }
  };

  // useEffect для отслеживания прокрутки (компактная навигация)
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // useEffect для трекинга видео
  useEffect(() => {
    if (fileViewerOpen && viewingFile?.mime_type?.startsWith('video/')) {
      setVideoWatchStartTime(Date.now());
      
      const interval = setInterval(() => {
        sendVideoWatchTime(viewingFile.id, 1);
      }, 60000);
      
      setVideoWatchInterval(interval);
      
      return () => {
        if (interval) {
          clearInterval(interval);
        }
      };
    }
  }, [fileViewerOpen, viewingFile]);

  // Таймер для отслеживания времени активности (каждую минуту отправляем данные)
  useEffect(() => {
    if (!currentLesson) return;

    // Запускаем таймер при открытии урока
    setActivityStartTime(Date.now());

    const interval = setInterval(() => {
      // Каждую минуту отправляем 1 минуту активности
      sendTimeActivity(currentLesson.id, 1);
    }, 60000); // 60000 мс = 1 минута

    // Очистка при размонтировании или смене урока
    return () => {
      clearInterval(interval);
      
      // При выходе из урока отправляем оставшееся время
      if (activityStartTime) {
        const elapsedMinutes = Math.floor((Date.now() - activityStartTime) / 60000);
        if (elapsedMinutes > 0) {
          sendTimeActivity(currentLesson.id, elapsedMinutes);
        }
      }
    };
  }, [currentLesson]);

  // Сохранение заметки челленджа
  const saveChallengeNote = async (lessonId, challengeId, day, note, completed = false) => {
    try {
      setSavingChallengeNote(prev => ({ ...prev, [day]: true }));

      const response = await fetch(
        `${backendUrl}/api/student/challenge-progress`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            lesson_id: lessonId,
            challenge_id: challengeId,
            day: day,
            note: note,
            completed: completed
          })
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Обновляем локальное состояние
      setChallengeNotes(prev => ({
        ...prev,
        [day]: note
      }));

      // Перезагружаем прогресс и историю
      await loadChallengeProgress(lessonId, challengeId);
      await loadChallengeHistory(lessonId, challengeId);
      await loadLessonProgress(lessonId);

      return data;
    } catch (error) {
      console.error('Error saving challenge note:', error);
      throw error;
    } finally {
      setSavingChallengeNote(prev => ({ ...prev, [day]: false }));
    }
  };

  // Сброс челленджа для повторного прохождения (создание новой попытки)
  const restartChallenge = async () => {
    try {
      console.log('Restarting challenge...');
      
      // Сбрасываем локальное состояние на пустой прогресс
      setChallengeProgress({
        current_day: 1,
        completed_days: [],
        daily_notes: [],
        is_completed: false,
        attempt_number: (challengeProgress?.total_attempts || 0) + 1,
        total_attempts: (challengeProgress?.total_attempts || 0) + 1,
        points_earned: 0,
        total_points: challengeProgress?.total_points || 0
      });
      
      // Очищаем заметки
      setChallengeNotes({});
      
      console.log('Challenge restarted successfully - new attempt ready');
    } catch (error) {
      console.error('Error restarting challenge:', error);
    }
  };

  // Функции для работы с тестом
  const startQuiz = () => {
    setQuizStarted(true);
    setCurrentQuestionIndex(0);
    setQuizAnswers({});
    setQuizCompleted(false);
    setQuizScore(0);
  };

  const handleQuizAnswer = (questionId, answer) => {
    setQuizAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  };

  const nextQuestion = () => {
    if (currentQuestionIndex < currentLesson.quiz.questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    }
  };

  const previousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  };

  const submitQuiz = async () => {
    try {
      // Подсчет правильных ответов
      let correctCount = 0;
      const questions = currentLesson.quiz.questions;
      
      questions.forEach(question => {
        const userAnswer = quizAnswers[question.id];
        if (userAnswer === question.correct_answer) {
          correctCount++;
        }
      });

      const score = Math.round((correctCount / questions.length) * 100);
      const passingScore = currentLesson.quiz.passing_score || 70;
      const passed = score >= passingScore;
      
      // Начисляем 10 баллов за прохождение теста
      const pointsEarned = passed ? 10 : 0;

      // Сохраняем результат в БД
      const response = await fetch(
        `${backendUrl}/api/student/quiz-attempt`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            lesson_id: currentLesson.id,
            quiz_id: currentLesson.quiz.id || currentLesson.id,
            score: score,
            passed: passed,
            answers: quizAnswers,
            points_earned: pointsEarned
          })
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Quiz result saved:', data);

      // Обновляем состояние с баллами
      setQuizScore(score);
      setQuizCompleted(true);
      
      // Сохраняем заработанные баллы
      if (data.points_earned) {
        // Можно сохранить в состояние для отображения
        console.log(`Earned ${data.points_earned} points for quiz!`);
      }

      // Обновляем прогресс урока и историю тестов
      await loadLessonProgress(currentLesson.id);
      await loadQuizHistory(currentLesson.id);

    } catch (error) {
      console.error('Error submitting quiz:', error);
      // Даже если сохранение не удалось, показываем результат
      // Пересчитываем score локально
      let localCorrectCount = 0;
      const questions = currentLesson.quiz.questions;
      questions.forEach(question => {
        const userAnswer = quizAnswers[question.id];
        if (userAnswer === question.correct_answer) {
          localCorrectCount++;
        }
      });
      const score = Math.round((localCorrectCount / questions.length) * 100);
      setQuizScore(score);
      setQuizCompleted(true);
    }
  };

  const restartQuiz = () => {
    setQuizStarted(false);
    setCurrentQuestionIndex(0);
    setQuizAnswers({});
    setQuizCompleted(false);
    setQuizScore(0);
  };

  const renderLessonCard = (lesson) => {
    const isCompleted = lesson.progress_data?.is_completed || lesson.completed || false;
    const isAccessible = lesson.level <= userLevel;
    const isLocked = !isAccessible;

    const progress = lesson.progress || lesson.progress_data || {};
    const theoryProgress = progress.theory_read_time || 0;
    const exercisesCompleted = progress.exercises_completed || 0;
    const challengeProgress = progress.challenge_progress || 0;
    
    // Общий прогресс урока
    const completionPercentage = lesson.progress_data?.completion_percentage || 0;
    
    // Проверяем, начат ли урок (есть ли started_at или есть какой-то прогресс)
    const isStarted = progress.started_at || progress.last_activity_at || completionPercentage > 0 || theoryProgress > 0 || exercisesCompleted > 0 || challengeProgress > 0;
    
    // Определяем, что не завершено
    const totalExercises = lesson.exercises?.length || 0;
    const theoryRead = progress.theory_read || false;
    const allExercisesCompleted = exercisesCompleted >= totalExercises;
    const challengeCompleted = progress.challenge_completed || false;
    const quizPassed = progress.quiz_passed || false;
    
    // Список незавершенных секций
    const incompleteSections = [];
    if (!theoryRead && lesson.theory && lesson.theory.length > 0) {
      incompleteSections.push({ type: 'theory', label: 'Теория не прочитана', icon: BookOpen });
    }
    if (!allExercisesCompleted && totalExercises > 0) {
      incompleteSections.push({ 
        type: 'exercises', 
        label: `Упражнения: ${exercisesCompleted}/${totalExercises}`, 
        icon: Brain 
      });
    }
    if (!challengeCompleted && lesson.challenge) {
      const challengeDays = lesson.challenge.duration_days || 0;
      const completedDays = progress.challenge_completed_days || 0;
      incompleteSections.push({ 
        type: 'challenge', 
        label: `Челлендж: ${completedDays}/${challengeDays} дней`, 
        icon: Calendar 
      });
    }
    if (!quizPassed && lesson.quiz) {
      incompleteSections.push({ 
        type: 'quiz', 
        label: 'Тест не пройден', 
        icon: Target 
      });
    }

    return (
      <Card key={lesson.id} className={`mb-6 border border-gray-200 bg-white shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden ${!isLocked ? 'ring-2 ring-blue-400 ring-opacity-50' : ''}`}>
        <CardHeader className="pb-4">
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <Badge className="bg-blue-50 text-blue-700 border border-blue-200 px-3 py-1">
                  Интерактивный урок
                </Badge>
                {lesson.points_required === 0 ? (
                  <Badge className="bg-green-50 text-green-700 border border-green-200 px-3 py-1">
                    Бесплатно
                  </Badge>
                ) : (
                  <Badge className="bg-orange-50 text-orange-700 border border-orange-200 px-3 py-1">
                    {lesson.points_required} баллов
                  </Badge>
                )}
                {!isLocked && !isCompleted && (
                  <Badge className="bg-green-100 text-green-800 px-3 py-1 animate-pulse">
                    🔓 ДОСТУПЕН
                  </Badge>
                )}
                {isCompleted && (
                  <Badge className="bg-green-100 text-green-800 px-3 py-1">
                    ✓ ЗАВЕРШЕН
                  </Badge>
                )}
              </div>

              <CardTitle className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                {lesson.title}
              </CardTitle>

              <CardDescription className="text-gray-600 dark:text-gray-300 text-sm sm:text-base leading-relaxed mb-4">
                {lesson.description}
              </CardDescription>

              {/* Прогресс урока */}
              {isAccessible && (theoryProgress > 0 || exercisesCompleted > 0 || challengeProgress > 0) && (
                <div className="bg-blue-50 rounded-lg p-3 border border-blue-100 mb-4">
                  <div className="text-sm font-medium text-blue-900 mb-2">Ваш прогресс:</div>
                  <div className="space-y-2">
                    {theoryProgress > 0 && (
                      <div className="flex justify-between text-xs">
                        <span>Теория прочитана</span>
                        <span>{Math.round(theoryProgress)} мин</span>
                      </div>
                    )}
                    {exercisesCompleted > 0 && (
                      <div className="flex justify-between text-xs">
                        <span>Упражнения выполнено</span>
                        <span>{exercisesCompleted}</span>
                      </div>
                    )}
                    {challengeProgress > 0 && (
                      <div className="flex justify-between text-xs">
                        <span>Челлендж</span>
                        <span>{challengeProgress}%</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="flex sm:flex-col items-center sm:items-end gap-2">
              <div className="p-3 bg-blue-50 rounded-xl border border-blue-100">
                <BookOpen className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-0 space-y-4">
          {/* Что включено */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-100">
            <h4 className="font-medium mb-3 text-gray-900 dark:text-gray-100 flex items-center">
              <BookOpen className="w-4 h-4 mr-2 text-blue-600" />
              Что включено в урок:
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="flex items-center">
                <BookOpen className="w-4 h-4 mr-2 text-blue-600 flex-shrink-0" />
                <span className="text-sm text-gray-700 dark:text-gray-300">{lesson.theory?.length || 0} блоков теории</span>
              </div>
              <div className="flex items-center">
                <Brain className="w-4 h-4 mr-2 text-blue-600 flex-shrink-0" />
                <span className="text-sm text-gray-700 dark:text-gray-300">{lesson.exercises?.length || 0} интерактивных упражнений</span>
              </div>
              {lesson.challenge && (
                <div className="flex items-center">
                  <Calendar className="w-4 h-4 mr-2 text-blue-600 flex-shrink-0" />
                  <span className="text-sm text-gray-700 dark:text-gray-300">{lesson.challenge.duration_days}-дневный челлендж</span>
                </div>
              )}
              {lesson.quiz && (
                <div className="flex items-center">
                  <Target className="w-4 h-4 mr-2 text-blue-600 flex-shrink-0" />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Тест ({lesson.quiz.questions?.length || 0} вопросов)</span>
                </div>
              )}
              {lesson.analytics_enabled && (
                <div className="flex items-center">
                  <BarChart3 className="w-4 h-4 mr-2 text-blue-600 flex-shrink-0" />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Персональная аналитика</span>
                </div>
              )}
              {lessonsFilesStats[lesson.id]?.videoCount > 0 && (
                <div className="flex items-center">
                  <Film className="w-4 h-4 mr-2 flex-shrink-0" style={{ color: 'rgb(16, 185, 129)' }} />
                  <span className="text-sm text-gray-700 dark:text-gray-300">{lessonsFilesStats[lesson.id].videoCount} видеофайлов</span>
                </div>
              )}
              {lessonsFilesStats[lesson.id]?.documentCount > 0 && (
                <div className="flex items-center">
                  <FileText className="w-4 h-4 mr-2 flex-shrink-0" style={{ color: 'rgb(239, 68, 68)' }} />
                  <span className="text-sm text-gray-700 dark:text-gray-300">{lessonsFilesStats[lesson.id].documentCount} документов</span>
                </div>
              )}
            </div>
          </div>

          {/* Общий прогресс урока */}
          {isAccessible && completionPercentage > 0 && (
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-4 border border-indigo-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-indigo-900">Общий прогресс урока</span>
                <span className="text-lg font-bold text-indigo-600">{Math.round(completionPercentage)}%</span>
              </div>
              <Progress value={completionPercentage} className="h-2.5" />
              <p className="text-xs text-indigo-700 mt-2">
                {completionPercentage === 100 ? '🎉 Урок полностью завершен!' : 
                 completionPercentage >= 75 ? 'Отличная работа! Вы почти у цели!' :
                 completionPercentage >= 50 ? 'Хороший прогресс! Продолжайте!' :
                 completionPercentage >= 25 ? 'Вы на правильном пути!' :
                 'Начните с изучения теории'}
              </p>
            </div>
          )}

          {/* Что нужно завершить для 100% */}
          {isAccessible && !isCompleted && incompleteSections.length > 0 && (
            <div className="bg-gradient-to-r from-orange-50 to-red-50 rounded-lg p-4 border border-orange-200">
              <h4 className="font-medium mb-3 text-orange-900 flex items-center">
                <Target className="w-4 h-4 mr-2 text-orange-600" />
                Для завершения урока на 100%:
              </h4>
              <div className="space-y-2">
                {incompleteSections.map((section, index) => {
                  const IconComponent = section.icon;
                  return (
                    <div key={index} className="flex items-center text-sm text-orange-800 bg-white/50 rounded-lg p-2">
                      <IconComponent className="w-4 h-4 mr-2 text-orange-600 flex-shrink-0" />
                      <span>{section.label}</span>
                    </div>
                  );
                })}
              </div>
              <p className="text-xs text-orange-700 mt-3">
                Завершите все секции, чтобы получить максимальные баллы!
              </p>
            </div>
          )}

          {/* Кнопка действия */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
            <div className="text-sm text-gray-500 flex items-center">
              <Trophy className="w-4 h-4 mr-1 text-blue-500 flex-shrink-0" />
              <span>Уровень {lesson.level} • {lesson.points_required} баллов опыта</span>
            </div>

            <Button
              size="lg"
              variant={isCompleted ? "outline" : "default"}
              disabled={isLocked}
              onClick={() => startLesson(lesson)}
              className={`${!isCompleted && !isLocked ? "bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-2.5 rounded-lg shadow-sm hover:shadow-md transition-all duration-200" : ""} w-full sm:w-auto`}
            >
              <PlayCircle className="w-5 h-5 mr-2" />
              {isLocked ? "Заблокирован" : 
               isCompleted || completionPercentage === 100 ? "Пройти урок заново" : 
               isStarted ? "Продолжить обучение" : 
               "Начать обучение"}
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderLessonContent = () => {
    if (!currentLesson) return null;

    return (
      <div className="space-y-6">
        {/* Навигация - фиксированная при прокрутке, компактная на мобильных */}
        <div className={`sticky top-0 z-40 bg-white shadow-md transition-all duration-300 ${isScrolled ? 'py-1' : 'py-0'}`}>
          <Card className="border-0 rounded-none">
            <CardHeader className={`transition-all duration-300 ${isScrolled ? 'py-2 px-3 md:py-3 md:px-6' : 'py-3 px-4 md:py-4 md:px-6'}`}>
              <div className="flex items-center justify-between flex-wrap gap-2 md:gap-3">
              <div className="flex items-center gap-2 md:gap-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentLesson(null)}
                  className={`flex items-center gap-1 md:gap-2 transition-all ${isScrolled ? 'h-7 px-2 text-xs md:h-9 md:px-3 md:text-sm' : 'h-9 px-3'}`}
                >
                  <ChevronLeft className={`${isScrolled ? 'w-3 h-3 md:w-4 md:h-4' : 'w-4 h-4'}`} />
                  <span className="hidden sm:inline">К списку уроков</span>
                  <span className="sm:hidden">Назад</span>
                </Button>
                <div className={`w-px bg-gray-300 ${isScrolled ? 'h-4 md:h-6' : 'h-6'}`}></div>
                <div>
                  <h2 className={`font-semibold transition-all ${isScrolled ? 'text-sm md:text-lg' : 'text-lg md:text-xl'}`}>
                    <span className="hidden sm:inline">{currentLesson.title}</span>
                    <span className="sm:hidden">{currentLesson.title.length > 20 ? currentLesson.title.substring(0, 20) + '...' : currentLesson.title}</span>
                  </h2>
                  <p className={`text-gray-600 transition-all ${isScrolled ? 'text-xs hidden md:block' : 'text-xs md:text-sm'}`}>
                    Уровень {currentLesson.level}
                  </p>
                </div>
              </div>

              {/* Навигация по разделам */}
              <div className="flex gap-1 md:gap-2 flex-wrap">
                <Button
                  variant={currentSection === 'theory' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setCurrentSection('theory')}
                  className={`flex items-center gap-1 md:gap-2 transition-all ${isScrolled ? 'h-7 px-2 text-xs md:h-9 md:px-3 md:text-sm' : 'h-9 px-3'}`}
                >
                  <BookOpen className={`${isScrolled ? 'w-3 h-3 md:w-4 md:h-4' : 'w-4 h-4'}`} />
                  <span className="hidden sm:inline">Теория</span>
                  <span className="sm:hidden">📖</span>
                </Button>
                <Button
                  variant={currentSection === 'exercises' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setCurrentSection('exercises')}
                  className={`flex items-center gap-1 md:gap-2 transition-all ${isScrolled ? 'h-7 px-2 text-xs md:h-9 md:px-3 md:text-sm' : 'h-9 px-3'}`}
                >
                  <Brain className={`${isScrolled ? 'w-3 h-3 md:w-4 md:h-4' : 'w-4 h-4'}`} />
                  <span className="hidden sm:inline">Упражнения</span>
                  <span className="sm:hidden">🧠</span>
                </Button>
                {currentLesson.challenge && (
                  <Button
                    variant={currentSection === 'challenge' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setCurrentSection('challenge')}
                    className={`flex items-center gap-1 md:gap-2 transition-all ${isScrolled ? 'h-7 px-2 text-xs md:h-9 md:px-3 md:text-sm' : 'h-9 px-3'}`}
                  >
                    <Calendar className={`${isScrolled ? 'w-3 h-3 md:w-4 md:h-4' : 'w-4 h-4'}`} />
                    <span className="hidden sm:inline">Челлендж</span>
                    <span className="sm:hidden">📅</span>
                  </Button>
                )}
                {currentLesson.quiz && (
                  <Button
                    variant={currentSection === 'quiz' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setCurrentSection('quiz')}
                    className={`flex items-center gap-1 md:gap-2 transition-all ${isScrolled ? 'h-7 px-2 text-xs md:h-9 md:px-3 md:text-sm' : 'h-9 px-3'}`}
                  >
                    <Target className={`${isScrolled ? 'w-3 h-3 md:w-4 md:h-4' : 'w-4 h-4'}`} />
                    <span className="hidden sm:inline">Тест</span>
                    <span className="sm:hidden">🎯</span>
                  </Button>
                )}
                {/* Кнопка "Файлы" */}
                {(lessonFiles.theory.length > 0 || lessonFiles.exercises.length > 0 || 
                  lessonFiles.challenge.length > 0 || lessonFiles.quiz.length > 0) && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      // Если не в теории, переключаемся на теорию
                      if (currentSection !== 'theory') {
                        setCurrentSection('theory');
                      }
                      // Прокручиваем к файлам через небольшую задержку
                      setTimeout(() => {
                        const filesSection = document.getElementById('files-section');
                        if (filesSection) {
                          filesSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }
                      }, 100);
                    }}
                    className={`flex items-center gap-1 md:gap-2 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-300 text-blue-700 hover:from-blue-100 hover:to-indigo-100 transition-all ${isScrolled ? 'h-7 px-2 text-xs md:h-9 md:px-3 md:text-sm' : 'h-9 px-3'}`}
                  >
                    <Upload className={`${isScrolled ? 'w-3 h-3 md:w-4 md:h-4' : 'w-4 h-4'}`} />
                    <span className="hidden sm:inline">Файлы</span>
                    <span className="sm:hidden">📁</span>
                  </Button>
                )}
                {currentLesson.analytics_enabled && (
                  <Button
                    variant={currentSection === 'analytics' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setCurrentSection('analytics')}
                    className={`flex items-center gap-1 md:gap-2 transition-all ${isScrolled ? 'h-7 px-2 text-xs md:h-9 md:px-3 md:text-sm' : 'h-9 px-3'}`}
                  >
                    <BarChart3 className={`${isScrolled ? 'w-3 h-3 md:w-4 md:h-4' : 'w-4 h-4'}`} />
                    <span className="hidden sm:inline">Аналитика</span>
                    <span className="sm:hidden">📊</span>
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
        </Card>
        </div>

        {/* Содержимое разделов */}
        {currentSection === 'theory' && renderTheorySection()}
        {currentSection === 'exercises' && renderExercisesSection()}
        {currentSection === 'challenge' && renderChallengeSection()}
        {currentSection === 'quiz' && renderQuizSection()}
        {currentSection === 'analytics' && renderAnalyticsSection()}
      </div>
    );
  };

  // Функция для подсчета файлов урока
  const getLessonFilesCount = (lessonId) => {
    const allFiles = [
      ...(lessonFiles.theory || []),
      ...(lessonFiles.exercises || []),
      ...(lessonFiles.challenge || []),
      ...(lessonFiles.quiz || [])
    ];
    
    const videoCount = allFiles.filter(f => f.mime_type?.startsWith('video/')).length;
    const documentCount = allFiles.filter(f => 
      f.extension === 'pdf' || 
      f.extension === 'doc' || 
      f.extension === 'docx' || 
      f.extension === 'xls' || 
      f.extension === 'xlsx' || 
      f.extension === 'txt'
    ).length;
    
    return { videoCount, documentCount };
  };

  // Функция для получения цвета и иконки файла
  const getFileStyle = (file) => {
    const ext = file.extension?.toLowerCase();
    
    // PDF - красный
    if (ext === 'pdf') {
      return {
        color: 'rgb(239, 68, 68)',
        bgColor: 'rgb(254, 226, 226)',
        icon: <FileText className="w-4 h-4" style={{ color: 'rgb(239, 68, 68)' }} />
      };
    }
    // Word - синий
    if (ext === 'doc' || ext === 'docx') {
      return {
        color: 'rgb(59, 130, 246)',
        bgColor: 'rgb(219, 234, 254)',
        icon: <FileText className="w-4 h-4" style={{ color: 'rgb(59, 130, 246)' }} />
      };
    }
    // Excel - зелёный
    if (ext === 'xls' || ext === 'xlsx') {
      return {
        color: 'rgb(34, 197, 94)',
        bgColor: 'rgb(220, 252, 231)',
        icon: <FileSpreadsheet className="w-4 h-4" style={{ color: 'rgb(34, 197, 94)' }} />
      };
    }
    // TXT - серый
    if (ext === 'txt') {
      return {
        color: 'rgb(107, 114, 128)',
        bgColor: 'rgb(243, 244, 246)',
        icon: <FileText className="w-4 h-4" style={{ color: 'rgb(107, 114, 128)' }} />
      };
    }
    // Видео - зелёный (мягкий)
    if (file.mime_type?.startsWith('video/')) {
      return {
        color: 'rgb(16, 185, 129)',
        bgColor: 'rgb(209, 250, 229)',
        icon: <Film className="w-4 h-4" style={{ color: 'rgb(16, 185, 129)' }} />
      };
    }
    // Изображения - розовый
    if (file.mime_type?.startsWith('image/')) {
      return {
        color: 'rgb(236, 72, 153)',
        bgColor: 'rgb(252, 231, 243)',
        icon: <Image className="w-4 h-4" style={{ color: 'rgb(236, 72, 153)' }} />
      };
    }
    // По умолчанию - синий
    return {
      color: 'rgb(59, 130, 246)',
      bgColor: 'rgb(219, 234, 254)',
      icon: <FileText className="w-4 h-4" style={{ color: 'rgb(59, 130, 246)' }} />
    };
  };

  // Рендеринг файлов для раздела
  const renderFilesSection = (sectionName) => {
    const files = lessonFiles[sectionName] || [];
    
    if (files.length === 0) return null;
    
    return (
      <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Upload className="w-5 h-5 text-blue-600" />
          Файлы и материалы ({files.length})
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3" id="files-section">
          {files.map((file) => {
            const fileStyle = getFileStyle(file);
            return (
              <div 
                key={file.id} 
                className="bg-white p-4 rounded-lg border-2 hover:shadow-lg transition-all"
                style={{ borderColor: fileStyle.color }}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <div 
                        className="p-2 rounded-lg flex-shrink-0"
                        style={{ backgroundColor: fileStyle.bgColor }}
                      >
                        {fileStyle.icon}
                      </div>
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{file.original_name}</p>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge 
                        variant="outline" 
                        className="text-xs border-0"
                        style={{ 
                          backgroundColor: fileStyle.bgColor,
                          color: fileStyle.color
                        }}
                      >
                        {file.extension?.toUpperCase()}
                      </Badge>
                      <span className="text-xs text-gray-500">
                        {(file.file_size / 1024 / 1024).toFixed(2)} МБ
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={() => handleViewFile(file)}
                    className="flex-1 text-white"
                    style={{ 
                      backgroundColor: fileStyle.color,
                      borderColor: fileStyle.color
                    }}
                  >
                    <Eye className="w-4 h-4 mr-1" />
                    Просмотр
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDownloadFile(file)}
                    className="flex-1"
                    style={{ 
                      borderColor: fileStyle.color,
                      color: fileStyle.color
                    }}
                  >
                    <Download className="w-4 h-4 mr-1" />
                    Скачать
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderTheorySection = () => {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-blue-600" />
            Теоретическая часть
          </CardTitle>
          <CardDescription>
            Изучите основы материала перед выполнением практических заданий
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {currentLesson.theory?.map((block, index) => (
            <div key={block.id} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">{block.title}</h3>
              <div className="prose prose-gray dark:prose-invert max-w-none">
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
                  {block.content}
                </p>
              </div>

            </div>
          ))}

          {/* Файлы для теории */}
          {renderFilesSection('theory')}

          <div className="flex justify-end mt-6">
            <Button
              onClick={() => setCurrentSection('exercises')}
              className="flex items-center gap-2"
            >
              Перейти к упражнениям
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderExercisesSection = () => {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-green-600" />
            Практические упражнения
          </CardTitle>
          <CardDescription>
            Примените полученные знания на практике
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {currentLesson.exercises?.map((exercise, index) => {
            // Определяем статус упражнения
            const responseData = exerciseResponsesData[exercise.id];
            const isReviewed = responseData?.reviewed || false;
            const pointsEarned = responseData?.points_earned || 0;
            const hasResponse = !!exerciseResponses[exercise.id];
            
            // Определяем цвет границы и фона в зависимости от статуса
            let borderColor = 'border-gray-200';
            let bgColor = 'bg-white';
            let statusBadge = null;
            
            if (isReviewed) {
              if (pointsEarned > 0) {
                // Упражнение проверено и выполнено правильно - зелёный
                borderColor = 'border-green-500';
                bgColor = 'bg-green-50';
                statusBadge = (
                  <Badge className="bg-green-600 text-white ml-2">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    Выполнено правильно
                  </Badge>
                );
              } else {
                // Упражнение проверено, но не выполнено правильно - красный
                borderColor = 'border-red-500';
                bgColor = 'bg-red-50';
                statusBadge = (
                  <Badge className="bg-red-600 text-white ml-2">
                    <X className="w-3 h-3 mr-1" />
                    Требует доработки
                  </Badge>
                );
              }
            } else if (hasResponse) {
              // Упражнение отправлено, но не проверено - жёлтый
              borderColor = 'border-yellow-500';
              bgColor = 'bg-yellow-50';
              statusBadge = (
                <Badge className="bg-yellow-600 text-white ml-2">
                  <Clock className="w-3 h-3 mr-1" />
                  Ожидает проверки
                </Badge>
              );
            }
            
            return (
            <div key={exercise.id} className={`border-2 ${borderColor} ${bgColor} rounded-lg p-6 transition-all duration-300`}>
              <div className="flex items-start justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{exercise.title}</h3>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="ml-2">
                    {exercise.type === 'text' ? 'Текст' :
                     exercise.type === 'multiple_choice' ? 'Выбор' :
                     exercise.type === 'calculation' ? 'Расчет' : 'Рефлексия'}
                  </Badge>
                  {statusBadge}
                </div>
              </div>

              <div className="mb-4">
                <p className="text-gray-700 mb-2"><strong>Задание:</strong></p>
                <p className="text-gray-600 whitespace-pre-line">{exercise.description}</p>
              </div>

              <div className="mb-4">
                <p className="text-gray-700 mb-2"><strong>Инструкции:</strong></p>
                <p className="text-gray-600 whitespace-pre-line">{exercise.instructions}</p>
              </div>

              {/* Форма для ответа */}
              <div className="bg-gray-50 rounded-lg p-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Ваш ответ:
                </label>
                {exercise.type === 'multiple_choice' && exercise.options ? (
                  <div className="space-y-2">
                    {exercise.options.map((option, idx) => (
                      <label key={idx} className="flex items-center">
                        <input
                          type="radio"
                          name={`exercise-${exercise.id}`}
                          value={option}
                          checked={exerciseResponses[exercise.id] === option}
                          onChange={(e) => {
                            setExerciseResponses(prev => ({
                              ...prev,
                              [exercise.id]: e.target.value
                            }));
                          }}
                          className="mr-2"
                        />
                        {option}
                      </label>
                    ))}
                  </div>
                ) : (
                  <textarea
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows={4}
                    placeholder="Введите ваш ответ здесь..."
                    value={exerciseResponses[exercise.id] || ''}
                    onChange={(e) => {
                      setExerciseResponses(prev => ({
                        ...prev,
                        [exercise.id]: e.target.value
                      }));
                    }}
                  />
                )}

                <Button 
                  className="mt-3" 
                  size="sm"
                  onClick={() => saveExerciseResponse(currentLesson.id, exercise.id, exerciseResponses[exercise.id] || '')}
                  disabled={savingResponse[exercise.id]}
                >
                  {savingResponse[exercise.id] ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Сохранение...
                    </>
                  ) : exerciseResponses[exercise.id] ? (
                    <>
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Обновить ответ
                    </>
                  ) : (
                    'Отправить ответ'
                  )}
                </Button>
                
                {exerciseResponses[exercise.id] && (
                  <p className="text-xs text-green-600 mt-2">
                    ✓ Ответ сохранен
                  </p>
                )}
              </div>

              {/* Комментарий администратора */}
              {exerciseResponsesData[exercise.id]?.reviewed && exerciseResponsesData[exercise.id]?.admin_comment && (
                <div className={`mt-4 p-4 rounded-lg border-2 ${
                  pointsEarned > 0 
                    ? 'bg-green-100 border-green-300' 
                    : 'bg-red-100 border-red-300'
                }`}>
                  <p className={`text-sm font-semibold mb-2 ${
                    pointsEarned > 0 ? 'text-green-900' : 'text-red-900'
                  }`}>
                    💬 Комментарий преподавателя:
                  </p>
                  <p className={`text-sm whitespace-pre-wrap ${
                    pointsEarned > 0 ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {exerciseResponsesData[exercise.id].admin_comment}
                  </p>
                  {pointsEarned > 0 && (
                    <p className="text-xs text-green-700 mt-2 font-semibold">
                      ✓ Начислено баллов: {pointsEarned}
                    </p>
                  )}
                  {exerciseResponsesData[exercise.id].reviewed_at && (
                    <p className={`text-xs mt-2 ${
                      pointsEarned > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      Проверено: {new Date(exerciseResponsesData[exercise.id].reviewed_at).toLocaleString('ru-RU')}
                    </p>
                  )}
                </div>
              )}

              {exercise.expected_outcome && (
                <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-sm text-blue-800">
                    <strong>Ожидаемый результат:</strong> {exercise.expected_outcome}
                  </p>
                </div>
              )}
            </div>
            );
          })}

          <div className="flex justify-between items-center">
            <Button
              variant="outline"
              onClick={() => setCurrentSection('theory')}
              className="flex items-center gap-2"
            >
              <ChevronLeft className="w-4 h-4" />
              Назад к теории
            </Button>

            <div className="flex gap-2">
              <Button
                variant="destructive"
                onClick={async () => {
                  if (window.confirm('Вы уверены, что хотите пройти урок заново? Это удалит ваши ответы на упражнения и прогресс урока. История тестов и челленджей сохранится.')) {
                    try {
                      const response = await fetch(
                        `${backendUrl}/api/student/reset-lesson/${currentLesson.id}`,
                        {
                          method: 'DELETE',
                          headers: {
                            'Authorization': `Bearer ${localStorage.getItem('token')}`,
                            'Content-Type': 'application/json'
                          }
                        }
                      );
                      
                      if (response.ok) {
                        // Перезагружаем урок
                        await startLesson(currentLesson);
                        setCurrentSection('theory');
                        alert('Прогресс урока сброшен! Вы можете начать заново.');
                      } else {
                        alert('Ошибка при сбросе прогресса');
                      }
                    } catch (error) {
                      console.error('Error resetting lesson:', error);
                      alert('Ошибка при сбросе прогресса');
                    }
                  }
                }}
                className="flex items-center gap-2"
              >
                <PlayCircle className="w-4 h-4" />
                Пройти урок заново
            </Button>

            {currentLesson.challenge ? (
              <Button
                onClick={() => setCurrentSection('challenge')}
                className="flex items-center gap-2"
              >
                Перейти к челленджу
                <ChevronRight className="w-4 h-4" />
              </Button>
            ) : currentLesson.quiz ? (
              <Button
                onClick={() => setCurrentSection('quiz')}
                className="flex items-center gap-2"
              >
                Перейти к тесту
                <ChevronRight className="w-4 h-4" />
              </Button>
            ) : (
              <Button
                onClick={() => setCurrentSection('analytics')}
                className="flex items-center gap-2"
              >
                Перейти к аналитике
                <ChevronRight className="w-4 h-4" />
              </Button>
            )}
          </div>
          </div>
          
          {/* Файлы для упражнений */}
          {renderFilesSection('exercises')}
        </CardContent>
      </Card>
    );
  };

  const renderChallengeSection = () => {
    const completedDays = challengeProgress?.completed_days || [];
    const isCompleted = challengeProgress?.is_completed || false;
    const attemptNumber = challengeProgress?.attempt_number || 1;
    const totalAttempts = challengeProgress?.total_attempts || 0;
    const pointsEarned = challengeProgress?.points_earned || 0;
    const totalPoints = challengeProgress?.total_points || 0;

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-purple-600" />
            Ежедневный челлендж
          </CardTitle>
          <CardDescription>
            {currentLesson.challenge?.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Статистика попыток и баллов */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <div className="text-sm text-blue-700 mb-1">Попытка</div>
              <div className="text-2xl font-bold text-blue-900">#{attemptNumber}</div>
              <div className="text-xs text-blue-600 mt-1">Всего: {totalAttempts}</div>
            </div>
            
            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <div className="text-sm text-green-700 mb-1">Баллы (текущая)</div>
              <div className="text-2xl font-bold text-green-900">{pointsEarned}</div>
              <div className="text-xs text-green-600 mt-1">
                {currentLesson.challenge?.points_per_day || 10} за день
              </div>
            </div>
            
            <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
              <div className="text-sm text-yellow-700 mb-1">Всего баллов</div>
              <div className="text-2xl font-bold text-yellow-900">{totalPoints}</div>
              <div className="text-xs text-yellow-600 mt-1">За все попытки</div>
            </div>
          </div>

          <div className="text-center bg-purple-50 p-4 rounded-lg">
            <div className="text-3xl font-bold text-purple-600 mb-2">
              {completedDays.length} / {currentLesson.challenge?.duration_days} дней
            </div>
            <p className="text-gray-600">
              {isCompleted ? '🎉 Челлендж завершен!' : 'Продолжайте выполнять задания'}
            </p>
            <Progress 
              value={(completedDays.length / currentLesson.challenge?.duration_days) * 100} 
              className="mt-3"
            />
          </div>

          <div className="space-y-4">
            {currentLesson.challenge?.daily_tasks?.map((day) => {
              const isDayCompleted = completedDays.includes(day.day);
              const dayNote = challengeNotes[day.day] || '';
              
              return (
                <div 
                  key={day.day} 
                  className={`border rounded-lg p-4 ${
                    isDayCompleted ? 'border-green-300 bg-green-50' : 'border-gray-200'
                  }`}
                >
                <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold text-lg">День {day.day}: {day.title}</h4>
                    <Badge variant={isDayCompleted ? "default" : "outline"} className={isDayCompleted ? 'bg-green-600' : ''}>
                      {isDayCompleted ? "✓ Выполнено" : "В процессе"}
                  </Badge>
                </div>

                  {day.description && (
                <div className="mb-3">
                  <p className="text-gray-700 mb-2"><strong>Описание:</strong></p>
                  <p className="text-gray-600">{day.description}</p>
                </div>
                  )}

                  <div className="mb-4">
                  <p className="text-gray-700 mb-2"><strong>Задачи:</strong></p>
                  <ul className="list-disc list-inside text-gray-600 space-y-1">
                    {day.tasks.map((task, idx) => (
                      <li key={idx}>{task}</li>
                    ))}
                  </ul>
                </div>

                  {/* Поле для заметок */}
                  <div className="bg-white rounded-lg p-4 border border-gray-200 mb-3">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      📝 Ваши заметки и наблюдения:
                    </label>
                    <textarea
                      className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      rows={4}
                      placeholder="Запишите свои мысли, наблюдения и результаты выполнения задач..."
                      value={dayNote}
                      onChange={(e) => {
                        setChallengeNotes(prev => ({
                          ...prev,
                          [day.day]: e.target.value
                        }));
                      }}
                    />
                    <div className="flex gap-2 mt-2">
                      <Button 
                        size="sm"
                        variant="outline"
                        onClick={() => saveChallengeNote(
                          currentLesson.id, 
                          currentLesson.challenge.id, 
                          day.day, 
                          dayNote,
                          false
                        )}
                        disabled={savingChallengeNote[day.day]}
                        className="flex-1"
                      >
                        {savingChallengeNote[day.day] ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-600 mr-2"></div>
                            Сохранение...
                          </>
                        ) : (
                          <>💾 Сохранить заметку</>
                        )}
                      </Button>
                      
                      {!isDayCompleted && dayNote && (
                        <Button 
                          size="sm"
                          onClick={() => saveChallengeNote(
                            currentLesson.id, 
                            currentLesson.challenge.id, 
                            day.day, 
                            dayNote,
                            true
                          )}
                          disabled={savingChallengeNote[day.day]}
                          className="flex-1 bg-green-600 hover:bg-green-700"
                        >
                          ✓ Отметить выполненным
                  </Button>
                )}
              </div>
                    
                    {dayNote && !savingChallengeNote[day.day] && (
                      <p className="text-xs text-green-600 mt-2">
                        ✓ Заметка сохранена
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {isCompleted && (
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-6 rounded-lg border border-green-200">
              <div className="text-center mb-4">
                <div className="text-4xl mb-3">🎉</div>
                <h3 className="text-xl font-bold text-green-800 mb-2">
                  Поздравляем! Вы завершили челлендж!
                </h3>
                <p className="text-green-700 mb-2">
                  Вы успешно прошли все {currentLesson.challenge?.duration_days} дней челленджа
                </p>
                <div className="bg-white rounded-lg p-4 mt-4 inline-block">
                  <div className="text-sm text-gray-600 mb-1">Заработано баллов:</div>
                  <div className="text-3xl font-bold text-green-600">
                    +{pointsEarned} 🌟
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    ({completedDays.length} дней × {currentLesson.challenge?.points_per_day || 10} + бонус {currentLesson.challenge?.bonus_points || 50})
                  </div>
                </div>
              </div>
              <div className="flex justify-center gap-3">
                <Button
                  variant="outline"
                  onClick={restartChallenge}
                  className="flex items-center gap-2 border-green-600 text-green-700 hover:bg-green-100"
                >
                  <Calendar className="w-4 h-4" />
                  Пройти челлендж заново
                </Button>
              </div>
              <p className="text-center text-xs text-green-600 mt-3">
                💡 Пройдите челлендж снова, чтобы заработать еще больше баллов!
              </p>
            </div>
          )}

          <div className="flex justify-between">
            <Button
              variant="outline"
              onClick={() => setCurrentSection('exercises')}
              className="flex items-center gap-2"
            >
              <ChevronLeft className="w-4 h-4" />
              Назад к упражнениям
            </Button>

            {currentLesson.quiz ? (
              <Button
                onClick={() => setCurrentSection('quiz')}
                className="flex items-center gap-2"
              >
                Перейти к тесту
                <ChevronRight className="w-4 h-4" />
              </Button>
            ) : (
              <Button
                onClick={() => setCurrentSection('analytics')}
                className="flex items-center gap-2"
              >
                Перейти к аналитике
                <ChevronRight className="w-4 h-4" />
              </Button>
            )}
          </div>
          
          {/* Файлы для челленджа */}
          {renderFilesSection('challenge')}
        </CardContent>
      </Card>
    );
  };

  const renderQuizSection = () => {
    if (!currentLesson.quiz || !currentLesson.quiz.questions || currentLesson.quiz.questions.length === 0) {
      return (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-red-600" />
              Тест на знания
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Alert>
              <AlertDescription>
                Тест для этого урока пока не добавлен.
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      );
    }

    // Если тест завершен - показываем результаты
    if (quizCompleted) {
      const passingScore = currentLesson.quiz.passing_score || 70;
      const passed = quizScore >= passingScore;

      return (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-red-600" />
              Результаты теста
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="text-center">
              <div className={`text-6xl font-bold mb-4 ${passed ? 'text-green-600' : 'text-red-600'}`}>
                {quizScore}%
              </div>
              {passed ? (
                <div className="flex flex-col items-center gap-2">
                  <CheckCircle className="w-16 h-16 text-green-600" />
                  <p className="text-xl font-semibold text-green-900">Тест пройден!</p>
                  <p className="text-gray-600">Отличная работа! Вы успешно усвоили материал.</p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <Target className="w-16 h-16 text-red-600" />
                  <p className="text-xl font-semibold text-red-900">Тест не пройден</p>
                  <p className="text-gray-600">Проходной балл: {passingScore}%. Попробуйте еще раз!</p>
                </div>
              )}
            </div>

            <div className="bg-gray-50 rounded-lg p-6">
              <h4 className="font-semibold mb-4">Детальные результаты:</h4>
              <div className="space-y-3">
                {currentLesson.quiz.questions.map((question, index) => {
                  const userAnswer = quizAnswers[question.id];
                  const isCorrect = userAnswer === question.correct_answer;
                  
                  return (
                    <div key={question.id} className={`p-4 rounded-lg border ${isCorrect ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                      <div className="flex items-start gap-3">
                        {isCorrect ? (
                          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-1" />
                        ) : (
                          <Target className="w-5 h-5 text-red-600 flex-shrink-0 mt-1" />
                        )}
                        <div className="flex-1">
                          <p className="font-medium mb-2">{index + 1}. {question.question}</p>
                          <p className="text-sm text-gray-600">Ваш ответ: {userAnswer || 'Не отвечено'}</p>
                          {!isCorrect && (
                            <p className="text-sm text-green-700 mt-1">Правильный ответ: {question.correct_answer}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="flex justify-center gap-4">
              <Button onClick={restartQuiz} variant="outline">
                Пройти тест заново
              </Button>
              <Button onClick={() => setCurrentSection('analytics')}>
                Перейти к аналитике
              </Button>
            </div>
          </CardContent>
        </Card>
      );
    }

    // Если тест не начат - показываем стартовую страницу
    if (!quizStarted) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5 text-red-600" />
            Тест на знания
          </CardTitle>
          <CardDescription>
            {currentLesson.quiz?.description || "Проверьте свои знания"}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-red-600 mb-2">
                {currentLesson.quiz.questions.length}
            </div>
            <p className="text-gray-600">вопросов для проверки</p>
            <p className="text-sm text-gray-500 mt-1">
                Проходной балл: {currentLesson.quiz.passing_score || 70}%
            </p>
          </div>

          <Alert>
            <Target className="h-4 w-4" />
            <AlertDescription>
              Тест поможет вам закрепить полученные знания и получить персональные рекомендации.
            </AlertDescription>
          </Alert>

          <div className="text-center">
              <Button size="lg" className="px-8 py-3" onClick={startQuiz}>
              Начать тест
            </Button>
          </div>

          <div className="flex justify-between">
            {currentLesson.challenge ? (
              <Button
                variant="outline"
                onClick={() => setCurrentSection('challenge')}
                className="flex items-center gap-2"
              >
                <ChevronLeft className="w-4 h-4" />
                Назад к челленджу
              </Button>
            ) : (
              <Button
                variant="outline"
                onClick={() => setCurrentSection('exercises')}
                className="flex items-center gap-2"
              >
                <ChevronLeft className="w-4 h-4" />
                Назад к упражнениям
              </Button>
            )}

            <Button
              onClick={() => setCurrentSection('analytics')}
              className="flex items-center gap-2"
            >
              Перейти к аналитике
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
          </CardContent>
        </Card>
      );
    }

    // Прохождение теста - показываем текущий вопрос
    const currentQuestion = currentLesson.quiz.questions[currentQuestionIndex];
    const totalQuestions = currentLesson.quiz.questions.length;
    const progress = ((currentQuestionIndex + 1) / totalQuestions) * 100;
    const allQuestionsAnswered = currentLesson.quiz.questions.every(q => quizAnswers[q.id]);

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Target className="w-5 h-5 text-red-600" />
              Вопрос {currentQuestionIndex + 1} из {totalQuestions}
            </span>
            <Badge variant="outline">
              {Object.keys(quizAnswers).length} / {totalQuestions} отвечено
            </Badge>
          </CardTitle>
          <Progress value={progress} className="mt-2" />
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
            <h3 className="text-lg font-semibold mb-4 text-gray-900">
              {currentQuestion.question}
            </h3>

            <div className="space-y-3">
              {currentQuestion.options.map((option, index) => {
                const isSelected = quizAnswers[currentQuestion.id] === option;
                
                return (
                  <button
                    key={index}
                    onClick={() => handleQuizAnswer(currentQuestion.id, option)}
                    className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                      isSelected
                        ? 'border-blue-500 bg-blue-100'
                        : 'border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                        isSelected ? 'border-blue-500 bg-blue-500' : 'border-gray-300'
                      }`}>
                        {isSelected && <CheckCircle className="w-4 h-4 text-white" />}
                      </div>
                      <span className="font-medium">{option}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="flex justify-between items-center">
            <Button
              variant="outline"
              onClick={previousQuestion}
              disabled={currentQuestionIndex === 0}
              className="flex items-center gap-2"
            >
              <ChevronLeft className="w-4 h-4" />
              Предыдущий
            </Button>

            {currentQuestionIndex === totalQuestions - 1 ? (
              <Button
                onClick={submitQuiz}
                disabled={!allQuestionsAnswered}
                className="flex items-center gap-2 bg-green-600 hover:bg-green-700"
              >
                Завершить тест
                <CheckCircle className="w-4 h-4" />
              </Button>
            ) : (
              <Button
                onClick={nextQuestion}
                className="flex items-center gap-2"
              >
                Следующий
                <ChevronRight className="w-4 h-4" />
              </Button>
            )}
          </div>

          {!allQuestionsAnswered && currentQuestionIndex === totalQuestions - 1 && (
            <Alert>
              <AlertDescription>
                Ответьте на все вопросы перед завершением теста.
              </AlertDescription>
            </Alert>
          )}
          
          {/* Файлы для теста */}
          {renderFilesSection('quiz')}
        </CardContent>
      </Card>
    );
  };

  const renderAnalyticsSection = () => {
    // Подсчет статистики по текущему уроку
    const totalExercises = currentLesson.exercises?.length || 0;
    const completedExercises = Object.keys(exerciseResponses).filter(id => exerciseResponses[id]).length;
    const exerciseProgress = totalExercises > 0 ? Math.round((completedExercises / totalExercises) * 100) : 0;

    const hasChallenge = currentLesson.challenge && currentLesson.challenge.days?.length > 0;
    const challengeDays = currentLesson.challenge?.days?.length || 0;
    const completedChallengeDays = challengeProgress?.completed_days?.length || 0;
    const challengeProgressPercent = challengeDays > 0 ? Math.round((completedChallengeDays / challengeDays) * 100) : 0;

    const hasQuiz = currentLesson.quiz && currentLesson.quiz.questions?.length > 0;
    const quizPassed = quizCompleted && quizScore >= (currentLesson.quiz?.passing_score || 70);

    const overallProgress = lessonProgress?.completion_percentage || 0;

    // Подсчет комментариев от преподавателя
    const reviewedExercises = Object.values(exerciseResponsesData).filter(r => r?.reviewed && r?.admin_comment).length;
    
    // Проверка загрузки данных
    const isLoadingStats = !studentFilesStats && lessonFiles.theory.length === 0;

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-indigo-600" />
            Ваш прогресс по уроку
          </CardTitle>
          <CardDescription>
            Детальная статистика вашего обучения
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Индикатор загрузки */}
          {isLoadingStats && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
              <div className="flex items-center justify-center gap-3">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                <p className="text-blue-700 font-medium">Загрузка статистики...</p>
              </div>
            </div>
          )}
          {/* Общий прогресс */}
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-6 border border-indigo-200">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-semibold text-indigo-900 text-lg">Общий прогресс урока</h4>
              <div className="text-3xl font-bold text-indigo-600">{overallProgress}%</div>
            </div>
            <Progress value={overallProgress} className="h-3" />
            <p className="text-sm text-indigo-700 mt-2">
              {overallProgress === 100 ? '🎉 Урок полностью завершен!' : 
               overallProgress >= 75 ? 'Отличная работа! Вы почти у цели!' :
               overallProgress >= 50 ? 'Хороший прогресс! Продолжайте в том же духе!' :
               overallProgress >= 25 ? 'Вы на правильном пути!' :
               'Начните с изучения теории и выполнения упражнений'}
            </p>
          </div>

          {/* Общие заработанные баллы */}
          <div className="bg-gradient-to-r from-yellow-50 via-amber-50 to-orange-50 rounded-lg p-6 border-2 border-yellow-300 shadow-lg">
            <h4 className="font-semibold text-yellow-900 text-lg mb-4 flex items-center gap-2">
              <Trophy className="w-6 h-6 text-yellow-600" />
              Заработанные баллы
              </h4>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              {/* Баллы за челленджи */}
              {challengeHistory.length > 0 && (
                <div className="bg-white rounded-lg p-4 border border-yellow-200">
                  <div className="flex items-center gap-2 mb-2">
                    <Calendar className="w-5 h-5 text-orange-600" />
                    <p className="text-sm font-medium text-gray-700">Челленджи</p>
            </div>
                  <p className="text-3xl font-bold text-orange-600">
                    {challengeHistory.reduce((sum, a) => sum + (a.points_earned || 0), 0)} 🌟
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    {challengeHistory.filter(a => a.is_completed).length} завершено
                  </p>
                </div>
              )}
              
              {/* Баллы за тесты */}
              {quizHistory.length > 0 && (
                <div className="bg-white rounded-lg p-4 border border-purple-200">
                  <div className="flex items-center gap-2 mb-2">
                    <Target className="w-5 h-5 text-purple-600" />
                    <p className="text-sm font-medium text-gray-700">Тесты</p>
                  </div>
                  <p className="text-3xl font-bold text-purple-600">
                    {quizHistory.reduce((sum, a) => sum + (a.points_earned || 0), 0)} 🎯
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    {quizHistory.filter(a => a.passed).length} пройдено
                  </p>
                </div>
              )}
              
              {/* Баллы за время активности */}
              <div className="bg-white rounded-lg p-4 border border-blue-200">
                <div className="flex items-center gap-2 mb-2">
                  <Clock className="w-5 h-5 text-blue-600" />
                  <p className="text-sm font-medium text-gray-700">Активность</p>
                </div>
                <p className="text-3xl font-bold text-blue-600">
                  {timeActivity.total_points} ⏱️
                </p>
                <p className="text-xs text-gray-600 mt-1">
                  {timeActivity.total_minutes} минут
                </p>
              </div>
              
              {/* Баллы за видео */}
              {studentFilesStats && studentFilesStats.summary.total_video_points > 0 && (
                <div className="bg-white rounded-lg p-4 border border-pink-200">
                  <div className="flex items-center gap-2 mb-2">
                    <Eye className="w-5 h-5 text-pink-600" />
                    <p className="text-sm font-medium text-gray-700">Видео</p>
                  </div>
                  <p className="text-3xl font-bold text-pink-600">
                    {studentFilesStats.summary.total_video_points} 🎬
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    {studentFilesStats.summary.total_video_minutes} минут
                  </p>
                </div>
              )}
              
              {/* Общая сумма */}
              <div className="bg-gradient-to-br from-yellow-400 to-orange-400 rounded-lg p-4 border-2 border-yellow-500 text-white">
                <div className="flex items-center gap-2 mb-2">
                  <Trophy className="w-5 h-5" />
                  <p className="text-sm font-medium">Всего</p>
                </div>
                <p className="text-4xl font-bold">
                  {(challengeHistory.reduce((sum, a) => sum + (a.points_earned || 0), 0) +
                    quizHistory.reduce((sum, a) => sum + (a.points_earned || 0), 0) +
                    timeActivity.total_points +
                    (studentFilesStats?.summary.total_video_points || 0))} ⭐
                </p>
                <p className="text-xs mt-1 opacity-90">
                  Общий результат
                </p>
              </div>
            </div>
          </div>

          {/* Статистика по разделам */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Упражнения */}
            <div className="bg-green-50 rounded-lg p-5 border border-green-200">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Brain className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h5 className="font-semibold text-green-900">Упражнения</h5>
                  <p className="text-sm text-green-700">{completedExercises} из {totalExercises}</p>
                </div>
              </div>
              <Progress value={exerciseProgress} className="h-2 mb-2" />
              <p className="text-xs text-green-600">{exerciseProgress}% выполнено</p>
              {reviewedExercises > 0 && (
                <p className="text-xs text-green-700 mt-2">
                  ✓ {reviewedExercises} ответов проверено преподавателем
                </p>
              )}
            </div>

            {/* Челлендж */}
            {hasChallenge && (
              <div className="bg-orange-50 rounded-lg p-5 border border-orange-200">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 bg-orange-100 rounded-lg">
                    <Calendar className="w-6 h-6 text-orange-600" />
                  </div>
                  <div className="flex-1">
                    <h5 className="font-semibold text-orange-900">Челлендж</h5>
                    <p className="text-sm text-orange-700">{completedChallengeDays} из {challengeDays} дней</p>
                  </div>
                  {/* Баллы за челлендж */}
                  {challengeHistory.length > 0 && (
                    <div className="text-right">
                      <p className="text-xl font-bold text-orange-600">
                        {challengeHistory.reduce((sum, a) => sum + (a.points_earned || 0), 0)} 🌟
                      </p>
                      <p className="text-xs text-orange-600">баллов</p>
                    </div>
                  )}
                </div>
                <Progress value={challengeProgressPercent} className="h-2 mb-2" />
                <div className="flex items-center justify-between">
                  <p className="text-xs text-orange-600">{challengeProgressPercent}% выполнено</p>
                  {challengeHistory.length > 0 && (
                    <p className="text-xs text-orange-700">
                      Попыток: {challengeHistory.length}
                    </p>
                  )}
                </div>
                {challengeProgress?.is_completed && (
                  <p className="text-xs text-green-700 mt-2 font-semibold">
                    ✅ Челлендж завершен!
                  </p>
                )}
                {!challengeProgress?.is_completed && challengeHistory.filter(a => a.is_completed).length > 0 && (
                  <p className="text-xs text-orange-700 mt-2">
                    ✓ Завершено попыток: {challengeHistory.filter(a => a.is_completed).length}
                  </p>
                )}
              </div>
            )}

            {/* Тест */}
            {hasQuiz && (
              <div className={`rounded-lg p-5 border ${quizPassed ? 'bg-blue-50 border-blue-200' : 'bg-gray-50 border-gray-200'}`}>
                <div className="flex items-center gap-3 mb-3">
                  <div className={`p-2 rounded-lg ${quizPassed ? 'bg-blue-100' : 'bg-gray-100'}`}>
                    <Target className={`w-6 h-6 ${quizPassed ? 'text-blue-600' : 'text-gray-600'}`} />
                  </div>
                  <div>
                    <h5 className={`font-semibold ${quizPassed ? 'text-blue-900' : 'text-gray-900'}`}>Тест</h5>
                    <p className={`text-sm ${quizPassed ? 'text-blue-700' : 'text-gray-700'}`}>
                      {quizCompleted ? `${quizScore}%` : 'Не пройден'}
                    </p>
                  </div>
                </div>
                {quizCompleted ? (
                  <>
                    <Progress value={quizScore} className="h-2 mb-2" />
                    <p className={`text-xs ${quizPassed ? 'text-blue-600' : 'text-red-600'}`}>
                      {quizPassed ? '✓ Тест пройден успешно!' : '✗ Тест не пройден'}
                    </p>
                  </>
                ) : (
                  <p className="text-xs text-gray-600">Перейдите к разделу "Тест"</p>
                )}
              </div>
            )}
          </div>

          {/* Комментарии преподавателя */}
          {reviewedExercises > 0 && (
            <div className="bg-purple-50 rounded-lg p-6 border border-purple-200">
              <h4 className="font-semibold text-purple-900 mb-4 flex items-center gap-2">
                <Star className="w-5 h-5" />
                Обратная связь от преподавателя
              </h4>
              <div className="space-y-3">
                {Object.entries(exerciseResponsesData).map(([exerciseId, data]) => {
                  if (!data?.reviewed || !data?.admin_comment) return null;
                  
                  const exercise = currentLesson.exercises?.find(e => e.id === exerciseId);
                  if (!exercise) return null;

                  return (
                    <div key={exerciseId} className="bg-white rounded-lg p-4 border border-purple-200">
                      <p className="text-sm font-medium text-purple-900 mb-2">
                        {exercise.title}
                      </p>
                      <p className="text-sm text-purple-800 whitespace-pre-wrap">
                        {data.admin_comment}
                      </p>
                      <p className="text-xs text-purple-600 mt-2">
                        {new Date(data.reviewed_at).toLocaleString('ru-RU')}
                      </p>
            </div>
                  );
                })}
          </div>
            </div>
          )}

          {/* Достижения */}
          <div className="bg-gradient-to-r from-yellow-50 to-amber-50 rounded-lg p-6 border border-yellow-200">
            <h4 className="font-semibold text-yellow-900 mb-4 flex items-center gap-2">
              <Trophy className="w-5 h-5" />
              Ваши достижения
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {completedExercises > 0 && (
                <div className="text-center">
                  <div className="text-3xl mb-2">✍️</div>
                  <p className="text-sm font-medium text-yellow-900">Практик</p>
                  <p className="text-xs text-yellow-700">{completedExercises} упражнений</p>
                </div>
              )}
              {completedChallengeDays > 0 && (
                <div className="text-center">
                  <div className="text-3xl mb-2">🔥</div>
                  <p className="text-sm font-medium text-yellow-900">Целеустремленный</p>
                  <p className="text-xs text-yellow-700">{completedChallengeDays} дней челленджа</p>
                </div>
              )}
              {quizPassed && (
                <div className="text-center">
                  <div className="text-3xl mb-2">🎓</div>
                  <p className="text-sm font-medium text-yellow-900">Знаток</p>
                  <p className="text-xs text-yellow-700">Тест пройден на {quizScore}%</p>
                </div>
              )}
              {overallProgress === 100 && (
                <div className="text-center">
                  <div className="text-3xl mb-2">🏆</div>
                  <p className="text-sm font-medium text-yellow-900">Мастер</p>
                  <p className="text-xs text-yellow-700">Урок завершен на 100%</p>
                </div>
              )}
            </div>
          </div>

          {/* История прохождения челленджа */}
          {hasChallenge && challengeHistory.length > 0 && (
            <div className="bg-gradient-to-r from-orange-50 to-yellow-50 rounded-lg p-6 border border-orange-200">
              <h4 className="font-semibold text-orange-900 mb-4 flex items-center gap-2">
                <Calendar className="w-5 h-5" />
                История прохождения челленджа
            </h4>
              <div className="space-y-3">
                {challengeHistory.map((attempt, index) => (
                  <div 
                    key={index} 
                    className={`bg-white rounded-lg p-4 border-2 ${
                      attempt.is_completed 
                        ? 'border-green-300' 
                        : 'border-orange-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                          attempt.is_completed 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-orange-100 text-orange-700'
                        }`}>
                          #{attempt.attempt_number}
                        </div>
                        <div>
                          <p className="font-semibold text-gray-900">
                            Попытка {attempt.attempt_number}
                            {attempt.is_completed && ' ✓'}
                          </p>
                          <p className="text-xs text-gray-600">
                            {new Date(attempt.started_at).toLocaleDateString('ru-RU')}
                            {attempt.completed_at && ` - ${new Date(attempt.completed_at).toLocaleDateString('ru-RU')}`}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-yellow-600">
                          {attempt.points_earned} 🌟
                        </p>
                        <p className="text-xs text-gray-600">
                          {attempt.completed_days?.length || 0} / {challengeDays} дней
              </p>
            </div>
          </div>

                    {/* Прогресс-бар */}
                    <div className="mb-3">
                      <Progress 
                        value={(attempt.completed_days?.length || 0) / challengeDays * 100} 
                        className="h-2"
                      />
                    </div>
                    
                    {/* Заметки */}
                    {attempt.daily_notes && attempt.daily_notes.length > 0 && (
                      <div className="mt-3 space-y-2">
                        <p className="text-xs font-semibold text-gray-700">Заметки:</p>
                        <div className="grid grid-cols-1 gap-2 max-h-40 overflow-y-auto">
                          {attempt.daily_notes.slice(0, 3).map((note, noteIndex) => (
                            <div key={noteIndex} className="bg-gray-50 rounded p-2">
                              <p className="text-xs text-gray-600">
                                <span className="font-medium">День {note.day}:</span> {note.note.substring(0, 100)}
                                {note.note.length > 100 && '...'}
                              </p>
                            </div>
                          ))}
                          {attempt.daily_notes.length > 3 && (
                            <p className="text-xs text-gray-500 text-center">
                              +{attempt.daily_notes.length - 3} заметок
                            </p>
                          )}
                        </div>
                      </div>
                    )}
                    
                    {/* Статус */}
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      {attempt.is_completed ? (
                        <p className="text-sm text-green-700 font-medium">
                          🎉 Челлендж завершен! Заработано {attempt.points_earned} баллов
                        </p>
                      ) : (
                        <p className="text-sm text-orange-700 font-medium">
                          ⏳ В процессе выполнения
                        </p>
                      )}
                    </div>
                  </div>
                ))}
                
                {/* Общая статистика */}
                <div className="bg-gradient-to-r from-yellow-100 to-orange-100 rounded-lg p-4 mt-4">
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-2xl font-bold text-orange-700">
                        {challengeHistory.length}
                      </p>
                      <p className="text-xs text-orange-600">Попыток</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-green-700">
                        {challengeHistory.filter(a => a.is_completed).length}
                      </p>
                      <p className="text-xs text-green-600">Завершено</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-yellow-700">
                        {challengeHistory.reduce((sum, a) => sum + (a.points_earned || 0), 0)} 🌟
                      </p>
                      <p className="text-xs text-yellow-600">Всего баллов</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* История прохождения тестов */}
          {hasQuiz && quizHistory.length > 0 && (
            <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-6 border border-purple-200">
              <h4 className="font-semibold text-purple-900 mb-4 flex items-center gap-2">
                <Target className="w-5 h-5" />
                История прохождения тестов
            </h4>
              <div className="space-y-3">
                {quizHistory.map((attempt, index) => (
                  <div 
                    key={index} 
                    className={`bg-white rounded-lg p-4 border-2 ${
                      attempt.passed 
                        ? 'border-green-300' 
                        : 'border-red-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                          attempt.passed 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-red-100 text-red-700'
                        }`}>
                          #{index + 1}
                        </div>
                        <div>
                          <p className="font-semibold text-gray-900">
                            Попытка {index + 1}
                            {attempt.passed && ' ✓'}
                          </p>
                          <p className="text-xs text-gray-600">
                            {new Date(attempt.attempted_at).toLocaleString('ru-RU')}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-purple-600">
                          {attempt.points_earned || 0} 🎯
                        </p>
                        <p className="text-xs text-gray-600">
                          {attempt.score}%
                        </p>
            </div>
          </div>
                    
                    {/* Прогресс-бар */}
                    <div className="mb-3">
                      <Progress 
                        value={attempt.score} 
                        className={`h-2 ${attempt.passed ? 'bg-green-200' : 'bg-red-200'}`}
                      />
                    </div>
                    
                    {/* Статус */}
                    <div className="pt-3 border-t border-gray-200">
                      {attempt.passed ? (
                        <p className="text-sm text-green-700 font-medium">
                          ✅ Тест пройден! Заработано {attempt.points_earned || 0} баллов
                        </p>
                      ) : (
                        <p className="text-sm text-red-700 font-medium">
                          ❌ Тест не пройден. Заработано {attempt.points_earned || 0} баллов
                        </p>
                      )}
                    </div>
                  </div>
                ))}
                
                {/* Общая статистика по тестам */}
                <div className="bg-gradient-to-r from-purple-100 to-indigo-100 rounded-lg p-4 mt-4">
                  <div className="grid grid-cols-4 gap-4 text-center">
                    <div>
                      <p className="text-2xl font-bold text-purple-700">
                        {quizHistory.length}
                      </p>
                      <p className="text-xs text-purple-600">Попыток</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-green-700">
                        {quizHistory.filter(a => a.passed).length}
                      </p>
                      <p className="text-xs text-green-600">Пройдено</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-indigo-700">
                        {Math.max(...quizHistory.map(a => a.score))}%
                      </p>
                      <p className="text-xs text-indigo-600">Лучший результат</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-purple-700">
                        {quizHistory.reduce((sum, a) => sum + (a.points_earned || 0), 0)} 🎯
                      </p>
                      <p className="text-xs text-purple-600">Всего баллов</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Рекомендации */}
          <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
            <h4 className="font-semibold text-blue-900 mb-4 flex items-center gap-2">
              <Brain className="w-5 h-5" />
              Что делать дальше?
            </h4>
            <div className="space-y-3 text-sm text-blue-800">
              {completedExercises < totalExercises && (
                <p>• Завершите оставшиеся упражнения ({totalExercises - completedExercises} из {totalExercises})</p>
              )}
              {hasChallenge && completedChallengeDays < challengeDays && (
                <p>• Продолжите челлендж (осталось {challengeDays - completedChallengeDays} дней)</p>
              )}
              {hasQuiz && !quizCompleted && (
                <p>• Пройдите тест для проверки знаний</p>
              )}
              {hasQuiz && quizCompleted && !quizPassed && (
                <p>• Повторите материал и пройдите тест заново</p>
              )}
              {overallProgress === 100 && (
                <p>• 🎉 Отличная работа! Переходите к следующему уроку</p>
              )}
              {overallProgress < 100 && overallProgress >= 75 && (
                <p>• Вы почти у цели! Завершите оставшиеся задания</p>
              )}
            </div>
          </div>

          {/* Статистика файлов */}
          {studentFilesStats && studentFilesStats.summary.total_files > 0 && (
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
              <h4 className="font-semibold text-blue-900 text-lg mb-4 flex items-center gap-2">
                <Upload className="w-6 h-6 text-blue-600" />
                Статистика работы с файлами
              </h4>
              
              {/* Общая статистика */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-white rounded-lg p-4 border border-blue-200 text-center">
                  <p className="text-3xl font-bold text-blue-600">{studentFilesStats.summary.total_files}</p>
                  <p className="text-sm text-gray-600 mt-1">Всего файлов</p>
                </div>
                <div className="bg-white rounded-lg p-4 border border-green-200 text-center">
                  <p className="text-3xl font-bold text-green-600">{studentFilesStats.summary.total_views}</p>
                  <p className="text-sm text-gray-600 mt-1">Просмотров</p>
                </div>
                <div className="bg-white rounded-lg p-4 border border-purple-200 text-center">
                  <p className="text-3xl font-bold text-purple-600">{studentFilesStats.summary.total_downloads}</p>
                  <p className="text-sm text-gray-600 mt-1">Скачиваний</p>
                </div>
                <div className="bg-white rounded-lg p-4 border border-yellow-200 text-center">
                  <p className="text-3xl font-bold text-yellow-600">{studentFilesStats.summary.total_video_points} 🎬</p>
                  <p className="text-sm text-gray-600 mt-1">Баллов за видео</p>
                </div>
              </div>
              
              {/* Детальная статистика по файлам */}
              {studentFilesStats && studentFilesStats.files && Array.isArray(studentFilesStats.files) && studentFilesStats.files.length > 0 && (
                <div className="space-y-4">
                  <h5 className="font-medium text-gray-700">Материалы урока:</h5>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {studentFilesStats.files.map((file) => {
                      // Убеждаемся, что file - это объект с нужными полями
                      if (!file || typeof file !== 'object') {
                        return null;
                      }
                      const fileId = file.file_id || file.id || '';
                      if (!fileId) {
                        return null;
                      }
                      const baseFile = lessonFileMap[fileId];
                        const fallbackFile = baseFile || {
                          id: fileId,
                          original_name: file.file_name || '',
                          mime_type: file.mime_type || '',
                          extension: (file.file_name || '').split('.').pop() || '',
                          file_size: 0
                        };
                      const fileStyle = getFileStyle(fallbackFile);
                      const canOpen = Boolean(baseFile);

                      return (
                        <div
                          key={file.file_id}
                          className="bg-white rounded-lg p-4 border-2 shadow-sm flex flex-col gap-3"
                          style={{ borderColor: fileStyle.color }}
                        >
                          <div className="flex items-start gap-3">
                            <div
                              className="p-2 rounded-lg flex-shrink-0"
                              style={{ backgroundColor: fileStyle.bgColor }}
                            >
                              {fileStyle.icon}
                            </div>
                            <div className="min-w-0 flex-1">
                              <p className="text-sm font-semibold text-gray-900 truncate">{file.file_name}</p>
                              <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500 mt-1">
                                <span>Раздел: {file.section || '—'}</span>
                                <span>Просмотров: {typeof file.views === 'number' ? file.views : 0}</span>
                                <span>Скачиваний: {typeof file.downloads === 'number' ? file.downloads : 0}</span>
                                {file.video_stats && typeof file.video_stats === 'object' && (
                                  <span className="text-purple-600">
                                    🎬 {typeof file.video_stats.minutes_watched === 'number' ? file.video_stats.minutes_watched : 0} мин • {typeof file.video_stats.points_earned === 'number' ? file.video_stats.points_earned : 0} баллов
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>

                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              onClick={() => baseFile && handleViewFile(baseFile)}
                              disabled={!canOpen}
                              className="flex-1 text-white"
                              style={{
                                backgroundColor: canOpen ? fileStyle.color : '#CBD5F5',
                                borderColor: canOpen ? fileStyle.color : '#CBD5F5'
                              }}
                            >
                              <Eye className="w-4 h-4 mr-1" />
                              Просмотр
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => baseFile && handleDownloadFile(baseFile)}
                              disabled={!canOpen}
                              className="flex-1"
                              style={{
                                borderColor: fileStyle.color,
                                color: canOpen ? fileStyle.color : '#9CA3AF'
                              }}
                            >
                              <Download className="w-4 h-4 mr-1" />
                              Скачать
                            </Button>
                          </div>

                          {!canOpen && (
                            <p className="text-xs text-gray-500">
                              * Файл недоступен для просмотра. Обратитесь к администратору.
                            </p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="flex justify-between items-center">
            {currentLesson.quiz ? (
              <Button
                variant="outline"
                onClick={() => setCurrentSection('quiz')}
                className="flex items-center gap-2"
              >
                <ChevronLeft className="w-4 h-4" />
                Назад к тесту
              </Button>
            ) : currentLesson.challenge ? (
              <Button
                variant="outline"
                onClick={() => setCurrentSection('challenge')}
                className="flex items-center gap-2"
              >
                <ChevronLeft className="w-4 h-4" />
                Назад к челленджу
              </Button>
            ) : (
              <Button
                variant="outline"
                onClick={() => setCurrentSection('exercises')}
                className="flex items-center gap-2"
              >
                <ChevronLeft className="w-4 h-4" />
                Назад к упражнениям
              </Button>
            )}

            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => setCurrentLesson(null)}
                className="flex items-center gap-2"
              >
                <Home className="w-4 h-4 mr-1" />
                К списку уроков
              </Button>

              <Button
                onClick={() => window.location.href = '/personal-data'}
                className="flex items-center gap-2"
              >
                <User className="w-4 h-4 mr-1" />
                Личные данные
              </Button>

              <Button
                onClick={() => window.location.href = '/numerology'}
                className="flex items-center gap-2"
              >
                <Calculator className="w-4 h-4 mr-1" />
                Нумерология
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Загрузка системы обучения...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Alert className="max-w-md mx-auto">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  // Функция для получения заголовка аналитики
  const getAnalyticsTitle = () => {
    switch (analyticsSection) {
      case 'lessons':
        return 'Детальная аналитика по урокам';
      case 'challenges':
        return 'Детальная аналитика по челленджам';
      case 'quizzes':
        return 'Детальная аналитика по тестам';
      case 'exercises':
        return 'Детальная аналитика по упражнениям';
      default:
        return 'Аналитика';
    }
  };

  // Функция для получения иконки аналитики
  const getAnalyticsIcon = () => {
    switch (analyticsSection) {
      case 'lessons':
        return <BookOpen className="w-6 h-6 text-blue-600" />;
      case 'challenges':
        return <Zap className="w-6 h-6 text-yellow-600" />;
      case 'quizzes':
        return <Target className="w-6 h-6 text-green-600" />;
      case 'exercises':
        return <Brain className="w-6 h-6 text-purple-600" />;
      default:
        return null;
    }
  };

  // Функция для отображения аналитики
  const renderAnalytics = () => {
    if (analyticsLoading) {
      return (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Загрузка данных...</p>
          </div>
        </div>
      );
    }

    const stats = analyticsStats || dashboardStats;

    return (
      <div className="space-y-6">
        {/* Заголовок с кнопкой назад */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            {getAnalyticsIcon()}
            <h2 className="text-2xl font-bold text-gray-900">{getAnalyticsTitle()}</h2>
          </div>
          <Button
            variant="outline"
            onClick={() => {
              setShowAnalytics(false);
              setAnalyticsSection(null);
              setDetailedAnalytics(null);
            }}
            className="flex items-center gap-2"
          >
            <ChevronLeft className="w-4 h-4" />
            Назад к списку уроков
          </Button>
        </div>

        {stats && (
          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview">Обзор</TabsTrigger>
              <TabsTrigger value="statistics">Статистика</TabsTrigger>
              <TabsTrigger value="charts">Графики</TabsTrigger>
              <TabsTrigger value="recommendations">Рекомендации</TabsTrigger>
            </TabsList>

            {/* Аналитика по урокам */}
            {analyticsSection === 'lessons' && (
              <>
                <TabsContent value="overview" className="space-y-4 mt-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Завершено уроков</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-blue-600">
                          {stats?.lessons?.completed || 0} / {stats?.lessons?.total || 0}
                        </div>
                        <Progress value={stats?.lessons?.completion_percentage || 0} className="mt-2" />
                        <p className="text-xs text-gray-500 mt-1">{stats?.lessons?.completion_percentage || 0}% завершено</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">В процессе</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-orange-600">
                          {stats?.lessons?.in_progress || 0}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">Активных уроков</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Среднее время</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-green-600">
                          {stats?.time_stats?.study_minutes ? Math.round(stats.time_stats.study_minutes / (stats?.lessons?.completed || 1)) : 0}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">минут на урок</p>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="statistics" className="space-y-4 mt-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Детальная статистика</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm text-gray-600">Всего времени изучения</p>
                          <p className="text-2xl font-bold">{stats?.time_stats?.study_minutes || 0} минут</p>
                          <p className="text-xs text-gray-500">{Math.round((stats?.time_stats?.study_minutes || 0) / 60)} часов</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Время просмотра видео</p>
                          <p className="text-2xl font-bold">{stats?.time_stats?.video_minutes || 0} минут</p>
                          <p className="text-xs text-gray-500">{Math.round((stats?.time_stats?.video_minutes || 0) / 60)} часов</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Просмотрено файлов</p>
                          <p className="text-2xl font-bold">{stats?.files?.views || 0}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Скачано файлов</p>
                          <p className="text-2xl font-bold">{stats?.files?.downloads || 0}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  
                  {/* Детали по каждому уроку */}
                  {detailedAnalytics && detailedAnalytics.length > 0 ? (
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold">Детали по урокам ({detailedAnalytics.length})</h3>
                      {detailedAnalytics.map((lesson, index) => (
                        <Card key={index}>
                          <CardHeader>
                            <CardTitle>{lesson.lesson_title}</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                              <div>
                                <p className="text-sm text-gray-600">Прогресс</p>
                                <p className="text-xl font-bold">{lesson.completion_percentage}%</p>
                                <Progress value={lesson.completion_percentage} className="mt-2" />
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Время изучения</p>
                                <p className="text-xl font-bold">{lesson.time_minutes} мин</p>
                                <p className="text-xs text-gray-500">{Math.round(lesson.time_minutes / 60)} ч</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Видео время</p>
                                <p className="text-xl font-bold">{lesson.video_minutes} мин</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Файлы</p>
                                <p className="text-xl font-bold">{lesson.file_views} просмотров</p>
                                <p className="text-xs text-gray-500">{lesson.file_downloads} скачиваний</p>
                              </div>
                            </div>
                            {lesson.started_at && (
                              <div className="mt-4 pt-4 border-t">
                                <p className="text-sm text-gray-600">Начато: {new Date(lesson.started_at).toLocaleDateString('ru-RU')}</p>
                                {lesson.completed_at && (
                                  <p className="text-sm text-gray-600">Завершено: {new Date(lesson.completed_at).toLocaleDateString('ru-RU')}</p>
                                )}
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <Card>
                      <CardContent className="py-8 text-center text-gray-500">
                        {analyticsLoading ? 'Загрузка данных...' : 'Нет данных об уроках'}
                        {!analyticsLoading && detailedAnalytics && detailedAnalytics.length === 0 && (
                          <p className="text-xs mt-2">Попробуйте обновить страницу</p>
                        )}
                      </CardContent>
                    </Card>
                  )}
                </TabsContent>

                <TabsContent value="charts" className="space-y-4 mt-6">
                  <Card>
                    <CardHeader>
                      <div className="flex items-center justify-between flex-wrap gap-4">
                        <CardTitle>График активности по урокам</CardTitle>
                        {/* Фильтры по периодам и календарь */}
                        <div className="flex gap-2 items-center flex-wrap">
                          <Button
                            variant={timelinePeriod === 'day' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => handleTimelinePeriodChange('day')}
                            className="flex items-center gap-2"
                          >
                            <Clock className="w-4 h-4" />
                            Один день 24:00
                          </Button>
                          <Button
                            variant={timelinePeriod === 'week' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => handleTimelinePeriodChange('week')}
                          >
                            Неделя
                          </Button>
                          <Button
                            variant={timelinePeriod === 'month' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => handleTimelinePeriodChange('month')}
                          >
                            Месяц
                          </Button>
                          <Button
                            variant={timelinePeriod === 'quarter' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => handleTimelinePeriodChange('quarter')}
                          >
                            Квартал
                          </Button>
                          <Button
                            variant={showCalendar ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => setShowCalendar(!showCalendar)}
                            className="flex items-center gap-2"
                          >
                            <Calendar className="w-4 h-4" />
                            Календарь
                          </Button>
                        </div>
                      </div>
                      {/* Календарь для выбора дат */}
                      {showCalendar && (
                        <div className="mt-4 p-4 bg-gray-50 rounded-lg border">
                          <div className="flex gap-4 items-end">
                            <div className="flex-1">
                              <label className="text-sm font-medium text-gray-700 mb-2 block">
                                Начальная дата
                              </label>
                              <input
                                type="date"
                                value={selectedStartDate ? selectedStartDate.toISOString().split('T')[0] : ''}
                                onChange={(e) => {
                                  if (e.target.value) {
                                    setSelectedStartDate(new Date(e.target.value));
                                  }
                                }}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                              />
                            </div>
                            <div className="flex-1">
                              <label className="text-sm font-medium text-gray-700 mb-2 block">
                                Конечная дата
                              </label>
                              <input
                                type="date"
                                value={selectedEndDate ? selectedEndDate.toISOString().split('T')[0] : ''}
                                onChange={(e) => {
                                  if (e.target.value) {
                                    setSelectedEndDate(new Date(e.target.value));
                                  }
                                }}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                              />
                            </div>
                            <Button
                              size="sm"
                              onClick={() => {
                                if (selectedStartDate && selectedEndDate) {
                                  handleDateRangeSelect(selectedStartDate, selectedEndDate);
                                }
                              }}
                              disabled={!selectedStartDate || !selectedEndDate}
                            >
                              Применить
                            </Button>
                          </div>
                        </div>
                      )}
                    </CardHeader>
                    <CardContent>
                      {detailedAnalytics && detailedAnalytics.length > 0 ? (
                        <div className="space-y-6">
                          {/* Описание графика активности */}
                          <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                            <h5 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                              <BarChart3 className="w-5 h-5" />
                              График активности по урокам
                            </h5>
                            <p className="text-sm text-blue-800 mb-3">
                              Этот график показывает вашу ежедневную активность в обучении. Каждая линия представляет определенный тип активности:
                            </p>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-blue-700">
                              <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: '#8b5cf6' }}></span>
                                <span><strong>Фиолетовая линия</strong> - Активность теории (количество сессий изучения теории)</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: '#3b82f6' }}></span>
                                <span><strong>Синяя линия</strong> - Присутствие в уроке (количество входов в урок)</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: '#ef4444' }}></span>
                                <span><strong>Красная линия</strong> - Просмотр видео (время в минутах)</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: '#10b981' }}></span>
                                <span><strong>Зеленая линия</strong> - Просмотр PDF файлов (количество файлов)</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full border-2" style={{ borderColor: '#f59e0b', backgroundColor: 'transparent' }}></span>
                                <span><strong>Оранжевая пунктирная</strong> - Общая активность (суммарный показатель)</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: '#06b6d4' }}></span>
                                <span><strong>Голубая линия</strong> - Эффективность обучения (0-100%, справа)</span>
                              </div>
                            </div>
                            <p className="text-xs text-blue-600 mt-3 italic">
                              💡 Наведите курсор на график, чтобы увидеть детальную информацию по каждому дню
                            </p>
                          </div>
                          
                          {/* График активности с плавными линиями - объединенный график со всеми данными */}
                          {(stats?.activity_chart && stats.activity_chart.length > 0) || (analyticsStats?.activity_chart && analyticsStats.activity_chart.length > 0) || videoTimeline?.length > 0 || theoryTimeline?.length > 0 ? (
                            <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                              <ActivityLineChart 
                                data={analyticsStats?.activity_chart || stats?.activity_chart || []}
                                videoTimeline={videoTimeline}
                                theoryTimeline={theoryTimeline}
                                challengeTimeline={challengeTimeline}
                                quizTimeline={quizTimeline}
                                section="lessons"
                              />
                            </div>
                          ) : (
                            <div className="h-80 flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200">
                              <div className="text-center">
                                <BarChart3 className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                                <p className="text-gray-400 font-medium">Нет данных об активности</p>
                                <p className="text-xs text-gray-500 mt-2">Данные появятся после начала обучения</p>
                              </div>
                            </div>
                          )}
                          
                          {/* Прогресс по урокам с улучшенным дизайном */}
                          <div className="mt-8">
                            <div className="mb-4 p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
                              <h4 className="text-lg font-semibold mb-2 flex items-center gap-2 text-indigo-900">
                                <TrendingUp className="w-5 h-5" />
                                Детальный прогресс по урокам
                              </h4>
                              <p className="text-sm text-indigo-800">
                                Ниже представлена детальная статистика по каждому уроку: процент завершения, время изучения, просмотры файлов и другие метрики.
                              </p>
                            </div>
                            <div className="space-y-4">
                              {detailedAnalytics.map((lesson, idx) => (
                                <Card key={idx} className="hover:shadow-lg transition-all duration-200 border-2 hover:border-blue-300">
                                  <CardContent className="pt-4">
                                    <div className="flex items-center justify-between mb-3">
                                      <div className="flex-1">
                                        <h5 className="font-semibold text-gray-900 text-lg mb-1">{lesson.lesson_title}</h5>
                                        {lesson.started_at && (
                                          <p className="text-xs text-gray-500">
                                            Начато: {new Date(lesson.started_at).toLocaleDateString('ru-RU', { 
                                              day: 'numeric', 
                                              month: 'long', 
                                              year: 'numeric' 
                                            })}
                                            {lesson.completed_at && (
                                              <span className="ml-2">
                                                • Завершено: {new Date(lesson.completed_at).toLocaleDateString('ru-RU', { 
                                                  day: 'numeric', 
                                                  month: 'long', 
                                                  year: 'numeric' 
                                                })}
                                              </span>
                                            )}
                                          </p>
                                        )}
                                      </div>
                                      <div className="flex items-center gap-2 ml-4">
                                        <span className={`text-2xl font-bold ${
                                          lesson.completion_percentage === 100 ? 'text-green-600' : 
                                          lesson.completion_percentage >= 75 ? 'text-blue-600' : 
                                          lesson.completion_percentage >= 50 ? 'text-yellow-600' : 
                                          'text-orange-600'
                                        }`}>
                                          {lesson.completion_percentage}%
                                        </span>
                                        {lesson.completion_percentage === 100 && (
                                          <CheckCircle2 className="w-6 h-6 text-green-500" />
                                        )}
                                      </div>
                                    </div>
                                    <Progress 
                                      value={lesson.completion_percentage} 
                                      className={`h-4 mb-4 ${
                                        lesson.completion_percentage === 100 ? 'bg-green-100' : 
                                        lesson.completion_percentage >= 75 ? 'bg-blue-100' : 
                                        lesson.completion_percentage >= 50 ? 'bg-yellow-100' : 
                                        'bg-orange-100'
                                      }`} 
                                    />
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-3 border-t border-gray-200">
                                      <div className="text-center p-2 bg-blue-50 rounded">
                                        <p className="text-xs text-gray-600 mb-1">⏱️ Время осознания</p>
                                        <p className="text-lg font-bold text-blue-600">{lesson.time_minutes} мин</p>
                                        <p className="text-xs text-gray-500">{Math.round(lesson.time_minutes / 60)} ч</p>
                                      </div>
                                      <div className="text-center p-2 bg-red-50 rounded">
                                        <p className="text-xs text-gray-600 mb-1">🎥 Видео</p>
                                        <p className="text-lg font-bold text-red-600">{lesson.video_minutes || 0} мин</p>
                                      </div>
                                      <div className="text-center p-2 bg-green-50 rounded">
                                        <p className="text-xs text-gray-600 mb-1">📄 Файлы</p>
                                        <p className="text-lg font-bold text-green-600">{lesson.file_views || 0}</p>
                                        <p className="text-xs text-gray-500">{lesson.file_downloads || 0} скачиваний</p>
                                      </div>
                                      <div className="text-center p-2 bg-purple-50 rounded">
                                        <p className="text-xs text-gray-600 mb-1">📊 Активность</p>
                                        <p className="text-lg font-bold text-purple-600">
                                          {lesson.completion_percentage >= 75 ? 'Высокая' : 
                                           lesson.completion_percentage >= 50 ? 'Средняя' : 
                                           lesson.completion_percentage >= 25 ? 'Низкая' : 'Минимальная'}
                                        </p>
                                      </div>
                                    </div>
                                  </CardContent>
                                </Card>
                              ))}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="h-64 flex items-center justify-center">
                          <div className="text-center">
                            <BarChart3 className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                            <p className="text-gray-500">Нет данных для отображения</p>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="recommendations" className="space-y-4 mt-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Lightbulb className="w-5 h-5 text-yellow-500" />
                        Рекомендации для улучшения
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {stats?.lessons?.completion_percentage < 50 && (
                        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                          <p className="font-semibold text-yellow-900 mb-2">⚠️ Низкий процент завершения</p>
                          <p className="text-sm text-yellow-800">Рекомендуем завершить начатые уроки перед переходом к новым. Это поможет лучше усвоить материал.</p>
                        </div>
                      )}
                      {stats?.time_stats?.study_minutes < 60 && (
                        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                          <p className="font-semibold text-blue-900 mb-2">💡 Увеличьте время изучения</p>
                          <p className="text-sm text-blue-800">Вы тратите мало времени на изучение. Рекомендуем уделять минимум 30 минут в день для лучшего усвоения материала.</p>
                        </div>
                      )}
                      {stats?.files?.views === 0 && (
                        <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
                          <p className="font-semibold text-purple-900 mb-2">📚 Изучите дополнительные материалы</p>
                          <p className="text-sm text-purple-800">Просмотрите файлы и видео, прикрепленные к урокам. Это поможет глубже понять материал.</p>
                        </div>
                      )}
                      {stats?.lessons?.completion_percentage >= 75 && (
                        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                          <p className="font-semibold text-green-900 mb-2">🎉 Отличный прогресс!</p>
                          <p className="text-sm text-green-800">Вы показываете отличные результаты! Продолжайте в том же духе и не забывайте про челленджи и тесты.</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>
              </>
            )}

            {/* Аналитика по челленджам */}
            {analyticsSection === 'challenges' && (
              <>
                <TabsContent value="overview" className="space-y-4 mt-6">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Дней пройдено</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-yellow-600">
                          {stats?.challenge_analytics?.total_days_completed || 0}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Время осознания</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-blue-600">
                          {stats?.challenge_analytics?.total_time_hours || 0}ч
                        </div>
                        <p className="text-xs text-gray-500">{stats?.challenge_analytics?.total_time_minutes || 0} мин</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Завершено</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-green-600">
                          {stats?.challenge_analytics?.details?.filter(c => c.is_completed).length || 0}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Баллов заработано</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-purple-600">
                          {stats?.points_breakdown?.challenges || 0}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="statistics" className="space-y-4 mt-6">
                  {detailedAnalytics && detailedAnalytics.length > 0 ? (
                    <div className="space-y-4">
                      {detailedAnalytics.map((challenge, index) => (
                        <Card key={index}>
                          <CardHeader>
                            <CardTitle>{challenge.lesson_title}</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                              <div>
                                <p className="text-sm text-gray-600">Прогресс</p>
                                <p className="text-xl font-bold">{challenge.completion_percentage}%</p>
                                <Progress value={challenge.completion_percentage} className="mt-2" />
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Дней завершено</p>
                                <p className="text-xl font-bold">{challenge.completed_days?.length || 0} / {challenge.total_days || '?'}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Время</p>
                                <p className="text-xl font-bold">{challenge.time_minutes} мин</p>
                                <p className="text-xs text-gray-500">{Math.round(challenge.time_minutes / 60)} ч</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Баллов</p>
                                <p className="text-xl font-bold">{challenge.points_earned}</p>
                              </div>
                            </div>
                            {challenge.started_at && (
                              <div className="mt-4 pt-4 border-t">
                                <p className="text-sm text-gray-600">Начато: {new Date(challenge.started_at).toLocaleDateString('ru-RU')}</p>
                                {challenge.completed_at && (
                                  <p className="text-sm text-gray-600">Завершено: {new Date(challenge.completed_at).toLocaleDateString('ru-RU')}</p>
                                )}
                                {challenge.daily_notes && challenge.daily_notes.length > 0 && (
                                  <div className="mt-2">
                                    <p className="text-sm font-semibold">Заметки по дням:</p>
                                    <ul className="text-sm text-gray-600 list-disc list-inside">
                                      {challenge.daily_notes.map((note, idx) => (
                                        <li key={idx}>День {note.day}: {note.note || 'Без заметки'}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <Card>
                      <CardContent className="py-8 text-center text-gray-500">
                        Нет данных о челленджах
                      </CardContent>
                    </Card>
                  )}
                </TabsContent>

                <TabsContent value="charts" className="space-y-4 mt-6">
                  <Card>
                    <CardHeader>
                      <div className="flex items-center justify-between flex-wrap gap-4">
                        <CardTitle>График выполнения челленджей</CardTitle>
                        {/* Фильтры по периодам и календарь */}
                        <div className="flex gap-2 items-center flex-wrap">
                          <Button
                            variant={timelinePeriod === 'day' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => handleTimelinePeriodChange('day')}
                            className="flex items-center gap-2"
                          >
                            <Clock className="w-4 h-4" />
                            Один день 24:00
                          </Button>
                          <Button
                            variant={timelinePeriod === 'week' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => handleTimelinePeriodChange('week')}
                          >
                            Неделя
                          </Button>
                          <Button
                            variant={timelinePeriod === 'month' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => handleTimelinePeriodChange('month')}
                          >
                            Месяц
                          </Button>
                          <Button
                            variant={timelinePeriod === 'quarter' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => handleTimelinePeriodChange('quarter')}
                          >
                            Квартал
                          </Button>
                          <Button
                            variant={showCalendar ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => setShowCalendar(!showCalendar)}
                            className="flex items-center gap-2"
                          >
                            <Calendar className="w-4 h-4" />
                            Календарь
                          </Button>
                        </div>
                      </div>
                      {/* Календарь для выбора дат */}
                      {showCalendar && (
                        <div className="mt-4 p-4 bg-gray-50 rounded-lg border">
                          <div className="flex gap-4 items-end">
                            <div className="flex-1">
                              <label className="text-sm font-medium text-gray-700 mb-2 block">
                                Начальная дата
                              </label>
                              <input
                                type="date"
                                value={selectedStartDate ? selectedStartDate.toISOString().split('T')[0] : ''}
                                onChange={(e) => {
                                  if (e.target.value) {
                                    setSelectedStartDate(new Date(e.target.value));
                                  }
                                }}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                              />
                            </div>
                            <div className="flex-1">
                              <label className="text-sm font-medium text-gray-700 mb-2 block">
                                Конечная дата
                              </label>
                              <input
                                type="date"
                                value={selectedEndDate ? selectedEndDate.toISOString().split('T')[0] : ''}
                                onChange={(e) => {
                                  if (e.target.value) {
                                    setSelectedEndDate(new Date(e.target.value));
                                  }
                                }}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                              />
                            </div>
                            <Button
                              size="sm"
                              onClick={() => {
                                if (selectedStartDate && selectedEndDate) {
                                  handleDateRangeSelect(selectedStartDate, selectedEndDate);
                                }
                              }}
                              disabled={!selectedStartDate || !selectedEndDate}
                            >
                              Применить
                            </Button>
                          </div>
                        </div>
                      )}
                    </CardHeader>
                    <CardContent>
                      {challengeTimeline && challengeTimeline.length > 0 ? (
                        <ActivityLineChart 
                          data={[]}
                          challengeTimeline={challengeTimeline}
                          section="challenges"
                        />
                      ) : (
                        <div className="h-80 flex items-center justify-center">
                          <div className="text-center">
                            <Zap className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                            <p className="text-gray-400">Нет данных о челленджах</p>
                            <p className="text-xs text-gray-500 mt-2">Данные появятся после начала выполнения челленджей</p>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="recommendations" className="space-y-4 mt-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Lightbulb className="w-5 h-5 text-yellow-500" />
                        Рекомендации
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {stats?.challenge_analytics?.problem_days && stats.challenge_analytics.problem_days.length > 0 && (
                        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                          <p className="font-semibold text-red-900 mb-2">⚠️ Дни с проблемами</p>
                          <ul className="list-disc list-inside text-sm text-red-800 space-y-1">
                            {stats.challenge_analytics.problem_days.map((problem, idx) => (
                              <li key={idx}>{problem.lesson_title} - День {problem.day}: {problem.reason}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {(() => {
                        const totalDays = stats?.challenge_analytics?.total_days_completed || detailedAnalytics?.reduce((sum, c) => sum + (c.completed_days?.length || 0), 0) || 0;
                        return totalDays < 10 && (
                          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                            <p className="font-semibold text-yellow-900 mb-2">💪 Увеличьте активность</p>
                            <p className="text-sm text-yellow-800">Попробуйте выполнять челленджи ежедневно. Регулярность - ключ к успеху!</p>
                          </div>
                        );
                      })()}
                      {detailedAnalytics && detailedAnalytics.length === 0 && (
                        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                          <p className="font-semibold text-blue-900 mb-2">📝 Начните челлендж</p>
                          <p className="text-sm text-blue-800">Вы еще не начали ни одного челленджа. Найдите урок с челленджем и начните свой путь к успеху!</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>
              </>
            )}

            {/* Аналитика по тестам */}
            {analyticsSection === 'quizzes' && (
              <>
                <TabsContent value="overview" className="space-y-4 mt-6">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Всего попыток</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-green-600">
                          {stats?.quiz_analytics?.total_attempts || detailedAnalytics?.reduce((sum, q) => sum + (q.total_attempts || 0), 0) || 0}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Максимальный балл</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-blue-600">
                          {stats?.quiz_analytics?.max_score || Math.max(...(detailedAnalytics?.map(q => q.best_score || 0) || [0]), 0)}%
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Средний балл</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-purple-600">
                          {stats?.quiz_analytics?.avg_score || (detailedAnalytics?.length > 0 ? Math.round(detailedAnalytics.reduce((sum, q) => sum + (q.avg_score || 0), 0) / detailedAnalytics.length) : 0)}%
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Баллов заработано</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-yellow-600">
                          {stats?.points_breakdown?.quizzes || detailedAnalytics?.reduce((sum, q) => sum + (q.total_points_earned || 0), 0) || 0}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="statistics" className="space-y-4 mt-6">
                  {detailedAnalytics && detailedAnalytics.length > 0 ? (
                    <div className="space-y-4">
                      {detailedAnalytics.map((quiz, index) => (
                        <Card key={index}>
                          <CardHeader>
                            <CardTitle>{quiz.lesson_title}</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                              <div>
                                <p className="text-sm text-gray-600">Попыток</p>
                                <p className="text-xl font-bold">{quiz.total_attempts}</p>
                                <p className="text-xs text-gray-500">{quiz.passed_attempts} успешных</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Лучший результат</p>
                                <p className="text-xl font-bold">{quiz.best_score}</p>
                                <p className="text-xs text-gray-500">из {quiz.max_possible_score}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Средний балл</p>
                                <p className="text-xl font-bold">{quiz.avg_score}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Баллов заработано</p>
                                <p className="text-xl font-bold">{quiz.total_points_earned}</p>
                                <p className="text-xs text-gray-500">{quiz.total_time_minutes} мин</p>
                              </div>
                            </div>
                            {quiz.attempts && quiz.attempts.length > 0 && (
                              <div className="mt-6">
                                <p className="text-sm font-semibold mb-4 flex items-center gap-2">
                                  <BarChart3 className="w-4 h-4 text-green-600" />
                                  История попыток
                                </p>
                                <QuizAttemptsLineChart attempts={quiz.attempts} maxPossibleScore={quiz.max_possible_score} />
                                <div className="mt-4 space-y-2">
                                  {quiz.attempts.map((attempt, idx) => (
                                    <div key={idx} className="text-sm border-b pb-2">
                                      <div className="flex justify-between">
                                        <span>Попытка #{idx + 1}</span>
                                        <span className="font-semibold">{attempt.score} ({attempt.score_percentage}%)</span>
                                      </div>
                                      <div className="flex justify-between text-xs text-gray-500">
                                        <span>{attempt.passed ? '✅ Пройдено' : '❌ Не пройдено'}</span>
                                        <span>{attempt.points_earned} баллов • {attempt.time_spent_minutes} мин</span>
                                      </div>
                                      {attempt.attempted_at && (
                                        <p className="text-xs text-gray-400">{new Date(attempt.attempted_at).toLocaleString('ru-RU')}</p>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <Card>
                      <CardContent className="py-8 text-center text-gray-500">
                        Нет данных о тестах
                      </CardContent>
                    </Card>
                  )}
                </TabsContent>

                <TabsContent value="charts" className="space-y-4 mt-6">
                  <Card>
                    <CardHeader>
                      <div className="flex items-center justify-between flex-wrap gap-4">
                        <CardTitle>График прохождения тестов</CardTitle>
                        {/* Фильтры по периодам и календарь */}
                        <div className="flex gap-2 items-center flex-wrap">
                          <Button
                            variant={timelinePeriod === 'day' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => handleTimelinePeriodChange('day')}
                            className="flex items-center gap-2"
                          >
                            <Clock className="w-4 h-4" />
                            Один день 24:00
                          </Button>
                          <Button
                            variant={timelinePeriod === 'week' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => handleTimelinePeriodChange('week')}
                          >
                            Неделя
                          </Button>
                          <Button
                            variant={timelinePeriod === 'month' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => handleTimelinePeriodChange('month')}
                          >
                            Месяц
                          </Button>
                          <Button
                            variant={timelinePeriod === 'quarter' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => handleTimelinePeriodChange('quarter')}
                          >
                            Квартал
                          </Button>
                          <Button
                            variant={showCalendar ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => setShowCalendar(!showCalendar)}
                            className="flex items-center gap-2"
                          >
                            <Calendar className="w-4 h-4" />
                            Календарь
                          </Button>
                        </div>
                      </div>
                      {/* Календарь для выбора дат */}
                      {showCalendar && (
                        <div className="mt-4 p-4 bg-gray-50 rounded-lg border">
                          <div className="flex gap-4 items-end">
                            <div className="flex-1">
                              <label className="text-sm font-medium text-gray-700 mb-2 block">
                                Начальная дата
                              </label>
                              <input
                                type="date"
                                value={selectedStartDate ? selectedStartDate.toISOString().split('T')[0] : ''}
                                onChange={(e) => {
                                  if (e.target.value) {
                                    setSelectedStartDate(new Date(e.target.value));
                                  }
                                }}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                              />
                            </div>
                            <div className="flex-1">
                              <label className="text-sm font-medium text-gray-700 mb-2 block">
                                Конечная дата
                              </label>
                              <input
                                type="date"
                                value={selectedEndDate ? selectedEndDate.toISOString().split('T')[0] : ''}
                                onChange={(e) => {
                                  if (e.target.value) {
                                    setSelectedEndDate(new Date(e.target.value));
                                  }
                                }}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                              />
                            </div>
                            <Button
                              size="sm"
                              onClick={() => {
                                if (selectedStartDate && selectedEndDate) {
                                  handleDateRangeSelect(selectedStartDate, selectedEndDate);
                                }
                              }}
                              disabled={!selectedStartDate || !selectedEndDate}
                            >
                              Применить
                            </Button>
                          </div>
                        </div>
                      )}
                    </CardHeader>
                    <CardContent>
                      {quizTimeline && quizTimeline.length > 0 ? (
                        <ActivityLineChart 
                          data={[]}
                          quizTimeline={quizTimeline}
                          section="quizzes"
                        />
                      ) : (
                        <div className="h-80 flex items-center justify-center">
                          <div className="text-center">
                            <Target className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                            <p className="text-gray-400">Нет данных о тестах</p>
                            <p className="text-xs text-gray-500 mt-2">Данные появятся после прохождения тестов</p>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="recommendations" className="space-y-4 mt-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Lightbulb className="w-5 h-5 text-yellow-500" />
                        Рекомендации
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {(() => {
                        const avgScore = stats?.quiz_analytics?.avg_score || (detailedAnalytics?.length > 0 ? detailedAnalytics.reduce((sum, q) => sum + (q.avg_score || 0), 0) / detailedAnalytics.length : 0);
                        const maxScore = stats?.quiz_analytics?.max_score || Math.max(...(detailedAnalytics?.map(q => q.best_score || 0) || [0]), 0);
                        
                        return (
                          <>
                            {avgScore < 70 && avgScore > 0 && (
                              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                                <p className="font-semibold text-red-900 mb-2">⚠️ Низкий средний балл</p>
                                <p className="text-sm text-red-800">Рекомендуем повторить материал перед повторной попыткой. Изучите теорию и упражнения более внимательно.</p>
                              </div>
                            )}
                            {maxScore >= 90 && (
                              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                                <p className="font-semibold text-green-900 mb-2">🎉 Отличные результаты!</p>
                                <p className="text-sm text-green-800">Вы показываете отличные знания! Продолжайте в том же духе.</p>
                              </div>
                            )}
                            {detailedAnalytics && detailedAnalytics.length === 0 && (
                              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                                <p className="font-semibold text-blue-900 mb-2">📝 Начните проходить тесты</p>
                                <p className="text-sm text-blue-800">Вы еще не прошли ни одного теста. Найдите урок с тестом и проверьте свои знания!</p>
                              </div>
                            )}
                          </>
                        );
                      })()}
                    </CardContent>
                  </Card>
                </TabsContent>
              </>
            )}

            {/* Аналитика по упражнениям */}
            {analyticsSection === 'exercises' && (
              <>
                <TabsContent value="overview" className="space-y-4 mt-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Выполнено упражнений</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-purple-600">
                          {stats?.total_exercises_completed || 0}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Баллов заработано</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-green-600">
                          {stats?.points_breakdown?.exercises || stats?.points_breakdown?.exercise_review || 0}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-600">Время на упражнения</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold text-blue-600">
                          {stats?.points_breakdown?.exercise_review_time_minutes || 0}
                        </div>
                        <p className="text-xs text-gray-500">минут</p>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="statistics" className="space-y-4 mt-6">
                  {detailedAnalytics && detailedAnalytics.length > 0 ? (
                    <div className="space-y-4">
                      {detailedAnalytics.map((lessonExercises, index) => (
                        <Card key={index}>
                          <CardHeader>
                            <CardTitle>{lessonExercises.lesson_title}</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                              <div>
                                <p className="text-sm text-gray-600">Всего упражнений</p>
                                <p className="text-xl font-bold">{lessonExercises.total_exercises}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Проверено</p>
                                <p className="text-xl font-bold">{lessonExercises.reviewed_exercises}</p>
                                <p className="text-xs text-gray-500">из {lessonExercises.total_exercises}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Баллов заработано</p>
                                <p className="text-xl font-bold">{lessonExercises.total_points_earned}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Время проверки</p>
                                <p className="text-xl font-bold">{lessonExercises.total_review_time_minutes} мин</p>
                              </div>
                            </div>
                            {lessonExercises.exercises && lessonExercises.exercises.length > 0 && (
                              <div className="mt-4 space-y-3">
                                <p className="text-sm font-semibold">Детали упражнений:</p>
                                {lessonExercises.exercises.map((exercise, idx) => (
                                  <div key={idx} className="border rounded-lg p-4">
                                    <div className="flex justify-between items-start mb-2">
                                      <span className="font-semibold">Упражнение #{idx + 1}</span>
                                      <span className={`px-2 py-1 rounded text-xs ${
                                        exercise.reviewed 
                                          ? exercise.points_earned > 0 
                                            ? 'bg-green-100 text-green-800' 
                                            : 'bg-red-100 text-red-800'
                                          : 'bg-yellow-100 text-yellow-800'
                                      }`}>
                                        {exercise.reviewed 
                                          ? exercise.points_earned > 0 
                                            ? '✅ Проверено' 
                                            : '❌ Не засчитано'
                                          : '⏳ Ожидает проверки'}
                                      </span>
                                    </div>
                                    <p className="text-sm text-gray-700 mb-2">{exercise.response_text}</p>
                                    {exercise.admin_comment && (
                                      <div className="mt-2 p-2 bg-blue-50 rounded">
                                        <p className="text-xs font-semibold text-blue-900">Комментарий преподавателя:</p>
                                        <p className="text-sm text-blue-800">{exercise.admin_comment}</p>
                                      </div>
                                    )}
                                    <div className="flex justify-between text-xs text-gray-500 mt-2">
                                      <span>Баллов: {exercise.points_earned}</span>
                                      {exercise.submitted_at && (
                                        <span>Отправлено: {new Date(exercise.submitted_at).toLocaleString('ru-RU')}</span>
                                      )}
                                      {exercise.reviewed_at && (
                                        <span>Проверено: {new Date(exercise.reviewed_at).toLocaleString('ru-RU')}</span>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <Card>
                      <CardContent className="py-8 text-center text-gray-500">
                        Нет данных об упражнениях
                      </CardContent>
                    </Card>
                  )}
                </TabsContent>

                <TabsContent value="recommendations" className="space-y-4 mt-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Lightbulb className="w-5 h-5 text-yellow-500" />
                        Рекомендации
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {stats?.total_exercises_completed < 5 && (
                        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                          <p className="font-semibold text-yellow-900 mb-2">💪 Увеличьте количество упражнений</p>
                          <p className="text-sm text-yellow-800">Выполняйте больше упражнений для лучшего закрепления материала. Практика - ключ к успеху!</p>
                        </div>
                      )}
                      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <p className="font-semibold text-blue-900 mb-2">📝 Внимательно читайте комментарии</p>
                        <p className="text-sm text-blue-800">Обращайте внимание на комментарии преподавателя к вашим ответам. Это поможет улучшить результаты.</p>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </>
            )}
          </Tabs>
        )}
      </div>
    );
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {showAnalytics ? (
        renderAnalytics()
      ) : currentLesson ? (
        renderLessonContent()
      ) : (
        <>
          {/* Заголовок */}
          <div className="text-center mb-8">
            <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Система Обучения V2
            </h1>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Интерактивная платформа для глубокого изучения нумерологии с персональной аналитикой
            </p>
          </div>

          {/* Дашборд студента */}
          {dashboardStats ? (
            <div className="mb-8 space-y-6">
              {/* Hero Section - Уровень и прогресс */}
              <Card className="bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-600 text-white border-0 shadow-xl overflow-hidden relative">
                <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -translate-y-32 translate-x-32"></div>
                <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/10 rounded-full translate-y-24 -translate-x-24"></div>
                <CardContent className="pt-8 pb-8 relative z-10">
                  <div className="text-center">
                    <div className="text-6xl mb-4">{['🌱', '📚', '🎓', '⭐', '👑'][dashboardStats.level - 1] || '🌱'}</div>
                    <h2 className="text-3xl font-bold mb-2">Уровень {dashboardStats.level} - {dashboardStats.level_name}</h2>
                    <p className="text-xl text-white/90 mb-6">{dashboardStats.total_points} баллов</p>
                    <div className="max-w-md mx-auto">
                      <div className="flex justify-between text-sm mb-2">
                        <span>Прогресс до следующего уровня</span>
                        <span>{dashboardStats.progress_to_next_level}%</span>
                      </div>
                      <Progress value={dashboardStats.progress_to_next_level} className="h-3 bg-white/20" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Quick Stats */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Уроки */}
                <Card 
                  onClick={() => handleStatsCardClick('lessons')}
                  className="hover:shadow-lg transition-shadow cursor-pointer select-none hover:scale-[1.02] active:scale-[0.98]"
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleStatsCardClick('lessons');
                    }
                  }}
                >
            <CardContent className="pt-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="p-3 bg-blue-100 rounded-lg">
                        <BookOpen className="w-6 h-6 text-blue-600" />
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {dashboardStats.completed_lessons}/{dashboardStats.total_lessons}
                      </Badge>
                    </div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-1">{dashboardStats.completed_lessons}</h3>
                    <p className="text-sm text-gray-600">Уроков завершено</p>
                    <Progress value={(dashboardStats.completed_lessons / dashboardStats.total_lessons) * 100} className="mt-3 h-2" />
                  </CardContent>
                </Card>

                {/* Челленджи */}
                <Card 
                  onClick={() => handleStatsCardClick('challenges')}
                  className="hover:shadow-lg transition-shadow cursor-pointer select-none hover:scale-[1.02] active:scale-[0.98]"
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleStatsCardClick('challenges');
                    }
                  }}
                >
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="p-3 bg-purple-100 rounded-lg">
                        <Zap className="w-6 h-6 text-purple-600" />
                      </div>
                      <Badge variant="outline" className="text-xs bg-purple-50">
                        {dashboardStats.total_challenge_points} баллов
                      </Badge>
                    </div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-1">{dashboardStats.total_challenge_attempts}</h3>
                    <p className="text-sm text-gray-600">Челленджей пройдено</p>
                  </CardContent>
                </Card>

                {/* Тесты */}
                <Card 
                  onClick={() => handleStatsCardClick('quizzes')}
                  className="hover:shadow-lg transition-shadow cursor-pointer select-none hover:scale-[1.02] active:scale-[0.98]"
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleStatsCardClick('quizzes');
                    }
                  }}
                >
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="p-3 bg-green-100 rounded-lg">
                        <Target className="w-6 h-6 text-green-600" />
                      </div>
                      <Badge variant="outline" className="text-xs bg-green-50">
                        {dashboardStats.total_quiz_points} баллов
                      </Badge>
                    </div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-1">{dashboardStats.total_quiz_attempts}</h3>
                    <p className="text-sm text-gray-600">Тестов пройдено</p>
                  </CardContent>
                </Card>

                {/* Упражнения */}
                <Card 
                  onClick={() => handleStatsCardClick('exercises')}
                  className="hover:shadow-lg transition-shadow cursor-pointer select-none hover:scale-[1.02] active:scale-[0.98]"
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleStatsCardClick('exercises');
                    }
                  }}
                >
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="p-3 bg-orange-100 rounded-lg">
                        <Brain className="w-6 h-6 text-orange-600" />
                      </div>
                    </div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-1">{dashboardStats.total_exercises_completed}</h3>
                    <p className="text-sm text-gray-600">Упражнений выполнено</p>
                  </CardContent>
                </Card>
              </div>

              {/* Разбивка баллов */}
              {dashboardStats.points_breakdown && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="w-5 h-5 text-blue-600" />
                      Разбивка баллов
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {/* Челленджи */}
                      <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
                        <div className="flex items-center gap-2 mb-2">
                          <Zap className="w-5 h-5 text-purple-600" />
                          <p className="text-sm font-medium text-gray-700">Челленджи</p>
                        </div>
                        <p className="text-2xl font-bold text-purple-600">
                          {dashboardStats.points_breakdown.challenges || 0}
                        </p>
                        <p className="text-xs text-gray-600 mt-1">баллов</p>
                      </div>

                      {/* Тесты */}
                      <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
                        <div className="flex items-center gap-2 mb-2">
                          <Target className="w-5 h-5 text-green-600" />
                          <p className="text-sm font-medium text-gray-700">Тесты</p>
                        </div>
                        <p className="text-2xl font-bold text-green-600">
                          {dashboardStats.points_breakdown.quizzes || 0}
                        </p>
                        <p className="text-xs text-gray-600 mt-1">баллов</p>
                      </div>

                      {/* Время */}
                      <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
                        <div className="flex items-center gap-2 mb-2">
                          <Clock className="w-5 h-5 text-blue-600" />
                          <p className="text-sm font-medium text-gray-700">Время</p>
                        </div>
                        <p className="text-2xl font-bold text-blue-600">
                          {dashboardStats.points_breakdown.time || 0}
                        </p>
                        <p className="text-xs text-gray-600 mt-1">баллов</p>
                        <p className="text-xs text-gray-500">
                          {dashboardStats.points_breakdown.time_minutes || 0} минут
                        </p>
                      </div>

                      {/* Видео */}
                      <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-4 rounded-lg border border-orange-200">
                        <div className="flex items-center gap-2 mb-2">
                          <Eye className="w-5 h-5 text-orange-600" />
                          <p className="text-sm font-medium text-gray-700">Видео</p>
                        </div>
                        <p className="text-2xl font-bold text-orange-600">
                          {dashboardStats.points_breakdown.videos || 0}
                        </p>
                        <p className="text-xs text-gray-600 mt-1">баллов</p>
                        <p className="text-xs text-gray-500">
                          {dashboardStats.points_breakdown.video_minutes || 0} минут просмотра
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Достижения (компактная версия) */}
              {dashboardStats.achievements && dashboardStats.achievements.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Trophy className="w-5 h-5 text-yellow-600" />
                      Достижения
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-3">
                      {dashboardStats.achievements.filter(a => a.earned).slice(0, 6).map((achievement) => (
                        <div
                          key={achievement.id}
                          className="flex items-center gap-2 bg-gradient-to-br from-yellow-50 to-orange-50 px-4 py-2 rounded-lg border border-yellow-200"
                        >
                          <span className="text-2xl">{achievement.icon}</span>
                          <div>
                            <p className="text-sm font-semibold text-gray-900">{achievement.title}</p>
                            <p className="text-xs text-gray-600">{achievement.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          ) : (
            <Card className="mb-8">
              <CardContent className="pt-6 pb-6">
              <div className="text-center">
                  <div className="animate-pulse flex flex-col items-center gap-3">
                    <BarChart3 className="w-12 h-12 text-blue-600" />
                    <p className="text-gray-600">Загрузка статистики...</p>
                </div>
              </div>
            </CardContent>
          </Card>
          )}

          {/* Список уроков */}
          <div className="space-y-6">
            {lessons.map(lesson => renderLessonCard(lesson))}
          </div>

          {lessons.length === 0 && (
            <div className="text-center py-12">
              <BookOpen className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Уроки готовятся
              </h3>
              <p className="text-gray-600">
                Скоро здесь появятся новые интерактивные уроки
              </p>
            </div>
          )}
        </>
      )}
      
      {/* Модальное окно просмотра файлов */}
      {fileViewerOpen && viewingFile && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4">
          <div 
            className={`bg-white rounded-lg flex flex-col shadow-2xl transition-all ${
              isFullscreen 
                ? 'w-full h-full max-w-full max-h-full' 
                : 'max-w-6xl w-full h-[95vh]'
            }`}
          >
            {/* Заголовок */}
            <div className="border-b border-gray-200 px-6 py-4 bg-gradient-to-r from-blue-50 to-indigo-50 flex-shrink-0">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {(() => {
                    const fileStyle = getFileStyle(viewingFile);
                    return (
                      <div 
                        className="p-2 rounded-lg"
                        style={{ backgroundColor: fileStyle.bgColor }}
                      >
                        {fileStyle.icon}
                      </div>
                    );
                  })()}
                  <div>
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                      Просмотр файла
                    </h2>
                    <p className="text-sm text-gray-600 mt-1">
                      {viewingFile.original_name} • {(viewingFile.file_size / 1024 / 1024).toFixed(2)} МБ
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsFullscreen(!isFullscreen)}
                    className="text-gray-500 hover:text-gray-700"
                    title={isFullscreen ? "Свернуть" : "Развернуть на весь экран"}
                  >
                    {isFullscreen ? (
                      <Minimize2 className="w-5 h-5" />
                    ) : (
                      <Maximize2 className="w-5 h-5" />
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleCloseFileViewer}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <X className="w-5 h-5" />
                  </Button>
                </div>
              </div>
            </div>

            {/* Содержимое */}
            <div className="flex-1 overflow-auto p-6 bg-gray-50">
              {/* Изображения */}
              {viewingFile.mime_type?.startsWith('image/') && (
                <div className="flex items-center justify-center h-full">
                  <div
                    className="relative"
                    style={{ transform: `rotate(${imageRotation}deg)`, transition: 'transform 0.3s ease' }}
                  >
                    <img
                      src={`${backendUrl}/uploads/learning_v2/${viewingFile.stored_name}`}
                      alt={viewingFile.original_name}
                      className="max-w-full max-h-full object-contain rounded-lg shadow-lg"
                    />
                  </div>
                </div>
              )}

              {/* Видео */}
              {viewingFile.mime_type?.startsWith('video/') && (
                <div className="flex items-center justify-center h-full">
                  <video
                    controls
                    className="max-w-full max-h-full rounded-lg shadow-lg"
                    src={`${backendUrl}/uploads/learning_v2/${viewingFile.stored_name}`}
                  >
                    Ваш браузер не поддерживает воспроизведение видео.
                  </video>
                </div>
              )}

              {/* PDF */}
              {viewingFile.extension === 'pdf' && (
                <iframe
                  src={`${backendUrl}/uploads/learning_v2/${viewingFile.stored_name}`}
                  className="w-full h-full rounded-lg shadow-lg"
                  title={viewingFile.original_name}
                />
              )}

              {/* Текстовые файлы */}
              {viewingFile.mime_type?.startsWith('text/') && (
                <div className="bg-white p-6 rounded-lg shadow-lg h-full overflow-auto">
                  <iframe
                    src={`${backendUrl}/uploads/learning_v2/${viewingFile.stored_name}`}
                    className="w-full h-full border-0"
                    title={viewingFile.original_name}
                  />
                </div>
              )}

              {/* Документы Word, Excel */}
              {(viewingFile.extension === 'doc' || 
                viewingFile.extension === 'docx' || 
                viewingFile.extension === 'xls' || 
                viewingFile.extension === 'xlsx') && (
                <div className="flex flex-col items-center justify-center h-full gap-4">
                  <FileText className="w-24 h-24 text-gray-400" />
                  <p className="text-lg font-semibold text-gray-700">
                    Просмотр {viewingFile.extension.toUpperCase()} файлов в браузере не поддерживается
                  </p>
                  <p className="text-sm text-gray-500 mb-4">
                    Скачайте файл для просмотра
                  </p>
                  <Button
                    onClick={() => handleDownloadFile(viewingFile)}
                    className="bg-green-600 hover:bg-green-700 text-white"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Скачать файл
                  </Button>
                </div>
              )}
            </div>

            {/* Футер */}
            <div className="border-t border-gray-200 px-6 py-4 bg-gray-50 flex gap-2 justify-between items-center">
              {/* Кнопки поворота (только для изображений) */}
              {viewingFile.mime_type?.startsWith('image/') && (
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setImageRotation((prev) => (prev - 90) % 360)}
                    title="Повернуть влево"
                  >
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Повернуть влево
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setImageRotation((prev) => (prev + 90) % 360)}
                    title="Повернуть вправо"
                  >
                    <RotateCw className="w-4 h-4 mr-2" />
                    Повернуть вправо
                  </Button>
                </div>
              )}
              
              {/* Основные кнопки */}
              <div className="flex gap-2 ml-auto">
                <Button
                  variant="outline"
                  onClick={handleCloseFileViewer}
                >
                  <X className="w-4 h-4 mr-2" />
                  Закрыть
                </Button>
                <Button
                  onClick={() => handleDownloadFile(viewingFile)}
                  className="bg-green-600 hover:bg-green-700 text-white"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Скачать
                </Button>
                <Button
                  onClick={() => {
                    window.open(`${backendUrl}/api/download-file/${viewingFile.id}`, '_blank');
                  }}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  <ExternalLink className="w-4 h-4 mr-2" />
                  Открыть в новой вкладке
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LearningSystemV2;
