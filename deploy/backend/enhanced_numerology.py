"""
Улучшенная нумерология с полным набором расчетов
Убрано упоминание Александрова, заменено на "Ведическая система"
"""
from datetime import datetime
from typing import Dict, List, Any, Tuple
import re

def parse_birth_date(birth_date: str) -> Tuple[int, int, int]:
    """Парсинг даты рождения в формате DD.MM.YYYY"""
    try:
        day, month, year = birth_date.split('.')
        return int(day), int(month), int(year)
    except:
        raise ValueError("Неверный формат даты. Используйте DD.MM.YYYY")

def reduce_to_single_digit(number: int) -> int:
    """Сведение числа к однозначному (кроме мастер-чисел 11, 22, 33)"""
    if number in [11, 22, 33]:
        return number
    
    while number > 9:
        number = sum(int(digit) for digit in str(number))
    return number

def calculate_life_path(day: int, month: int, year: int) -> int:
    """Число жизненного пути"""
    total = day + month + year
    return reduce_to_single_digit(total)

def calculate_destiny_number(day: int, month: int, year: int) -> int:
    """Число судьбы (сумма всех цифр)"""
    all_digits = [int(d) for d in str(day) + str(month) + str(year)]
    total = sum(all_digits)
    return reduce_to_single_digit(total)

def calculate_soul_number(day: int) -> int:
    """Число души (из дня рождения)"""
    return reduce_to_single_digit(day)

def calculate_mind_number(month: int) -> int:
    """Число ума (из месяца рождения) - ЧУ"""
    return reduce_to_single_digit(month)

def calculate_personality_number(year: int) -> int:
    """Число личности (из года рождения) - ЧМ"""
    year_digits = sum(int(d) for d in str(year))
    return reduce_to_single_digit(year_digits)

def calculate_power_number(day: int, month: int, year: int) -> int:
    """Число силы (ПЧ) - специальный расчет"""
    # Особая ведическая формула
    power = (day * month) + year
    return reduce_to_single_digit(power)

def calculate_ruling_number(day: int, month: int) -> int:
    """Управляющее число"""
    total = day + month
    return reduce_to_single_digit(total)

def calculate_problem_number(life_path: int, ruling_number: int) -> int:
    """Число проблемы"""
    total = life_path + ruling_number
    return reduce_to_single_digit(total)

def create_enhanced_pythagorean_square(day: int, month: int, year: int) -> Dict[str, Any]:
    """
    Создает улучшенный квадрат Пифагора с полным набором энергий
    Использует классическую систему расчета дополнительных чисел
    """
    # Получаем все цифры даты рождения (DD.MM.YYYY)
    day_str = str(day).zfill(2) if day < 10 else str(day)
    month_str = str(month).zfill(2) if month < 10 else str(month)
    year_str = str(year)
    
    birth_digits = list(day_str + month_str + year_str)
    
    # Вычисляем дополнительные числа по классической системе
    # Первое дополнительное число - сумма всех цифр даты рождения
    first_additional = sum(int(d) for d in birth_digits)
    
    # Второе дополнительное число - сумма цифр первого дополнительного
    second_additional = sum(int(d) for d in str(first_additional))
    
    # Третье дополнительное число
    first_digit_of_day = int(day_str[0])  # Первая значащая цифра дня рождения
    third_additional = first_additional - 2 * first_digit_of_day
    # Если получается отрицательное число, берем по модулю
    if third_additional <= 0:
        third_additional = abs(third_additional)
    
    # Четвертое дополнительное число - сумма цифр третьего дополнительного
    fourth_additional = sum(int(d) for d in str(third_additional))
    
    # Все числа для квадрата: дата + дополнительные
    additional_numbers = [first_additional, second_additional, third_additional, fourth_additional]
    all_digits_for_square = birth_digits + [d for num in additional_numbers for d in str(num)]
    
    # Создаем квадрат 3x3
    # Расположение по ведической системе:
    # 1-Солнце  2-Луна     3-Юпитер
    # 4-Раху    5-Центр    6-Венера  
    # 7-Кету    8-Сатурн   9-Марс
    
    square_matrix = [[[], [], []], [[], [], []], [[], [], []]]
    planet_positions = {
        '1': (0, 0),  # Солнце (Сурья)
        '2': (0, 1),  # Луна (Чандра)  
        '3': (0, 2),  # Юпитер (Гуру)
        '4': (1, 0),  # Раху
        '5': (1, 1),  # Центр (свободная энергия)
        '6': (1, 2),  # Венера (Шукра)
        '7': (2, 0),  # Кету  
        '8': (2, 1),  # Сатурн (Шани)
        '9': (2, 2),  # Марс (Мангал)
    }
    
    # Подсчитываем количество каждой цифры
    digit_counts = {}
    for digit in all_digits_for_square:
        if digit != '0' and digit.isdigit():  # Исключаем нули и проверяем что это цифра
            if digit not in digit_counts:
                digit_counts[digit] = 0
            digit_counts[digit] += 1
    
    # Заполняем матрицу квадрата
    for digit, count in digit_counts.items():
        if digit in planet_positions and count > 0:
            row, col = planet_positions[digit]
            # Заполняем ячейку количеством цифр
            square_matrix[row][col] = [digit] * count
    
    # Преобразуем для отображения (строки с цифрами)
    display_square = []
    for row in square_matrix:
        display_row = []
        for cell in row:
            if cell:
                display_row.append(''.join(cell))  # Например: "111" если три единицы
            else:
                display_row.append('')  # Пустая ячейка
        display_square.append(display_row)
    
    # Планетарный анализ с цветовой схемой из дизайна
    planet_analysis = {
        '1': {'name': 'Солнце (सूर्य)', 'sphere': 'лидерство, власть, эго', 'color': '#ff6b35'},
        '2': {'name': 'Луна (चन्द्र)', 'sphere': 'эмоции, семья, интуиция', 'color': '#87ceeb'},
        '3': {'name': 'Юпитер (गुरु)', 'sphere': 'мудрость, знания, духовность', 'color': '#ffd700'},
        '4': {'name': 'Раху (राहु)', 'sphere': 'амбиции, иллюзии, материальность', 'color': '#8b4513'}, 
        '5': {'name': 'Центр (केंद्र)', 'sphere': 'баланс, гармония, поиск', 'color': '#90ee90'},
        '6': {'name': 'Венера (शुक्र)', 'sphere': 'любовь, красота, творчество', 'color': '#ff69b4'},
        '7': {'name': 'Кету (केतु)', 'sphere': 'духовность, интуиция, отречение', 'color': '#9370db'},
        '8': {'name': 'Сатурн (शनि)', 'sphere': 'дисциплина, ответственность, карма', 'color': '#4169e1'},
        '9': {'name': 'Марс (मंगल)', 'sphere': 'энергия, действие, конфликты', 'color': '#dc143c'},
    }
    
    # Определяем силу планет по количеству цифр
    energy_strength = {}
    for digit in '123456789':
        count = digit_counts.get(digit, 0)
        if count == 0:
            energy_strength[digit] = 'отсутствует'
        elif count == 1:
            energy_strength[digit] = 'слабая'
        elif count == 2:
            energy_strength[digit] = 'нормальная'
        elif count == 3:
            energy_strength[digit] = 'сильная'
        elif count >= 4:
            energy_strength[digit] = 'избыточная'
    
    # Вычисляем суммы линий (по количеству ПЛАНЕТ в ячейках)
    # Горизонтальные суммы (материальная сфера)
    horizontal_sums = []
    for row in square_matrix:
        row_sum = sum(len(cell) for cell in row)  # Количество планет в строке
        horizontal_sums.append(row_sum)
    
    # Вертикальные суммы (духовная сфера)  
    vertical_sums = []
    for col in range(3):
        col_sum = sum(len(square_matrix[row][col]) for row in range(3))
        vertical_sums.append(col_sum)
    
    # Диагональные суммы (баланс)
    main_diagonal = sum(len(square_matrix[i][i]) for i in range(3))
    anti_diagonal = sum(len(square_matrix[i][2-i]) for i in range(3))
    diagonal_sums = [main_diagonal, anti_diagonal]
    
    # Расчет всех чисел личности
    life_path = calculate_life_path(day, month, year)
    destiny = calculate_destiny_number(day, month, year)
    soul = calculate_soul_number(day)
    mind = calculate_mind_number(month)
    personality = calculate_personality_number(year)
    power = calculate_power_number(day, month, year)
    
    # Персональные рекомендации для каждой планеты
    recommendations = generate_planetary_recommendations(digit_counts, energy_strength)
    
    return {
        'square': display_square,
        'raw_matrix': square_matrix,  # Для внутренних расчетов
        'planet_positions': {
            digit: {
                'name': planet_analysis[digit]['name'],
                'sphere': planet_analysis[digit]['sphere'],
                'color': planet_analysis[digit]['color'],
                'strength': energy_strength[digit],
                'count': digit_counts.get(digit, 0),
                'recommendations': get_planet_recommendations(digit, digit_counts.get(digit, 0))
            }
            for digit in '123456789'
        },
        'life_path': life_path,
        'destiny': destiny, 
        'soul': soul,
        'mind': mind,
        'personality': personality,
        'power': power,
        'energy_totals': digit_counts,
        'energy_strength': energy_strength,
        'horizontal_sums': horizontal_sums,
        'vertical_sums': vertical_sums,
        'diagonal_sums': diagonal_sums,
        'recommendations': recommendations,
        'method': 'Ведическая система нумерологии',
        'calculation_details': {
            'birth_date': f"{day:02d}.{month:02d}.{year}",
            'birth_digits': birth_digits,
            'additional_numbers': {
                'first': first_additional,
                'second': second_additional, 
                'third': third_additional,
                'fourth': fourth_additional
            },
            'all_working_digits': all_digits_for_square
        }
    }

def generate_planetary_recommendations(digit_counts: Dict[str, int], 
                                     energy_strength: Dict[str, str]) -> Dict[str, List[str]]:
    """Генерирует рекомендации для каждой планеты"""
    recommendations = {}
    
    for digit in '123456789':
        count = digit_counts.get(digit, 0)
        strength = energy_strength[digit]
        planet_recs = get_planet_recommendations(digit, count)
        recommendations[digit] = planet_recs
    
    return recommendations

def get_planet_recommendations(digit: str, count: int) -> List[str]:
    """Возвращает рекомендации для конкретной планеты"""
    planet_advice = {
        '1': {  # Солнце
            0: ['Развивайте лидерские качества', 'Работайте над уверенностью в себе', 'Носите золотые украшения по воскресеньям'],
            1: ['Поддерживайте здоровый баланс эго', 'Развивайте творческие способности'],
            2: ['Отличные лидерские качества', 'Используйте харизму для добрых дел'],
            3: ['Очень сильная солнечная энергия', 'Избегайте эгоизма и высокомерия'],
            4: ['Избыток солнечной энергии', 'Практикуйте смирение', 'Помогайте другим развивать уверенность']
        },
        '2': {  # Луна
            0: ['Развивайте эмпатию', 'Уделяйте больше внимания семье', 'Медитируйте при лунном свете'],
            1: ['Хорошая интуиция', 'Доверяйте внутреннему голосу'],
            2: ['Сильная эмоциональная природа', 'Отличная семейная энергия'],
            3: ['Очень развитая интуиция', 'Берегитесь эмоциональных перепадов'],
            4: ['Избыток лунной энергии', 'Практикуйте эмоциональный баланс']
        },
        '3': {  # Юпитер
            0: ['Развивайте мудрость', 'Изучайте философию', 'Практикуйте благотворительность'],
            1: ['Хороший потенциал к обучению', 'Развивайте духовность'],
            2: ['Сильная тяга к знаниям', 'Отличные учительские способности'],
            3: ['Очень мудрая натура', 'Делитесь знаниями с другими'],
            4: ['Избыток юпитерианской энергии', 'Избегайте догматизма']
        },
        '4': {  # Раху
            0: ['Развивайте практичность', 'Работайте над организованностью', 'Создавайте стабильные структуры'],
            1: ['Хорошие организаторские способности', 'Цените стабильность'],
            2: ['Сильная практическая натура', 'Отличные строительные способности'],
            3: ['Очень организованная личность', 'Избегайте излишней консервативности'],
            4: ['Избыток раху энергии', 'Практикуйте гибкость мышления']
        },
        '5': {  # Центр
            0: ['Ищите свободу выражения', 'Путешествуйте больше', 'Развивайте коммуникативные навыки'],
            1: ['Хорошие коммуникативные способности', 'Любите разнообразие'],
            2: ['Сильная тяга к свободе', 'Отличные способности к адаптации'],
            3: ['Очень свободолюбивая натура', 'Избегайте поверхностности'],
            4: ['Избыток свободной энергии', 'Учитесь концентрации и постоянству']
        },
        '6': {  # Венера
            0: ['Развивайте чувство красоты', 'Занимайтесь творчеством', 'Создавайте гармонию вокруг себя'],
            1: ['Хороший эстетический вкус', 'Развивайте творческие таланты'],
            2: ['Сильная творческая энергия', 'Отличное чувство гармонии'],
            3: ['Очень развитое чувство красоты', 'Избегайте излишнего материализма'],
            4: ['Избыток венерианской энергии', 'Практикуйте духовные ценности']
        },
        '7': {  # Кету
            0: ['Развивайте духовность', 'Изучайте мистические науки', 'Практикуйте медитацию'],
            1: ['Хорошая интуиция', 'Развивайте духовные практики'],
            2: ['Сильные мистические способности', 'Отличная интуиция'],
            3: ['Очень развитая духовная натура', 'Избегайте излишней отрешенности'],
            4: ['Избыток кету энергии', 'Балансируйте духовность с практичностью']
        },
        '8': {  # Сатурн
            0: ['Развивайте дисциплину', 'Учитесь терпению', 'Работайте систематически'],
            1: ['Хорошая дисциплина', 'Развивайте ответственность'],
            2: ['Сильная дисциплинированная натура', 'Отличная выносливость'],
            3: ['Очень дисциплинированная личность', 'Избегайте излишней строгости'],
            4: ['Избыток сатурнианской энергии', 'Практикуйте гибкость и сострадание']
        },
        '9': {  # Марс
            0: ['Развивайте решительность', 'Занимайтесь спортом', 'Учитесь управлять гневом'],
            1: ['Хорошая энергия действия', 'Развивайте лидерские качества'],
            2: ['Сильная боевая энергия', 'Отличные способности к достижению целей'],
            3: ['Очень энергичная натура', 'Избегайте агрессивности и конфликтов'],
            4: ['Избыток марсианской энергии', 'Практикуйте терпение и дипломатию']
        }
    }
    
    if count >= 4:
        count = 4
        
    return planet_advice.get(digit, {}).get(count, ['Развивайте эту энергию гармонично'])

def get_personal_numbers(birth_date: str, name: str = "") -> Dict[str, Any]:
    """Получает все персональные числа человека"""
    try:
        day, month, year = parse_birth_date(birth_date)
        
        # Основные числа
        life_path = calculate_life_path(day, month, year)
        destiny = calculate_destiny_number(day, month, year)
        soul = calculate_soul_number(day)
        mind = calculate_mind_number(month)
        personality = calculate_personality_number(year)
        power = calculate_power_number(day, month, year)
        ruling = calculate_ruling_number(day, month)
        problem = calculate_problem_number(life_path, ruling)
        
        # Имя число (если имя предоставлено)
        name_number = None
        if name:
            name_number = calculate_name_number(name)
        
        return {
            'life_path': life_path,
            'destiny': destiny,
            'soul': soul,
            'mind': mind,
            'personality': personality, 
            'power': power,
            'ruling': ruling,
            'problem': problem,
            'name_number': name_number,
            'birth_date': birth_date,
            'name': name,
            'method': 'Ведическая нумерология'
        }
        
    except Exception as e:
        return {'error': f'Ошибка расчета: {str(e)}'}

def calculate_name_number(name: str) -> int:
    """Вычисляет число имени"""
    # Русский алфавит с числовыми значениями
    russian_values = {
        'а': 1, 'б': 2, 'в': 6, 'г': 3, 'д': 4, 'е': 5, 'ё': 5, 'ж': 2, 'з': 7, 'и': 1, 'й': 1,
        'к': 2, 'л': 3, 'м': 4, 'н': 5, 'о': 7, 'п': 8, 'р': 2, 'с': 3, 'т': 4, 'у': 6, 'ф': 8,
        'х': 5, 'ц': 3, 'ч': 7, 'ш': 2, 'щ': 9, 'ъ': 1, 'ы': 1, 'ь': 1, 'э': 6, 'ю': 7, 'я': 2
    }
    
    total = 0
    for char in name.lower():
        if char in russian_values:
            total += russian_values[char]
    
    return reduce_to_single_digit(total)

def get_compatibility_score(birth_date1: str, birth_date2: str) -> Dict[str, Any]:
    """Вычисляет совместимость двух людей"""
    try:
        # Получаем основные числа для каждого человека
        person1_numbers = get_personal_numbers(birth_date1)
        person2_numbers = get_personal_numbers(birth_date2)
        
        # Базовая совместимость по числам жизненного пути
        life_path1 = person1_numbers['life_path']
        life_path2 = person2_numbers['life_path'] 
        
        compatibility_matrix = {
            1: {1: 85, 2: 70, 3: 90, 4: 60, 5: 85, 6: 75, 7: 65, 8: 80, 9: 75},
            2: {1: 70, 2: 90, 3: 75, 4: 80, 5: 65, 6: 95, 7: 70, 8: 75, 9: 70},
            3: {1: 90, 2: 75, 3: 85, 4: 65, 5: 95, 6: 80, 7: 75, 8: 70, 9: 90},
            4: {1: 60, 2: 80, 3: 65, 4: 85, 5: 60, 6: 75, 7: 80, 8: 90, 9: 65},
            5: {1: 85, 2: 65, 3: 95, 4: 60, 5: 80, 6: 70, 7: 75, 8: 65, 9: 85},
            6: {1: 75, 2: 95, 3: 80, 4: 75, 5: 70, 6: 85, 7: 75, 8: 80, 9: 75},
            7: {1: 65, 2: 70, 3: 75, 4: 80, 5: 75, 6: 75, 7: 90, 8: 75, 9: 70},
            8: {1: 80, 2: 75, 3: 70, 4: 90, 5: 65, 6: 80, 7: 75, 8: 85, 9: 75},
            9: {1: 75, 2: 70, 3: 90, 4: 65, 5: 85, 6: 75, 7: 70, 8: 75, 9: 80}
        }
        
        base_compatibility = compatibility_matrix.get(life_path1, {}).get(life_path2, 50)
        
        # Дополнительная совместимость по другим числам
        soul_compatibility = 100 - abs(person1_numbers['soul'] - person2_numbers['soul']) * 10
        destiny_compatibility = 100 - abs(person1_numbers['destiny'] - person2_numbers['destiny']) * 10
        
        # Общий показатель совместимости
        total_compatibility = int((base_compatibility + soul_compatibility + destiny_compatibility) / 3)
        
        # Описание совместимости
        if total_compatibility >= 80:
            description = "Отличная совместимость! Вы дополняете друг друга и имеете схожие жизненные цели."
        elif total_compatibility >= 60:
            description = "Хорошая совместимость. При взаимных усилиях отношения будут гармоничными."
        elif total_compatibility >= 40:
            description = "Средняя совместимость. Потребуется работа над пониманием друг друга."
        else:
            description = "Низкая совместимость. Отношения потребуют значительных усилий от обеих сторон."
        
        return {
            'compatibility_score': total_compatibility,
            'person1_life_path': life_path1,
            'person2_life_path': life_path2,
            'base_compatibility': base_compatibility,
            'soul_compatibility': soul_compatibility,
            'destiny_compatibility': destiny_compatibility,
            'description': description,
            'birth_date1': birth_date1,
            'birth_date2': birth_date2,
            'method': 'Ведическая совместимость'
        }
        
    except Exception as e:
        return {'error': f'Ошибка расчета совместимости: {str(e)}'}

# Основная функция для получения всех расчетов
def get_full_numerology_analysis(birth_date: str, name: str = "") -> Dict[str, Any]:
    """Полный нумерологический анализ"""
    try:
        day, month, year = parse_birth_date(birth_date)
        
        # Персональные числа
        personal_numbers = get_personal_numbers(birth_date, name)
        
        # Улучшенный квадрат Пифагора
        enhanced_square = create_enhanced_pythagorean_square(day, month, year)
        
        return {
            'personal_numbers': personal_numbers,
            'enhanced_square': enhanced_square,
            'birth_date': birth_date,
            'name': name,
            'calculation_date': datetime.now().isoformat(),
            'system': 'Ведическая нумерология - полная система самопознания'
        }
        
    except Exception as e:
        return {'error': f'Ошибка полного анализа: {str(e)}'}