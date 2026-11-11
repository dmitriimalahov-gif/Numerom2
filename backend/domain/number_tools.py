"""Name, address and vehicle reports using the existing server formulas."""
import re
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator
from numerology import calculate_name_numerology, calculate_address_numerology, calculate_car_number_numerology

ALPHABETS = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
LETTERS = {letter: index % 9 + 1 for alphabet in ALPHABETS for index, letter in enumerate(alphabet)}
TITLES = {'name': 'Число имени', 'address': 'Числа адреса', 'car': 'Число автомобиля'}
FIELDS = {'name': {'name', 'surname'}, 'address': {'street', 'house_number', 'apartment_number', 'postal_code'}, 'car': {'car_number'}}
THEMES = {
    1: ('Инициатива', 'Сформулируйте своё решение и сделайте первый конкретный шаг.'),
    2: ('Сотрудничество', 'Уточняйте ожидания вслух: чуткость становится опорой, когда есть ясные договорённости.'),
    3: ('Самовыражение', 'Придайте идее форму: запишите, расскажите или покажите её.'),
    4: ('Порядок', 'Выберите устойчивый ритм и оставьте в нём место для корректировок.'),
    5: ('Свобода', 'Пробуйте новое, заранее определив границы времени и ресурсов.'),
    6: ('Забота', 'Соотнесите внимание к другим со своими потребностями и возможностями.'),
    7: ('Осмысление', 'Дайте себе время разобраться в деталях, затем проверьте вывод на практике.'),
    8: ('Организация', 'Свяжите цель с измеримыми действиями и ответственностью за результат.'),
    9: ('Завершение', 'Подведите итог сделанного и освободите место для следующего этапа.'),
    11: ('Вдохновение', 'Запишите тонкое наблюдение и найдите для него простое практическое применение.'),
    22: ('Воплощение', 'Разделите большой замысел на этапы, которые можно последовательно завершить.'),
    33: ('Наставничество', 'Делитесь опытом так, чтобы другой человек сохранял самостоятельность.'),
}


class ToolRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    kind: Literal['name', 'address', 'car']
    request_id: UUID
    expected_cost: int = Field(strict=True, ge=0, le=1000000)
    inputs: dict[str, str]

    @model_validator(mode='after')
    def valid_inputs(self):
        if set(self.inputs) - FIELDS[self.kind]:
            raise ValueError('Лишние поля расчёта')
        self.inputs = {key: value.strip() for key, value in self.inputs.items()}
        if any(len(value) > 120 or any(ord(c) < 32 for c in value) for value in self.inputs.values()):
            raise ValueError('Проверьте длину и символы полей')
        if self.kind == 'name':
            for key in ('name', 'surname'):
                value = self.inputs.get(key, '')
                if (key == 'name' and not value) or value and (not re.fullmatch(r"[A-Za-zА-Яа-яЁё '\-’]+", value) or not any(c.upper() in LETTERS for c in value)):
                    raise ValueError('Укажите имя буквами русского или латинского алфавита')
        elif self.kind == 'car':
            value = self.inputs.get('car_number', '')
            if not 1 <= len(value) <= 13 or not re.fullmatch(r'[A-Za-zА-Яа-яЁё0-9 -]+', value) or not sum(token_value(c) for c in value.upper()):
                raise ValueError('Укажите номер до 13 символов: русские или латинские буквы и цифры')
        else:
            for key in ('house_number', 'apartment_number', 'postal_code'):
                value = self.inputs.get(key, '')
                if (key == 'house_number' and not value) or value and (not re.fullmatch(r'[A-Za-zА-Яа-яЁё0-9 /-]{1,24}', value) or not sum(int(c) for c in value if c in '0123456789')):
                    raise ValueError('Номер дома, квартиры и индекс должны содержать ненулевую цифру')
        return self


def token_value(char):
    return int(char) if char in '0123456789' else LETTERS.get(char, 0)


def item(key, label, source, *, numeric=False, kind):
    tokens = [{'symbol': c, 'value': int(c) if numeric else token_value(c)} for c in source.upper()
              if c in '0123456789' or not numeric and c in LETTERS]
    total = sum(token['value'] for token in tokens)
    value = total
    steps = [' + '.join(str(token['value']) for token in tokens) + f' = {total}']
    while value > 9 and value not in (11, 22, 33):
        digits = list(map(int, str(value)))
        value = sum(digits)
        steps.append(' + '.join(map(str, digits)) + f' = {value}')
    title, context, focus = explanation(kind, value)
    return {'key': key, 'label': label, 'source': source, 'number': value, 'total': total, 'tokens': tokens,
            'steps': steps, 'title': title, 'interpretation': context, 'focus': focus,
            'narration_id': f'tool-{kind}-{value}'}


def explanation(kind, value):
    title, focus = THEMES[value]
    context = {'name': f'В числе имени {value} центральная тема — {title.lower()}. Рассмотрите, как она проявляется в вашем способе представляться, общаться и принимать решения.',
               'address': f'В числе адреса {value} выделяется тема «{title.lower()}». Она предлагает взглянуть на привычки, общение и атмосферу своего пространства.',
               'car': f'В символике номера автомобиля {value} выделяется тема «{title.lower()}». Подумайте, с какими задачами и впечатлениями у вас связаны поездки.'}[kind]
    return title, context, focus



def build_tools(data):
    fields, kind = data.inputs, data.kind
    if kind == 'name':
        full_name = ' '.join(filter(None, [fields['name'], fields.get('surname')]))
        items = [item('name', 'Полное имя', full_name, kind=kind)]
        legacy = calculate_name_numerology(full_name)
        assert items[0]['number'] == legacy['name_number']
        method = 'Буквам присваиваются значения от 1 до 9 по порядку алфавита, затем цикл повторяется. Русский алфавит включает Ё: Е = 6, Ё = 7, Ж = 8. Латинский: A = 1, B = 2, …, I = 9, J = 1. Пробелы, дефисы и апострофы не участвуют.'
        summary = full_name
    elif kind == 'car':
        summary = fields['car_number']
        items = [item('car', 'Номер автомобиля', summary, kind=kind)]
        legacy = calculate_car_number_numerology(summary)
        assert items[0]['number'] == legacy['numerology_value']
        method = 'Складываем цифры номера и значения его букв. Русский и латинский алфавиты имеют отдельные циклы 1–9; Ё = 7. Пробелы и дефисы не участвуют. Регион учитывается, если вы ввели его цифры.'
    else:
        labels = [('house_number', 'Номер дома'), ('apartment_number', 'Номер квартиры'), ('postal_code', 'Почтовый индекс')]
        items = [item(key, label, fields[key], numeric=True, kind=kind) for key, label in labels if fields.get(key)]
        legacy = calculate_address_numerology(**fields)
        for part, old_key in [('house_number', 'house_numerology'), ('apartment_number', 'apartment_numerology'), ('postal_code', 'postal_code_numerology')]:
            if fields.get(part):
                assert next(i['number'] for i in items if i['key'] == part) == legacy[old_key]['value']
        summary = ', '.join(filter(None, [fields.get('street'), 'дом ' + fields['house_number'], 'кв. ' + fields['apartment_number'] if fields.get('apartment_number') else '', fields.get('postal_code')]))
        method = 'Дом, квартира и почтовый индекс рассчитываются отдельно: складываем цифры каждого значения. Буквы корпуса и название улицы не участвуют. Общего числа из трёх результатов этот метод не вычисляет.'
    return {'version': 1, 'kind': kind, 'title': TITLES[kind], 'summary': summary, 'inputs': fields, 'items': items,
            'method': method + ' Сумму сводим сложением её цифр, сохраняя мастер-числа 11, 22 и 33.', 'legacy': legacy}
