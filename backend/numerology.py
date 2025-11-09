from datetime import datetime
from typing import Dict, List, Any
import re
import calendar


def parse_birth_date(birth_date: str) -> tuple[int, int, int]:
    """Parse birth date in DD.MM.YYYY format"""
    try:
        day, month, year = birth_date.split('.')
        return int(day), int(month), int(year)
    except:
        raise ValueError("Invalid date format. Use DD.MM.YYYY")


def reduce_to_single_digit(number: int) -> int:
    """Reduce number to single digit (except master numbers 11, 22, 33)"""
    if number in [11, 22, 33]:
        return number
    
    while number > 9:
        number = sum(int(digit) for digit in str(number))
        # Check if we have a master number during reduction
        if number in [11, 22, 33]:
            return number
    return number


def calculate_life_path(day: int, month: int, year: int) -> int:
    """Calculate Life Path number"""
    total = day + month + year
    return reduce_to_single_digit(total)


def reduce_to_single_digit_always(number: int) -> int:
    """Reduce number to single digit always, no exceptions for master numbers"""
    while number > 9:
        number = sum(int(digit) for digit in str(number))
    return number


def reduce_for_ruling_number(number: int) -> int:
    """Reduce number for ruling number - keeps only 11 and 22 as master numbers"""
    if number in [11, 22]:
        return number
    
    while number > 9:
        number = sum(int(digit) for digit in str(number))
        # Check if we have 11 or 22 during reduction
        if number in [11, 22]:
            return number
    return number


def calculate_destiny_number(day: int, month: int, year: int) -> int:
    """Calculate Destiny number (day + month + year as numbers, always reduced to single digit)"""
    total = day + month + year
    return reduce_to_single_digit_always(total)


def calculate_soul_number(day: int) -> int:
    """Calculate Soul number from birth day"""
    return reduce_to_single_digit(day)


def calculate_mind_number(month: int) -> int:
    """Calculate Mind number from birth month"""
    return reduce_to_single_digit(month)


def calculate_ruling_number(day: int, month: int, year: int) -> int:
    """Calculate Ruling number - sum of all digits of birth date, month and year
    Special cases: 11 and 22 are ALWAYS preserved as master numbers"""
    # Get all digits from day, month, year
    all_digits = [int(d) for d in str(day) + str(month) + str(year)]
    total = sum(all_digits)
    
    # Check for master numbers at ANY stage and preserve them
    if total == 11 or total == 22:
        return total
    
    # Reduce to single digit, but check for master numbers at each step
    while total > 9:
        total = sum(int(digit) for digit in str(total))
        # Check again after each reduction
        if total == 11 or total == 22:
            return total
    
    return total


def calculate_helping_mind_number(day: int, month: int) -> int:
    """Calculate Helping Mind number (ЧУ*) - day + month as numbers, reduced to single digit"""
    total = day + month
    return reduce_to_single_digit(total)


def calculate_wisdom_number(day: int, month: int, year: int) -> int:
    """Calculate Wisdom number (ЧМ) - sum of destiny number + full name number
    Note: For now using simplified calculation until name is provided"""
    # Calculate destiny number first
    destiny_number = calculate_destiny_number(day, month, year)
    
    # TODO: Add full name number calculation when name data is available
    # For now, using destiny number doubled as placeholder
    name_number = destiny_number  # Placeholder until name calculation is implemented
    
    total = destiny_number + name_number
    return reduce_to_single_digit(total)


def calculate_planetary_strength(day: int, month: int, year: int) -> Dict[str, Any]:
    """Calculate Planetary Strength according to the formula with 7 planets (no Rahu/Ketu)"""
    # Формула: день+месяц (как число) * год = результат
    # Пример: 10.01.1982 -> 1001 * 1982 = 1983982
    
    day_month_combined = int(f"{day:02d}{month:02d}")
    result_number = day_month_combined * year
    
    # Получаем день недели рождения
    birth_date_obj = datetime(year, month, day)
    weekday = birth_date_obj.weekday()  # 0=Monday, 6=Sunday
    weekday_names = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
    weekday_short = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']
    
    # Конвертируем в нумерологический порядок (0=Воскресенье=Солнце)
    if weekday == 6:  # Sunday
        start_planet = 0  # Солнце (начинаем с индекса 0)
    else:
        start_planet = weekday + 1  # Monday=1 (Луна), Tuesday=2, etc.
    
    # Цифры результата определяют силу планет по порядку, начиная с дня недели
    result_digits = [int(d) for d in str(result_number)]
    
    # Только 7 планет (убираем Раху и Кету)
    planet_names = ['Солнце', 'Луна', 'Марс', 'Меркурий', 'Юпитер', 'Венера', 'Сатурн']
    weekdays = ['ВС', 'ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ']
    
    # Initialize all planets with 0
    planet_strength = {planet: 0 for planet in planet_names}
    planet_weekday_map = {}  # Для графика: какой планете какой день недели соответствует
    
    # Assign values from result digits
    for i, digit in enumerate(result_digits):
        planet_index = (start_planet + i) % 7  # Используем 7 планет
        planet_name = planet_names[planet_index]
        weekday_abbr = weekdays[planet_index]
        
        planet_strength[planet_name] = digit
        planet_weekday_map[planet_name] = weekday_abbr
    
    return {
        'strength': planet_strength,
        'weekday_map': planet_weekday_map,
        'calculation_number': result_number,
        'birth_weekday': weekday_names[weekday],
        'start_planet_index': start_planet
    }


def calculate_personal_numbers(birth_date: str) -> Dict[str, Any]:
    """Calculate all personal numbers"""
    day, month, year = parse_birth_date(birth_date)
    
    # Основные числа
    soul_number = calculate_soul_number(day)
    mind_number = calculate_mind_number(month)
    destiny_number = calculate_destiny_number(day, month, year)
    helping_mind_number = calculate_helping_mind_number(day, month)
    wisdom_number = calculate_wisdom_number(day, month, year)
    ruling_number = calculate_ruling_number(day, month, year)
    
    # Сила планет
    planetary_data = calculate_planetary_strength(day, month, year)
    
    return {
        'soul_number': soul_number,
        'mind_number': mind_number,
        'destiny_number': destiny_number,
        'helping_mind_number': helping_mind_number,
        'wisdom_number': wisdom_number,
        'ruling_number': ruling_number,
        'planetary_strength': planetary_data['strength'],
        'birth_weekday': planetary_data['birth_weekday'],
        'calculation_details': {
            'calculation_number': planetary_data['calculation_number'],
            'start_planet_index': planetary_data['start_planet_index']
        }
    }


def calculate_problem_number(life_path: int, ruling_number: int) -> int:
    """Calculate Problem number"""
    total = life_path + ruling_number
    return reduce_to_single_digit(total)


def get_life_path_code(life_path: int) -> str:
    """Get Life Path Code description"""
    codes = {
        1: "Лидер",
        2: "Дипломат",
        3: "Творец",
        4: "Строитель",
        5: "Исследователь",
        6: "Воспитатель",
        7: "Мистик",
        8: "Материалист",
        9: "Гуманист",
        11: "Вдохновитель",
        22: "Мастер-строитель",
        33: "Учитель"
    }
    return codes.get(life_path, "Неизвестно")


# This function was removed as it was duplicating the enhanced version above


def calculate_individual_numbers(birth_date: str) -> Dict[str, int]:
    """Calculate individual year, month, day numbers"""
    day, month, year = parse_birth_date(birth_date)
    current_year = datetime.now().year
    current_month = datetime.now().month
    current_day = datetime.now().day
    
    individual_year = reduce_to_single_digit(current_year + day + month)
    individual_month = reduce_to_single_digit(current_month + individual_year)
    individual_day = reduce_to_single_digit(current_day + individual_month)
    
    return {
        "individual_year": individual_year,
        "individual_month": individual_month,
        "individual_day": individual_day
    }


def create_pythagorean_square(day: int, month: int, year: int) -> Dict[str, Any]:
    """Create Pythagorean Square (Классический, с 4 доп. числами по методу Александрова)"""
    # Подготовка цифр даты (с ведущими нулями для дня/месяца)
    day_str = str(day).zfill(2) if day < 10 else str(day)
    month_str = str(month).zfill(2) if month < 10 else str(month)
    year_str = str(year)
    birth_digits = list(day_str + month_str + year_str)

    # Дополнительные числа
    first_additional = sum(int(d) for d in birth_digits)                   # А1
    second_additional = sum(int(d) for d in str(first_additional))         # А2
    first_digit_of_day = int(day_str[0])                                   # Первая цифра дня
    third_additional = first_additional - 2 * first_digit_of_day           # А3
    if third_additional <= 0:
        third_additional = abs(third_additional)
    fourth_additional = sum(int(d) for d in str(third_additional))         # А4

    # Все рабочие цифры для квадрата: дата + цифры А1..А4
    all_digits_for_square = birth_digits + [d for num in [first_additional, second_additional, third_additional, fourth_additional] for d in str(num)]

    # Создаем 3x3 сетку
    square = [['', '', ''], ['', '', ''], ['', '', '']]

    # Соответствие позиций 1..9
    number_positions = {
        1: (0, 0), 2: (1, 0), 3: (2, 0),
        4: (0, 1), 5: (1, 1), 6: (2, 1),
        7: (0, 2), 8: (1, 2), 9: (2, 2)
    }

    # Подсчет количества цифр 1..9 (ноль игнорируем)
    digit_counts = {str(i): 0 for i in range(1, 10)}
    for d in all_digits_for_square:
        if d.isdigit() and d != '0':
            digit_counts[d] += 1

    # Заполняем квадрат строками ("111", "55" и т.д.)
    for i in range(1, 10):
        count = digit_counts[str(i)]
        r, c = number_positions[i]
        square[r][c] = str(i) * count if count > 0 else ''

    # Суммы по линиям (считаем количество цифр в ячейках)
    horizontal_sums = [sum(len(cell) for cell in row) for row in square]
    vertical_sums = [sum(len(square[r][c]) for r in range(3)) for c in range(3)]
    diagonal_sums = [
        sum(len(square[i][i]) for i in range(3)),
        sum(len(square[i][2 - i]) for i in range(3))
    ]

    additional_numbers = [first_additional, second_additional, third_additional, fourth_additional]

    return {
        "square": square,
        "horizontal_sums": horizontal_sums,
        "vertical_sums": vertical_sums,
        "diagonal_sums": diagonal_sums,
        "additional_numbers": additional_numbers,
        "number_positions": {str(k): v for k, v in number_positions.items()}
    }


# This function was removed as it was duplicating the enhanced version above


def calculate_compatibility(birth_date1: str, birth_date2: str) -> Dict[str, Any]:
    """Calculate compatibility between two birth dates"""
    day1, month1, year1 = parse_birth_date(birth_date1)
    day2, month2, year2 = parse_birth_date(birth_date2)
    
    life_path1 = calculate_life_path(day1, month1, year1)
    life_path2 = calculate_life_path(day2, month2, year2)
    
    # Simple compatibility calculation
    compatibility_score = 10 - abs(life_path1 - life_path2)
    if compatibility_score < 1:
        compatibility_score = 1
    
    return {
        "person1_life_path": life_path1,
        "person2_life_path": life_path2,
        "compatibility_score": compatibility_score,
        "description": f"Совместимость {compatibility_score}/10"
    }

def calculate_name_numerology(full_name: str) -> Dict[str, Any]:
    """
    Рассчитывает нумерологию имени и фамилии
    """
    if not full_name:
        return {"error": "Имя не указано"}
    
    # Конвертируем буквы в числа
    letter_values = {
        'А': 1, 'Б': 2, 'В': 3, 'Г': 4, 'Д': 5, 'Е': 6, 'Ё': 6, 'Ж': 7, 'З': 8, 'И': 9,
        'Й': 1, 'К': 2, 'Л': 3, 'М': 4, 'Н': 5, 'О': 6, 'П': 7, 'Р': 8, 'С': 9,
        'Т': 1, 'У': 2, 'Ф': 3, 'Х': 4, 'Ц': 5, 'Ч': 6, 'Ш': 7, 'Щ': 8, 'Ъ': 9,
        'Ы': 1, 'Ь': 2, 'Э': 3, 'Ю': 4, 'Я': 5,
        'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9,
        'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'O': 6, 'P': 7, 'Q': 8, 'R': 9,
        'S': 1, 'T': 2, 'U': 3, 'V': 4, 'W': 5, 'X': 6, 'Y': 7, 'Z': 8
    }
    
    # Разделяем имя и фамилию
    name_parts = full_name.strip().split()
    if len(name_parts) < 2:
        name_parts.append("")  # Добавляем пустую фамилию если только имя
    
    first_name = name_parts[0].upper()
    last_name = name_parts[1].upper() if len(name_parts) > 1 else ""
    
    # Рассчитываем числа имени
    first_name_sum = sum(letter_values.get(char, 0) for char in first_name if char.isalpha())
    first_name_number = reduce_to_single_digit(first_name_sum)
    
    # Рассчитываем числа фамилии
    last_name_sum = sum(letter_values.get(char, 0) for char in last_name if char.isalpha())
    last_name_number = reduce_to_single_digit(last_name_sum) if last_name else 0
    
    # Общее число имени
    total_name_number = reduce_to_single_digit(first_name_sum + last_name_sum)
    
    # Интерпретации
    name_interpretations = {
        1: "Лидерство, независимость, новаторство",
        2: "Сотрудничество, дипломатия, чувствительность", 
        3: "Творчество, общительность, оптимизм",
        4: "Стабильность, практичность, трудолюбие",
        5: "Свобода, приключения, любознательность",
        6: "Забота, ответственность, гармония",
        7: "Духовность, анализ, мудрость",
        8: "Материальный успех, власть, амбиции",
        9: "Служение, сострадание, универсальность"
    }
    
    return {
        "full_name": full_name,
        "first_name": first_name.title(),
        "last_name": last_name.title(),
        "first_name_number": first_name_number,
        "last_name_number": last_name_number,
        "total_name_number": total_name_number,
        "first_name_interpretation": name_interpretations.get(first_name_number, "Неизвестно"),
        "last_name_interpretation": name_interpretations.get(last_name_number, "Неизвестно") if last_name_number else "Фамилия не указана",
        "total_interpretation": name_interpretations.get(total_name_number, "Неизвестно")
    }

def calculate_car_number_numerology(car_number: str) -> Dict[str, Any]:
    """
    Рассчитывает нумерологию номера автомобиля
    car_number: буквенно-цифровой код до 13 символов (любая раскладка)
    """
    if not car_number:
        return {"error": "Номер автомобиля не указан"}
    
    # Конвертируем буквы в числа (А=1, Б=2, и т.д.)
    letter_values = {
        'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9,
        'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'O': 6, 'P': 7, 'Q': 8, 'R': 9,
        'S': 1, 'T': 2, 'U': 3, 'V': 4, 'W': 5, 'X': 6, 'Y': 7, 'Z': 8,
        'А': 1, 'Б': 2, 'В': 3, 'Г': 4, 'Д': 5, 'Е': 6, 'Ё': 7, 'Ж': 8, 'З': 9,
        'И': 1, 'Й': 2, 'К': 3, 'Л': 4, 'М': 5, 'Н': 6, 'О': 7, 'П': 8, 'Р': 9,
        'С': 1, 'Т': 2, 'У': 3, 'Ф': 4, 'Х': 5, 'Ц': 6, 'Ч': 7, 'Ш': 8, 'Щ': 9,
        'Ъ': 1, 'Ы': 2, 'Ь': 3, 'Э': 4, 'Ю': 5, 'Я': 6
    }
    
    total_sum = 0
    for char in car_number.upper():
        if char.isdigit():
            total_sum += int(char)
        elif char in letter_values:
            total_sum += letter_values[char]
    
    # Сводим к однозначному числу
    car_number_value = reduce_to_single_digit(total_sum)
    
    # Интерпретации для номеров автомобилей
    interpretations = {
        1: "Автомобиль лидера. Подходит для деловых поездок и карьерного роста.",
        2: "Автомобиль партнерства. Идеален для семейных поездок и сотрудничества.",
        3: "Автомобиль творчества. Способствует вдохновению и общению.",
        4: "Автомобиль стабильности. Надежен для повседневных поездок.",
        5: "Автомобиль свободы. Подходит для путешествий и приключений.",
        6: "Автомобиль семьи. Идеален для заботы о близких.",
        7: "Автомобиль мудрости. Способствует духовному развитию.",
        8: "Автомобиль успеха. Подходит для материального достатка.",
        9: "Автомобиль служения. Идеален для помощи другим."
    }
    
    return {
        "car_number": car_number,
        "numerology_value": car_number_value,
        "interpretation": interpretations.get(car_number_value, "Интерпретация не найдена"),
        "total_sum": total_sum
    }

def calculate_address_numerology(street: str = None, house_number: str = None, 
                                apartment_number: str = None, postal_code: str = None) -> Dict[str, Any]:
    """
    Рассчитывает нумерологию адреса проживания
    """
    results = {}
    
    if house_number:
        house_sum = sum(int(d) for d in house_number if d.isdigit())
        house_value = reduce_to_single_digit(house_sum)
        results["house_numerology"] = {
            "value": house_value,
            "interpretation": get_house_interpretation(house_value)
        }
    
    if apartment_number:
        apt_sum = sum(int(d) for d in apartment_number if d.isdigit())
        apt_value = reduce_to_single_digit(apt_sum)
        results["apartment_numerology"] = {
            "value": apt_value,
            "interpretation": get_apartment_interpretation(apt_value)
        }
    
    if postal_code:
        postal_sum = sum(int(d) for d in postal_code if d.isdigit())
        postal_value = reduce_to_single_digit(postal_sum)
        results["postal_code_numerology"] = {
            "value": postal_value,
            "interpretation": get_postal_interpretation(postal_value)
        }
    
    return results

def get_house_interpretation(value: int) -> str:
    """Интерпретации для номера дома"""
    interpretations = {
        1: "Дом лидерства и новых начинаний. Подходит для амбициозных людей.",
        2: "Дом партнерства и гармонии. Идеален для семейной жизни.",
        3: "Дом творчества и радости. Способствует самовыражению.",
        4: "Дом стабильности и порядка. Подходит для практичных людей.",
        5: "Дом свободы и перемен. Идеален для путешественников.",
        6: "Дом любви и заботы. Центр семейного очага.",
        7: "Дом духовности и мудрости. Подходит для саморазвития.",
        8: "Дом материального успеха. Способствует достатку.",
        9: "Дом служения и мудрости. Подходит для помощи другим."
    }
    return interpretations.get(value, "Интерпретация не найдена")

def get_apartment_interpretation(value: int) -> str:
    """Интерпретации для номера квартиры"""
    interpretations = {
        1: "Квартира независимости. Подходит для самостоятельных людей.",
        2: "Квартира сотрудничества. Идеальна для пар.",
        3: "Квартира общения. Центр социальной активности.",
        4: "Квартира порядка. Подходит для организованных людей.",
        5: "Квартира динамики. Идеальна для активных людей.",
        6: "Квартира уюта. Центр домашнего тепла.",
        7: "Квартира размышлений. Подходит для интровертов.",
        8: "Квартира достижений. Способствует карьерному росту.",
        9: "Квартира щедрости. Подходит для гостеприимных людей."
    }
    return interpretations.get(value, "Интерпретация не найдена")

def get_postal_interpretation(value: int) -> str:
    """Интерпретации для почтового индекса"""
    interpretations = {
        1: "Район лидерства. Способствует карьерному росту.",
        2: "Район сотрудничества. Подходит для семейной жизни.",
        3: "Район творчества. Стимулирует самовыражение.",
        4: "Район стабильности. Подходит для спокойной жизни.",
        5: "Район активности. Способствует переменам.",
        6: "Район гармонии. Идеален для семейного счастья.",
        7: "Район духовности. Подходит для саморазвития.",
        8: "Район процветания. Способствует материальному успеху.",
        9: "Район мудрости. Подходит для духовного роста."
    }
    return interpretations.get(value, "Интерпретация не найдена")

def calculate_group_compatibility(main_person_birth_date: str, people_data: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Рассчитывает групповую совместимость основного человека с группой людей (до 5)
    """
    if len(people_data) > 5:
        return {"error": "Максимальное количество людей для анализа: 5"}
    
    main_day, main_month, main_year = parse_birth_date(main_person_birth_date)
    main_life_path = calculate_life_path(main_day, main_month, main_year)
    
    group_results = []
    for person in people_data:
        try:
            person_day, person_month, person_year = parse_birth_date(person['birth_date'])
            person_life_path = calculate_life_path(person_day, person_month, person_year)
            
            # Расчет совместимости
            compatibility_score = 10 - abs(main_life_path - person_life_path)
            if compatibility_score < 1:
                compatibility_score = 1
            
            # Определение типа отношений
            relationship_type = get_relationship_type(main_life_path, person_life_path)
            
            group_results.append({
                "name": person['name'],
                "birth_date": person['birth_date'],
                "life_path": person_life_path,
                "compatibility_score": compatibility_score,
                "relationship_type": relationship_type,
                "advice": get_compatibility_advice(main_life_path, person_life_path)
            })
        except Exception as e:
            group_results.append({
                "name": person['name'],
                "error": f"Ошибка расчета: {str(e)}"
            })
    
    return {
        "main_person": {
            "birth_date": main_person_birth_date,
            "life_path": main_life_path
        },
        "group_analysis": group_results,
        "average_compatibility": sum(r.get('compatibility_score', 0) for r in group_results) / len(group_results) if group_results else 0
    }

def get_relationship_type(main_life_path: int, person_life_path: int) -> str:
    """Определяет тип отношений на основе чисел жизненного пути"""
    diff = abs(main_life_path - person_life_path)
    
    if diff == 0:
        return "Зеркальные души"
    elif diff == 1:
        return "Гармоничные партнеры"
    elif diff == 2:
        return "Взаимодополняющие"
    elif diff == 3:
        return "Стимулирующие"
    elif diff == 4:
        return "Вызывающие"
    else:
        return "Кармические"

def get_compatibility_advice(main_life_path: int, person_life_path: int) -> str:
    """Дает советы по совместимости"""
    diff = abs(main_life_path - person_life_path)
    
    if diff == 0:
        return "Вы очень похожи. Развивайте разные интересы для разнообразия."
    elif diff <= 2:
        return "Отличная совместимость. Поддерживайте друг друга в целях."
    elif diff <= 4:
        return "Хорошие отношения через понимание различий."
    else:
        return "Требуется терпение и компромиссы для гармонии."

def calculate_name_numerology(full_name: str) -> Dict[str, Any]:
    """
    Рассчитывает нумерологию имени и фамилии
    """
    if not full_name:
        return {"error": "Имя не указано"}
    
    # Конвертируем буквы в числа
    letter_values = {
        'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9,
        'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'O': 6, 'P': 7, 'Q': 8, 'R': 9,
        'S': 1, 'T': 2, 'U': 3, 'V': 4, 'W': 5, 'X': 6, 'Y': 7, 'Z': 8,
        'А': 1, 'Б': 2, 'В': 3, 'Г': 4, 'Д': 5, 'Е': 6, 'Ё': 7, 'Ж': 8, 'З': 9,
        'И': 1, 'Й': 2, 'К': 3, 'Л': 4, 'М': 5, 'Н': 6, 'О': 7, 'П': 8, 'Р': 9,
        'С': 1, 'Т': 2, 'У': 3, 'Ф': 4, 'Х': 5, 'Ц': 6, 'Ч': 7, 'Ш': 8, 'Щ': 9,
        'Ъ': 1, 'Ы': 2, 'Ь': 3, 'Э': 4, 'Ю': 5, 'Я': 6
    }
    
    total_sum = 0
    for char in full_name.upper().replace(' ', ''):
        if char in letter_values:
            total_sum += letter_values[char]
    
    # Сводим к однозначному числу
    name_number = reduce_to_single_digit(total_sum)
    
    # Интерпретации для чисел имени
    interpretations = {
        1: "Лидерство, независимость, новаторство. Вы рождены быть первым.",
        2: "Сотрудничество, дипломатия, чувствительность. Вы миротворец.",
        3: "Творчество, общительность, оптимизм. Вы вдохновляете других.",
        4: "Стабильность, практичность, трудолюбие. Вы надежная опора.",
        5: "Свобода, приключения, любознательность. Вы исследователь жизни.",
        6: "Забота, ответственность, гармония. Вы хранитель семьи.",
        7: "Мудрость, духовность, анализ. Вы искатель истины.",
        8: "Материальный успех, амбиции, власть. Вы организатор.",
        9: "Служение, мудрость, завершение. Вы помогаете человечеству."
    }
    
    return {
        "name_number": name_number,
        "total_sum": total_sum,
        "interpretation": interpretations.get(name_number, "Интерпретация не найдена"),
        "compatibility": get_name_birth_compatibility(name_number)
    }

def get_name_birth_compatibility(name_number: int) -> str:
    """Дает общие советы по совместимости имени с датой рождения"""
    compatibility_advice = {
        1: "Имя усиливает лидерские качества. Подходит для карьерного роста.",
        2: "Имя способствует гармоничным отношениям и сотрудничеству.",
        3: "Имя поддерживает творческие способности и социальную активность.",
        4: "Имя укрепляет стабильность и практические навыки.",
        5: "Имя способствует свободе выражения и новым возможностям.",
        6: "Имя усиливает заботливость и семейные ценности.",
        7: "Имя поддерживает духовное развитие и интуицию.",
        8: "Имя способствует материальному успеху и достижениям.",
        9: "Имя усиливает мудрость и желание помогать другим."
    }
    
    return compatibility_advice.get(name_number, "Совместимость требует индивидуального анализа")