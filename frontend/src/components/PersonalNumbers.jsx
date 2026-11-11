import React, { useState, useEffect } from 'react';
import NarrationPanel from '../features/learning/NarrationPanel';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Loader, Calculator, Menu, X, Info } from 'lucide-react';
import { useAuth } from './AuthContext';
import axios from 'axios';
import { PLANET_COLORS } from './constants/colors';
import { getBackendUrl } from '../utils/backendUrl';
import { useTheme } from '../hooks/useTheme';
import { getTitleGlow, getTextGlow } from '../utils/textGlow';

const PersonalNumbers = ({ fullScreen = false, onBack, theme = 'dark' }) => {
  const { user } = useAuth();
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [cost, setCost] = useState(7); // Стоимость расчёта
  
  // Detail modal state
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailTitle, setDetailTitle] = useState('');
  const [detailText, setDetailText] = useState('');
  const [showFormula, setShowFormula] = useState(null);

  const backendUrl = getBackendUrl();
  const themeConfig = useTheme(theme);

  // Загружаем стоимость из API
  useEffect(() => {
    const fetchCost = async () => {
      try {
        const response = await fetch(`${backendUrl}/api/credits/costs`);
        if (response.ok) {
          const data = await response.json();
          setCost(data.personal_numbers || 7);
        }
      } catch (e) {
        console.warn('Не удалось загрузить стоимость:', e);
      }
    };
    fetchCost();
  }, [backendUrl]);

  // УБРАНА автозагрузка - пользователь должен сам нажать кнопку и увидеть стоимость
  // useEffect(() => {
  //   if (user?.birth_date) calculate();
  // }, [user?.birth_date]);

  const calculate = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${backendUrl}/api/numerology/personal-numbers`);
      setResults(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || 'Ошибка расчёта');
    } finally {
      setLoading(false);
    }
  };

  const openDetail = (title, text) => { 
    setDetailTitle(title); 
    setDetailText(text); 
    setDetailOpen(true); 
  };

  const getNumberFormula = (type, value, birthDate) => {
    const detail = results?.report?.numbers?.find(item => item.key === type);
    if (detail) return {title:detail.title, calculation:detail.steps.join(' → ') || 'Недостаточно данных',
      method:detail.method, explanation:[detail.meaning, detail.interpretation, detail.note].filter(Boolean).join(' ')};
    const date = birthDate || user?.birth_date || '';
    const cleanDate = date.replace(/\D/g, '');
    
    const formulas = {
      'soul_number': {
        title: 'Число души (ЧД)',
        description: 'Вычисляется из дня месяца рождения',
        calculation: `День рождения: ${date.split('.')[0]} → ${value}`,
        explanation: 'Число души показывает вашу внутреннюю природу, врождённые качества и таланты.',
        method: 'Берём день месяца из даты рождения. Если число двузначное, складываем цифры до получения однозначного (кроме 11, 22, 33).'
      },
      'mind_number': {
        title: 'Число ума (ЧУ)', 
        description: 'Вычисляется из полной даты рождения',
        calculation: `${date} → ${cleanDate.split('').join(' + ')} = ${value}`,
        explanation: 'Число ума отражает ваш способ мышления, подход к решению проблем и интеллектуальные особенности.',
        method: 'Складываем все цифры даты рождения и приводим к однозначному числу (кроме мастер-чисел 11, 22, 33).'
      },
      'destiny_number': {
        title: 'Число судьбы (ЧС)',
        description: 'Главное число жизненного пути',
        calculation: `${date} → ${cleanDate.split('').join(' + ')} = ${value}`,
        explanation: 'Число судьбы определяет ваш жизненный путь, основные задачи и предназначение в этой жизни.',
        method: 'Идентично числу ума - складываем все цифры даты рождения до однозначного числа.'
      },
      'helping_mind_number': {
        title: 'Помогающее число ума (ЧУ*)',
        description: 'Дополнительные качества ума',
        calculation: `Особый расчёт на основе ${date} = ${value}`,
        explanation: 'Помогающее число ума показывает дополнительные ментальные качества, которые помогают в развитии.',
        method: 'Специальный алгоритм, учитывающий взаимодействие цифр даты рождения и мастер-числа.'
      },
      'wisdom_number': {
        title: 'Число мудрости (ЧМ)',
        description: 'Накопленная мудрость души',
        calculation: `Расчёт мудрости для ${date} = ${value}`,
        explanation: 'Число мудрости отражает духовный опыт души, накопленный в предыдущих воплощениях.',
        method: 'Сложный алгоритм, основанный на нумерологическом анализе полной даты рождения.'
      },
      'ruling_number': {
        title: 'Правящее число (ПЧ)',
        description: 'Управляющее число личности',
        calculation: `Правящее число для ${date} = ${value}`,
        explanation: 'Правящее число определяет доминирующие черты характера и стиль руководства.',
        method: 'Вычисляется как сумма всех цифр даты рождения (день + месяц + год). Мастер-числа 11 и 22 не сводятся к одной цифре.'
      }
    };

    return formulas[type] || {
      title: 'Неизвестное число',
      description: 'Описание недоступно',
      calculation: `${value}`,
      explanation: 'Интерпретация не найдена.',
      method: 'Метод расчёта не определён.'
    };
  };

  const FormulaModal = ({ formula, onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div className={`rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl ${themeConfig.isDark ? 'bg-slate-900 text-slate-100 border border-slate-700' : 'bg-white text-slate-900'}`}>
        <div className={`sticky top-0 border-b p-6 flex justify-between items-center ${themeConfig.isDark ? 'bg-slate-900 border-slate-700' : 'bg-white border-slate-200'}`}>
          <h3 
            className={`text-2xl font-bold flex items-center ${themeConfig.text}`}
            style={getTitleGlow(themeConfig.isDark, '#60a5fa')}
          >
            <Calculator className="w-7 h-7 mr-3 text-blue-500" />
            {formula.title}
          </h3>
          <button 
            onClick={onClose} 
            className={`p-2 rounded-lg transition-colors ${themeConfig.isDark ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-800' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'}`}
          >
            <X className="w-6 h-6" />
          </button>
        </div>
        
        <div className="p-6 space-y-5">
          {formula.narrationId&&<NarrationPanel clipId={formula.narrationId}/>}
          <div className={`p-5 rounded-xl ${themeConfig.isDark ? 'bg-blue-500/20 border border-blue-500/30' : 'bg-blue-50'}`}>
            <h4 
              className={`font-semibold mb-3 text-lg ${themeConfig.isDark ? 'text-blue-300' : 'text-blue-800'}`}
              style={getTitleGlow(themeConfig.isDark, '#60a5fa')}
            >
              🧮 Формула расчёта:
            </h4>
            <div 
              className={`font-mono text-base ${themeConfig.isDark ? 'text-blue-100' : 'text-blue-900'}`}
              style={getTextGlow(themeConfig.isDark, '#93c5fd')}
            >
              {formula.calculation}
            </div>
          </div>
          
          <div className={`p-5 rounded-xl ${themeConfig.isDark ? 'bg-green-500/20 border border-green-500/30' : 'bg-green-50'}`}>
            <h4 
              className={`font-semibold mb-3 text-lg ${themeConfig.isDark ? 'text-green-300' : 'text-green-800'}`}
              style={getTitleGlow(themeConfig.isDark, '#34d399')}
            >
              📖 Метод вычисления:
            </h4>
            <p 
              className={`text-base leading-relaxed ${themeConfig.isDark ? 'text-green-100' : 'text-green-900'}`}
              style={getTextGlow(themeConfig.isDark, '#86efac')}
            >
              {formula.method}
            </p>
          </div>
          
          <div className={`p-5 rounded-xl ${themeConfig.isDark ? 'bg-purple-500/20 border border-purple-500/30' : 'bg-purple-50'}`}>
            <h4 
              className={`font-semibold mb-3 text-lg ${themeConfig.isDark ? 'text-purple-300' : 'text-purple-800'}`}
              style={getTitleGlow(themeConfig.isDark, '#c084fc')}
            >
              💫 Значение числа:
            </h4>
            <p 
              className={`text-base leading-relaxed ${themeConfig.isDark ? 'text-purple-100' : 'text-purple-900'}`}
              style={getTextGlow(themeConfig.isDark, '#d8b4fe')}
            >
              {formula.explanation}
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  const planetLabelColor = (digit) => {
    switch (digit) {
      case 1: return PLANET_COLORS.Surya;
      case 2: return PLANET_COLORS.Chandra;
      case 3: return PLANET_COLORS.Guru;
      case 4: return PLANET_COLORS.Rahu;
      case 5: return PLANET_COLORS.Buddhi;
      case 6: return PLANET_COLORS.Shukra;
      case 7: return PLANET_COLORS.Ketu;
      case 8: return PLANET_COLORS.Shani;
      case 9: return PLANET_COLORS.Mangal;
      default: return '#475569';
    }
  };

  // Detailed interpretations for personal numbers
  const getNumberInterpretation = (type, number) => {
    const detail = results?.report?.numbers?.find(item => item.key === `${type}_number`);
    if (detail) return [detail.meaning, detail.interpretation, detail.note].filter(Boolean).join('\n\n');
    const interpretations = {
      soul: {
        description: 'Число Души (ЧД) рассчитывается по дню рождения и показывает вашу истинную сущность, внутреннюю природу и то, кем вы являетесь на самом глубоком уровне.',
        calculation: 'Рассчитывается путем сведения дня рождения к однозначному числу. Например: 10.01.1982 → день 10 → 1+0 = 1',
        details: {
          1: 'Число Души 1 (Солнце): Лидер и индивидуалист. Вы прирожденный руководитель с сильной волей и стремлением к независимости. Ваша задача — вести других за собой, проявляя великодушие и мудрость.',
          2: 'Число Души 2 (Луна): Эмоциональная и чувствительная натура. Вы обладаете интуицией, умением сотрудничать и создавать гармонию. Ваша сила — в способности объединять людей.',
          3: 'Число Души 3 (Юпитер): Мудрый учитель и оптимист. Вы стремитесь к знаниям, любите делиться опытом и вдохновлять других. Ваша миссия — нести свет мудрости в мир.',
          4: 'Число Души 4 (Раху): Трансформатор и революционер. Вы мыслите нестандартно, стремитесь к переменам и имеете сильные амбиции. Ваш путь — через преодоление препятствий к великим достижениям.',
          5: 'Число Души 5 (Меркурий): Коммуникатор и интеллектуал. Вы обладаете живым умом, любознательностью и способностью к адаптации. Ваша роль — связывать людей и идеи.',
          6: 'Число Души 6 (Венера): Творец красоты и гармонии. Вы цените прекрасное, умеете любить и создавать уют. Ваше предназначение — приносить в мир красоту и радость.',
          7: 'Число Души 7 (Кету): Мистик и духовный искатель. Вы обладаете глубокой интуицией и стремитесь к познанию тайн жизни. Ваш путь — духовное развитие и помощь другим в поиске истины.',
          8: 'Число Души 8 (Сатурн): Практик и строитель. Вы дисциплинированы, ответственны и умеете создавать прочные основы. Ваша миссия — создавать стабильность и порядок.',
          9: 'Число Души 9 (Марс): Воин и защитник. Вы обладаете энергией, силой воли и стремлением к справедливости. Ваше предназначение — служить высшим идеалам и защищать слабых.'
        }
      },
      mind: {
        description: 'Число Ума (ЧУ) рассчитывается по месяцу рождения и показывает, как вы мыслите, обрабатываете информацию и принимаете решения.',
        calculation: 'Рассчитывается путем сведения месяца рождения к однозначному числу. Например: 10.01.1982 → месяц 01 → 0+1 = 1',
        details: {
          1: 'Число Ума 1: Независимое и оригинальное мышление. Вы думаете самостоятельно, не следуете толпе и часто находите нестандартные решения.',
          2: 'Число Ума 2: Интуитивное и эмоциональное мышление. Вы принимаете решения сердцем, хорошо чувствуете людей и ситуации.',
          3: 'Число Ума 3: Оптимистичное и расширенное мышление. Вы видите возможности там, где другие видят проблемы, и мыслите глобально.',
          4: 'Число Ума 4: Практичное и методичное мышление. Вы любите порядок, планирование и пошаговое решение задач.',
          5: 'Число Ума 5: Быстрое и гибкое мышление. Вы легко переключаетесь между задачами и быстро обрабатываете информацию.',
          6: 'Число Ума 6: Гармоничное и творческое мышление. Вы стремитесь к балансу и красоте в своих решениях.',
          7: 'Число Ума 7: Глубокое и аналитическое мышление. Вы любите докапываться до сути и понимать скрытые причины.',
          8: 'Число Ума 8: Стратегическое и долгосрочное мышление. Вы планируете на годы вперед и видите большую картину.',
          9: 'Число Ума 9: Идеалистическое и справедливое мышление. Вы думаете о благе многих и стремитесь к высшим целям.'
        }
      },
      destiny: {
        description: 'Число Судьбы (ЧС) рассчитывается как сумма дня, месяца и года рождения (как чисел) и показывает ваш жизненный путь, основные задачи и предназначение. ВСЕГДА приводится к однозначному числу.',
        calculation: 'Сумма дня + месяц + год как чисел, ВСЕГДА сводится к однозначному. Например: 10.01.1982 → 10 + 1 + 1982 = 1993 → 1+9+9+3 = 22 → 2+2 = 4',
        details: {
          1: 'Число Судьбы 1: Путь лидера. Ваша судьба — развивать лидерские качества, быть первопроходцем и вдохновлять других своим примером.',
          2: 'Число Судьбы 2: Путь миротворца. Ваша судьба — создавать гармонию, помогать людям находить общий язык и развивать дипломатические способности.',
          3: 'Число Судьбы 3: Путь творца. Ваша судьба — развивать творческие способности, делиться знаниями и вдохновлять других на рост.',
          4: 'Число Судьбы 4: Путь строителя. Ваша судьба — создавать прочные основы, развивать практические навыки и служить обществу.',
          5: 'Число Судьбы 5: Путь исследователя. Ваша судьба — познавать мир, развивать коммуникативные способности и адаптироваться к переменам.',
          6: 'Число Судьбы 6: Путь заботливого. Ваша судьба — служить семье и обществу, создавать красоту и гармонию в отношениях.',
          7: 'Число Судьбы 7: Путь мудреца. Ваша судьба — развивать духовные способности, искать истину и делиться мудростью с другими.',
          8: 'Число Судьбы 8: Путь достижений. Ваша судьба — развивать организаторские способности, достигать материального успеха и создавать структуры.',
          9: 'Число Судьбы 9: Путь служения. Ваша судьба — служить человечеству, развивать сострадание и помогать в решении глобальных задач.'
        }
      },
      helping_mind: {
        description: 'Помогающее Число Ума (ЧУ*) рассчитывается как сумма дня и месяца рождения (как чисел). Показывает дополнительные ментальные ресурсы и способы мышления, которые поддерживают вас.',
        calculation: 'Сумма дня и месяца как чисел. Например: 10.01.1982 → день 10 + месяц 1 = 11 → 11 (остается мастер-число)',
        details: {
          1: 'Помогающее Число Ума 1: Поддержка через независимость мышления и лидерские решения.',
          2: 'Помогающее Число Ума 2: Поддержка через интуицию, сотрудничество и эмоциональный интеллект.',
          3: 'Помогающее Число Ума 3: Поддержка через оптимизм, творческие решения и обучение.',
          4: 'Помогающее Число Ума 4: Поддержка через систематичность, практичность и терпение.',
          5: 'Помогающее Число Ума 5: Поддержка через адаптивность, коммуникацию и быстрое мышление.',
          6: 'Помогающее Число Ума 6: Поддержка через поиск гармонии, творческий подход и заботу о других.',
          7: 'Помогающее Число Ума 7: Поддержка через глубокий анализ, интуицию и духовное понимание.',
          8: 'Помогающее Число Ума 8: Поддержка через стратегическое планирование и организационные способности.',
          9: 'Помогающее Число Ума 9: Поддержка через широкое видение, идеализм и служение высшим целям.'
        }
      },
      wisdom: {
        description: 'Число Мудрости (ЧМ) рассчитывается как сумма Числа Судьбы + полное число имени. Показывает ваш потенциал накопления и применения жизненной мудрости.',
        calculation: 'Сумма Числа Судьбы + полное число имени. Например: 10.01.1982 → ЧС(22) + число имени = (расчет зависит от имени)',
        details: {
          1: 'Число Мудрости 1: Мудрость лидерства — умение вести других с пониманием и ответственностью.',
          2: 'Число Мудрости 2: Мудрость сердца — способность понимать эмоции и создавать гармонию.',
          3: 'Число Мудрости 3: Мудрость учителя — умение передавать знания и вдохновлять на рост.',
          4: 'Число Мудрости 4: Мудрость строителя — понимание того, как создавать прочные основы.',
          5: 'Число Мудрости 5: Мудрость путешественника — способность адаптироваться и находить связи.',
          6: 'Число Мудрости 6: Мудрость заботливого — понимание важности любви и служения другим.',
          7: 'Число Мудрости 7: Мудрость мистика — способность видеть глубокие истины и духовные законы.',
          8: 'Число Мудрости 8: Мудрость правителя — понимание материального мира и законов успеха.',
          9: 'Число Мудрости 9: Мудрость гуманиста — способность видеть единство всего и служить общему благу.'
        }
      },
      ruling: {
        description: 'Правящее Число (ПЧ) показывает, как вы управляете своей жизнью и какие энергии доминируют в вашем характере.',
        calculation: 'Сумма всех цифр даты, месяца и года рождения. Исключения: 11 и 22 не сводятся к однозначному. Например: 10.01.1982 → 1+0+0+1+1+9+8+2 = 22 → остается 22 (мастер-число)',
        details: {
          1: 'Правящее Число 1: Управление через лидерство, независимость и личную силу.',
          2: 'Правящее Число 2: Управление через сотрудничество, дипломатию и эмоциональную мудрость.',
          3: 'Правящее Число 3: Управление через творчество, оптимизм и способность вдохновлять.',
          4: 'Правящее Число 4: Управление через порядок, систематичность и практичность.',
          5: 'Правящее Число 5: Управление через адаптивность, коммуникацию и свободу.',
          6: 'Правящее Число 6: Управление через гармонию, красоту и служение другим.',
          7: 'Правящее Число 7: Управление через духовность, интуицию и глубокое понимание.',
          8: 'Правящее Число 8: Управление через амбиции, организацию и материальные достижения.',
          9: 'Правящее Число 9: Управление через идеализм, справедливость и служение человечеству.',
          11: 'Правящее Число 11: Мастер-число. Управление через высшую интуицию, духовное лидерство и вдохновение других на пути к просветлению.',
          22: 'Правящее Число 22: Мастер-строитель. Управление через материализацию грандиозных планов, создание долговременных структур и служение человечеству через практические достижения.'
        }
      }
    };
    
    const typeInfo = interpretations[type];
    if (!typeInfo) return 'Информация не найдена';
    
    const fullText = `${typeInfo.description}

КАК РАССЧИТЫВАЕТСЯ:
${typeInfo.calculation}

ДЕТАЛЬНАЯ ИНТЕРПРЕТАЦИЯ:
${typeInfo.details[number] || 'Интерпретация не найдена'}`;
    
    return fullText;
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader className="w-6 h-6 animate-spin mr-2" />
          <span>Рассчитываем ваши персональные числа...</span>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-12">
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          <Button onClick={calculate} className="mt-4 w-full">
            Попробовать снова
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!results) {
    return (
      <Card className={themeConfig.card}>
        <CardHeader className="text-center">
          <CardTitle className={`text-2xl ${themeConfig.text}`}>
            <Calculator className="w-8 h-8 mx-auto mb-2 text-purple-500" />
            Персональные числа
          </CardTitle>
          <CardDescription className={themeConfig.mutedText}>
            Расчёт ваших нумерологических чисел на основе даты рождения
          </CardDescription>
        </CardHeader>
        <CardContent className="py-8 text-center space-y-6">
          <div className={`p-4 rounded-xl border-2 border-dashed ${themeConfig.isDark ? 'border-purple-500/40 bg-purple-500/10' : 'border-purple-300 bg-purple-50'}`}>
            <p className={`text-lg font-semibold ${themeConfig.text}`}>
              💰 Стоимость расчёта
            </p>
            <p className={`text-3xl font-bold mt-2 ${themeConfig.isDark ? 'text-purple-400' : 'text-purple-600'}`}>
              {cost} {cost === 1 ? 'балл' : cost >= 2 && cost <= 4 ? 'балла' : 'баллов'}
            </p>
            {user && (
              <p className={`text-sm mt-2 ${themeConfig.mutedText}`}>
                Ваш баланс: <span className="font-bold">{user.credits_remaining ?? 0}</span> баллов
              </p>
            )}
          </div>
          <Button 
            onClick={calculate} 
            className="numerology-gradient text-lg py-6 px-8"
            disabled={(user?.credits_remaining ?? 0) < cost}
          >
            <Calculator className="w-5 h-5 mr-2" />
            Рассчитать числа ({cost} {cost === 1 ? 'балл' : cost >= 2 && cost <= 4 ? 'балла' : 'баллов'})
          </Button>
          {(user?.credits_remaining ?? 0) < cost && (
            <p className="text-red-500 text-sm">
              ⚠️ Недостаточно баллов для расчёта
            </p>
          )}
        </CardContent>
      </Card>
    );
  }

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

  const PersonalNumberCard = ({ title, value, type, shortDescription }) => (
    <div className={`p-4 rounded-xl shadow border text-center transition-colors ${themeConfig.isDark ? 'bg-slate-800/50 border-slate-700 hover:bg-slate-700/50' : 'bg-white border-slate-200 hover:bg-slate-50'}`}>
      <div className={`text-xs mb-1 ${themeConfig.isDark ? 'text-slate-400' : 'text-gray-500'}`}>{title}</div>
      <div 
        className="text-3xl font-bold mb-2 cursor-pointer hover:scale-110 transition-transform" 
        style={{ color: planetLabelColor(value) }}
        onClick={() => openDetail(title, getNumberInterpretation(type, value))}
      >
        {value ?? '—'}
      </div>
      <div className={`text-xs leading-tight mb-2 ${themeConfig.isDark ? 'text-slate-300' : 'text-gray-600'}`}>{shortDescription}</div>
      {value == null && <p className="text-xs mb-2">Для расчёта укажите имя и фамилию латиницей в профиле.</p>}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setShowFormula({...getNumberFormula(type + '_number', value, user?.birth_date),narrationId:type})}
        className={`text-xs p-1 h-auto ${themeConfig.isDark ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-800'}`}
      >
        <Calculator className="w-3 h-3 mr-1" />
        Формула
      </Button>
    </div>
  );

  const PlanetaryStrengthChart = () => {
    if (!results.planetary_strength) return null;

    const planetNames = ['Солнце', 'Луна', 'Марс', 'Меркурий', 'Юпитер', 'Венера', 'Сатурн'];
    const weekdays = ['ВС', 'ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ'];
    const planetColors = [
      PLANET_COLORS.Surya,    // Солнце
      PLANET_COLORS.Chandra,  // Луна
      PLANET_COLORS.Mangal,   // Марс
      PLANET_COLORS.Buddhi,   // Меркурий
      PLANET_COLORS.Guru,     // Юпитер
      PLANET_COLORS.Shukra,   // Венера
      PLANET_COLORS.Shani     // Сатурн
    ];

    // Создаем данные для графика: день недели -> сила планеты
    const chartData = weekdays.map((day, index) => {
      const planet = planetNames[index];
      const strength = results.planetary_strength[planet] || 0;
      const color = planetColors[index];
      
      return {
        day,
        planet,
        strength,
        color
      };
    });

    return (
      <div className="mt-6">
        <h4 className={`text-lg font-semibold mb-4 text-center ${themeConfig.text}`}>Сила Планет по Дням Недели</h4>
        <div className={`text-xs mb-4 text-center ${themeConfig.isDark ? 'text-slate-400' : 'text-gray-600'}`}>
          День недели рождения: {results.birth_weekday}
        </div>
        
        {/* График с сеткой */}
        <div className={`rounded-lg p-4 relative overflow-hidden ${themeConfig.isDark ? 'bg-slate-900' : 'bg-gray-100'}`}>
          <svg 
            viewBox="0 0 700 400" 
            className="w-full h-64"
            style={{ background: 'linear-gradient(180deg, #1f2937 0%, #111827 100%)' }}
          >
            {/* Сетка */}
            {/* Вертикальные линии */}
            {Array.from({length: 8}, (_, i) => (
              <line 
                key={`v-${i}`}
                x1={100 + i * 80} 
                y1={50} 
                x2={100 + i * 80} 
                y2={350} 
                stroke="rgba(255,255,255,0.2)" 
                strokeWidth="1"
              />
            ))}
            
            {/* Горизонтальные линии */}
            {Array.from({length: 11}, (_, i) => (
              <line 
                key={`h-${i}`}
                x1={100} 
                y1={50 + i * 30} 
                x2={660} 
                y2={50 + i * 30} 
                stroke="rgba(255,255,255,0.2)" 
                strokeWidth="1"
              />
            ))}
            
            {/* Цифры по вертикали (0-9) */}
            {Array.from({length: 10}, (_, i) => (
              <text 
                key={`y-label-${i}`}
                x="85" 
                y={350 - i * 30} 
                fill="rgba(255,255,255,0.7)" 
                fontSize="14" 
                textAnchor="end"
                dominantBaseline="middle"
              >
                {i}
              </text>
            ))}
            
            {/* Дни недели по горизонтали */}
            {weekdays.map((day, i) => (
              <text 
                key={`x-label-${i}`}
                x={140 + i * 80} 
                y="370" 
                fill="rgba(255,255,255,0.8)" 
                fontSize="16" 
                textAnchor="middle"
                fontWeight="bold"
              >
                {day}
              </text>
            ))}
            
            {/* Линия графика */}
            <polyline
              points={chartData.map((point, i) => 
                `${140 + i * 80},${350 - point.strength * 30}`
              ).join(' ')}
              fill="none"
              stroke="#10b981"
              strokeWidth="3"
              strokeLinejoin="round"
            />
            
            {/* Точки на графике */}
            {chartData.map((point, i) => (
              <g key={`point-${i}`}>
                <circle
                  cx={140 + i * 80}
                  cy={350 - point.strength * 30}
                  r="8"
                  fill={point.color}
                  stroke="white"
                  strokeWidth="2"
                />
                <text
                  x={140 + i * 80}
                  y={350 - point.strength * 30}
                  fill="white"
                  fontSize="12"
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fontWeight="bold"
                >
                  {point.strength}
                </text>
              </g>
            ))}
          </svg>
        </div>

        {/* Легенда планет */}
        <div className="mt-4 grid grid-cols-4 md:grid-cols-7 gap-2">
          {chartData.map((point, index) => (
            <div key={point.planet} className={`text-center p-2 rounded-lg border ${themeConfig.isDark ? 'bg-slate-800/50 border-slate-700' : 'bg-gray-50 border-slate-200'}`}>
              <div 
                className="text-sm font-semibold mb-1"
                style={{ color: point.color }}
              >
                {point.planet}
              </div>
              <div className={`text-xs ${themeConfig.isDark ? 'text-slate-400' : 'text-gray-500'}`}>{point.day}</div>
              <div className={`text-lg font-bold ${themeConfig.isDark ? 'text-slate-200' : 'text-gray-800'}`}>
                {point.strength}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className={`${fullScreen ? 'min-h-[calc(100vh-4rem)] py-3' : ''}`}>
      {fullScreen && <FloatingMenu />}
      
      {!fullScreen && (
        <Card className="numerology-gradient">
          <CardHeader className="text-white">
            <CardTitle className="text-2xl">Персональные числа</CardTitle>
            <CardDescription className="text-white/90">
              Ваши ключевые нумерологические характеристики на основе даты: {user?.birth_date}
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      <Card>
        {fullScreen && (
          <CardHeader>
            <CardTitle>Ваши Персональные Числа</CardTitle>
            <CardDescription>
              Кликните на любое число для получения подробной интерпретации
            </CardDescription>
          </CardHeader>
        )}
        <CardContent className="space-y-6">
          
          {/* Основные числа */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <PersonalNumberCard 
              title="ЧД (Число Души)"
              value={results.soul_number}
              type="soul"
              shortDescription="Ваша истинная сущность"
            />
            <PersonalNumberCard 
              title="ЧУ (Число Ума)"
              value={results.mind_number}
              type="mind"
              shortDescription="Как вы мыслите"
            />
            <PersonalNumberCard 
              title="ЧС (Число Судьбы)"
              value={results.destiny_number}
              type="destiny"
              shortDescription="Ваш жизненный путь"
            />
            <PersonalNumberCard 
              title="ЧУ* (Помогающее ЧУ)"
              value={results.helping_mind_number}
              type="helping_mind"
              shortDescription="Дополнительная ментальная поддержка"
            />
            <PersonalNumberCard 
              title="ЧМ (Число Мудрости)"
              value={results.wisdom_number}
              type="wisdom"
              shortDescription="Потенциал мудрости"
            />
            <PersonalNumberCard 
              title="ПЧ (Правящее Число)"
              value={results.ruling_number}
              type="ruling"
              shortDescription="Как вы управляете жизнью"
            />
          </div>

          {/* График силы планет */}
          <PlanetaryStrengthChart />

        </CardContent>
      </Card>

      {/* Detail Modal */}
      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className={`max-w-2xl shadow-2xl ${themeConfig.isDark ? 'bg-slate-900 text-slate-100 border-slate-700' : 'bg-white text-slate-900'}`}>
          <DialogHeader>
            <DialogTitle 
              className={`text-2xl ${themeConfig.text}`}
              style={getTitleGlow(themeConfig.isDark, '#a78bfa')}
            >
              {detailTitle}
            </DialogTitle>
          </DialogHeader>
          <div 
            className={`text-base whitespace-pre-line leading-relaxed max-h-96 overflow-y-auto p-2 ${themeConfig.isDark ? 'text-slate-200' : 'text-slate-700'}`}
            style={getTextGlow(themeConfig.isDark)}
          >
            {detailText}
          </div>
        </DialogContent>
      </Dialog>

      {/* Modal для отображения формул */}
      {showFormula && (
        <FormulaModal formula={showFormula} onClose={() => setShowFormula(null)} />
      )}
    </div>
  );
};



export default PersonalNumbers;
