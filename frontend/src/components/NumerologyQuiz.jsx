import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Progress } from './ui/progress';

const NumerologyQuiz = () => {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [score, setScore] = useState(0);
  const [showResult, setShowResult] = useState(false);
  const [answers, setAnswers] = useState([]);

  const questions = [
    {
      question: "Какая планета управляет числом 1 в ведической нумерологии?",
      options: ["Луна", "Солнце", "Марс", "Меркурий"],
      correct: 1,
      explanation: "Число 1 управляется Сурьей (Солнцем) - планетой лидерства и авторитета."
    },
    {
      question: "Что означает ПЧ в нашем калькуляторе?",
      options: ["Правящее число", "Проблемное число", "Планетное число", "Полное число"],
      correct: 0,
      explanation: "ПЧ - это Правящее Число, которое показывает основную энергию человека."
    },
    {
      question: "Какой цвет соответствует числу 5 (Буддхи/Меркурий)?",
      options: ["Красный", "Синий", "Салатовый", "Фиолетовый"],
      correct: 2,
      explanation: "Число 5 (Буддхи/Меркурий) имеет салатовый цвет, символизирующий рост и развитие ума."
    },
    {
      question: "Что такое ЧИГ?",
      options: ["Число индивидуального года", "Число интуитивной гармонии", "Число измерения года", "Число исходной гипотезы"],
      correct: 0,
      explanation: "ЧИГ - Число Индивидуального Года, показывающее энергетику текущего года для человека."
    },
    {
      question: "В каком порядке расположены планеты в ведическом квадрате?",
      options: ["1-2-3 сверху", "1-4-7 сверху", "7-8-9 сверху", "3-6-9 сверху"],
      correct: 1,
      explanation: "В ведическом квадрате верхний ряд: 1(Сурья), 4(Раху), 7(Кету)."
    },
    {
      question: "Какая планета управляет понедельником?",
      options: ["Солнце", "Луна", "Марс", "Меркурий"],
      correct: 1,
      explanation: "Понедельником управляет Чандра (Луна) - планета эмоций и интуиции."
    },
    {
      question: "Что показывают линии характера в квадрате?",
      options: ["Вертикальные линии", "Горизонтальные линии", "Диагональные линии", "Все линии"],
      correct: 1,
      explanation: "Линии характера - это горизонтальные линии, показывающие силу характера на разных уровнях."
    },
    {
      question: "Как рассчитывается число души?",
      options: ["По году рождения", "По месяцу рождения", "По дню рождения", "По полной дате"],
      correct: 2,
      explanation: "Число души рассчитывается по дню рождения человека."
    },
    {
      question: "Что такое ПИД в нумерологических расчетах?",
      options: ["Проблема индивидуального дня", "Планета индивидуального дня", "Прогноз идеального дня", "Период интенсивного дня"],
      correct: 0,
      explanation: "ПИД - Проблема Индивидуального Дня, указывающая на возможные трудности дня."
    },
    {
      question: "Какое число считается самым мощным в центре квадрата?",
      options: ["1", "5", "9", "7"],
      correct: 1,
      explanation: "Число 5 (Буддхи/Меркурий) в центре квадрата - самое мощное, управляет интеллектом и коммуникацией."
    }
  ];

  const handleAnswer = (selectedIndex) => {
    const isCorrect = selectedIndex === questions[currentQuestion].correct;
    const newAnswers = [...answers, { questionIndex: currentQuestion, selectedIndex, isCorrect }];
    setAnswers(newAnswers);
    
    if (isCorrect) {
      setScore(score + 1);
    }
    
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      setShowResult(true);
    }
  };

  const restartQuiz = () => {
    setCurrentQuestion(0);
    setScore(0);
    setShowResult(false);
    setAnswers([]);
  };

  const getScoreMessage = () => {
    const percentage = (score / questions.length) * 100;
    if (percentage >= 80) return "Отлично! Вы прекрасно знаете ведическую нумерологию!";
    if (percentage >= 60) return "Хорошо! У вас есть базовые знания, продолжайте изучение.";
    if (percentage >= 40) return "Неплохо! Рекомендуем пройти обучающие видео еще раз.";
    return "Нужно больше практики! Изучите материалы и попробуйте снова.";
  };

  const getScoreColor = () => {
    const percentage = (score / questions.length) * 100;
    if (percentage >= 80) return "#22C55E";
    if (percentage >= 60) return "#84CC16";
    if (percentage >= 40) return "#EAB308";
    return "#EF4444";
  };

  if (showResult) {
    return (
      <Card className="border-lime-300 shadow-lg">
        <CardHeader style={{ background: 'linear-gradient(to right, #D9F99D, #BEF264)' }}>
          <CardTitle className="text-lime-800">Результаты квиза</CardTitle>
        </CardHeader>
        <CardContent className="p-6 text-center">
          <div 
            className="text-6xl font-bold mb-4"
            style={{ color: getScoreColor() }}
          >
            {score}/{questions.length}
          </div>
          <div 
            className="text-xl font-semibold mb-4"
            style={{ color: getScoreColor() }}
          >
            {Math.round((score / questions.length) * 100)}%
          </div>
          <p className="text-lg text-gray-700 mb-6">
            {getScoreMessage()}
          </p>
          
          <div className="space-y-3 mb-6 text-left">
            <h4 className="font-semibold text-lime-800">Разбор ответов:</h4>
            {questions.map((q, index) => {
              const userAnswer = answers.find(a => a.questionIndex === index);
              return (
                <div 
                  key={index}
                  className={`p-3 rounded-lg border ${userAnswer?.isCorrect ? 'border-green-300 bg-green-50' : 'border-red-300 bg-red-50'}`}
                >
                  <div className="font-semibold text-sm mb-1">
                    Вопрос {index + 1}: {userAnswer?.isCorrect ? '✓' : '✗'}
                  </div>
                  <div className="text-xs text-gray-600 mb-2">{q.question}</div>
                  <div className="text-xs">
                    <span className="font-semibold">Правильный ответ:</span> {q.options[q.correct]}
                  </div>
                  <div className="text-xs text-gray-600 mt-1">{q.explanation}</div>
                </div>
              );
            })}
          </div>

          <div className="flex gap-4 justify-center">
            <Button 
              onClick={restartQuiz}
              style={{ background: 'linear-gradient(to right, #65A30D, #7FB069)' }}
            >
              Пройти заново
            </Button>
            <Button 
              variant="outline"
              className="border-lime-400 text-lime-700 hover:bg-lime-50"
            >
              Изучить материалы
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-lime-300 shadow-lg">
      <CardHeader style={{ background: 'linear-gradient(to right, #D9F99D, #BEF264)' }}>
        <CardTitle className="text-lime-800">
          Квиз по ведической нумерологии
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-gray-600">
              Вопрос {currentQuestion + 1} из {questions.length}
            </span>
            <span className="text-sm text-lime-700">
              Правильных: {score}
            </span>
          </div>
          <Progress 
            value={((currentQuestion) / questions.length) * 100} 
            className="h-2"
          />
        </div>

        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            {questions[currentQuestion].question}
          </h3>
          
          <div className="space-y-3">
            {questions[currentQuestion].options.map((option, index) => (
              <Button
                key={index}
                variant="outline"
                className="w-full p-4 text-left justify-start border-lime-200 hover:bg-lime-50 hover:border-lime-400"
                onClick={() => handleAnswer(index)}
              >
                <span className="mr-3 font-bold text-lime-700">
                  {String.fromCharCode(65 + index)}.
                </span>
                {option}
              </Button>
            ))}
          </div>
        </div>

        <div className="text-center text-sm text-gray-500">
          Выберите правильный ответ, чтобы продолжить
        </div>
      </CardContent>
    </Card>
  );
};

export default NumerologyQuiz;