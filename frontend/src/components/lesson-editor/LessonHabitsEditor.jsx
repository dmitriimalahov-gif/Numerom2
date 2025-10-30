import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Plus, Edit, Save, Trash2, X } from 'lucide-react';

/**
 * LESSON HABITS EDITOR
 * Компонент для редактирования трекера привычек урока
 *
 * Props:
 * - habitTracker: объект трекера привычек
 * - onAddHabit: (planet, habitData) => Promise<void>
 * - onUpdateHabit: (planet, habitIndex, habitData) => Promise<void>
 * - onDeleteHabit: (planet, habitIndex) => Promise<void>
 * - saving: boolean - идет ли сохранение
 */
const LessonHabitsEditor = ({
  habitTracker,
  onAddHabit,
  onUpdateHabit,
  onDeleteHabit,
  saving = false
}) => {
  const [addingToPlanet, setAddingToPlanet] = useState(null);
  const [editingHabit, setEditingHabit] = useState(null);
  const [habitForm, setHabitForm] = useState({
    habit: '',
    description: ''
  });

  const planets = [
    { key: 'sun', name: 'Солнце (1)', emoji: '☀️' },
    { key: 'moon', name: 'Луна (2)', emoji: '🌙' },
    { key: 'jupiter', name: 'Юпитер (3)', emoji: '🪐' },
    { key: 'rahu', name: 'Раху (4)', emoji: '🌀' },
    { key: 'mercury', name: 'Меркурий (5)', emoji: '☿️' },
    { key: 'venus', name: 'Венера (6)', emoji: '♀️' },
    { key: 'ketu', name: 'Кету (7)', emoji: '🔮' },
    { key: 'saturn', name: 'Сатурн (8)', emoji: '🪐' },
    { key: 'mars', name: 'Марс (9)', emoji: '⚔️' }
  ];

  const handleStartAdding = (planetKey) => {
    setAddingToPlanet(planetKey);
    setHabitForm({ habit: '', description: '' });
    setEditingHabit(null);
  };

  const handleStartEditing = (planetKey, habitIndex, habit) => {
    setEditingHabit({ planet: planetKey, index: habitIndex });
    setHabitForm({ habit: habit.habit, description: habit.description });
    setAddingToPlanet(null);
  };

  const handleSaveNew = async () => {
    if (!habitForm.habit.trim()) return;
    await onAddHabit(addingToPlanet, habitForm);
    setHabitForm({ habit: '', description: '' });
    setAddingToPlanet(null);
  };

  const handleSaveEdit = async () => {
    if (!habitForm.habit.trim()) return;
    await onUpdateHabit(editingHabit.planet, editingHabit.index, habitForm);
    setHabitForm({ habit: '', description: '' });
    setEditingHabit(null);
  };

  const handleDelete = async (planetKey, habitIndex) => {
    if (window.confirm('Удалить эту привычку?')) {
      await onDeleteHabit(planetKey, habitIndex);
    }
  };

  const handleCancel = () => {
    setAddingToPlanet(null);
    setEditingHabit(null);
    setHabitForm({ habit: '', description: '' });
  };

  if (!habitTracker || !habitTracker.planet_habits) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <p className="text-gray-600">Трекер привычек еще не создан для этого урока</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Трекер привычек</CardTitle>
        <CardDescription>
          Редактирование привычек для активации энергий планет
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {planets.map((planet) => {
          const planetHabits = habitTracker.planet_habits?.[planet.key] || [];
          const isAddingHere = addingToPlanet === planet.key;

          return (
            <Card key={planet.key} className="border-purple-200">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <span>{planet.emoji}</span>
                    <span>{planet.name}</span>
                    <Badge variant="outline">{planetHabits.length}</Badge>
                  </CardTitle>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleStartAdding(planet.key)}
                    disabled={isAddingHere || saving}
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    Добавить
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Список привычек */}
                {planetHabits.map((habit, index) => {
                  const isEditing = editingHabit?.planet === planet.key && editingHabit?.index === index;

                  if (isEditing) {
                    return (
                      <Card key={index} className="border-blue-200 bg-blue-50">
                        <CardContent className="p-4 space-y-3">
                          <div>
                            <Label>Название привычки</Label>
                            <input
                              type="text"
                              className="w-full p-2 border rounded-md"
                              value={habitForm.habit}
                              onChange={(e) => setHabitForm({...habitForm, habit: e.target.value})}
                              placeholder="Название привычки"
                            />
                          </div>
                          <div>
                            <Label>Описание</Label>
                            <textarea
                              className="w-full p-2 border rounded-md min-h-20"
                              value={habitForm.description}
                              onChange={(e) => setHabitForm({...habitForm, description: e.target.value})}
                              placeholder="Описание привычки..."
                            />
                          </div>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              onClick={handleSaveEdit}
                              disabled={saving || !habitForm.habit.trim()}
                            >
                              <Save className="w-4 h-4 mr-1" />
                              {saving ? 'Сохранение...' : 'Сохранить'}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={handleCancel}
                              disabled={saving}
                            >
                              <X className="w-4 h-4 mr-1" />
                              Отмена
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  }

                  return (
                    <Card key={index} className="border-gray-200">
                      <CardContent className="p-3">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1">
                            <h5 className="font-semibold text-sm">{habit.habit}</h5>
                            <p className="text-xs text-gray-600 mt-1">{habit.description}</p>
                          </div>
                          <div className="flex gap-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleStartEditing(planet.key, index, habit)}
                              disabled={saving}
                            >
                              <Edit className="w-3 h-3" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleDelete(planet.key, index)}
                              disabled={saving}
                            >
                              <Trash2 className="w-3 h-3 text-red-500" />
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}

                {/* Форма добавления новой привычки */}
                {isAddingHere && (
                  <Card className="border-green-200 bg-green-50">
                    <CardContent className="p-4 space-y-3">
                      <div>
                        <Label>Название привычки</Label>
                        <input
                          type="text"
                          className="w-full p-2 border rounded-md"
                          value={habitForm.habit}
                          onChange={(e) => setHabitForm({...habitForm, habit: e.target.value})}
                          placeholder="Название привычки"
                        />
                      </div>
                      <div>
                        <Label>Описание</Label>
                        <textarea
                          className="w-full p-2 border rounded-md min-h-20"
                          value={habitForm.description}
                          onChange={(e) => setHabitForm({...habitForm, description: e.target.value})}
                          placeholder="Описание привычки..."
                        />
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          onClick={handleSaveNew}
                          disabled={saving || !habitForm.habit.trim()}
                        >
                          <Save className="w-4 h-4 mr-1" />
                          {saving ? 'Сохранение...' : 'Добавить'}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={handleCancel}
                          disabled={saving}
                        >
                          <X className="w-4 h-4 mr-1" />
                          Отмена
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Пустое состояние */}
                {planetHabits.length === 0 && !isAddingHere && (
                  <p className="text-sm text-gray-400 text-center py-4">
                    Привычки для {planet.name} еще не добавлены
                  </p>
                )}
              </CardContent>
            </Card>
          );
        })}
      </CardContent>
    </Card>
  );
};

// Badge component (если его нет в ui/badge)
const Badge = ({ children, variant = "default" }) => {
  const variantClasses = {
    default: "bg-blue-100 text-blue-800",
    outline: "border border-gray-300 text-gray-700"
  };

  return (
    <span className={`px-2 py-1 text-xs rounded-full ${variantClasses[variant]}`}>
      {children}
    </span>
  );
};

export default LessonHabitsEditor;
