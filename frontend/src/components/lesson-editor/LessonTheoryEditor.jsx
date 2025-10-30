import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Label } from '../ui/label';

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
  const theoryFields = isFirstLesson ? [
    {
      key: 'what_is_numerology',
      label: 'Что такое нумерология?',
      placeholder: 'Описание нумерологии...',
      rows: 8
    },
    {
      key: 'cosmic_ship_story',
      label: 'История космического корабля',
      placeholder: 'История о космическом корабле и планетах...',
      rows: 12
    },
    {
      key: 'planets_and_numbers',
      label: 'Соответствие планет и чисел',
      placeholder: 'Описание соответствия планет и чисел...',
      rows: 8
    }
  ] : [
    {
      key: 'what_is_topic',
      label: 'Что изучаем в этом уроке?',
      placeholder: 'Введение в тему урока...',
      rows: 8
    },
    {
      key: 'main_story',
      label: 'Основная история/объяснение',
      placeholder: 'Основное содержание урока...',
      rows: 12
    },
    {
      key: 'key_concepts',
      label: 'Ключевые концепции',
      placeholder: 'Важные понятия и термины...',
      rows: 8
    },
    {
      key: 'practical_applications',
      label: 'Практическое применение',
      placeholder: 'Как применить знания на практике...',
      rows: 8
    }
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Теоретическая часть</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {theoryFields.map((field) => (
          <div key={field.key}>
            <Label>{field.label}</Label>
            <textarea
              key={`${field.key}_${lessonId}_${lessonContent.theory?.[field.key]?.length || 0}`}
              className="w-full p-3 border rounded-lg min-h-32 text-sm"
              rows={field.rows}
              defaultValue={lessonContent.theory?.[field.key] || ''}
              onBlur={(e) => onSave('theory', field.key, e.target.value)}
              placeholder={field.placeholder}
            />
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

export default LessonTheoryEditor;
