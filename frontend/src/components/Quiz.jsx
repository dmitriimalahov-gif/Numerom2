import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Progress } from './ui/progress';
import { Loader, HelpCircle, CheckCircle, Star, Lightbulb } from 'lucide-react';
import { useAuth } from './AuthContext';
import axios from 'axios';
import { getBackendUrl } from '../utils/backendUrl';

// Функция для склонения слова "балл"
const formatCredits = (num) => {
  if (num === 1) return `${num} балл`;
  if (num >= 2 && num <= 4) return `${num} балла`;
  return `${num} баллов`;
};

const Quiz = () => {
  const { user } = useAuth();
  const [quizData, setQuizData] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [quizStarted, setQuizStarted] = useState(false);
  const [cost, setCost] = useState(7); // Стоимость прохождения теста

  const backendUrl = getBackendUrl();

  // Загружаем стоимость из API
  useEffect(() => {
    const fetchCost = async () => {
      try {
        const response = await fetch(`${backendUrl}/api/credits/costs`);
        if (response.ok) {
          const data = await response.json();
          setCost(data.personality_test || 7);
        }
      } catch (e) {
        console.warn('Не удалось загрузить стоимость:', e);
      }
    };
    fetchCost();
  }, [backendUrl]);

  useEffect(() => {
    loadRandomizedQuiz();
  }, []);

  const loadRandomizedQuiz = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${backendUrl}/api/quiz/randomized-questions`);
      setQuizData(response.data);
    } catch (error) {
      console.error('Error loading randomized quiz questions:', error);
      setError('Ошибка при загрузке вопросов');
    } finally {
      setLoading(false);
    }
  };

  const startQuiz = () => {
    setQuizStarted(true);
    setCurrentQuestion(0);
    setAnswers([]);
    setResults(null);
    setError('');
  };

  const handleAnswer = (questionId, selectedOption) => {
    const newAnswer = {
      question_id: questionId,
      value: selectedOption.value,
      text: selectedOption.text
    };

    const newAnswers = [...answers];
    newAnswers[currentQuestion] = newAnswer;
    setAnswers(newAnswers);

    // Move to next question or finish quiz
    if (currentQuestion < quizData.questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      submitQuiz(newAnswers);
    }
  };

  const submitQuiz = async (finalAnswers) => {
    setLoading(true);
    try {
      const response = await axios.post(`${backendUrl}/api/quiz/submit`, finalAnswers);
      setResults(response.data);
      setQuizStarted(false);
    } catch (error) {
      console.error('Error submitting quiz:', error);
      setError(error.response?.data?.detail || 'Ошибка при обработке результатов');
    } finally {
      setLoading(false);
    }
  };

  const goToPreviousQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const getPersonalityDescription = (dominantNumber) => {
    const descriptions = {
      1: "Вы прирожденный лидер с сильной волей и независимым характером. Стремитесь к новым достижениям и не боитесь брать инициативу в свои руки.",
      2: "Вы миротворец и дипломат, цените гармонию в отношениях. Обладаете природной способностью к сотрудничеству и пониманию других людей.",
      3: "Вы творческая личность с ярким воображением и коммуникативными способностями. Легко вдохновляете других своим энтузиазмом.",
      4: "Вы практичный и надежный человек, цените стабильность и порядок. Умеете создавать прочную основу для будущих достижений.",
      5: "Вы свободолюбивая натура, стремящаяся к переменам и новым впечатлениям. Обладаете природным любопытством и жаждой приключений.",
      6: "Вы заботливый и ответственный человек, для которого семья и близкие люди имеют первостепенное значение. Обладаете развитым чувством долга.",
      7: "Вы глубокий мыслитель и интуитивная личность, стремящаяся к познанию тайн жизни. Цените уединение и внутреннее развитие.",
      8: "Вы амбициозный и целеустремленный человек с хорошими организаторскими способностями. Стремитесь к материальному успеху и признанию.",
      9: "Вы мудрый и сострадательный человек с широким взглядом на мир. Стремитесь помогать другим и делать мир лучше."
    };
    return descriptions[dominantNumber] || "Ваша личность уникальна и не укладывается в стандартные рамки.";
  };

  if (loading && !quizData) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader className="w-6 h-6 animate-spin mr-2" />
          <span>Загружаем тест...</span>
        </CardContent>
      </Card>
    );
  }

  if (error && !quizData) {
    return (
      <Card>
        <CardContent className="py-12">
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          <Button onClick={loadRandomizedQuiz} className="mt-4 w-full">
            Попробовать снова
          </Button>
        </CardContent>
      </Card>
    );
  }

  // Quiz Start Screen
  if (!quizStarted && !results && quizData) {
    return (
      <div className="space-y-6">
        <Card className="numerology-gradient">
          <CardHeader className="text-white">
            <CardTitle className="text-2xl flex items-center">
              <HelpCircle className="w-6 h-6 mr-2" />
              {quizData.title}
            </CardTitle>
            <CardDescription className="text-white/90">
              {quizData.description}
            </CardDescription>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>О тесте</CardTitle>
            <CardDescription>
              Что вас ждет в этом путешествии самопознания
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <span className="text-primary font-bold">10</span>
                </div>
                <div>
                  <h4 className="font-semibold">Вопросов</h4>
                  <p className="text-sm text-muted-foreground">Тщательно подобранные для анализа личности</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Star className="w-4 h-4 text-primary" />
                </div>
                <div>
                  <h4 className="font-semibold">Персональный анализ</h4>
                  <p className="text-sm text-muted-foreground">Основанный на ваших ответах</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Lightbulb className="w-4 h-4 text-primary" />
                </div>
                <div>
                  <h4 className="font-semibold">Рекомендации</h4>
                  <p className="text-sm text-muted-foreground">Для личностного развития</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <CheckCircle className="w-4 h-4 text-primary" />
                </div>
                <div>
                  <h4 className="font-semibold">5 минут</h4>
                  <p className="text-sm text-muted-foreground">Среднее время прохождения</p>
                </div>
              </div>
            </div>

            <div className="border-t pt-4">
              <p className="text-sm text-muted-foreground mb-4">
                <strong>Инструкция:</strong> Отвечайте честно и интуитивно. Выбирайте первый ответ, 
                который приходит в голову. Нет правильных или неправильных ответов.
              </p>

              {/* Блок со стоимостью */}
              <div className="mb-4 p-4 rounded-xl border-2 border-dashed border-purple-300 bg-purple-50 dark:border-purple-500/40 dark:bg-purple-500/10">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">💰</span>
                    <span className="text-sm font-semibold">Стоимость прохождения:</span>
                    <span className="text-lg font-bold text-purple-600 dark:text-purple-400">
                      {formatCredits(cost)}
                    </span>
                  </div>
                  {user && (
                    <span className="text-xs text-muted-foreground">
                      Ваш баланс: <span className="font-bold">{user.credits_remaining ?? 0}</span> баллов
                    </span>
                  )}
                </div>
              </div>

              <Button 
                onClick={startQuiz} 
                className="w-full numerology-gradient" 
                size="lg"
                disabled={(user?.credits_remaining ?? 0) < cost}
              >
                <HelpCircle className="w-5 h-5 mr-2" />
                Начать тест самопознания ({formatCredits(cost)})
              </Button>
              {(user?.credits_remaining ?? 0) < cost && (
                <p className="text-sm text-red-500 mt-2 text-center">
                  ⚠️ Недостаточно баллов для прохождения теста
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Quiz Questions
  if (quizStarted && quizData) {
    const question = quizData.questions[currentQuestion];
    const progress = ((currentQuestion + 1) / quizData.questions.length) * 100;

    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between mb-4">
              <Badge variant="outline">
                Вопрос {currentQuestion + 1} из {quizData.questions.length}
              </Badge>
              <span className="text-sm text-muted-foreground">{Math.round(progress)}%</span>
            </div>
            <Progress value={progress} className="mb-4" />
            <CardTitle className="text-xl">{question.question}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {question.options.map((option, index) => (
              <Button
                key={index}
                variant="outline"
                className="w-full text-left justify-start h-auto p-4 hover:bg-primary/5"
                onClick={() => handleAnswer(question.id, option)}
                disabled={loading}
              >
                <div className="flex items-center">
                  <div className="w-6 h-6 rounded-full border-2 border-primary/30 flex items-center justify-center mr-3 flex-shrink-0">
                    <span className="text-xs text-primary">{index + 1}</span>
                  </div>
                  <span>{option.text}</span>
                </div>
              </Button>
            ))}

            <div className="flex justify-between mt-6">
              <Button
                variant="outline"
                onClick={goToPreviousQuestion}
                disabled={currentQuestion === 0 || loading}
              >
                Назад
              </Button>
              
              <div className="text-sm text-muted-foreground flex items-center">
                {loading && <Loader className="w-4 h-4 animate-spin mr-2" />}
                {loading ? 'Обрабатываем результаты...' : 'Выберите ответ'}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Quiz Results
  if (results) {
    return (
      <div className="space-y-6">
        <Card className="numerology-gradient">
          <CardHeader className="text-white text-center">
            <CardTitle className="text-2xl">
              <CheckCircle className="w-8 h-8 mx-auto mb-4" />
              Ваш результат готов!
            </CardTitle>
            <CardDescription className="text-white/90">
              Персональный анализ на основе ваших ответов
            </CardDescription>
          </CardHeader>
        </Card>

        {/* Dominant Number */}
        <Card>
          <CardHeader className="text-center">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center mx-auto mb-4">
              <span className="text-3xl font-bold text-white">{results.dominant_number}</span>
            </div>
            <CardTitle className="text-2xl">{results.personality_type}</CardTitle>
            <CardDescription>Ваш доминирующий нумерологический архетип</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="p-4 bg-muted rounded-lg mb-6">
              <p className="text-center">
                {getPersonalityDescription(results.dominant_number)}
              </p>
            </div>

            {/* Number Frequencies */}
            <div className="space-y-3 mb-6">
              <h4 className="font-semibold">Распределение ваших ответов:</h4>
              {Object.entries(results.frequencies)
                .sort(([,a], [,b]) => b - a)
                .map(([number, count]) => (
                  <div key={number} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className={`w-6 h-6 rounded num-${number} flex items-center justify-center`}>
                        <span className="text-xs font-bold text-white">{number}</span>
                      </div>
                      <span className="text-sm">Число {number}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-muted rounded-full h-2">
                        <div
                          className="bg-primary h-2 rounded-full"
                          style={{ width: `${(count / 10) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm text-muted-foreground">{count}/10</span>
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>

        {/* Recommendations */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Lightbulb className="w-5 h-5 mr-2" />
              Персональные рекомендации
            </CardTitle>
            <CardDescription>
              Советы для вашего развития и самореализации
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {results.recommendations.map((recommendation, index) => (
                <div key={index} className="flex items-start space-x-3 p-4 bg-primary/5 rounded-lg">
                  <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-xs font-bold text-primary">{index + 1}</span>
                  </div>
                  <p className="text-sm">{recommendation}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Total Score */}
        <Card>
          <CardContent className="text-center py-6">
            <div className="text-3xl font-bold text-primary mb-2">{results.total_score}</div>
            <div className="text-sm text-muted-foreground">Общий балл теста</div>
          </CardContent>
        </Card>

        {/* Retake Quiz */}
        <div className="text-center">
          <Button onClick={() => {
            setResults(null);
            setQuizStarted(false);
            setCurrentQuestion(0);
            setAnswers([]);
          }} variant="outline" className="w-full md:w-auto">
            <HelpCircle className="w-4 h-4 mr-2" />
            Пройти тест заново
          </Button>
        </div>
      </div>
    );
  }

  return null;
};

export default Quiz;