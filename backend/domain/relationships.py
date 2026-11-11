"""Validated relationship inputs and explanations of the existing NumerOM formula."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from numerology import calculate_compatibility, calculate_group_compatibility, calculate_life_path


class Person(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=80)
    birth_date: str

    @field_validator('name')
    @classmethod
    def readable_name(cls, value):
        if any(ord(char) < 32 for char in value):
            raise ValueError('Имя не должно содержать управляющие символы')
        return value

    @field_validator('birth_date')
    @classmethod
    def real_date(cls, value):
        try:
            date = datetime.strptime(value, '%d.%m.%Y')
            if date.strftime('%d.%m.%Y') != value or date.year < 1900 or date > datetime.utcnow():
                raise ValueError()
        except ValueError:
            raise ValueError('Укажите существующую дату рождения: ДД.ММ.ГГГГ, начиная с 1900 года')
        return value


class RelationshipRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    kind: Literal['pair', 'group']
    request_id: UUID
    expected_cost: int = Field(strict=True, ge=0, le=1000000)
    main: Person
    people: list[Person] = Field(min_length=1, max_length=5)

    @model_validator(mode='after')
    def pair_size(self):
        if self.kind == 'pair' and len(self.people) != 1:
            raise ValueError('Для пары укажите ровно одного второго участника')
        return self


def member(person):
    day, month, year = map(int, person.birth_date.split('.'))
    value = day + month + year
    steps = [f'{day} + {month} + {year} = {value}']
    while value > 9 and value not in (11, 22, 33):
        digits = list(map(int, str(value)))
        value = sum(digits)
        steps.append(' + '.join(map(str, digits)) + f' = {value}')
    steps.append(f'Число жизненного пути: {value}' + (' — мастер-число сохраняется' if value in (11, 22, 33) else ''))
    assert value == calculate_life_path(day, month, year)
    return {**person.model_dump(), 'number': value, 'steps': steps}


def connection(main, other):
    difference = abs(main['number'] - other['number'])
    # Preserve the established backend formula, including its lower bound.
    score = max(1, 10 - difference)
    if difference == 0:
        title = 'Созвучный ритм'
        text = 'Одинаковые числа подчёркивают общую тему самовыражения. Легче узнавать знакомые мотивы друг в друге; полезно оставлять место разным привычкам и интересам.'
        focus = 'Обсудите, какие решения вы принимаете вместе, а где каждому нужна самостоятельность.'
    elif difference <= 2:
        title = 'Близкие акценты'
        text = 'В этой схеме числа расположены рядом. Сходство подходов может стать точкой опоры, а различия — поводом уточнить ожидания, не считая их само собой разумеющимися.'
        focus = 'Выберите одну общую цель и договоритесь о конкретном вкладе каждого.'
    elif difference <= 4:
        title = 'Разные способы действия'
        text = 'Схема выделяет различие акцентов. Один и тот же вопрос можно решать в разном темпе: через обсуждение, самостоятельный шаг или последовательный план.'
        focus = 'Сравните, как каждый предпочитает получать поддержку и обсуждать разногласия.'
    else:
        title = 'Контраст акцентов'
        text = 'Большое расстояние между числами уменьшает индекс по формуле. Это повод подробнее рассмотреть индивидуальные трактовки и реальные договорённости между вами.'
        focus = 'Назовите свои приоритеты и границы. Опирайтесь на поступки и разговор, принимая совместные решения.'
    return {'name': other['name'], 'score': score, 'title': title, 'interpretation': text,
            'focus': focus, 'formula': f'max(1, 10 − |{main["number"]} − {other["number"]}|) = {score}'}


def build_relationships(data):
    main = member(data.main)
    people = [member(person) for person in data.people]
    connections = [connection(main, person) for person in people]
    legacy = (calculate_compatibility(data.main.birth_date, data.people[0].birth_date)
              if data.kind == 'pair' else
              calculate_group_compatibility(data.main.birth_date, [person.model_dump() for person in data.people]))
    return {'version': 1, 'kind': data.kind, 'main': main, 'people': people,
            'connections': connections, 'average': sum(item['score'] for item in connections) / len(connections),
            'method': 'Число жизненного пути: день + месяц + год как целые числа; сумму сводим, сохраняя 11, 22 и 33. Индекс пары: 10 минус расстояние между числами, минимум 1. В группе каждый участник сравнивается с основным, затем берётся среднее индексов.',
            'note': 'Индекс 1–10 — условная шкала метода NumerOM, не вероятность и не прогноз отношений.',
            'legacy': legacy}
