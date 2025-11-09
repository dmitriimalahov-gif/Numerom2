import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Plus, Edit, Save } from 'lucide-react';

/**
 * LESSON QUIZ EDITOR
 * Компонент для редактирования теста урока
 *
 * Props:
 * - lessonContent: объект с контентом урока
 * - onAddQuestion: (questionData) => Promise<void>
 * - onUpdateQuestion: (questionData) => Promise<void>
 * - saving: boolean - идет ли сохранение
 */
const LessonQuizEditor = ({
  lessonContent,
  onAddQuestion,
  onUpdateQuestion,
  saving = false
}) => {
  const [addingQuestion, setAddingQuestion] = useState(false);
  const [editingQuestionId, setEditingQuestionId] = useState(null);
  const [questionForm, setQuestionForm] = useState({
    question: '',
    options: ['', '', '', ''],
    correct_answer: '',
    explanation: ''
  });

  const handleEditQuestion = (question) => {
    setEditingQuestionId(question.id);
    setQuestionForm({
      question: question.question,
      options: question.options || ['', '', '', ''],
      correct_answer: question.correct_answer,
      explanation: question.explanation || ''
    });
    setAddingQuestion(false); // Закрываем форму добавления если была открыта
  };

  const handleStartAdding = () => {
    setAddingQuestion(true);
    setEditingQuestionId(null);
    setQuestionForm({
      question: '',
      options: ['', '', '', ''],
      correct_answer: '',
      explanation: ''
    });
  };

  const handleSaveQuestion = async () => {
    // Валидация
    if (!questionForm.question.trim()) {
      alert('Введите текст вопроса');
      return;
    }

    const filledOptions = questionForm.options.filter(opt => opt.trim());
    if (filledOptions.length < 2) {
      alert('Заполните минимум 2 варианта ответа');
      return;
    }

    if (!questionForm.correct_answer || !questionForm.correct_answer.trim()) {
      alert('Выберите правильный ответ');
      return;
    }

    if (editingQuestionId) {
      // Режим редактирования - обновляем существующий вопрос
      await onUpdateQuestion({
        ...questionForm,
        id: editingQuestionId
      });
    } else {
      // Режим добавления - создаем новый вопрос
      await onAddQuestion(questionForm);
    }

    // Очищаем форму
    setQuestionForm({
      question: '',
      options: ['', '', '', ''],
      correct_answer: '',
      explanation: ''
    });
    setAddingQuestion(false);
    setEditingQuestionId(null);
  };

  const handleCancel = () => {
    setQuestionForm({
      question: '',
      options: ['', '', '', ''],
      correct_answer: '',
      explanation: ''
    });
    setAddingQuestion(false);
    setEditingQuestionId(null);
  };

  // Функция для рендеринга формы вопроса
  const renderQuestionForm = (isEditMode, questionId = null) => {
    return (
      <Card className={isEditMode ? "border-blue-200 bg-blue-50" : "border-purple-200 bg-purple-50"}>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>{isEditMode ? 'Редактирование вопроса' : 'Новый вопрос'}</span>
            <Button
              size="sm"
              variant="outline"
              onClick={handleCancel}
            >
              Отмена
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Текст вопроса</Label>
            <input
              type="text"
              className="w-full p-2 border rounded-md"
              value={questionForm.question}
              onChange={(e) => setQuestionForm({...questionForm, question: e.target.value})}
              placeholder="Введите вопрос"
            />
          </div>

          <div>
            <Label>Варианты ответов</Label>
            {questionForm.options.map((option, idx) => (
              <input
                key={idx}
                type="text"
                className="w-full p-2 border rounded-md mb-2"
                value={option}
                onChange={(e) => {
                  const newOptions = [...questionForm.options];
                  newOptions[idx] = e.target.value;
                  setQuestionForm({...questionForm, options: newOptions});
                }}
                placeholder={`Вариант ${String.fromCharCode(97 + idx)}) ...`}
              />
            ))}
          </div>

          <div>
            <Label>Правильный ответ</Label>
            <select
              className="w-full p-2 border rounded-md"
              value={questionForm.correct_answer}
              onChange={(e) => setQuestionForm({...questionForm, correct_answer: e.target.value})}
            >
              <option value="">Выберите правильный ответ</option>
              <option value="a">a) {questionForm.options[0]}</option>
              <option value="b">b) {questionForm.options[1]}</option>
              <option value="c">c) {questionForm.options[2]}</option>
              <option value="d">d) {questionForm.options[3]}</option>
            </select>
          </div>

          <div>
            <Label>Объяснение правильного ответа</Label>
            <textarea
              className="w-full p-3 border rounded-lg min-h-24"
              value={questionForm.explanation}
              onChange={(e) => setQuestionForm({...questionForm, explanation: e.target.value})}
              placeholder="Объясните почему этот ответ правильный..."
            />
          </div>

          <Button
            onClick={handleSaveQuestion}
            disabled={saving || !questionForm.question.trim()}
            className="w-full"
          >
            <Save className="w-4 h-4 mr-2" />
            {saving ? 'Сохранение...' : (isEditMode ? 'Обновить вопрос' : 'Добавить вопрос')}
          </Button>
        </CardContent>
      </Card>
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Тест по уроку</span>
          <Button onClick={handleStartAdding} size="sm">
            <Plus className="w-4 h-4 mr-2" />
            Добавить вопрос
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Список существующих вопросов */}
        {Array.isArray(lessonContent.quiz?.questions) && lessonContent.quiz.questions.map((question, index) => (
          <div key={question.id || index} className="space-y-4">
            <Card className="border border-gray-200">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold">Вопрос {index + 1}</h4>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleEditQuestion(question)}
                  >
                    <Edit className="w-3 h-3" />
                  </Button>
                </div>
                <p className="text-sm text-gray-700 mb-2">{question.question}</p>
                <div className="text-xs text-gray-500 space-y-1">
                  {Array.isArray(question.options) && question.options.map((opt, idx) => (
                    <p key={idx}>{opt}</p>
                  ))}
                  <p className="font-semibold mt-2">
                    Правильный ответ: {question.correct_answer}
                  </p>
                  {question.explanation && (
                    <p>Объяснение: {question.explanation}</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Форма редактирования под этим вопросом */}
            {editingQuestionId === question.id && renderQuestionForm(true, question.id)}
          </div>
        ))}

        {/* Форма добавления нового вопроса */}
        {addingQuestion && renderQuestionForm(false)}
      </CardContent>
    </Card>
  );
};

export default LessonQuizEditor;
