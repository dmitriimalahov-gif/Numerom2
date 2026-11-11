"""Presentation data for the existing, authoritative Pythagorean square."""
import re
from datetime import datetime

from numerology import create_pythagorean_square


CELL_LAYOUT = ((1, 4, 7), (2, 5, 8), (3, 6, 9))
CELL_INFO = {
    1: ('Солнце', 'В символике NumerOM — инициатива, самовыражение и самостоятельность.'),
    2: ('Луна', 'В символике NumerOM — чуткость, забота и взаимодействие.'),
    3: ('Юпитер', 'В символике NumerOM — обучение, кругозор и обмен знаниями.'),
    4: ('Раху', 'В символике NumerOM — перемены, замыслы и поиск новых подходов.'),
    5: ('Меркурий', 'В символике NumerOM — общение, любознательность и гибкость мышления.'),
    6: ('Венера', 'В символике NumerOM — отношения, красота и гармония.'),
    7: ('Кету', 'В символике NumerOM — размышление, внутренний поиск и осмысление опыта.'),
    8: ('Сатурн', 'В символике NumerOM — последовательность, ответственность и организация.'),
    9: ('Марс', 'В символике NumerOM — действие, решительность и личные границы.'),
}
LINE_INFO = (
    ('row-0', (1, 4, 7), 'Горизонталь 1-4-7', 'Тема целей, воли и внутренних опор.', 'horizontal_sums', 0),
    ('row-1', (2, 5, 8), 'Горизонталь 2-5-8', 'Тема общения, чувств и взаимодействия.', 'horizontal_sums', 1),
    ('row-2', (3, 6, 9), 'Горизонталь 3-6-9', 'Тема практических действий и воплощения идей.', 'horizontal_sums', 2),
    ('col-0', (1, 2, 3), 'Вертикаль 1-2-3', 'Тема любознательности, обучения и анализа.', 'vertical_sums', 0),
    ('col-1', (4, 5, 6), 'Вертикаль 4-5-6', 'Тема организации дел, информации и ответственности.', 'vertical_sums', 1),
    ('col-2', (7, 8, 9), 'Вертикаль 7-8-9', 'Тема опыта, настойчивости и реализации решений.', 'vertical_sums', 2),
    ('diag-0', (1, 5, 9), 'Диагональ 1-5-9', 'Тема личных смыслов, самопознания и развития.', 'diagonal_sums', 0),
    ('diag-1', (3, 5, 7), 'Диагональ 3-5-7', 'Тема практического опыта, мастерства и творчества.', 'diagonal_sums', 1),
)
METHOD = ('Классический квадрат Пифагора с четырьмя дополнительными числами по методу Александрова. '
          'А1 — сумма цифр даты; А2 — сумма цифр А1; А3 — модуль разности А1 и удвоенной '
          'первой цифры дня в записи ДД (для 01–09 это 0); А4 — сумма цифр А3. '
          'В квадрат входят цифры даты и А1–А4; нули пропускаются. '
          'Значение линии — количество цифр в трёх её ячейках.')
NOTE = ('Символическая схема для размышления, не оценка способностей и не прогноз событий. '
        'Количество цифр не означает «лучше» или «хуже»; пустая ячейка означает только отсутствие '
        'этой цифры в расчёте.')


def build_personal_scheme(birth_date, *, legacy=False):
    """Use only the supplied saved date; never substitute profile or example data."""
    if not isinstance(birth_date, str) or not re.fullmatch(r'[0-9]{2}\.[0-9]{2}\.[0-9]{4}', birth_date):
        return None
    try:
        date = datetime.strptime(birth_date, '%d.%m.%Y')
    except ValueError:
        return None

    square = create_pythagorean_square(date.day, date.month, date.year)
    cells = []
    for row_index, row in enumerate(CELL_LAYOUT):
        for column_index, digit in enumerate(row):
            digits = square['square'][row_index][column_index]
            title, meaning = CELL_INFO[digit]
            cells.append({'digit': digit, 'count': len(digits), 'digits': digits,
                          'title': title, 'meaning': meaning})
    lines = [{'key': key, 'digits': list(digits), 'value': square[source][index],
              'title': title, 'meaning': 'В символике NumerOM: ' + meaning}
             for key, digits, title, meaning, source, index in LINE_INFO]
    note = NOTE
    if legacy:
        note = ('Схема рассчитана по сохранённой дате рождения текущим методом NumerOM. '
                'Исторические значения отчёта не пересчитывались. ' + note)
    return {'version': 1, 'birth_date': birth_date, 'method': METHOD, 'note': note,
            'additional_numbers': square['additional_numbers'], 'cells': cells, 'lines': lines}
