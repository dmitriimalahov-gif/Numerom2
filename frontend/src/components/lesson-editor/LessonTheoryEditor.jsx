import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Label } from '../ui/label';
import { Input } from '../ui/input';

/**
 * LESSON THEORY EDITOR
 * Компонент для редактирования теоретической части урока
 *
 * Props:
 * - lessonContent: объект с контентом урока
 * - isFirstLesson: boolean - это первый урок?
 * - onSave: (section, field, value) => void - коллбэк сохранения
 * - lessonId: string - ID урока для уникальных ключей
 */
const LessonTheoryEditor = ({
  lessonContent,
  isFirstLesson = false,
  onSave,
  lessonId
}) => {

  // Для первого урока - 3 поля, для остальных - 4 поля
  const defaultTheoryFields = isFirstLesson ? [
    {
      key: 'what_is_numerology',
      defaultLabel: 'Что такое нумерология?',
      placeholder: 'Описание нумерологии...',
      rows: 8
    },
    {
      key: 'cosmic_ship_story',
      defaultLabel: 'История космического корабля',
      placeholder: 'История о космическом корабле и планетах...',
      rows: 12
    },
    {
      key: 'planets_and_numbers',
      defaultLabel: 'Соответствие планет и чисел',
      placeholder: 'Описание соответствия планет и чисел...',
      rows: 8
    }
  ] : [
    {
      key: 'what_is_topic',
      defaultLabel: 'Что изучаем в этом уроке?',
      placeholder: 'Введение в тему урока...',
      rows: 8
    },
    {
      key: 'main_story',
      defaultLabel: 'Основная история/объяснение',
      placeholder: 'Основное содержание урока...',
      rows: 12
    },
    {
      key: 'key_concepts',
      defaultLabel: 'Ключевые концепции',
      placeholder: 'Важные понятия и термины...',
      rows: 8
    },
    {
      key: 'practical_applications',
      defaultLabel: 'Практическое применение',
      placeholder: 'Как применить знания на практике...',
      rows: 8
    }
  ];

  // Получаем кастомные заголовки из theory_labels или используем дефолтные
  const getFieldLabel = (field) => {
    const labelKey = `${field.key}_label`;
    return lessonContent.theory_labels?.[labelKey] || field.defaultLabel;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Теоретическая часть</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {defaultTheoryFields.map((field) => (
          <div key={field.key} className="space-y-2">
            {/* Редактируемый заголовок */}
            <div>
              <Label className="text-xs text-gray-500">Заголовок блока</Label>
              <Input
                key={`label_${field.key}_${lessonId}`}
                className="font-medium"
                defaultValue={getFieldLabel(field)}
                onBlur={(e) => onSave('theory_labels', `${field.key}_label`, e.target.value)}
                placeholder={field.defaultLabel}
              />
            </div>

            {/* Контент блока */}
            <div>
              <Label className="text-xs text-gray-500">Содержание</Label>
              <textarea
                key={`${field.key}_${lessonId}_${lessonContent.theory?.[field.key]?.length || 0}`}
                className="w-full p-3 border rounded-lg min-h-32 text-sm"
                rows={field.rows}
                defaultValue={lessonContent.theory?.[field.key] || ''}
                onBlur={(e) => onSave('theory', field.key, e.target.value)}
                placeholder={field.placeholder}
              />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

export default LessonTheoryEditor;
