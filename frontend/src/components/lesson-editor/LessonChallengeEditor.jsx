import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Plus, Edit, Save } from 'lucide-react';

/**
 * LESSON CHALLENGE EDITOR
 * Компонент для редактирования челленджа урока
 *
 * Props:
 * - lessonContent: объект с контентом урока
 * - onSave: (section, field, value) => void - коллбэк сохранения
 * - onAddDay: (dayData) => Promise<void> - добавить новый день
 * - onUpdateDay: (dayData) => Promise<void> - обновить существующий день
 * - lessonId: string - ID урока для уникальных ключей
 * - saving: boolean - идет ли сохранение
 */
const LessonChallengeEditor = ({
  lessonContent,
  onSave,
  onAddDay,
  onUpdateDay,
  lessonId,
  saving = false
}) => {
  const challenge = lessonContent.challenge;

  const [addingDay, setAddingDay] = useState(false);
  const [editingDay, setEditingDay] = useState(null);
  const [dayForm, setDayForm] = useState({
    title: '',
    tasks: ''
  });

  const handleEditDay = (dayTask) => {
    setEditingDay(dayTask.day);
    setDayForm({
      title: dayTask.title,
      tasks: Array.isArray(dayTask.tasks) ? dayTask.tasks.join('\n') : dayTask.tasks
    });
    setAddingDay(false);
  };

  const handleStartAdding = () => {
    setAddingDay(true);
    setEditingDay(null);
    setDayForm({
      title: '',
      tasks: ''
    });
  };

  const handleSaveDay = async () => {
    if (editingDay !== null) {
      // Режим редактирования
      await onUpdateDay({
        day: editingDay,
        title: dayForm.title,
        tasks: dayForm.tasks
      });
    } else {
      // Режим добавления
      await onAddDay({
        title: dayForm.title,
        tasks: dayForm.tasks
      });
    }

    // Очищаем форму
    setDayForm({ title: '', tasks: '' });
    setAddingDay(false);
    setEditingDay(null);
  };

  const handleCancel = () => {
    setDayForm({ title: '', tasks: '' });
    setAddingDay(false);
    setEditingDay(null);
  };

  // Функция для рендеринга формы дня
  const renderDayForm = (isEditMode, dayNum = null) => {
    return (
      <Card className={isEditMode ? "border-blue-200 bg-blue-50 mt-3" : "border-green-200 bg-green-50"}>
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-lg">
            <span>{isEditMode ? `Редактирование дня ${dayNum}` : 'Новый день челленджа'}</span>
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
            <Label>Название дня</Label>
            <input
              type="text"
              className="w-full p-2 border rounded-md"
              value={dayForm.title}
              onChange={(e) => setDayForm({...dayForm, title: e.target.value})}
              placeholder="Осознание своей силы"
            />
          </div>

          <div>
            <Label>Задания на день (по одному на строку)</Label>
            <textarea
              className="w-full p-3 border rounded-lg min-h-32"
              value={dayForm.tasks}
              onChange={(e) => setDayForm({...dayForm, tasks: e.target.value})}
              placeholder="Утром приветствуйте восход солнца...&#10;Запишите 3 свои сильные стороны...&#10;Медитация на Сурью 10 минут..."
            />
          </div>

          <Button
            onClick={handleSaveDay}
            disabled={saving || !dayForm.title.trim()}
            className="w-full"
          >
            <Save className="w-4 h-4 mr-2" />
            {saving ? 'Сохранение...' : (isEditMode ? 'Обновить день' : 'Добавить день')}
          </Button>
        </CardContent>
      </Card>
    );
  };

  if (!challenge) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <p className="text-gray-600">Челлендж пока не создан для этого урока</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Редактирование челленджа</CardTitle>
        <CardDescription>
          Челлендж для активации энергии планет (обычно 7 дней)
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label>Название челленджа</Label>
          <input
            type="text"
            className="w-full p-2 border rounded-md"
            defaultValue={challenge.title || ''}
            onBlur={(e) => onSave('challenge', 'title', e.target.value)}
            placeholder="Название челленджа"
          />
        </div>

        <div>
          <Label>Описание челленджа</Label>
          <textarea
            key={`challenge_desc_${lessonId}_${challenge.description?.length || 0}`}
            className="w-full p-3 border rounded-lg min-h-32"
            defaultValue={challenge.description || ''}
            onBlur={(e) => onSave('challenge', 'description', e.target.value)}
            placeholder="Описание челленджа..."
          />
        </div>

        <div className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-semibold">Задания по дням</h4>
            <Button onClick={handleStartAdding} size="sm">
              <Plus className="w-4 h-4 mr-2" />
              Добавить день
            </Button>
          </div>

          {Array.isArray(challenge.daily_tasks) && challenge.daily_tasks.map((dayTask, index) => (
            <div key={index} className="mb-3">
              <Card className="border-blue-200">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h5 className="font-semibold text-blue-800">
                      День {dayTask.day}: {dayTask.title}
                    </h5>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleEditDay(dayTask)}
                    >
                      <Edit className="w-3 h-3" />
                    </Button>
                  </div>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {Array.isArray(dayTask.tasks) && dayTask.tasks.map((task, taskIdx) => (
                      <li key={taskIdx}>• {task}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              {/* Форма редактирования под этим днем */}
              {editingDay === dayTask.day && renderDayForm(true, dayTask.day)}
            </div>
          ))}

          {/* Форма добавления нового дня */}
          {addingDay && renderDayForm(false)}
        </div>
      </CardContent>
    </Card>
  );
};

export default LessonChallengeEditor;
