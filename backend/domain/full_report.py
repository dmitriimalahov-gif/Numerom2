"""Deterministic birth-date report, with a frozen interpretation and audio script.

There is no clock, database, network, user profile or generative model in this
module. The caller persists the returned snapshot; reopening must not rebuild it.
The comprehensive arithmetic mirrors packages/numerology-core/comprehensive.js.
"""
import json
import re
from datetime import datetime
from pathlib import Path

from domain.narration import clip
from domain.consultation import section_parts
from domain.personal_report import _date_formulas, _reduction_steps, NUMBER_THEMES
from domain.personal_scheme import build_personal_scheme, CELL_LAYOUT, LINE_INFO
from numerology import (
    calculate_life_path, calculate_planetary_strength, calculate_problem_number,
    reduce_to_single_digit_always,
)
from vedic_numerology import (
    calculate_atma_ank, calculate_bhagya_ank, calculate_janma_ank,
    calculate_graha_shakti, create_vedic_yantra,
)


_PACKAGES = Path(__file__).resolve().parents[2] / 'packages'


def _knowledge(name, key):
    data = json.loads((_PACKAGES / f'{name}-knowledge' / 'ru.json').read_text())
    return {item[key]: item for item in data['items' if name != 'scheme' else 'entries']}


_NUMBERS = _knowledge('number', 'digit')
_COMPREHENSIVE = _knowledge('comprehensive', 'id')
_SCHEMES = _knowledge('scheme', 'id')
_CELL_IDS = {1: 'SU', 2: 'CHA', 3: 'GU', 4: 'RA', 5: 'BU', 6: 'HSU', 7: 'KE', 8: 'SHA', 9: 'MA'}
_REDUCE = reduce_to_single_digit_always
_LINE_FOCUS = {
    'row-0': 'Сопоставьте намерение, готовность менять подход и выводы из собственного опыта. Выберите одну цель и ближайший проверяемый шаг.',
    'row-1': 'Соедините внимание к чувствам, ясность разговора и соблюдение договорённостей. Сформулируйте просьбу, которую можно понять без догадок.',
    'row-2': 'Сопоставьте понимание, личную заинтересованность и конкретное действие. Проверьте одну идею на небольшом завершённом примере.',
    'col-0': _SCHEMES['123']['focus'],
    'col-1': _SCHEMES['456']['focus'],
    'col-2': 'Свяжите вывод из прошлого опыта с последовательными действиями. Определите, что стоит продолжить, а какой способ пора пересмотреть.',
    'diag-0': _SCHEMES['159']['focus'],
    'diag-1': _SCHEMES['357']['focus'],
}


def _date(value, *, iso=False):
    if not isinstance(value, str):
        raise ValueError('Укажите существующую дату в формате ДД.ММ.ГГГГ.')
    pattern = r'[0-9]{4}-[0-9]{2}-[0-9]{2}' if iso else r'[0-9]{2}\.[0-9]{2}\.[0-9]{4}'
    if not re.fullmatch(pattern, value):
        raise ValueError('Укажите существующую дату в формате ДД.ММ.ГГГГ.')
    return datetime.strptime(value, '%Y-%m-%d' if iso else '%d.%m.%Y').date()


def _theme(value):
    if value == 0:
        return 'Пауза и открытый вопрос: назовите собственный приоритет, прежде чем выбирать действие.'
    if value in (11, 22, 33):
        theme, focus = NUMBER_THEMES[value]
        return f'Мастер-число {value} связывает тему с {theme}. {focus}'
    return _NUMBERS[value]['segments'][1]


def _short(value):
    if value == 0:
        return 'открытый вопрос и осознанный выбор'
    if value in (11, 22, 33):
        return NUMBER_THEMES[value][0]
    return _NUMBERS[value]['summary'].rstrip('.').lower()


def _value(label, value, meaning, **extra):
    return {'label': label, 'value': value, 'meaning': meaning, **extra}


def _section(identifier, title, paragraphs, method, steps, values, *, chart=None, sources=None):
    result = {'id': identifier, 'title': title, 'paragraphs': paragraphs, 'method': method,
              'steps': steps, 'values': values}
    if chart:
        result['chart'] = chart
    if sources:
        result['sources'] = sources
    return result


def _chart(kind, values):
    return {'type': kind, 'items': [{'label': item['label'], 'value': item['value']} for item in values]}


def _comprehensive(birth, target, personal):
    """Faithful Python port; the JS core is only used to generate test fixtures."""
    day, month, year = birth.day, birth.month, birth.year
    digits = [_REDUCE(day), _REDUCE(month), _REDUCE(year), _REDUCE(day + month + year)]
    fractal = {**{f'digit{i + 1}': value for i, value in enumerate(digits)},
               'fractal': ''.join(map(str, digits))}
    soul, mind, destiny, year_number = personal['soul'], personal['mind'], personal['destiny'], digits[2]
    raw = [abs(soul - mind), abs(soul - year_number)]
    raw.extend([abs(_REDUCE(raw[0]) - _REDUCE(raw[1])), abs(mind - year_number)])
    start = 36 - destiny
    tasks = {**{f'problem{i + 1}': _REDUCE(value) for i, value in enumerate(raw)},
             'period1': {'start': start, 'end': start + 9},
             'period2': {'start': start + 9, 'end': start + 18},
             'period3': {'start': 0, 'end': None},
             'period4': {'start': start + 18, 'end': None},
             'calculations': {**{f'problem{i + 1}Raw': value for i, value in enumerate(raw)},
                              'soulNumber': soul, 'mindNumber': mind, 'destinyNumber': destiny,
                              'yearNumber': year_number}}
    chig = _REDUCE(day + month + target.year)
    chim = _REDUCE(chig + target.month)
    chid = _REDUCE(chim + target.day)
    chpg, chpm, chpd = _REDUCE(abs(chig - destiny)), _REDUCE(abs(month - chim)), _REDUCE(abs(day - chid))
    individual = {
        'birthDate': {'day': day, 'month': month, 'year': year},
        'currentDate': {'day': target.day, 'month': target.month, 'year': target.year},
        'destinyNumber': destiny,
        'chig': {'value': chig, 'calculation': f'{day} + {month} + {target.year} = {day + month + target.year} → {chig}'},
        'chim': {'value': chim, 'calculation': f'{chig} + {target.month} = {chig + target.month} → {chim}'},
        'chid': {'value': chid, 'calculation': f'{chim} + {target.day} = {chim + target.day} → {chid}'},
        'chpg': {'value': chpg, 'calculation': f'|{chig} - {destiny}| = {abs(chig - destiny)} → {chpg}'},
        'chpm': {'value': chpm, 'calculation': f'|{month} - {chim}| = {abs(month - chim)} → {chpm}'},
        'chpd': {'value': chpd, 'calculation': f'|{day} - {chid}| = {abs(day - chid)} → {chpd}'},
    }
    years = [{'age': age, 'year': year + age, 'chlg': _REDUCE(digits[0] + digits[1] + year + age)}
             for age in range(1, 101)]
    # Author's table «Тени · Вершины · Вызовы · Переходы»: four 9-year periods (labelled 23–32, 32–41, …).
    # Peaks: day + month, day + year, the sum of both, month + year; challenges are the matching differences;
    # shadow = peak + day, month, year, destiny in turn; transition = shadow + peak + challenge.
    d, m, y = digits[0], digits[1], digits[2]
    first_peak, second_peak = _REDUCE(d + m), _REDUCE(d + y)
    peaks = [first_peak, second_peak, _REDUCE(first_peak + second_peak), _REDUCE(m + y)]
    first_challenge, second_challenge = abs(m - d), abs(d - y)
    challenges = [first_challenge, second_challenge, abs(first_challenge - second_challenge), abs(m - y)]
    periods = []
    for index, (peak, challenge, base) in enumerate(zip(peaks, challenges, (d, m, y, destiny)), 1):
        start = 27 - destiny + (index - 1) * 9
        shadow = _REDUCE(base + peak)
        transition = _REDUCE(shadow + peak + challenge)
        periods.append({'index': index, 'startAge': start, 'endAge': start + 9,
                        'years': [dict(item) for item in years if start <= item['age'] < start + 9],
                        'shadow': shadow, 'peak': peak, 'challenge': challenge, 'transition': transition,
                        'periodNumbers': [shadow, peak, challenge, transition]})
    cycles = {'baseNumber': _REDUCE(day + month), 'destinyNumber': destiny,
              'birthDate': {'day': day, 'month': month, 'year': year},
              'years': years, 'periods': periods, 'sequence': ' '.join(str(item['chlg']) for item in years)}
    return {'fractal': fractal, 'tasks': tasks, 'individual': individual, 'cycles': cycles}


def _personal_sections(birth):
    formulas = _date_formulas(birth)
    life_path = calculate_life_path(birth.day, birth.month, birth.year)
    problem = calculate_problem_number(life_path, formulas['ruling'][0])
    _, problem_steps = _reduction_steps(life_path + formulas['ruling'][0])
    formulas['life_path'] = (life_path, 'Как у числа судьбы, но при сведении сохраняются 11, 22 и 33.',
                             [f'{birth.day} + {birth.month} + {birth.year} = {birth.day + birth.month + birth.year}']
                             + _reduction_steps(birth.day + birth.month + birth.year)[1])
    formulas['problem'] = (problem, 'Сумма числа жизненного пути и правящего числа с сохранением 11, 22 и 33.',
                           [f'{life_path} + {formulas["ruling"][0]} = {life_path + formulas["ruling"][0]}'] + problem_steps)
    labels = {'soul': 'Число души', 'mind': 'Число ума', 'destiny': 'Число судьбы',
              'helping_mind': 'Помогающее число ума', 'ruling': 'Правящее число',
              'life_path': 'Число жизненного пути', 'problem': 'Общая задача'}
    contexts = {'soul': 'Рассмотрите это число как вопрос о том, что побуждает вас начинать и чего хочется самому.',
                'mind': 'Здесь та же символика относится к работе с информацией: как сформулировать вопрос и проверить решение.',
                'destiny': 'Для темы пути выберите долгосрочный замысел и соотнесите его с этим числовым акцентом.',
                'helping_mind': 'Это дополнительный ракурс для ситуации, в которой привычный способ решения не помогает.',
                'ruling': 'Перенесите этот образ на организацию дела: что требует личного решения, обсуждения и последовательного выполнения.',
                'life_path': 'Этот показатель сохраняет мастер-числа, поэтому может отличаться от однозначного числа судьбы.',
                'problem': 'В проекте это сумма жизненного пути и правящего числа; она задаёт тему вопроса к выбранной цели.'}
    values, steps = [], []
    for key, (value, method, calculation) in formulas.items():
        values.append(_value(labels[key], value, f'{contexts[key]} {_theme(value)}', key=key))
        steps.append(f'{labels[key]}. {method} ' + '; '.join(calculation))
    personal = {key: value[0] for key, value in formulas.items()}
    soul, mind, destiny = personal['soul'], personal['mind'], personal['destiny']
    # Read each symbolic theme once, while retaining every position that yields
    # that number. The summary is spoken verbatim as well as shown on screen.
    groups = {}
    for position, value in [('души', soul), ('ума', mind), ('судьбы', destiny)]:
        groups.setdefault(value, []).append(position)
    master_themes = {
        11: 'интуиция, вдохновение и чувствительность',
        22: 'масштабный замысел, практическое воплощение и сотрудничество',
        33: 'наставничество, забота и ответственный обмен опытом',
    }
    synthesis_parts = []
    for value, positions in groups.items():
        theme = master_themes.get(value, _short(value))
        if len(positions) == 1:
            synthesis_parts.append(f'Число {positions[0]} — {value}: {theme}.')
        else:
            linked = ', '.join(positions[:-1]) + ' и ' + positions[-1]
            synthesis_parts.append(f'Числа {linked} совпали: {value}. Общая тема — {theme}.')
    synthesis = [' '.join(synthesis_parts)]
    if soul == mind:
        synthesis.append('Проверьте на конкретном примере, согласуются ли ваше желание, '
                         'способ принятия решения и выбранная цель.')
    else:
        synthesis.append('Сформулируйте отдельно, чего вы хотите, и какие сведения нужны для решения; '
                         'сопоставьте оба ответа с выбранной целью.')
    return personal, _section('personal', 'Личные числа и их сочетание', synthesis,
        'Использована действующая арифметика NumerOM. Сведение — повторное сложение цифр. '
        'Числа души, ума, помогающего ума, пути и общей задачи сохраняют 11, 22, 33; '
        'правящее число — только 11 и 22; число судьбы всегда однозначное.', steps, values,
        sources=['Личные числа NumerOM', 'Числа и девять планет', 'Авторские схемы: Ч/Д, Ч/У, Ч/С, Ч/У*, П/Ч'])


def _square_sections(birth_date):
    scheme = build_personal_scheme(birth_date)
    date_digits = birth_date.replace('.', '')
    extra_digits = ''.join(map(str, scheme['additional_numbers']))
    values = []
    for cell in scheme['cells']:
        digit, count = cell['digit'], cell['count']
        item = _NUMBERS[digit]
        sources = f'В дате: {date_digits.count(str(digit))}; в дополнительных числах: {extra_digits.count(str(digit))}.'
        meaning = f'{sources} {item["summary"]} {item["segments"][1]} {_SCHEMES[_CELL_IDS[digit]]["focus"]}'
        values.append(_value(f'{digit} · {item["planet"]}', count, meaning, digit=digit, digits=cell['digits']))
    day = int(birth_date[:2])
    a1, a2, a3, a4 = scheme['additional_numbers']
    steps = [f'А1: {" + ".join(date_digits)} = {a1}', f'А2: {" + ".join(str(a1))} = {a2}',
             f'А3: |{a1} − 2 × {day // 10}| = {a3}', f'А4: {" + ".join(str(a3))} = {a4}']
    square = _section('square', 'Квадрат Пифагора: девять ячеек',
        ['Расположение ячеек: 1–4–7, 2–5–8, 3–6–9. В каждой ячейке показано количество соответствующих цифр. '
         'Пустая ячейка означает отсутствие цифры в исходном наборе.'], scheme['method'], steps, values,
        chart=_chart('matrix', values), sources=['Авторские схемы: Квадрат чисел', 'Уроки девяти планет NumerOM'])
    counts = {cell['digit']: cell['count'] for cell in scheme['cells']}
    line_values, line_steps = [], []
    for line in scheme['lines']:
        numbers = line['digits']
        line_values.append(_value(line['title'], line['value'],
            line['meaning'].replace('В символике NumerOM: ', '') + ' ' + _LINE_FOCUS[line['key']], key=line['key']))
        line_steps.append(f'{line["title"]}: ' + ' + '.join(str(counts[digit]) for digit in numbers) + f' = {line["value"]}')
    lines = _section('lines', 'Три горизонтали, три вертикали и две диагонали',
        ['Линия соединяет темы трёх ячеек. Её сумма описывает состав квадрата и не превращается в отдельную планету: '
         'например, сумма 8 остаётся суммой этой линии.'],
        'Складываем количества цифр в трёх ячейках каждой линии; сумму не сокращаем.',
        line_steps, line_values, chart=_chart('bars', line_values), sources=['Авторские схемы NumerOM: вертикали и диагонали'])
    return scheme, [square, lines]


def _planet_section(birth):
    raw = calculate_planetary_strength(birth.day, birth.month, birth.year)
    by_planet = {item['planet']: item for item in _NUMBERS.values()}
    values = [_value(planet, value, by_planet[planet]['summary'] + ' ' + by_planet[planet]['segments'][1])
              for planet, value in raw['strength'].items()]
    names = list(raw['strength'])
    assignments = [f'{names[(raw["start_planet_index"] + index) % 7]}: {digit}'
                   for index, digit in enumerate(str(raw['calculation_number']))]
    section = _section('planets', 'Семь планет: числовая диаграмма',
        [f'День рождения — {raw["birth_weekday"]}. Первая позиция — {names[raw["start_planet_index"]]}. '
         'Столбцы показывают цифры произведения на шкале 0–9. Сопоставьте тему каждого столбца с личными числами и ячейками квадрата.'],
        'Число ДДММ умножаем на год рождения. Цифры произведения распределяем по кругу: '
        'Солнце, Луна, Марс, Меркурий, Юпитер, Венера, Сатурн, начиная с планеты дня рождения. '
        'Незаполненная позиция равна нулю; при новом круге последняя цифра заменяет прежнюю.',
        [f'{birth.day:02d}{birth.month:02d} × {birth.year} = {raw["calculation_number"]}', '; '.join(assignments)],
        values, chart=_chart('bars', values), sources=['Действующая формула силы семи планет NumerOM', 'Числа и девять планет'])
    return raw, section


def _comprehensive_sections(data, target, personal):
    sections = []
    fractal, tasks, individual, cycles = (data[key] for key in ('fractal', 'tasks', 'individual', 'cycles'))
    knowledge = _COMPREHENSIVE['comprehensive-fractal']
    labels = ['Начало · день', 'Осмысление · месяц', 'Опыт · год', 'Соединение · сумма']
    fvalues = [_value(labels[index], fractal[f'digit{index + 1}'], _theme(fractal[f'digit{index + 1}'])) for index in range(4)]
    birth = individual['birthDate']
    sections.append(_section('fractal', 'Фрактал поведения · ' + fractal['fractal'],
        [knowledge['meaning'], knowledge['focus']], knowledge['method'],
        [f'День {birth["day"]} → {fractal["digit1"]}', f'Месяц {birth["month"]} → {fractal["digit2"]}',
         f'Год {birth["year"]} → {fractal["digit3"]}',
         f'{birth["day"]} + {birth["month"]} + {birth["year"]} → {fractal["digit4"]}'],
        fvalues, chart=_chart('bars', fvalues), sources=['Дополнительные расчёты NumerOM: фрактал поведения']))
    knowledge = _COMPREHENSIVE['comprehensive-tasks']
    task_values = []
    inputs = [(personal['soul'], personal['mind']), (personal['soul'], fractal['digit3']),
              (tasks['problem1'], tasks['problem2']), (personal['mind'], fractal['digit3'])]
    task_steps = []
    for index, (first, second) in enumerate(inputs, 1):
        value, period = tasks[f'problem{index}'], tasks[f'period{index}']
        boundary = 'на протяжении жизни' if index == 3 else (
            f'от {period["start"]} лет' if period['end'] is None else f'границы {period["start"]} и {period["end"]} лет')
        focus = ('Числа совпали: сформулируйте вопрос самостоятельно, опираясь на текущую ситуацию.' if value == 0 else _theme(value))
        task_values.append(_value(f'Задача {index} · {boundary}', value, focus, key=f'problem{index}'))
        task_steps.append(f'Задача {index}: |{first} − {second}| = {abs(first - second)} → {value}')
    sections.append(_section('tasks', 'Четыре задачи и возрастные границы',
        [knowledge['meaning'], 'Граничный возраст завершает один интервал и открывает следующий; третья задача рассматривается отдельно для всего пути.'],
        knowledge['method'], task_steps, task_values, chart=_chart('bars', task_values), sources=['Дополнительные расчёты NumerOM: четыре задачи']))
    knowledge = _COMPREHENSIVE['comprehensive-individual']
    ilabels = ['Личный год', 'Личный месяц', 'Личный день', 'Задача года', 'Задача месяца', 'Задача дня']
    ikeys = ['chig', 'chim', 'chid', 'chpg', 'chpm', 'chpd']
    ivalues = [_value(label, individual[key]['value'], _theme(individual[key]['value']), key=key)
               for key, label in zip(ikeys, ilabels)]
    sections.append(_section('individual', 'Личный календарь на ' + target.strftime('%d.%m.%Y'),
        [knowledge['meaning'], f'Годовая тема: {_short(individual["chig"]["value"])}. '
         f'Месяц уточняет её через {_short(individual["chim"]["value"])}; '
         f'день предлагает обратить внимание на {_short(individual["chid"]["value"])}.'],
        knowledge['method'], [f'{label}: {individual[key]["calculation"]}' for key, label in zip(ikeys, ilabels)],
        ivalues, chart=_chart('bars', ivalues), sources=['Дополнительные расчёты NumerOM: личный календарь']))
    knowledge = _COMPREHENSIVE['comprehensive-cycles']
    age = target.year - birth['year'] - ((target.month, target.day) < (birth['month'], birth['day']))
    current = next((p for p in cycles['periods'] if p['startAge'] <= age < p['endAge']), None)
    current_text = (f'На дату отчёта вам {age} лет; в схеме это период {current["startAge"]}–{current["endAge"]} лет.' if current else
                    f'На дату отчёта вам {age} лет. Этот возраст находится вне четырёх девятилетних периодов схемы.')
    year_values = [_value(f'{item["age"]} лет · {item["year"]}', item['chlg'], _short(item['chlg']),
                          age=item['age'], year=item['year']) for item in cycles['years']]
    cycle_section = _section('cycles', 'Линия личных годов: от 1 до 100 лет',
        [knowledge['meaning'], current_text, 'На графике показана повторяющаяся арифметическая последовательность 1–9. '
         'Под ней — разборы четырёх девятилетних периодов: тень, вершина, вызов и переход.'],
        knowledge['method'], [f'Первая граница: 27 − {cycles["destinyNumber"]} = {cycles["periods"][0]["startAge"]} лет',
                             f'Базовое число дня и месяца: {birth["day"]} + {birth["month"]} → {cycles["baseNumber"]}'],
        year_values, chart=_chart('series', year_values), sources=['Дополнительные расчёты NumerOM: тени, вершины и переходы'])
    # The complete 100 rows remain in the report. Audio presents the pattern and
    # each period, rather than reading a monotonous hundred-value table aloud.
    cycle_section['narration_values'] = False
    sections.append(cycle_section)
    for period in cycles['periods']:
        definitions = [('shadow', 'Тень', 'Рассмотрите привычную реакцию через тему'),
                       ('peak', 'Вершина', 'Тему развития предлагает'),
                       ('challenge', 'Вызов', 'Вопрос для осмысления связан с темой'),
                       ('transition', 'Переход', 'Объединяющий акцент периода')]
        values = [_value(label, period[key], f'{intro}: {_short(period[key])}. {_theme(period[key])}')
                  for key, label, intro in definitions if period[key] is not None]
        last = period['years'][-1]
        index = period['index']
        d, m, y = fractal['digit1'], fractal['digit2'], fractal['digit3']
        peaks = [p['peak'] for p in cycles['periods']]
        challenges = [p['challenge'] for p in cycles['periods']]
        peak_formula = [f'{d} + {m}', f'{d} + {y}', f'{peaks[0]} + {peaks[1]}', f'{m} + {y}'][index - 1]
        challenge_formula = [f'|{m} − {d}|', f'|{d} − {y}|', f'|{challenges[0]} − {challenges[1]}|', f'|{m} − {y}|'][index - 1]
        base_name, base = [('день', d), ('месяц', m), ('год', y), ('число судьбы', cycles['destinyNumber'])][index - 1]
        steps = [f'Вершина: {peak_formula} → {period["peak"]}',
                 f'Тень: вершина {period["peak"]} + {base_name} {base} → {period["shadow"]}',
                 f'Вызов: {challenge_formula} = {period["challenge"]}',
                 f'Переход: {period["shadow"]} + {period["peak"]} + {period["challenge"]} → {period["transition"]}']
        sections.append(_section(f'cycle-period-{index}', f'Период {period["startAge"]}–{period["endAge"]} лет',
            [f'Календарные годы схемы: {period["years"][0]["year"]}–{last["year"]}. '
             'Сопоставьте привычный способ реагировать с темой развития, затем выберите вопрос для наблюдения за своим опытом.'],
            '', steps, values, chart=_chart('bars', values)))
    return sections


def _vedic_sections(birth):
    day, month, year = birth.day, birth.month, birth.year
    numbers = {'janma': calculate_janma_ank(day, month, year),
               'atma': calculate_atma_ank(day), 'bhagya': calculate_bhagya_ank(day, month, year)}
    raw = {'numbers': numbers, 'graha_shakti': calculate_graha_shakti(day, month, year),
           'yantra': create_vedic_yantra(day, month, year)}
    labels = {'janma': 'Джанма-анк', 'atma': 'Атма-анк', 'bhagya': 'Бхагья-анк'}
    values = [_value(labels[key], value, _theme(value), key=key) for key, value in numbers.items()]
    numbers_section = _section('vedic-numbers', 'Ведический модуль: три числа даты',
        ['Это отдельный метод существующего ведического модуля проекта. Джанма-анк показывает тему суммы всей даты, '
         'Атма-анк — тему дня, Бхагья-анк — однозначный итог цифр даты.'],
        'Джанма-анк: день + месяц + год; Атма-анк: день. В этом модуле 11, 22 и 33 сохраняются только '
        'если исходное число уже равно им; промежуточные суммы сокращаются. Бхагья-анк — сумма всех цифр даты до 1–9.',
        [f'Джанма-анк: {day} + {month} + {year} → {numbers["janma"]}',
         f'Атма-анк: {day} → {numbers["atma"]}',
         f'Бхагья-анк: ' + ' + '.join(f'{day:02d}{month:02d}{year:04d}') + f' → {numbers["bhagya"]}'],
        values, sources=['Ведический модуль NumerOM: три числа даты'])
    digits = f'{day:02d}{month:02d}{year:04d}'
    cells = [_value(f'{digit} · {_NUMBERS[digit]["planet"]}', digits.count(str(digit)),
                    _NUMBERS[digit]['summary'], digit=digit)
             for row in CELL_LAYOUT for digit in row]
    matrix_section = _section('vedic-yantra', 'Ведическая янтра: цифры самой даты',
        ['Здесь учитываются только цифры рождения, без четырёх дополнительных чисел квадрата Пифагора. '
         'Поэтому количество в одинаково расположенных ячейках двух схем может различаться.'],
        'Считаем повторения цифр 1–9 в дате. Нули пропускаем. Позиции: 1–4–7, 2–5–8, 3–6–9.',
        ['Исходные цифры: ' + ' '.join(digits)], cells, chart=_chart('matrix', cells),
        sources=['Ведический модуль NumerOM: янтра и Граха-шакти'])
    sums = raw['yantra']['yantra_sums']
    line_values, steps = [], []
    for key, line_digits, title, meaning, source, index in LINE_INFO:
        axis = {'horizontal_sums': 'horizontal', 'vertical_sums': 'vertical', 'diagonal_sums': 'diagonal'}[source]
        value = sums[axis][index]
        line_values.append(_value(title, value, meaning + ' ' + _LINE_FOCUS[key]))
        parts = [str(digits.count(str(digit))) for digit in line_digits]
        steps.append(f'{title}: ' + ' + '.join(parts) + f' = {value}')
    lines_section = _section('vedic-lines', 'Линии ведической янтры',
        ['Линия янтры показывает, сколько планет стоит в её трёх ячейках: две восьмёрки — это две планеты Сатурна, то есть 2. '
         'В отличие от квадрата Пифагора здесь учитываются только цифры самой даты.'],
        'Складываем количество цифр в трёх ячейках каждой линии янтры, без сведения и без дополнительных чисел квадрата.',
        steps, line_values, chart=_chart('bars', line_values))
    return raw, [numbers_section, matrix_section, lines_section]


_UNITS = ('', 'один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять',
          'десять', 'одиннадцать', 'двенадцать', 'тринадцать', 'четырнадцать', 'пятнадцать',
          'шестнадцать', 'семнадцать', 'восемнадцать', 'девятнадцать')
_TENS = ('', '', 'двадцать', 'тридцать', 'сорок', 'пятьдесят', 'шестьдесят', 'семьдесят', 'восемьдесят', 'девяносто')
_HUNDREDS = ('', 'сто', 'двести', 'триста', 'четыреста', 'пятьсот', 'шестьсот', 'семьсот', 'восемьсот', 'девятьсот')
_ORDINAL_YEAR = {
    1: 'первого', 2: 'второго', 3: 'третьего', 4: 'четвёртого', 5: 'пятого', 6: 'шестого',
    7: 'седьмого', 8: 'восьмого', 9: 'девятого', 10: 'десятого', 11: 'одиннадцатого',
    12: 'двенадцатого', 13: 'тринадцатого', 14: 'четырнадцатого', 15: 'пятнадцатого',
    16: 'шестнадцатого', 17: 'семнадцатого', 18: 'восемнадцатого', 19: 'девятнадцатого',
    20: 'двадцатого', 30: 'тридцатого', 40: 'сорокового', 50: 'пятидесятого',
    60: 'шестидесятого', 70: 'семидесятого', 80: 'восьмидесятого', 90: 'девяностого',
    100: 'сотого', 200: 'двухсотого', 300: 'трёхсотого', 400: 'четырёхсотого',
    500: 'пятисотого', 600: 'шестисотого', 700: 'семисотого', 800: 'восьмисотого', 900: 'девятисотого',
    1000: 'тысячного', 2000: 'двухтысячного', 3000: 'трёхтысячного', 4000: 'четырёхтысячного',
    5000: 'пятитысячного', 6000: 'шеститысячного', 7000: 'семитысячного', 8000: 'восьмитысячного', 9000: 'девятитысячного',
}
_MONTHS = ('', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля',
           'августа', 'сентября', 'октября', 'ноября', 'декабря')


def _cardinal(value):
    parts = []
    thousands, tail = divmod(value, 1000)
    if thousands:
        parts.append('тысяча' if thousands == 1 else
                     ('две' if thousands == 2 else _UNITS[thousands]) + (' тысячи' if thousands < 5 else ' тысяч'))
    hundreds, tail = divmod(tail, 100)
    if hundreds:
        parts.append(_HUNDREDS[hundreds])
    if tail < 20:
        if tail:
            parts.append(_UNITS[tail])
    else:
        tens, units = divmod(tail, 10)
        parts.append(_TENS[tens])
        if units:
            parts.append(_UNITS[units])
    return ' '.join(parts)


def _speech_date(value):
    date = _date(value, iso='-' in value)
    day_tail = date.day if date.day <= 20 or date.day == 30 else date.day % 10
    day_ordinal = _ORDINAL_YEAR[day_tail]
    # Genitive -ого becomes nominative neuter -ое: десятого -> десятое.
    day_word = 'третье' if day_tail == 3 else day_ordinal[:-2] + 'е'
    day = ((_cardinal(date.day - day_tail) + ' ') if date.day != day_tail else '') + day_word
    year = date.year
    tail = year % 100
    unit = tail if 0 < tail < 20 else year % 10 if year % 10 else tail if tail else year % 1000 if year % 1000 else year
    year_words = ((_cardinal(year - unit) + ' ') if year != unit else '') + _ORDINAL_YEAR[unit]
    return f'{day} {_MONTHS[date.month]} {year_words} года'


def _speech_formula(text):
    text = re.sub(r'\b[0-9]{2}\.[0-9]{2}\.[0-9]{4}\b|\b[0-9]{4}-[0-9]{2}-[0-9]{2}\b',
                  lambda match: _speech_date(match[0]), text)
    digit_words = ('ноль', *_UNITS[1:10])
    # Fractal is a four-position code, not an integer. Scope the replacement to
    # its labels so actual years, master numbers and products remain numbers.
    text = re.sub(r'(\bФрактал(?: поведения)?\s*[:·]\s*)([0-9]{4})(?![0-9])',
                  lambda match: match[1] + ', '.join(digit_words[int(d)] for d in match[2]), text)
    # Square routes are also ordered positions; separators must not sound like
    # subtraction or join the sequence into a three-digit number.
    text = re.sub(r'(?<![0-9–-])([1-9])[–-]([1-9])[–-]([1-9])(?![0-9–-])',
                  lambda match: ', '.join(digit_words[int(d)] for d in match.groups()), text)
    text = re.sub(r'\|([^|]+)\|', r'модуль разности: \1', text)
    text = text.replace('×', ' умножить на ').replace('−', ' минус ')
    text = re.sub(r'(?<=\d) - (?=\d)', ' минус ', text)
    text = re.sub(r'(?<!\d)(\d+)[–—](\d+) лет', r'с возрастными границами: \1 и \2', text)
    return text


def full_report_clips(report):
    """Narrate only the persisted report, using stable IDs for the paid worker."""
    out = []
    intro = clip('full-report-summary', 'full-report', report['title'],
                 'Дата рождения: ' + _speech_date(report['birth_date']), 'Дата отчёта: ' + _speech_date(report['as_of_date']),
                 'Посмотрим, какие темы даёт ваша дата в нумерологическом прочтении. Начнём с внутренних желаний и того, как вы принимаете решения.')
    if intro:
        out.append(intro)
    # The visual report can open with an executive summary. The spoken consultation
    # explains all terms/results before its cross-chapter practices.
    sections = sorted(report['sections'], key=lambda section: section['id'] == 'synthesis')
    for section in sections:
        parts = section_parts(section)
        if section['id'] == 'synthesis':
            parts = [text for group in report.get('highlights', [])
                     for text in (group['title']+'.', *[item['text'] for item in group['items']])] + parts
        chunks, current = [], ''
        for part in parts:
            part = _speech_formula(part)
            # Bound untrusted future content too, without dropping any words.
            while len(part) > 18000:
                split = part.rfind(' ', 0, 18000)
                split = split if split > 0 else 18000
                if current:
                    chunks.append(current)
                    current = ''
                chunks.append(part[:split])
                part = part[split:].lstrip()
            if current and len(current) + len(part) + 2 > 18000:
                chunks.append(current)
                current = ''
            current += ('\n\n' if current else '') + part
        if current:
            chunks.append(current)
        for index, text in enumerate(chunks):
            suffix = f'-{index + 1}' if len(chunks) > 1 else ''
            item = clip('full-report-' + section['id'] + suffix, 'full-report', section['title'], text)
            if item:
                out.append(item)
    excluded = clip('full-report-excluded', 'full-report', 'Границы расчёта',
                    *[item['title'] + '. ' + item['reason'] for item in report['excluded']])
    if excluded:
        out.append(excluded)
    return out


def build_full_report(birth_date: str, as_of_date: str, profile_snapshot=None):
    """Build one JSON-safe snapshot. Target date is mandatory and never inferred."""
    birth = _date(birth_date)
    target = _date(as_of_date, iso=isinstance(as_of_date, str) and '-' in as_of_date)
    if birth > target:
        raise ValueError('Дата рождения не может быть позже даты отчёта.')
    personal, personal_section = _personal_sections(birth)
    scheme, square_sections = _square_sections(birth_date)
    planets, planet_section = _planet_section(birth)
    comprehensive = _comprehensive(birth, target, personal)
    vedic, vedic_sections = _vedic_sections(birth)
    report = {
        'version': 1, 'birth_date': birth_date, 'as_of_date': target.isoformat(),
        'title': 'Полный разбор даты рождения · NumerOM',
        'notice': 'Символический разбор по методам NumerOM для самопознания; он не измеряет способности и не предсказывает события.',
        'summary': [*personal_section['paragraphs'],
                    f'Дата {birth_date}: душа {personal["soul"]}, ум {personal["mind"]}, судьба {personal["destiny"]}, '
                    f'помогающий ум {personal["helping_mind"]}, правящее число {personal["ruling"]}.',
                    f'Фрактал: {comprehensive["fractal"]["fractal"]}. В квадрате — '
                    f'{sum(cell["count"] for cell in scheme["cells"])} цифр; разобраны все девять ячеек и восемь линий.',
                    f'Личный календарь зафиксирован на {target.strftime("%d.%m.%Y")}. '
                    'Линия личных годов содержит 100 значений и четыре периода: тень, вершина, вызов, переход.'],
        'sections': [personal_section, *square_sections, planet_section,
                     *_comprehensive_sections(comprehensive, target, personal), *vedic_sections],
        'excluded': [
            {'title': 'Имя, фамилия, число мудрости, Абракадабра и человечек имени',
             'reason': 'Нужны отдельные исходные имя и фамилия. Они не определяются по дате рождения и не подставляются из аккаунта покупателя.'},
            {'title': 'Планетарные часы, солнечные периоды и маршруты',
             'reason': 'Нужны выбранные место, часовой пояс и дата наблюдения; для точных астрологических периодов также необходимо время рождения.'},
            {'title': 'Совместимость и групповые сопоставления',
             'reason': 'Нужны исходные данные других участников. Одной даты недостаточно для парного расчёта.'},
            {'title': 'Автомобиль, адрес и другие внешние объекты',
             'reason': 'Нужны номер автомобиля или отдельные данные адреса. Эти значения не следуют из даты рождения.'},
        ],
        'raw': {'personal': personal, 'scheme': scheme, 'planets': planets, **comprehensive, 'vedic': vedic},
    }
    if profile_snapshot is not None:
        from domain.full_report_profile import profile_sections
        additional, omitted, profile_raw = profile_sections(birth_date, target, profile_snapshot, personal)
        report['title'] = 'Полный личный разбор · NumerOM'
        report['profile_snapshot'] = profile_snapshot
        report['sections'].extend(additional)
        report['raw']['profile'] = profile_raw
        # The name the owner entered completes the personal numbers: the wisdom number (Ч/М on the
        # author's plate) and the full name number join them — scheme, voice and video — not only
        # the name chapter near the end of the report.
        named = next((section for section in additional if section['id'] == 'profile-wisdom'), None)
        if named:
            keys = {'wisdom_number': 'wisdom', 'full_name_number': 'full_name'}
            personal_section['values'].extend({**value, 'key': keys[value['key']]} for value in named['values'])
            personal_section['steps'].extend(named['steps'])
        report['excluded'] = [item for item in report['excluded']
                              if item['title'] not in ('Имя, фамилия, число мудрости, Абракадабра и человечек имени',
                                                       'Автомобиль, адрес и другие внешние объекты',
                                                       'Планетарные часы, солнечные периоды и маршруты')]
        report['excluded'].extend(omitted)
    report['narration'] = full_report_clips(report)
    # Detach all lists from the loaded knowledge and raw aliases. The caller owns
    # this snapshot; no later request can change its values or narration hashes.
    return json.loads(json.dumps(report, ensure_ascii=False, allow_nan=False))
