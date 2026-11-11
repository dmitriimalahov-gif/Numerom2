"""Position-specific reading contexts, over the saved calculation only.

The same digit is not the same observation in a name, a count, or a calendar.
No arithmetic, invented biography or new meanings for unnamed diagram nodes.
"""
from datetime import date, datetime
import re
from domain.consultation import explanation, CELL_TOPICS

CALENDAR = {
    'chig': ('year', 'Год задаёт направление для долгого замысла.', 'план на год, этапы и проверка продвижения'),
    'chim': ('month', 'Месяц уточняет ближайший рабочий акцент.', 'посильная задача месяца и проверка в конце месяца'),
    'chid': ('day', 'День помогает выбрать небольшой конкретный шаг.', 'короткое действие в выбранный день и вечернее наблюдение'),
    'chpg': ('year', 'Задача года — вопрос к привычкам, которые полезно пересматривать постепенно.', 'работа с привычкой в течение года'),
    'chpm': ('month', 'Задача месяца — повод попробовать другой способ действовать.', 'ограниченный эксперимент на этот месяц'),
    'chpd': ('day', 'Задача дня — повод заметить свою реакцию в конкретной ситуации.', 'доступный сегодня шаг, без судьбоносных решений'),
}
PERIOD_ROLES = {
    'Тень': ('Привычная реакция, которую полезно замечать в напряжённой ситуации.', 'наблюдение за повторяющейся реакцией'),
    'Вершина': ('Тема развития: какое качество можно осмысленно тренировать.', 'долгая практика развития, с небольшими этапами'),
    'Вызов': ('Вопрос для работы с затруднением, а не предсказание трудностей.', 'безопасный эксперимент с привычным затруднением'),
    'Переход': ('Как соединить наблюдение за собой, развитие и практический опыт.', 'подведение итогов и перенос полезного опыта в следующий этап'),
}
# Roles from project-knowledge/ru.json, comprehensive-human. Do not infer
# psychological functions from where a number happens to be drawn.
HUMAN_ROLES = {
    'head': 'Голова схемы — тема мыслей и способа осмысления.',
    'handLeft': 'Левая рука схемы — тема общения и выражения чувств.',
    'handRight': 'Правая рука схемы — тема реакции на напряжение.',
    'soul': 'Центр схемы — внимание к внутреннему состоянию.',
    'mindNumber': explanation('mind'), 'destinyNumber': explanation('destiny'),
    'bottomDigit': 'Точка опоры — привычный способ действовать.',
}


def position_targets(report):
    """Every narrated result has its own stable ref; graph-only series stay graphs."""
    targets = []
    day = date.fromisoformat(report['as_of_date'])
    periods = {str(p['index']): p for p in report.get('raw', {}).get('cycles', {}).get('periods', [])}
    for section in report['sections']:
        if section.get('narration_values') is False:
            continue
        sid = section['id']
        for index, value in enumerate(section['values']):
            ref = f'{sid}:{index}'
            key = value.get('key', '')
            context = {'area': sid, 'role': value['label'], 'horizon': 'personal',
                       'definition': explanation(key) or explanation(sid) or section['title'],
                       'action_scope': 'пример обычной ситуации, наблюдаемый шаг и способ проверить его пользу',
                       'boundary': '', 'value_kind': 'symbol'}
            if sid == 'personal' and key in {'full_name_number', 'wisdom_number', 'full_name', 'wisdom'}:
                context.update(area='name', definition=explanation('wisdom' if key in {'wisdom', 'wisdom_number'} else 'full_name'),
                    action_scope='выражение своей позиции и применение опыта; не переносить трактовку из календаря')
            if sid == 'individual' and key in CALENDAR:
                horizon, definition, action = CALENDAR[key]
                context.update(horizon=horizon, definition=definition, action_scope=action,
                    boundary=str(day.year) if horizon == 'year' else day.strftime('%m.%Y') if horizon == 'month' else day.strftime('%d.%m.%Y'))
            elif sid.startswith('cycle-period-'):
                context.update(horizon='life-stage')
                if value['label'] in PERIOD_ROLES:
                    context['definition'], context['action_scope'] = PERIOD_ROLES[value['label']]
                p = periods.get(sid.rsplit('-', 1)[-1])
                # Inclusive/exclusive ages are the existing model's boundaries,
                # not dates guessed from today's clock or a reconstructed birthday.
                context['boundary'] = section['title']
                if p and p.get('years'):
                    context['boundary'] += f'; календарные годы схемы {p["years"][0]["year"]}–{p["years"][-1]["year"]}'
            elif sid == 'tasks':
                context.update(horizon='life-stage', boundary=value['label'],
                    definition='Вопрос к привычной реакции в указанном возрастном отрезке.',
                    action_scope='практика наблюдения за реакцией; не обещать событие в определённом возрасте')
            elif sid in {'square', 'vedic-yantra', 'lines', 'vedic-lines'}:
                context.update(value_kind='count',
                    definition=explanation('cell-' + str(value.get('digit', ''))) or explanation(key) or context['definition'],
                    action_scope='наблюдение за темой этой ячейки или линии; количество не превращать в уровень способностей или тему другого числа')
                if sid == 'vedic-lines' and index < 8:
                    context['definition'] = explanation(('row-0', 'row-1', 'row-2', 'col-0', 'col-1', 'col-2', 'diag-0', 'diag-1')[index])
            elif sid == 'planets':
                context['value_kind'] = 'plot-level'
                planet = {'Солнце': 1, 'Луна': 2, 'Юпитер': 3, 'Меркурий': 5, 'Венера': 6, 'Сатурн': 8, 'Марс': 9}.get(value['label'])
                if planet:
                    context['definition'] = value['label'] + ' здесь — про ' + CELL_TOPICS[planet] + '.'
                context['action_scope'] = 'раскрыть тему названной планеты; высота столбца не меняет её на другую планету и не измеряет способности'
            elif sid == 'fractal':
                context['definition'] = ('Как вы начинаете действие.', 'Как вы осмысливаете ситуацию перед решением.',
                    'Как вы используете уже полученный опыт.', 'Как вы соединяете намерение, размышление и опыт в действие.')[index]
            elif sid.startswith('profile-') and sid in {'profile-name', 'profile-wisdom', 'profile-vedic-name', 'profile-human', 'profile-abracadabra'}:
                context['area'] = 'name'
                context['action_scope'] = 'самовыражение, слова, представление себя, диалог; не переносить сюда календарный прогноз'
                context['origin'] = section.get('steps', [])[index] if index < len(section.get('steps', [])) else ''
                if sid == 'profile-abracadabra':
                    context['definition'] = 'Отдельная позиция пирамиды имени. Сопоставьте её тему с соседними позициями, без выдуманного психологического назначения ряда.'
                    context['neighbours'] = [{k: v[k] for k in ('label', 'value', 'row', 'column') if k in v}
                        for v in section['values'] if v is not value and v.get('row') == value.get('row') and abs(v.get('column', -99) - value.get('column', -99)) == 1]
                if sid == 'profile-human':
                    context['definition'] = HUMAN_ROLES.get(key, context['definition'])
                if sid == 'profile-wisdom' and key in {'wisdom', 'wisdom_number'}:
                    context['definition'] = explanation('wisdom')
            elif sid in {'profile-phone', 'profile-car', 'profile-address'}:
                context['area'] = {'profile-phone': 'communication', 'profile-car': 'travel', 'profile-address': 'home'}[sid]
                context['action_scope'] = {'profile-phone': 'привычки переписки и разговоров', 'profile-car': 'организация поездок; без выводов о безопасности по номеру', 'profile-address': 'быт, отдых и организация пространства; без выводов о жильцах'}[sid]
            elif sid in {'profile-planetary-hours', 'profile-solar-periods', 'profile-daily-route'}:
                context.update(horizon='day', boundary=day.strftime('%d.%m.%Y'),
                    action_scope='небольшое занятие в сохранённый день или интервал; не обещать удачу и не переносить на другие даты')
                context['schedule'] = section.get('paragraphs', [])[:1]
                if value.get('start') and value.get('end'):
                    context['boundary'] += '; ' + '–'.join(datetime.fromisoformat(value[k]).strftime('%H:%M') for k in ('start', 'end'))
                if sid == 'profile-solar-periods':
                    interval = re.match(r'\d{2}:\d{2}[–—-]\d{2}:\d{2}', value['meaning'])
                    if interval:
                        context['boundary'] += '; ' + interval[0]
                if sid == 'profile-daily-route':
                    context['value_kind'] = 'model-score'
            targets.append({'ref': ref, 'section_id': sid, 'section_title': section['title'],
                'label': value['label'], 'value': value['value'], 'meaning': value['meaning'], 'context': context})
    # Mention actual coincidences only within the same kind of value. A count of
    # three in a cell is not the symbolic digit three in a name.
    for item in targets:
        item['same_value_positions'] = [other['ref'] for other in targets
            if other['ref'] != item['ref'] and other['value'] is not None and other['value'] == item['value']
            and other['context']['value_kind'] == item['context']['value_kind']][:24]
        item['coincidences'] = [{'ref': other['ref'], 'role': other['label'],
            'area': other['context']['area'], 'definition': other['context']['definition']}
            for other in targets if other['ref'] in item['same_value_positions']][:6]
    return targets
