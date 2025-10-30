import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Label } from '../ui/label';
import { Plus, Edit, Save } from 'lucide-react';

/**
 * LESSON EXERCISES EDITOR
 * Компонент для редактирования упражнений урока
 *
 * Props:
 * - lessonContent: объект с контентом урока
 * - onAddExercise: (exerciseData) => Promise<void>
 * - onUpdateExercise: (exerciseData) => Promise<void>
 * - saving: boolean - идет ли сохранение
 */
const LessonExercisesEditor = ({
  lessonContent,
  onAddExercise,
  onUpdateExercise,
  saving = false
}) => {
  const [addingExercise, setAddingExercise] = useState(false);
  const [editingExerciseId, setEditingExerciseId] = useState(null);
  const [exerciseForm, setExerciseForm] = useState({
    title: '',
    type: 'reflection',
    content: '',
    instructions: '',
    expected_outcome: ''
  });

  const handleSaveExercise = async () => {
    if (editingExerciseId) {
      // Режим редактирования - обновляем существующее упражнение
      await onUpdateExercise({
        ...exerciseForm,
        id: editingExerciseId
      });
    } else {
      // Режим добавления - создаем новое упражнение
      await onAddExercise(exerciseForm);
    }

    // Очищаем форму
    setExerciseForm({
      title: '',
      type: 'reflection',
      content: '',
      instructions: '',
      expected_outcome: ''
    });
    setAddingExercise(false);
    setEditingExerciseId(null);
  };

  const handleCancel = () => {
    setExerciseForm({
      title: '',
      type: 'reflection',
      content: '',
      instructions: '',
      expected_outcome: ''
    });
    setAddingExercise(false);
    setEditingExerciseId(null);
  };

  const handleEditExercise = (exercise) => {
    setEditingExerciseId(exercise.id);
    setExerciseForm({
      title: exercise.title,
      type: exercise.type,
      content: exercise.content,
      instructions: Array.isArray(exercise.instructions)
        ? exercise.instructions.join('\n')
        : exercise.instructions,
      expected_outcome: exercise.expected_outcome
    });
    setAddingExercise(false); // Закрываем форму добавления если была открыта
  };

  const handleStartAdding = () => {
    setAddingExercise(true);
    setEditingExerciseId(null);
    setExerciseForm({
      title: '',
      type: 'reflection',
      content: '',
      instructions: '',
      expected_outcome: ''
    });
  };

  // Функция для рендеринга формы упражнения
  const renderExerciseForm = (isEditMode, exerciseId = null) => {
    const isThisExerciseBeingEdited = isEditMode && exerciseId;

    return (
      <Card className={isEditMode ? "border-blue-200 bg-blue-50" : "border-green-200 bg-green-50"}>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>{isEditMode ? 'Редактирование упражнения' : 'Новое упражнение'}</span>
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
            <Label>Название упражнения</Label>
            <input
              type="text"
              className="w-full p-2 border rounded-md"
              value={exerciseForm.title}
              onChange={(e) => setExerciseForm({...exerciseForm, title: e.target.value})}
              placeholder="Название упражнения"
            />
          </div>

          <div>
            <Label>Тип упражнения</Label>
            <select
              className="w-full p-2 border rounded-md"
              value={exerciseForm.type}
              onChange={(e) => setExerciseForm({...exerciseForm, type: e.target.value})}
            >
              <option value="reflection">Рефлексия</option>
              <option value="calculation">Расчеты</option>
              <option value="meditation">Медитация</option>
              <option value="practical">Практическое</option>
            </select>
          </div>

          <div>
            <Label>Содержание упражнения</Label>
            <textarea
              className="w-full p-3 border rounded-lg min-h-32"
              value={exerciseForm.content}
              onChange={(e) => setExerciseForm({...exerciseForm, content: e.target.value})}
              placeholder="Описание упражнения..."
            />
          </div>

          <div>
            <Label>Инструкции (по одной на строку)</Label>
            <textarea
              className="w-full p-3 border rounded-lg min-h-24"
              value={exerciseForm.instructions}
              onChange={(e) => setExerciseForm({...exerciseForm, instructions: e.target.value})}
              placeholder="Шаг 1: ..."
            />
          </div>

          <div>
            <Label>Ожидаемый результат</Label>
            <input
              type="text"
              className="w-full p-2 border rounded-md"
              value={exerciseForm.expected_outcome}
              onChange={(e) => setExerciseForm({...exerciseForm, expected_outcome: e.target.value})}
              placeholder="Что должен получить ученик"
            />
          </div>

          <Button
            onClick={handleSaveExercise}
            disabled={saving || !exerciseForm.title.trim()}
            className="w-full"
          >
            <Save className="w-4 h-4 mr-2" />
            {saving ? 'Сохранение...' : (isEditMode ? 'Обновить упражнение' : 'Добавить упражнение')}
          </Button>
        </CardContent>
      </Card>
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Упражнения урока</span>
          <Button onClick={handleStartAdding} size="sm">
            <Plus className="w-4 h-4 mr-2" />
            Добавить упражнение
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Список существующих упражнений */}
        {lessonContent.exercises?.map((exercise, index) => (
          <div key={exercise.id || index} className="space-y-4">
            <Card className="border border-gray-200">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold">{exercise.title}</h4>
                  <div className="flex gap-2">
                    <Badge variant="outline">{exercise.type}</Badge>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleEditExercise(exercise)}
                    >
                      <Edit className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
                <p className="text-sm text-gray-600 mb-2">{exercise.content}</p>
                <p className="text-xs text-gray-500">
                  Ожидаемый результат: {exercise.expected_outcome}
                </p>
              </CardContent>
            </Card>

            {/* Форма редактирования под этим упражнением */}
            {editingExerciseId === exercise.id && renderExerciseForm(true, exercise.id)}
          </div>
        ))}

        {/* Форма добавления нового упражнения */}
        {addingExercise && renderExerciseForm(false)}
      </CardContent>
    </Card>
  );
};

export default LessonExercisesEditor;
