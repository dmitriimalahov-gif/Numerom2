"""Frozen profile inputs and adapters for existing NumerOM calculations.

No inferred names, transliteration or network geocoding. Phone reduction is
explicitly labelled as a new application of the existing base reduction.
Different name methods remain separate and retain their own alphabet/reduction.
"""
import copy
import re
from fastapi import HTTPException

from domain.name_numbers import calculate_full_name_number
from domain.personal_report import supported_profile_name, build_personal_report, _reduction_steps
from domain.number_tools import ToolRequest, build_tools, item as tool_item
from numerology import calculate_address_numerology
from vedic_numerology import calculate_nama_ank, calculate_shakti_ank

PROFILE_FIELDS = ('name', 'surname', 'full_name', 'phone_number', 'city', 'birth_city',
                  'street', 'house_number', 'apartment_number', 'postal_code', 'car_number')


def snapshot_profile(user):
    fields, issues = {}, []
    for key in PROFILE_FIELDS:
        value = user.get(key)
        if value is None:
            fields[key] = ''
        elif not isinstance(value, str) or len(value) > 500 or any(ord(c) < 32 for c in value):
            fields[key] = ''
            issues.append({'field': key, 'reason': 'Поле содержит неподдерживаемое значение; исправьте его в профиле.'})
        else:
            fields[key] = value.strip()
    identifier = user.get('birth_city_id')
    fields['birth_city_id'] = str(identifier) if isinstance(identifier, (str, int)) and re.fullmatch(r'[1-9][0-9]{0,11}', str(identifier)) else None
    return {'version': 1, 'fields': fields, 'issues': issues}


def name_schemes(name, surname, birth):
    """Parity with packages/numerology-core/name-schemes.js, without guessing."""
    if not isinstance(name, str) or not isinstance(surname, str):
        return {'available': False}
    if any(not re.fullmatch(r"[A-Za-z '\-’]*", value) for value in (name, surname)):
        return {'available': False}
    name, surname = [re.sub('[^A-Z]', '', v.upper()) for v in (name, surname)]
    digit = lambda ch: (ord(ch) - ord('A')) % 9 + 1
    reduce = lambda number: _reduction_steps(number, ())[0]
    first_nine = list((name + surname)[:9])
    rows = []
    if len(first_nine) == 9:
        rows.append([digit(c) for c in first_nine])
        while len(rows[-1]) > 1:
            rows.append([reduce(a + b) for a, b in zip(rows[-1], rows[-1][1:])])
    human = None
    if len(name) >= 4:
        numbers = [digit(c) for c in name]
        human = {'head': numbers[0], 'handLeft': numbers[2], 'handRight': numbers[1],
                 'soul': numbers[3], 'mindNumber': reduce(birth.month),
                 'destinyNumber': reduce(birth.day + birth.month + birth.year), 'bottomDigit': numbers[-1]}
    return {'available': True, 'name': name, 'surname': surname,
            'nameLetters': [{'letter': c, 'digit': digit(c)} for c in name],
            'surnameLetters': [{'letter': c, 'digit': digit(c)} for c in surname],
            'firstNine': first_nine, 'rows': rows, 'human': human}


def profile_sections(birth_date, target, snapshot, personal):
    # Import presentation helpers lazily to keep base report backward compatible.
    from domain.full_report import _section, _value, _chart, _theme, _date, _COMPREHENSIVE
    birth = _date(birth_date)
    fields = copy.deepcopy(snapshot['fields'])
    sections, excluded, raw = [], [], {}
    def omitted(title, reason):
        excluded.append({'title': title, 'reason': reason})
    def tools_section(kind, report):
        values = [_value(p['label'], p['number'], p['interpretation'] + ' ' + p['focus'], key=p['key']) for p in report['items']]
        sections.append(_section('profile-' + kind, report['title'], [report['summary']], report['method'],
            [p['label'] + ': ' + '; '.join(p['steps']) for p in report['items']], values,
            chart=_chart('bars', values), sources=['Действующий инструмент NumerOM: ' + kind]))
        raw[kind] = report
    name, surname = fields.get('name', ''), fields.get('surname', '')
    # The general name tool supports Russian and Latin, while authored name
    # diagrams require the separately saved Latin spelling. Keep both methods.
    general_name = name or fields.get('full_name', '')
    try:
        request = ToolRequest(kind='name', request_id='00000000-0000-4000-8000-000000000001',
                              expected_cost=0, inputs={'name': general_name, 'surname': surname if name else ''})
        tools_section('name', build_tools(request))
    except ValueError:
        omitted('Число имени по циклической таблице', 'Нужно имя русскими или латинскими буквами; число не вычисляется по пустому или неподдерживаемому полю.')
    parts = supported_profile_name(name, surname)
    if parts:
        full_name = calculate_full_name_number(*parts)
        wisdom, _ = _reduction_steps(personal['destiny'] + full_name)
        named = build_personal_report(birth_date, {'full_name_number': full_name, 'wisdom_number': wisdom,
            'destiny_number': personal['destiny']}, name=name, surname=surname)
        entries = [v for v in named['numbers'] if v['key'] in ('full_name_number', 'wisdom_number')]
        values = [_value(v['title'], v['value'], v['meaning'] + ' ' + (v['interpretation'] or ''), key=v['key']) for v in entries]
        sections.append(_section('profile-wisdom', 'Полное число имени и число мудрости',
            ['Имя и фамилия используются именно в сохранённом написании. Этот метод отличается от циклической таблицы инструмента имени.'],
            'Полное имя: A=1 … Z=26 с сокращением до одной цифры. Мудрость: число судьбы + полное число имени; сохраняются 11, 22, 33.',
            [v['title'] + '. ' + v['method'] + ' ' + '; '.join(v['steps']) for v in entries], values, chart=_chart('bars', values)))
        raw['name_personal'] = {'full_name_number': full_name, 'wisdom_number': wisdom, 'report': named}
        nama = calculate_nama_ank(' '.join(parts))
        from vedic_numerology import calculate_janma_ank
        janma = calculate_janma_ank(birth.day, birth.month, birth.year)
        shakti = calculate_shakti_ank(janma, nama)
        values = [_value('Нама-анк', nama, _theme(nama)), _value('Шакти-анк', shakti, _theme(shakti))]
        sections.append(_section('profile-vedic-name', 'Ведическое число имени и Шакти-анк',
            ['Применена латинская таблица действующего ведического модуля. Результат не подменяет полное число имени другого метода.'],
            'Нама-анк: циклические значения A–Z от 1 до 9. Шакти-анк: Джанма-анк + Нама-анк. Сохранение мастер-чисел — по ведическому модулю.',
            [f'Нама-анк: {nama}', f'{janma} + {nama} = {janma + nama} → {shakti}'], values, chart=_chart('bars', values)))
        raw['vedic_name'] = {'nama_ank': nama, 'shakti_ank': shakti}
    else:
        omitted('Полное число имени, число мудрости и ведическое число имени',
                'Для этих методов нужны отдельные имя и фамилия латинскими буквами A–Z. Автоматическая транслитерация не применяется.')
    scheme = name_schemes(name, surname, birth)
    raw['name_schemes'] = scheme
    if scheme.get('rows'):
        teaching = _COMPREHENSIVE['comprehensive-abracadabra']
        values, steps = [], []
        for row, items in enumerate(scheme['rows']):
            for column, number in enumerate(items):
                label = f'Ряд {row + 1}, позиция {column + 1}'
                source = (f'{scheme["firstNine"][column]} → {number}' if row == 0 else
                          f'{scheme["rows"][row - 1][column]} + {scheme["rows"][row - 1][column + 1]} → {number}')
                values.append(_value(label, number, _theme(number), row=row, column=column))
                steps.append(label + ': ' + source)
        sections.append(_section('profile-abracadabra', teaching['title'], [teaching['meaning'], teaching['focus']], teaching['method'], steps, values))
    else:
        omitted('Абракадабра имени', 'Нужно не менее девяти латинских букв A–Z в отдельных полях имени и фамилии вместе; короткие строки не дополняются.')
    if scheme.get('human'):
        teaching = _COMPREHENSIVE['comprehensive-human']
        positions = [('head','Голова','Первая буква имени'),('handLeft','Левая рука','Третья буква имени'),
                     ('handRight','Правая рука','Вторая буква имени'),('soul','Центр','Четвёртая буква имени'),
                     ('mindNumber','Число ума','Месяц рождения'),('destinyNumber','Число судьбы','День + месяц + год'),
                     ('bottomDigit','Точка опоры','Последняя буква имени')]
        values = [_value(label, scheme['human'][key], _theme(scheme['human'][key]), key=key) for key,label,_ in positions]
        sections.append(_section('profile-human', teaching['title'], [teaching['meaning'], teaching['focus']], teaching['method'],
            [f'{label}: {source} → {scheme["human"][key]}' for key,label,source in positions], values))
    else:
        omitted('Человечек имени', 'Нужно не менее четырёх латинских букв A–Z именно в отдельном поле имени.')
    address = {'street': fields.get('street', '')}
    for key in ('house_number','apartment_number','postal_code'):
        value = fields.get(key, '')
        if value and re.fullmatch(r'[A-Za-zА-Яа-яЁё0-9 /-]{1,24}', value) and sum(int(c) for c in value if c in '0123456789'):
            address[key] = value
        else:
            omitted({'house_number':'Номер дома','apartment_number':'Номер квартиры','postal_code':'Почтовый индекс'}[key],
                    'Значение не заполнено или не содержит подходящих цифр. Другие части адреса рассчитаны независимо.')
    if len(address) > 1:
        labels = {'house_number':'Номер дома','apartment_number':'Номер квартиры','postal_code':'Почтовый индекс'}
        items = [tool_item(key,label,address[key],numeric=True,kind='address') for key,label in labels.items() if key in address]
        legacy = calculate_address_numerology(**address)
        tools_section('address', {'title':'Числа адреса','summary':', '.join(f'{p["label"]}: {p["source"]}' for p in items),
            'method':'Дом, квартира и индекс рассчитываются отдельно сложением цифр. Буквы корпуса и название улицы не участвуют. Сохраняются 11, 22, 33.',
            'inputs':address,'items':items,'legacy':legacy})
    try:
        request = ToolRequest(kind='car', request_id='00000000-0000-4000-8000-000000000001', expected_cost=0,
                              inputs={'car_number':fields.get('car_number','')})
        tools_section('car', build_tools(request))
    except ValueError:
        omitted('Число автомобиля','Нужно указать номер автомобиля в поддерживаемом формате: до 13 русских или латинских букв, цифр, пробелов и дефисов.')
    phone = fields.get('phone_number', '')
    digits = ''.join(c for c in phone if c in '0123456789')
    if re.fullmatch(r'[+0-9 ()-]{3,40}', phone) and 3 <= len(digits) <= 20 and int(digits) > 0:
        total = sum(map(int, digits))
        number, reductions = _reduction_steps(total, ())
        steps = [' + '.join(digits) + f' = {total}', *reductions]
        values = [_value('Число номера телефона', number, _theme(number))]
        sections.append(_section('profile-phone', 'Символический разбор номера телефона',
            ['Номер: ' + phone, 'Учитываются все введённые цифры, включая указанный код страны. Страна не угадывается; ведущие нули и введённый формат не заменяются.'],
            'Символический разбор номера: цифровая редукция NumerOM. Это новое применение базового метода: складываем все цифры и сводим до 1–9 без сохранения мастер-чисел.',
            steps, values, chart=_chart('bars', values), sources=['Цифровая редукция NumerOM; новое применение к номеру телефона']))
        raw['phone'] = {'source': phone, 'digits': digits, 'total': total, 'number': number, 'steps': steps}
    else:
        omitted('Символический разбор телефона','Укажите номер цифрами, желательно с + и кодом страны; допускаются пробелы, скобки и дефисы. Страна и отсутствующие цифры не подставляются.')
    try:
        from domain.full_report_time import time_sections
        time_parts, time_raw, time_excluded = time_sections(birth_date, target, snapshot)
        sections.extend(time_parts)
        raw['time'] = time_raw
        excluded.extend(time_excluded)
    except (ValueError, ImportError, KeyError, HTTPException):
        omitted('Планетарные часы и дневной маршрут', 'Для сохранённого места и даты солнечные границы или расчётный модуль недоступны; другой город и условные значения не подставляются.')
    omitted('Расчёты по месту и времени рождения','Город рождения сохранён отдельно от текущего города. Действующие числовые методы не используют его вместо даты; для расчётов, требующих времени рождения, исходного времени нет.')
    return sections, excluded, raw
