"""Spoken explanations over frozen calculation facts, shared by guides and reports.

This module never calculates numbers or invents a personal trait. It explains the
project's terminology and arranges its existing interpretations before practices.
"""
import re

STYLE = 'numerom-consultation-v1'
VOICE = 'dmitrii-conversation-v1'
VOICE_IDENTITY = 'dmitrii-speaker-identity-e8bbe873-tempo120-v1'

CONCEPTS = {
    'soul': 'Число души — это про ваши внутренние желания: что вам хочется делать и что побуждает начать.',
    'mind': 'Число ума — это про способ думать: как вы разбираетесь в ситуации и приходите к решению.',
    'destiny': 'Число судьбы в нашем разборе — тема жизненных задач: чему вы учитесь, когда желания встречаются с обстоятельствами.',
    'helping_mind': 'Помогающее число ума — дополнительный способ посмотреть на задачу, когда привычного подхода недостаточно.',
    'ruling': 'Правящее число — про то, как вы соединяете намерения с действиями и выстраиваете общий порядок в жизни.',
    'life_path': 'Число жизненного пути — общая тема развития в этой системе: какие качества можно осмысленно применять в разных ситуациях.',
    'problem': 'Общая задача — вопрос для работы над привычными реакциями. Слово «задача» здесь не означает, что с вами что-то не так.',
    'wisdom': 'Число мудрости — про то, как превращать прожитый опыт в полезное понимание и решения.',
    'full_name': 'Число имени — про самовыражение: как вы представляете себя, общаетесь и проявляете свою позицию.',
    'square': 'Квадрат Пифагора — карта тем вашей даты рождения. Каждая ячейка отвечает за свою тему, а число внутри показывает количество повторений её цифры.',
    'lines': 'Линии квадрата связывают темы трёх ячеек. Так мы рассматриваем вместе желание, взаимодействие и действие. Сумма линии показывает количество цифр в этих ячейках.',
    'row-0': 'Горизонталь 1–4–7 — про движение к цели: чего вы хотите, на что опираетесь и как удерживаете направление.',
    'row-1': 'Горизонталь 2–5–8 — про взаимодействие: как замечать чувства, договариваться и выполнять договорённости.',
    'row-2': 'Горизонталь 3–6–9 — про воплощение: как превратить знания и замысел в конкретное действие.',
    'col-0': 'Вертикаль 1–2–3 — про обучение: как задавать вопросы, воспринимать новое и разбираться в сути.',
    'col-1': 'Вертикаль 4–5–6 — про организацию: как собрать информацию, навести порядок и распределить ответственность.',
    'col-2': 'Вертикаль 7–8–9 — про опыт и действие: как сделать выводы, сохранить настойчивость и довести дело до результата.',
    'diag-0': 'Диагональ 1–5–9 — про личный смысл: зачем вам выбранная цель и насколько ваши действия согласуются с вашими ценностями.',
    'diag-1': 'Диагональ 3–5–7 — про мастерство: как соединять знания, практику и творческий поиск.',
    'planets': 'Планетарный график — способ увидеть темы даты рядом. Высота столбца показывает цифру расчёта, а название планеты помогает понять тему этой позиции.',
    'fractal': 'Фрактал поведения — четыре взгляда на действие: как начать, обдумать, учесть опыт и собрать всё в решение.',
    'tasks': 'Четыре задачи — вопросы к привычным реакциям. Они помогают заметить, где внутреннее желание и способ действовать могут расходиться.',
    'individual': 'Личный календарь — темы для наблюдения на выбранную дату. Год задаёт общий контекст, месяц уточняет его, а день помогает выбрать небольшой практический акцент.',
    'cycles': 'Циклы — способ рассмотреть темы даты на возрастной шкале. Это последовательность вопросов для размышления, а не расписание будущих событий.',
    'cycle-period': 'В этом отрезке схемы тень означает привычную реакцию, вершина — тему развития, вызов — вопрос для работы, а переход соединяет эти темы.',
    'vedic-numbers': 'Ведические числа предлагают посмотреть на внутренний мотив и общий жизненный ориентир через символику планет.',
    'janma': 'Джанма-анк — общее число даты рождения в ведическом разделе. Здесь оно задаёт основную тему разбора.',
    'atma': 'Атма-анк — про внутренний мотив: что побуждает вас действовать по собственному желанию.',
    'bhagya': 'Бхагья-анк — про общий жизненный ориентир в ведическом прочтении даты.',
    'vedic-yantra': 'Янтра — карта цифр самой даты рождения. Темы ячеек те же, но дополнительные числа квадрата Пифагора сюда не входят.',
    'vedic-lines': 'Линии янтры объединяют темы трёх ячеек. Их сумма считается только по цифрам самой даты рождения.',
    'profile-name': 'Число имени — про самовыражение: как вы представляетесь и доносите свою позицию до других.',
    'profile-wisdom': 'Здесь мы соединяем тему имени с темой жизненного опыта: как выражать себя и применять то, чему вы научились.',
    'profile-vedic-name': 'Ведический разбор имени рассматривает его символическую тему и то, как она сочетается с датой рождения.',
    'profile-abracadabra': 'Абракадабра имени — числовая пирамида из букв. Её уровни помогают рассмотреть, как меняется тема при последовательном соединении соседних значений.',
    'profile-human': 'Человечек имени — рисунок, который распределяет числовые темы имени по позициям. Это условная карта самовыражения, а не описание тела.',
    'profile-address': 'Числа адреса — повод посмотреть на привычки и атмосферу вашего пространства: что помогает общению, отдыху и порядку.',
    'profile-car': 'Число автомобиля — символическая тема его номера. Через неё можно обсудить свои привычки в дороге.',
    'profile-phone': 'Число телефона — символическая тема номера, которую мы связываем с привычками общения.',
    'profile-planetary-hours': 'Планетарные часы делят время между восходами на отрезки. Название планеты задаёт традиционную тему отрезка, а часы зависят от города и даты.',
    'profile-solar-periods': 'Солнечные периоды — отдельные интервалы дня между восходом и закатом. В традиции у них разные темы для выбора ритма занятий.',
    'profile-daily-route': 'Маршрут дня соединяет местное расписание с числовой темой даты: так можно выбрать акцент для своих занятий.',
    'profile-monthly-route': 'Маршрут на несколько дней показывает их темы последовательно, чтобы вы могли сопоставить их со своими планами.',
    'relationship': 'Совместимость здесь — сопоставление двух числовых тем. Мы обсуждаем сходство подходов и различия, о которых полезно договориться.',
    'assessment': 'Этот разбор показывает темы выбранных вами ответов. Его смысл — помочь заметить привычные предпочтения и обсудить их.',
    'master-11': 'Мастер-число 11 в этой системе — тема чувствительности и вдохновения: как замечать тонкие впечатления и находить для них понятную форму.',
    'master-22': 'Мастер-число 22 — про соединение большого замысла с практикой: как выстроить понятные этапы и сотрудничество.',
    'master-33': 'Мастер-число 33 — про заботу и наставничество: как передавать опыт, оставляя другому пространство для собственного решения.',
}

CELL_TOPICS = {
    1: 'инициативу: как заявлять о своём желании и начинать',
    2: 'чувствительность: как замечать свои переживания и слышать другого',
    3: 'знания: как учиться, понимать и передавать опыт',
    4: 'новые подходы: как встречать перемены и пробовать другой путь',
    5: 'общение: как обмениваться идеями и гибко мыслить',
    6: 'отношения и гармонию: как заботиться и замечать качество повседневной жизни',
    7: 'осмысление: как делать выводы из опыта и искать личный смысл',
    8: 'ответственность: как выстраивать порядок и последовательно выполнять задуманное',
    9: 'действие и границы: как направлять усилия и защищать свою позицию',
}
for digit, topic in CELL_TOPICS.items():
    CONCEPTS[f'cell-{digit}'] = f'Ячейка {digit} — про {topic}.'
    CONCEPTS[f'number-{digit}'] = f'Число {digit} — про {topic}.'

ALIASES = {'planet-chart': 'planets', 'comprehensive-fractal': 'fractal',
    'scheme-guide': 'square', 'scheme-kvadrat': 'square',
    'comprehensive-tasks': 'tasks', 'comprehensive-individual': 'individual',
    'comprehensive-cycles': 'cycle-period', 'comprehensive-abracadabra': 'profile-abracadabra',
    'comprehensive-human': 'profile-human', 'vedic-schedule': 'profile-planetary-hours',
    'vedic-daily': 'profile-daily-route', 'vedic-weekly': 'profile-monthly-route',
    'vedic-monthly': 'profile-monthly-route', 'vedic-quarterly': 'profile-monthly-route',
    'scheme-4d': 'soul', 'scheme-4u': 'mind', 'scheme-4uz': 'helping_mind',
    'scheme-4s': 'destiny', 'scheme-4m': 'wisdom', 'scheme-p4': 'ruling'}
for route, key in [('147','row-0'),('258','row-1'),('369','row-2'),('123','col-0'),
                   ('456','col-1'),('789','col-2'),('159','diag-0'),('357','diag-1')]:
    ALIASES['scheme-'+route] = key
for symbol, digit in [('su',1),('cha',2),('gu',3),('ra',4),('bu',5),('hsu',6),('ke',7),('sha',8),('ma',9)]:
    ALIASES['scheme-'+symbol] = 'cell-'+str(digit)
for code in ('1101928','2112029','3122130','4132231','51423','61524','71625','81726','91827'):
    ALIASES['scheme-'+code] = 'number-'+code[0]

def explanation(key):
    key = ALIASES.get(key, key)
    if key.startswith('cycle-period-'): key = 'cycle-period'
    if key.startswith('relationship-'): key = 'relationship'
    if key.startswith('assessment-'): key = 'assessment'
    match = re.fullmatch(r'tool-(?:method-)?(name|address|car)(?:-\d+)?', key)
    if match: key = 'profile-'+match[1]
    return CONCEPTS.get(key, '')


ADVICE = re.compile(r'^(?:Практика:|Совет:|(?:Рассмотрите|Проверьте|Обратите|Попробуйте|Выберите|'
    r'Сформулируйте|Запишите|Заметьте|Сопоставьте|Понаблюдайте|Начните|Полезно|Можно попробовать)\b)', re.I)

def sentences(text):
    # Keep decimals, birth dates and calculation notation intact.
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+(?=[А-ЯЁA-Z])', text.strip()) if s.strip()]

def ordered(texts):
    observations, practices, seen = [], [], set()
    for text in texts:
        for sentence in sentences(text):
            if sentence in seen: continue
            seen.add(sentence)
            (practices if ADVICE.match(sentence) else observations).append(sentence)
    return observations, practices

def guide_text(key, section, title, text):
    """Shared guide/visible theory adaptation. Never touch exercises or quiz keys."""
    if section not in {'numbers','lines','methods','tools','schemes','comprehensive','vedic','relationships','assessment','theory'}:
        return text
    if section == 'theory':
        return explain_theory(text)
    intro = explanation(key)
    if not intro: return text
    parts = sentences(text)
    # Replace an old definition, not a calculation or the facts of an authored example.
    if parts and (parts[0] == intro or re.match(r'^(?:Число (?:души|ума|судьбы|мудрости)|Помогающее число ума|Правящее число)\s+(?:—|описывает|раскрывает|посвящено|в материалах)', parts[0])):
        parts.pop(0)
    observations, practices = ordered(parts)
    return '\n\n'.join([intro, *observations, *practices])


def explain_theory(text):
    """Explain the first mention in visible teaching text; never inspect quiz data."""
    terms = [
        (r'помогающ\w* числ\w* ума', 'helping_mind'),
        (r'числ\w* души', 'soul'), (r'(?<!помогающее )числ\w* ума', 'mind'),
        (r'числ\w* судьбы', 'destiny'), (r'правящ\w* числ\w*', 'ruling'),
        (r'числ\w* мудрости', 'wisdom'), (r'числ\w* жизненного пути', 'life_path'),
        (r'квадрат\w* Пифагора', 'square'), (r'фрактал\w* поведения', 'fractal'),
        (r'Абракадабр\w*', 'profile-abracadabra'), (r'человеч\w* имени', 'profile-human'),
    ]
    routes = {'147':'row-0','258':'row-1','369':'row-2','123':'col-0','456':'col-1',
              '789':'col-2','159':'diag-0','357':'diag-1'}
    for route, concept in routes.items():
        terms.append((r'(?:диагонал|горизонтал|вертикал)\w*\s+' + r'\s*[–—−,\-]\s*'.join(route), concept))
    terms.extend((r'ячейк\w*\s+'+str(digit)+r'\b',f'cell-{digit}') for digit in range(1,10))
    seen, parts = set(), []
    for sentence in sentences(text):
        for pattern, concept in terms:
            if concept not in seen and re.search(pattern,sentence,re.I):
                intro=explanation(concept)
                if sentence != intro: parts.append(intro)
                seen.add(concept)
        parts.append(sentence)
    return '\n\n'.join(parts)


def section_parts(section):
    """Explain, name the stored result and origin, interpret, then offer practices."""
    key = section['id']
    if section.get('position_readings'):
        # The consultation follows positions, not a dictionary keyed by digit.
        # Equations stay in steps/method; the video reads exactly this prose.
        parts = [explanation(key) or section['title']]
        definitions, boundaries = set(parts), set()
        if key in {'square', 'vedic-yantra'}:
            parts.append('Количество повторений не оценивает способности. Пустая ячейка означает отсутствие цифры в расчёте.')
        for reading in section['position_readings']:
            value = section['values'][reading['value_index']]
            boundary = reading.get('boundary')
            if boundary and boundary not in boundaries:
                parts.append('Контекст разбора: ' + boundary + '.')
                boundaries.add(boundary)
            definition = reading.get('definition')
            if definition and definition not in definitions:
                parts.append(definition)
                definitions.add(definition)
            parts.append(value['label'] + (f': {value["value"]}' if value['value'] is not None else '') + '.')
            parts.extend(reading[field] for field in ('insight', 'attention', 'practice'))
        return parts
    parts = [explanation(key) or section['title']]
    advice = []
    values = section.get('values', []) if section.get('narration_values', True) else []
    paired = key == 'personal' and [v.get('key') for v in values[:2]] == ['soul','mind']
    paired_meanings = []
    explained = set()
    if key in {'square','vedic-yantra'}:
        parts.append('Количество повторений не оценивает способности. Ноль означает, что этой цифры нет в данном расчёте.')
        parts.append('Строки схемы: 1–4–7, затем 2–5–8 и 3–6–9.')
    if key == 'fractal':
        parts.append(section['title'])
    # Keep a compact origin at the chapter level; the full method remains readable.
    # Methods are available in the document. Narration is a consultation, so it
    # does not rehearse arithmetic even for graph-only chapters.
    for index, value in enumerate(values):
        concept = value.get('key', '')
        if key in {'square','vedic-yantra'}:
            concept = 'cell-'+str(value.get('digit', value['label'].split(' ')[0]))
        elif key == 'vedic-lines':
            concept = ('row-0','row-1','row-2','col-0','col-1','col-2','diag-0','diag-1')[index] if index < 8 else ''
        intro = explanation(concept)
        if key == 'planets':
            planet = {'Солнце':1,'Луна':2,'Юпитер':3,'Меркурий':5,'Венера':6,'Сатурн':8,'Марс':9}.get(value['label'])
            if planet: intro = f'{value["label"]} здесь — про {CELL_TOPICS[planet]}.'
        if intro: parts.append(intro)
        label, number = value['label'], value['value']
        if key in {'square','vedic-yantra','lines','vedic-lines'}:
            parts.append(f'{label}. Количество в вашем расчёте: {number}.')
        else:
            parts.append(label + (f': {number}' if number is not None else '') + '.')
        meaning = value['meaning']
        if key == 'personal':
            meaning = re.sub(r'^(?:Рассмотрите это число как вопрос[^.]*|Здесь та же символика[^.]*)\.\s*', '', meaning)
        observations, practices = ordered([meaning])
        if intro:
            observations = [text for text in observations if not text.startswith('Тема ')]
        if paired and index < 2:
            paired_meanings.extend([*observations, *practices])
            if index == 0: continue
            if values[0]['value'] == values[1]['value']:
                parts.append('Когда числа души и ума совпадают, в этой системе желание и способ искать решение получают общую тему. Проще говоря: то, чего хочется, и то, как вы обдумываете путь к этому, можно рассмотреть с одной стороны.')
            observations, practices = ordered(paired_meanings)
        for text in [*observations, *practices]:
            if text not in explained:
                parts.append(text); explained.add(text)
    paragraphs = section.get('paragraphs', [])
    observations, practices = ordered(paragraphs)
    if key == 'personal' and not section.get('interpretation_sources'):
        observations = []  # The same base meanings and coincidence were explained above.
    parts.extend(observations); advice.extend(practices)
    # A practice is useful after the listener has heard the term and their result.
    parts.extend(dict.fromkeys(advice))
    return [part for part in parts if part]
