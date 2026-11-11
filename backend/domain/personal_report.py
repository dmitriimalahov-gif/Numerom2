"""Pure, versioned explanations of the actual saved personal-number values."""
import re
from datetime import datetime

from domain.name_numbers import calculate_full_name_number
from domain.personal_scheme import build_personal_scheme
from numerology import calculate_planetary_strength


MASTER_NUMBERS = (11, 22, 33)
NUMBER_INFO = {
    'soul': ('Число души', 'Тема внутренней мотивации, привычных стремлений и личных качеств.'),
    'mind': ('Число ума', 'Тема способа мышления, обработки информации и принятия решений.'),
    'destiny': ('Число судьбы', 'Тема жизненного пути и задач для личного размышления.'),
    'helping_mind': ('Помогающее число ума', 'Тема дополнительных способов мышления и внутренних ресурсов.'),
    'wisdom': ('Число мудрости', 'Тема осмысления опыта и применения накопленных знаний.'),
    'ruling': ('Правящее число', 'Тема организации своей жизни и подхода к действиям.'),
    'full_name': ('Полное число имени', 'Тема самовыражения и образа, связанного с именем и фамилией.'),
}
NUMBER_THEMES = {
    1: ('инициативой, самостоятельностью и лидерством', 'Заметьте, где полезно сделать первый шаг и где стоит услышать других.'),
    2: ('сотрудничеством, чуткостью и дипломатией', 'Подумайте, как учитывать чувства других и сохранять собственные границы.'),
    3: ('творчеством, общением и передачей знаний', 'Выберите идею, которой хочется придать форму или поделиться.'),
    4: ('последовательностью, практичностью и устойчивостью', 'Попробуйте превратить большую задачу в несколько понятных шагов.'),
    5: ('гибкостью, любознательностью и поиском нового', 'Обратите внимание, какие перемены помогают учиться, а какие рассеивают внимание.'),
    6: ('заботой, гармонией и ответственностью в отношениях', 'Подумайте о балансе между помощью другим и заботой о себе.'),
    7: ('анализом, углублённым исследованием и самопознанием', 'Выделите время на вопрос, который хочется понять глубже.'),
    8: ('организацией, стратегией и управлением ресурсами', 'Сопоставьте долгосрочную цель с доступными силами и временем.'),
    9: ('широтой взгляда, справедливостью и участием в общем деле', 'Подумайте, какое посильное действие принесёт пользу вам и окружающим.'),
    11: ('интуицией, вдохновением и чувствительностью', 'Проверьте внутреннее впечатление фактами и обсудите идею с теми, кому доверяете.'),
    22: ('масштабным замыслом, практическим воплощением и сотрудничеством', 'Разделите большой замысел на реалистичные этапы и определите поддержку.'),
    33: ('наставничеством, заботой и ответственным обменом опытом', 'Подумайте, чем вы готовы делиться без чрезмерной нагрузки на себя.'),
}
PLANET_MEANINGS = {
    'Солнце': 'В символике NumerOM — инициатива, самовыражение и уверенность.',
    'Луна': 'В символике NumerOM — чувствительность, забота и эмоциональная отзывчивость.',
    'Марс': 'В символике NumerOM — действие, решительность и защита границ.',
    'Меркурий': 'В символике NumerOM — общение, обучение и гибкость мышления.',
    'Юпитер': 'В символике NumerOM — расширение кругозора, знания и наставничество.',
    'Венера': 'В символике NumerOM — отношения, красота и поиск гармонии.',
    'Сатурн': 'В символике NumerOM — дисциплина, ответственность и последовательность.',
}
NAME_UNAVAILABLE = ('Для расчёта нужны имя и фамилия из профиля латинскими буквами A–Z. '
                    'Допустимы пробел, дефис и апостроф. Данные не дополняются автоматически.')


def supported_profile_name(name, surname):
    """Reject incomplete/mixed alphabets instead of silently discarding letters."""
    parts = []
    for part in (name, surname):
        if not isinstance(part, str):
            return None
        part = part.strip()
        if not re.fullmatch(r"[A-Za-z '\-’]+", part) or not re.search(r'[A-Za-z]', part):
            return None
        parts.append(part)
    return tuple(parts)


def full_name_number_for_report(name, surname):
    parts = supported_profile_name(name, surname)
    return calculate_full_name_number(*parts) if parts else None


def _reduction_steps(value, masters=MASTER_NUMBERS):
    steps = []
    while value > 9 and value not in masters:
        digits = [int(char) for char in str(value)]
        value = sum(digits)
        steps.append(' + '.join(map(str, digits)) + f' = {value}')
    steps.append(f'Итог: {value}' + (' — мастер-число, сохраняется' if value in masters else ''))
    return value, steps


def _date_formulas(date):
    day, month, year = date.day, date.month, date.year
    date_digits = [int(char) for char in f'{day:02d}{month:02d}{year:04d}']
    seeds = {
        'soul': (day, [f'День рождения: {day}'], MASTER_NUMBERS,
                 'Сводим день рождения; мастер-числа 11, 22 и 33 сохраняются.'),
        'mind': (month, [f'Месяц рождения: {month}'], MASTER_NUMBERS,
                 'Сводим месяц рождения; мастер-числа 11, 22 и 33 сохраняются.'),
        'destiny': (day + month + year, [f'{day} + {month} + {year} = {day + month + year}'], (),
                    'Складываем день, месяц и год как целые числа. Всегда сводим до одной цифры, включая 11, 22 и 33.'),
        'helping_mind': (day + month, [f'{day} + {month} = {day + month}'], MASTER_NUMBERS,
                         'Складываем день и месяц как целые числа; при сведении сохраняем 11, 22 и 33.'),
        'ruling': (sum(date_digits), [' + '.join(map(str, date_digits)) + f' = {sum(date_digits)}'], (11, 22),
                   'Складываем все цифры даты рождения. При сведении сохраняем только 11 и 22; 33 сводится до 6.'),
    }
    formulas = {}
    for key, (seed, start, masters, method) in seeds.items():
        value, steps = _reduction_steps(seed, masters)
        formulas[key] = (value, method, start + steps)
    return formulas


def _interpretation(value):
    if value not in NUMBER_THEMES:
        return None
    theme, reflection = NUMBER_THEMES[value]
    return f'В интерпретации NumerOM число {value} связывают с {theme}. {reflection}'


def _planet_report(date, results, legacy):
    expected = calculate_planetary_strength(date.day, date.month, date.year) if date else None
    stored = results.get('planetary_strength')
    stored = stored if isinstance(stored, dict) else {}
    details = results.get('calculation_details')
    details = details if isinstance(details, dict) else {}
    saved_number = details.get('calculation_number')
    saved_number = saved_number if type(saved_number) is int else None
    items = [{'name': name, 'value': stored[name], 'meaning': meaning}
             for name, meaning in PLANET_MEANINGS.items()
             if type(stored.get(name)) is int and 0 <= stored[name] <= 9]
    matches = expected is not None and stored == expected['strength'] and (
        saved_number is None or saved_number == expected['calculation_number'])
    formula, calculation_number = '', saved_number
    if expected and (not legacy or matches or not items):
        combined = int(f'{date.day:02d}{date.month:02d}')
        calculation_number = expected['calculation_number']
        formula = f'{combined} × {date.year} = {calculation_number}'
    note = ('Шкала 0–9, не проценты. Цифры произведения ДДММ × год распределяются по семи планетам, '
            'начиная с планеты дня рождения: воскресенье — Солнце, понедельник — Луна, вторник — Марс, '
            'среда — Меркурий, четверг — Юпитер, пятница — Венера, суббота — Сатурн, затем по кругу. '
            'Если цифр меньше семи, оставшиеся значения равны нулю; если больше — следующий круг '
            'заменяет прежнее значение планеты новой цифрой. '
            'Это числовая схема NumerOM, а не измерение физических сил планет.')
    if not items:
        note = 'Значения планет не сохранены; график недоступен. ' + note
    elif legacy and not matches:
        note = 'Показаны сохранённые значения. Историческая формула распределения не подтверждена. ' + note
    return {'formula': formula, 'calculation_number': calculation_number,
            'birth_weekday': results.get('birth_weekday') or (expected['birth_weekday'] if expected else ''),
            'items': items, 'note': note}


def build_personal_report(birth_date, results, *, name='', surname='', profile_birth_date=None, legacy=False):
    """Explain an immutable result. Legacy name inputs are deliberately not inferred."""
    try:
        date = datetime.strptime(birth_date, '%d.%m.%Y')
    except (ValueError, TypeError):
        date = None
    formulas = _date_formulas(date) if date else {}
    parts = supported_profile_name(name, surname) if not legacy else None
    name_note = 'Использованы имя и фамилия из профиля.'
    if profile_birth_date and birth_date != profile_birth_date:
        name_note += ' Дата этого расчёта отличается от даты рождения в профиле; имя относится к владельцу профиля.'
    numbers = []
    for key, (title, meaning) in NUMBER_INFO.items():
        raw_value = results.get(key + '_number')
        value = raw_value if type(raw_value) is int else None
        method, steps, note = 'Способ расчёта недоступен.', [], None
        interpretation = _interpretation(value) if value is not None else None
        if key in {'soul', 'mind', 'destiny', 'helping_mind', 'ruling'}:
            if key in formulas:
                expected, candidate_method, candidate_steps = formulas[key]
                if value == expected:
                    method, steps = candidate_method, candidate_steps
                else:
                    note = ('Сохранённое значение не совпадает с текущей формулой для этой даты. '
                            'Историческое значение сохранено без пересчёта.')
            else:
                note = 'Дата сохранённого расчёта недоступна; историческую формулу подтвердить нельзя.'
        elif legacy:
            if key == 'wisdom':
                note = ('Историческое значение: прежняя версия использовала удвоенное число судьбы вместо '
                        'суммы с числом имени. Правильность формулы по этому архиву подтвердить нельзя; '
                        'сохранённое число не пересчитывалось.')
            else:
                note = ('Исторические имя, фамилия и способ расчёта не сохранены. '
                        'Значение оставлено как в архиве и не пересчитано по текущему профилю.')
            interpretation = None
        elif not parts or value is None:
            note, interpretation = NAME_UNAVAILABLE, None
            method = ('Сумма числа судьбы и полного числа имени с сохранением 11, 22 и 33.' if key == 'wisdom'
                      else 'Сумма значений букв имени и фамилии: A=1, B=2, …, Z=26; сведение до одной цифры.')
        elif key == 'full_name':
            method = 'Буквы имени и фамилии: A=1, B=2, …, Z=26. Складываем значения и сводим до одной цифры без исключений.'
            sums = []
            for part in parts:
                letters = [(char, ord(char) - ord('A') + 1) for char in part.upper() if 'A' <= char <= 'Z']
                sums.append(sum(number for _, number in letters))
                steps.append(f'{part}: ' + ', '.join(f'{char}={number}' for char, number in letters) + f'; сумма = {sums[-1]}')
            steps.append(' + '.join(map(str, sums)) + f' = {sum(sums)}')
            _, reduced_steps = _reduction_steps(sum(sums), ())
            steps.extend(reduced_steps)
            note = name_note
        else:
            method = 'Складываем число судьбы и полное число имени. Сводим сумму, сохраняя мастер-числа 11, 22 и 33.'
            destiny, full_name = results['destiny_number'], results['full_name_number']
            steps = [f'{destiny} + {full_name} = {destiny + full_name}']
            _, reduced_steps = _reduction_steps(destiny + full_name)
            steps.extend(reduced_steps)
            note = name_note
        numbers.append({'key': key + '_number', 'title': title, 'value': value, 'meaning': meaning,
                        'interpretation': interpretation, 'method': method, 'steps': steps, 'note': note})
    planets = _planet_report(date, results, legacy)
    return {'version': 1, 'birth_date': birth_date, 'birth_weekday': planets['birth_weekday'],
            'profile_name': ' '.join(parts) if parts else None,
            'profile_parts': {'name': (name or '').strip(), 'surname': (surname or '').strip()} if not legacy and isinstance(name or '',str) and isinstance(surname or '',str) else None,
            'numbers': numbers, 'planets': planets,
            'scheme': build_personal_scheme(birth_date, legacy=legacy)}
