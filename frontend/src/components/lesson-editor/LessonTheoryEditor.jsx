import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Label } from '../ui/label';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { Plus, Trash2, GripVertical, Eye } from 'lucide-react';

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
      rows: 8,
      canDelete: false
    },
    {
      key: 'cosmic_ship_story',
      defaultLabel: 'История космического корабля',
      placeholder: 'История о космическом корабле и планетах...',
      rows: 12,
      canDelete: false
    },
    {
      key: 'planets_and_numbers',
      defaultLabel: 'Соответствие планет и чисел',
      placeholder: 'Описание соответствия планет и чисел...',
      rows: 8,
      canDelete: false
    }
  ] : [
    {
      key: 'what_is_topic',
      defaultLabel: 'Что изучаем в этом уроке?',
      placeholder: 'Введение в тему урока...',
      rows: 8,
      canDelete: false
    },
    {
      key: 'main_story',
      defaultLabel: 'Основная история/объяснение',
      placeholder: 'Основное содержание урока...',
      rows: 12,
      canDelete: false
    },
    {
      key: 'key_concepts',
      defaultLabel: 'Ключевые концепции',
      placeholder: 'Важные понятия и термины...',
      rows: 8,
      canDelete: false
    },
    {
      key: 'practical_applications',
      defaultLabel: 'Практическое применение',
      placeholder: 'Как применить знания на практике...',
      rows: 8,
      canDelete: false
    }
  ];

  // Получаем кастомные блоки из lessonContent
  const [customBlocks, setCustomBlocks] = useState(() => {
    let blocks = lessonContent.custom_theory_blocks?.blocks;
    if (!blocks) return [];

    // Если это строка JSON, парсим её
    if (typeof blocks === 'string') {
      try {
        return JSON.parse(blocks);
      } catch (e) {
        console.error('Error parsing custom_theory_blocks:', e);
        return [];
      }
    }

    // Если это уже массив, возвращаем как есть
    return Array.isArray(blocks) ? blocks : [];
  });

  // Состояние для скрытых основных блоков
  const [hiddenFields, setHiddenFields] = useState(() => {
    const hidden = lessonContent.hidden_theory_fields;
    if (!hidden) return new Set();

    if (typeof hidden === 'string') {
      try {
        return new Set(JSON.parse(hidden));
      } catch (e) {
        return new Set();
      }
    }

    return new Set(Array.isArray(hidden) ? hidden : []);
  });

  // Получаем кастомные заголовки из theory_labels или используем дефолтные
  const getFieldLabel = (field) => {
    const labelKey = `${field.key}_label`;
    return lessonContent.theory_labels?.[labelKey] || field.defaultLabel;
  };

  // Скрыть/показать основной блок
  const toggleFieldVisibility = (fieldKey) => {
    const newHidden = new Set(hiddenFields);

    if (newHidden.has(fieldKey)) {
      newHidden.delete(fieldKey);
    } else {
      newHidden.add(fieldKey);
    }

    setHiddenFields(newHidden);
    onSave('hidden_theory_fields', 'fields', JSON.stringify([...newHidden]));
  };

  // Добавить новый кастомный блок
  const addCustomBlock = () => {
    const newBlock = {
      id: `custom_${Date.now()}`,
      title: '',
      content: ''
    };
    const updatedBlocks = [...customBlocks, newBlock];
    setCustomBlocks(updatedBlocks);
    onSave('custom_theory_blocks', 'blocks', JSON.stringify(updatedBlocks));
  };

  // Удалить кастомный блок
  const deleteCustomBlock = (blockId) => {
    if (!window.confirm('Удалить этот блок?')) return;

    const updatedBlocks = customBlocks.filter(b => b.id !== blockId);
    setCustomBlocks(updatedBlocks);
    onSave('custom_theory_blocks', 'blocks', JSON.stringify(updatedBlocks));
  };

  // Обновить заголовок кастомного блока
  const updateCustomBlockTitle = (blockId, title) => {
    const updatedBlocks = customBlocks.map(b =>
      b.id === blockId ? { ...b, title } : b
    );
    setCustomBlocks(updatedBlocks);
    onSave('custom_theory_blocks', 'blocks', JSON.stringify(updatedBlocks));
  };

  // Обновить содержание кастомного блока
  const updateCustomBlockContent = (blockId, content) => {
    const updatedBlocks = customBlocks.map(b =>
      b.id === blockId ? { ...b, content } : b
    );
    setCustomBlocks(updatedBlocks);
    onSave('custom_theory_blocks', 'blocks', JSON.stringify(updatedBlocks));
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Теоретическая часть</span>
          <Button onClick={addCustomBlock} size="sm" variant="outline">
            <Plus className="w-4 h-4 mr-2" />
            Добавить блок
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Основные (фиксированные) блоки */}
        {defaultTheoryFields.map((field) => {
          const isHidden = hiddenFields.has(field.key);

          return (
            <div key={field.key} className={`space-y-2 p-4 border rounded-lg ${isHidden ? 'bg-gray-100 opacity-50' : 'bg-gray-50'}`}>
              <div className="flex items-start justify-between mb-2">
                <Label className="text-xs text-gray-500">
                  {isHidden ? '(Скрытый блок)' : 'Основной блок'}
                </Label>
                <Button
                  onClick={() => toggleFieldVisibility(field.key)}
                  size="sm"
                  variant="ghost"
                  className={isHidden ? 'text-green-600 hover:text-green-700' : 'text-gray-600 hover:text-gray-700'}
                  title={isHidden ? 'Показать блок' : 'Скрыть блок'}
                >
                  {isHidden ? <Eye className="w-4 h-4" /> : <Trash2 className="w-4 h-4" />}
                </Button>
              </div>

              {/* Редактируемый заголовок */}
              <div>
                <Label className="text-xs text-gray-500">Заголовок блока</Label>
                <Input
                  key={`label_${field.key}_${lessonId}`}
                  className="font-medium bg-white"
                  defaultValue={getFieldLabel(field)}
                  onBlur={(e) => onSave('theory_labels', `${field.key}_label`, e.target.value)}
                  placeholder={field.defaultLabel}
                  disabled={isHidden}
                />
              </div>

              {/* Контент блока */}
              <div>
                <Label className="text-xs text-gray-500">Содержание</Label>
                <textarea
                  key={`${field.key}_${lessonId}_${lessonContent.theory?.[field.key]?.length || 0}`}
                  className="w-full p-3 border rounded-lg min-h-32 text-sm bg-white"
                  rows={field.rows}
                  defaultValue={lessonContent.theory?.[field.key] || ''}
                  onBlur={(e) => onSave('theory', field.key, e.target.value)}
                  placeholder={field.placeholder}
                  disabled={isHidden}
                />
              </div>
            </div>
          );
        })}

        {/* Кастомные (добавленные) блоки */}
        {customBlocks.map((block) => (
          <div key={block.id} className="space-y-2 p-4 border-2 border-blue-200 rounded-lg bg-blue-50">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <GripVertical className="w-4 h-4 text-gray-400" />
                <Label className="text-xs text-blue-700 font-semibold">Дополнительный блок</Label>
              </div>
              <Button
                onClick={() => deleteCustomBlock(block.id)}
                size="sm"
                variant="ghost"
                className="text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>

            {/* Заголовок кастомного блока */}
            <div>
              <Label className="text-xs text-gray-500">Заголовок блока</Label>
              <Input
                className="font-medium bg-white"
                defaultValue={block.title}
                onBlur={(e) => updateCustomBlockTitle(block.id, e.target.value)}
                placeholder="Введите заголовок блока..."
              />
            </div>

            {/* Содержание кастомного блока */}
            <div>
              <Label className="text-xs text-gray-500">Содержание</Label>
              <textarea
                className="w-full p-3 border rounded-lg min-h-32 text-sm bg-white"
                rows={8}
                defaultValue={block.content}
                onBlur={(e) => updateCustomBlockContent(block.id, e.target.value)}
                placeholder="Введите содержание блока..."
              />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

export default LessonTheoryEditor;
