"""
Ведические временные расчеты с привязкой к городу и часовому поясу
"""
import pytz
from datetime import datetime, timedelta
import math
from typing import Dict, Any, Tuple, List
from geopy.geocoders import Nominatim

# Глобальный кеш для координат городов
_city_cache = {}

def get_city_coordinates(city: str) -> Tuple[float, float, str]:
    """
    Получает координаты и часовой пояс для города с кешированием
    """
    if city in _city_cache:
        return _city_cache[city]
    
    try:
        geolocator = Nominatim(user_agent="numerom_app", timeout=10)
        location = geolocator.geocode(city)
        if location:
            latitude = location.latitude
            longitude = location.longitude
            
            # Определяем часовой пояс по координатам
            import timezonefinder
            tf = timezonefinder.TimezoneFinder()
            timezone_str = tf.timezone_at(lat=latitude, lng=longitude)
            
            result = (latitude, longitude, timezone_str or "UTC")
            _city_cache[city] = result
            return result
    except:
        pass
    
    # Fallback для известных городов
    fallback_coords = {
        "кишинев": (47.0105, 28.8638, "Europe/Chisinau"),
        "москва": (55.7558, 37.6173, "Europe/Moscow"),
        "киев": (50.4501, 30.5234, "Europe/Kiev"),
        "минск": (53.9006, 27.5590, "Europe/Minsk"),
    }
    
    city_lower = city.lower()
    if city_lower in fallback_coords:
        result = fallback_coords[city_lower]
        _city_cache[city] = result
        return result
    
    # По умолчанию UTC
    result = (0.0, 0.0, "UTC")
    _city_cache[city] = result
    return result


def get_city_timezone(city: str) -> str:
    """
    Получает часовой пояс для указанного города
    """
    _, _, timezone = get_city_coordinates(city)
    return timezone


def get_sunrise_sunset(city: str, date: datetime) -> Tuple[datetime, datetime]:
    """
    Вычисляет время восхода и заката для указанного города и даты
    """
    try:
        from astral import LocationInfo
        from astral.sun import sun
        
        # Используем кешированные координаты
        latitude, longitude, timezone_str = get_city_coordinates(city)
        
        city_info = LocationInfo(city, "Unknown", timezone_str, latitude, longitude)
        
        s = sun(city_info.observer, date=date.date())
        sunrise = s['sunrise']
        sunset = s['sunset']
        
        # Переводим в локальный часовой пояс города (astral возвращает UTC)
        timezone = pytz.timezone(timezone_str)
        sunrise = sunrise.astimezone(timezone)
        sunset = sunset.astimezone(timezone)
        
        return sunrise, sunset
    except:
        pass
    
    # Fallback: примерные времена (6:00 и 18:00 по местному времени)
    timezone = pytz.timezone(get_city_timezone(city))
    sunrise = timezone.localize(datetime.combine(date.date(), datetime.min.time().replace(hour=6)))
    sunset = timezone.localize(datetime.combine(date.date(), datetime.min.time().replace(hour=18)))
    
    return sunrise, sunset


def calculate_rahu_kaal(sunrise: datetime, sunset: datetime, weekday: int) -> Tuple[datetime, datetime]:
    """
    Рассчитывает Раху Кала для указанного дня
    weekday: 0=Monday, 1=Tuesday, ..., 6=Sunday
    """
    day_duration = sunset - sunrise
    period_duration = day_duration / 8  # День делится на 8 периодов
    
    # Порядок Раху Кала по дням недели (порядковый номер периода от восхода)
    rahu_periods = {
        0: 7,  # Понедельник - 8-й период (7 в 0-индексации) 
        1: 0,  # Вторник - 1-й период
        2: 6,  # Среда - 7-й период  
        3: 3,  # Четверг - 4-й период
        4: 5,  # Пятница - 6-й период
        5: 4,  # Суббота - 5-й период
        6: 2   # Воскресенье - 3-й период
    }
    
    period = rahu_periods[weekday]
    rahu_start = sunrise + (period * period_duration)
    rahu_end = rahu_start + period_duration
    
    return rahu_start, rahu_end


def calculate_gulika_kaal(sunrise: datetime, sunset: datetime, weekday: int) -> Tuple[datetime, datetime]:
    """
    Рассчитывает Гулика Кала
    """
    day_duration = sunset - sunrise
    period_duration = day_duration / 8
    
    # Гулика периоды по дням недели
    gulika_periods = {
        0: 6,  # Понедельник - 7-й период
        1: 5,  # Вторник - 6-й период  
        2: 4,  # Среда - 5-й период
        3: 3,  # Четверг - 4-й период
        4: 2,  # Пятница - 3-й период
        5: 1,  # Суббота - 2-й период
        6: 0   # Воскресенье - 1-й период
    }
    
    period = gulika_periods[weekday]
    gulika_start = sunrise + (period * period_duration)
    gulika_end = gulika_start + period_duration
    
    return gulika_start, gulika_end


def calculate_yamaghanta(sunrise: datetime, sunset: datetime, weekday: int) -> Tuple[datetime, datetime]:
    """
    Рассчитывает Ямаганта
    """
    day_duration = sunset - sunrise
    period_duration = day_duration / 8
    
    # Ямаганта периоды по дням недели
    yamaghanta_periods = {
        0: 4,  # Понедельник - 5-й период
        1: 3,  # Вторник - 4-й период
        2: 2,  # Среда - 3-й период
        3: 1,  # Четверг - 2-й период
        4: 0,  # Пятница - 1-й период
        5: 6,  # Суббота - 7-й период
        6: 5   # Воскресенье - 6-й период
    }
    
    period = yamaghanta_periods[weekday]
    yama_start = sunrise + (period * period_duration)
    yama_end = yama_start + period_duration
    
    return yama_start, yama_end


def calculate_abhijit_muhurta(sunrise: datetime, sunset: datetime) -> Tuple[datetime, datetime]:
    """
    Рассчитывает Абхиджит Мухурта - всегда в полдень ±24 минуты
    """
    day_duration = sunset - sunrise
    midday = sunrise + (day_duration / 2)
    
    # Абхиджит длится 48 минут (24 минуты до и после полудня)
    abhijit_start = midday - timedelta(minutes=24)
    abhijit_end = midday + timedelta(minutes=24)
    
    return abhijit_start, abhijit_end


def calculate_planetary_hours(sunrise: datetime, sunset: datetime, weekday: int) -> List[Dict[str, Any]]:
    """
    Рассчитывает планетарные часы дня (12 дневных часов)
    """
    day_duration = sunset - sunrise
    hour_duration = day_duration / 12  # День делится на 12 планетарных часов
    
    # Планеты в порядке по дням недели (понедельник -> Луна, вторник -> Марс, ..., воскресенье -> Солнце)
    planets_order = ['Chandra', 'Mangal', 'Budh', 'Guru', 'Shukra', 'Shani', 'Surya']
    
    # Определяем планету дня
    ruling_planet = planets_order[weekday]
    
    # Полная последовательность планет для 12 часов
    planet_sequence = []
    start_index = planets_order.index(ruling_planet)
    
    for i in range(12):
        planet_index = (start_index + i) % 7
        planet_sequence.append(planets_order[planet_index])
    
    planetary_hours = []
    for i, planet in enumerate(planet_sequence):
        hour_start = sunrise + (i * hour_duration)
        hour_end = hour_start + hour_duration
        
        # Убираем микросекунды перед форматированием
        hour_start = hour_start.replace(microsecond=0)
        hour_end = hour_end.replace(microsecond=0)
        
        # Форматируем время без миллисекунд и timezone
        start_time_str = hour_start.strftime("%Y-%m-%dT%H:%M:%S")
        end_time_str = hour_end.strftime("%Y-%m-%dT%H:%M:%S")
        
        planetary_hours.append({
            "hour": i + 1,
            "planet": planet,
            "planet_sanskrit": get_planet_sanskrit(planet),
            "start_time": start_time_str,
            "end_time": end_time_str,
            "is_favorable": is_favorable_time(planet, hour_start),
            "period": "day"
        })
    
    return planetary_hours


def calculate_night_planetary_hours(sunset: datetime, next_sunrise: datetime, weekday: int) -> List[Dict[str, Any]]:
    """
    Рассчитывает планетарные часы ночи (12 ночных часов)
    """
    night_duration = next_sunrise - sunset
    hour_duration = night_duration / 12  # Ночь делится на 12 планетарных часов
    
    # Планеты в порядке по дням недели
    planets_order = ['Chandra', 'Mangal', 'Budh', 'Guru', 'Shukra', 'Shani', 'Surya']
    
    # Ночные часы начинаются с 5-го часа дня (продолжение последовательности)
    ruling_planet = planets_order[weekday]
    start_index = planets_order.index(ruling_planet)
    
    # Начинаем с 13-го часа (продолжение дневной последовательности)
    planet_sequence = []
    for i in range(12, 24):  # Часы с 13 по 24
        planet_index = (start_index + i) % 7
        planet_sequence.append(planets_order[planet_index])
    
    night_hours = []
    for i, planet in enumerate(planet_sequence):
        hour_start = sunset + (i * hour_duration)
        hour_end = hour_start + hour_duration
        
        # Убираем микросекунды перед форматированием
        hour_start = hour_start.replace(microsecond=0)
        hour_end = hour_end.replace(microsecond=0)
        
        # Форматируем время без миллисекунд и timezone
        start_time_str = hour_start.strftime("%Y-%m-%dT%H:%M:%S")
        end_time_str = hour_end.strftime("%Y-%m-%dT%H:%M:%S")
        
        night_hours.append({
            "hour": i + 13,  # Нумерация с 13 до 24
            "planet": planet,
            "planet_sanskrit": get_planet_sanskrit(planet),
            "start_time": start_time_str,
            "end_time": end_time_str,
            "is_favorable": is_favorable_time(planet, hour_start),
            "period": "night"
        })
    
    return night_hours


def get_planet_sanskrit(planet: str) -> str:
    """Возвращает санскритское название планеты"""
    sanskrit_names = {
        'Surya': 'Surya (सूर्य)',
        'Chandra': 'Chandra (चन्द्र)', 
        'Mangal': 'Mangal (मंगल)',
        'Budh': 'Budha (बुध)',
        'Guru': 'Guru (गुरु)',
        'Shukra': 'Shukra (शुक्र)',
        'Shani': 'Shani (शनि)'
    }
    return sanskrit_names.get(planet, planet)


def is_favorable_time(planet: str, time: datetime) -> bool:
    """
    Определяет, является ли время благоприятным
    Простая логика: некоторые планеты благоприятнее в определенное время
    """
    hour = time.hour
    
    favorable_hours = {
        'Surya': [6, 7, 8, 9, 10, 11, 12, 13],  # Утро и полдень
        'Chandra': [18, 19, 20, 21, 22],         # Вечер
        'Mangal': [6, 7, 8, 14, 15, 16],        # Утро и послеполуденное время
        'Budh': [9, 10, 11, 15, 16, 17],   # Середина утра и после обеда
        'Guru': [6, 7, 8, 9, 10, 11],      # Утренние часы
        'Shukra': [16, 17, 18, 19, 20],        # Вечерние часы  
        'Shani': [14, 15, 16, 17]            # Послеполуденное время
    }
    
    return hour in favorable_hours.get(planet, [])


def get_vedic_day_schedule(city: str, date: datetime, birth_date: str = None) -> Dict[str, Any]:
    """
    Полная ведическая сводка дня для указанного города
    """
    try:
        # Получаем часовой пояс города
        timezone_str = get_city_timezone(city)
        timezone = pytz.timezone(timezone_str)
        
        # Конвертируем дату в часовой пояс города
        if date.tzinfo is None:
            date = timezone.localize(date)
        else:
            date = date.astimezone(timezone)
        
        # Получаем восход и закат
        sunrise, sunset = get_sunrise_sunset(city, date)
        weekday = date.weekday()
        
        # Получаем восход следующего дня для расчета ночных часов
        next_day = date + timedelta(days=1)
        next_sunrise, _ = get_sunrise_sunset(city, next_day)
        
        # Рассчитываем все временные периоды
        rahu_start, rahu_end = calculate_rahu_kaal(sunrise, sunset, weekday)
        gulika_start, gulika_end = calculate_gulika_kaal(sunrise, sunset, weekday)
        yama_start, yama_end = calculate_yamaghanta(sunrise, sunset, weekday)
        abhijit_start, abhijit_end = calculate_abhijit_muhurta(sunrise, sunset)
        
        # Планетарные часы дня и ночи
        planetary_hours = calculate_planetary_hours(sunrise, sunset, weekday)
        night_hours = calculate_night_planetary_hours(sunset, next_sunrise, weekday)
        
        # Названия дней недели на санскрите
        sanskrit_days = [
            'Somavar (सोमवार)',     # Понедельник - День Луны
            'Mangalvar (मंगलवार)',  # Вторник - День Марса
            'Budhvar (बुधवार)',     # Среда - День Меркурия  
            'Guruvaar (गुरुवार)',   # Четверг - День Юпитера
            'Shukravar (शुक्रवार)',  # Пятница - День Венеры
            'Shanivar (शनिवार)',    # Суббота - День Сатурна
            'Ravivar (रविवार)'      # Воскресенье - День Солнца
        ]
        
        return {
            "city": city,
            "timezone": timezone_str,
            "date": date.strftime("%Y-%m-%d"),
            "weekday": {
                "name": sanskrit_days[weekday],
                "ruling_planet": get_planet_sanskrit(['Chandra', 'Mangal', 'Budh', 'Guru', 'Shukra', 'Shani', 'Surya'][weekday])
            },
            "sun_times": {
                "sunrise": sunrise.strftime("%H:%M"),
                "sunset": sunset.strftime("%H:%M"),
                "day_duration_hours": str(sunset - sunrise)
            },
            "inauspicious_periods": {
                "rahu_kaal": {
                    "name": "राहु काल (Rahu Kaal)",
                    "description": "Неблагоприятное время, избегайте начинания новых дел",
                    "start": rahu_start.strftime("%H:%M"),
                    "end": rahu_end.strftime("%H:%M"),
                    "duration_minutes": int((rahu_end - rahu_start).total_seconds() / 60)
                },
                "gulika_kaal": {
                    "name": "गुलिक काल (Gulika Kaal)", 
                    "description": "Период планеты Гулика, неблагоприятный для важных дел",
                    "start": gulika_start.strftime("%H:%M"),
                    "end": gulika_end.strftime("%H:%M"),
                    "duration_minutes": int((gulika_end - gulika_start).total_seconds() / 60)
                },
                "yamaghanta": {
                    "name": "यमगण्ड (Yamaghanta)",
                    "description": "Период Ямы, избегайте рискованных предприятий",
                    "start": yama_start.strftime("%H:%M"),
                    "end": yama_end.strftime("%H:%M"),
                    "duration_minutes": int((yama_end - yama_start).total_seconds() / 60)
                }
            },
            "auspicious_periods": {
                "abhijit_muhurta": {
                    "name": "अभिजित् मुहूर्त (Abhijit Muhurta)",
                    "description": "Самое благоприятное время дня для любых начинаний",
                    "start": abhijit_start.strftime("%H:%M"),
                    "end": abhijit_end.strftime("%H:%M"),
                    "duration_minutes": 48
                }
            },
            "planetary_hours": planetary_hours,
            "night_hours": night_hours,
            "recommendations": get_daily_recommendations(weekday, planetary_hours, birth_date)
        }
        
    except Exception as e:
        return {
            "error": f"Ошибка расчета ведического расписания: {str(e)}",
            "city": city,
            "date": date.strftime("%Y-%m-%d") if date else None
        }


def get_daily_recommendations(weekday: int, planetary_hours: List[Dict], birth_date: str = None) -> Dict[str, Any]:
    """
    Генерирует персональные рекомендации на день
    """
    day_planets = ['Chandra', 'Mangal', 'Budh', 'Guru', 'Shukra', 'Shani', 'Surya']
    ruling_planet = day_planets[weekday]
    
    # Общие рекомендации по дню недели
    day_recommendations = {
        'Surya': {
            'activities': ['Лидерство', 'Принятие важных решений', 'Публичные выступления', 'Работа с властью'],
            'avoid': ['Споры с начальством', 'Эгоистичные поступки'],
            'colors': ['Золотой', 'Оранжевый', 'Красный'],
            'gems': ['Рубин', 'Гранат']
        },
        'Chandra': {
            'activities': ['Семейные дела', 'Забота о близких', 'Интуитивные решения', 'Творчество'],
            'avoid': ['Конфликты в семье', 'Важные финансовые решения'],
            'colors': ['Белый', 'Серебристый', 'Молочный'],
            'gems': ['Жемчуг', 'Лунный камень']
        },
        'Mangal': {
            'activities': ['Спорт', 'Активные действия', 'Решение проблем', 'Защита интересов'],
            'avoid': ['Агрессивное поведение', 'Конфликты'],
            'colors': ['Красный', 'Алый'],
            'gems': ['Коралл', 'Красная яшма']
        },
        'Budh': {
            'activities': ['Обучение', 'Коммуникации', 'Торговля', 'Путешествия'],
            'avoid': ['Обман', 'Поверхностные суждения'],
            'colors': ['Зеленый', 'Изумрудный'],
            'gems': ['Изумруд', 'Зеленый турмалин']
        },
        'Guru': {
            'activities': ['Духовная практика', 'Образование', 'Благотворительность', 'Мудрые советы'],
            'avoid': ['Материализм', 'Невежество'],
            'colors': ['Желтый', 'Золотистый'],
            'gems': ['Желтый сапфир', 'Топаз']
        },
        'Shukra': {
            'activities': ['Искусство', 'Красота', 'Романтика', 'Финансы'],
            'avoid': ['Излишества', 'Поверхностность'],
            'colors': ['Розовый', 'Белый', 'Пастельные тона'],
            'gems': ['Алмаз', 'Белый сапфир']
        },
        'Shani': {
            'activities': ['Планирование', 'Дисциплина', 'Упорный труд', 'Структурирование'],
            'avoid': ['Лень', 'Откладывание дел'],
            'colors': ['Синий', 'Черный', 'Фиолетовый'],
            'gems': ['Синий сапфир', 'Аметист']
        }
    }
    
    # Лучшие часы для активности
    favorable_hours = [hour for hour in planetary_hours if hour['is_favorable']]
    
    recommendations = day_recommendations.get(ruling_planet, {})
    
    # Форматируем лучшие часы (извлекаем время из ISO строки)
    best_hours_formatted = []
    for h in favorable_hours[:3]:  # Топ-3 часа
        # Извлекаем время из ISO формата (YYYY-MM-DDTHH:MM:SS+TZ)
        start_time = h['start_time'][11:16] if len(h['start_time']) > 16 else h['start_time']
        end_time = h['end_time'][11:16] if len(h['end_time']) > 16 else h['end_time']
        best_hours_formatted.append(f"{start_time}-{end_time} ({h['planet_sanskrit']})")
    
    recommendations.update({
        'ruling_planet': get_planet_sanskrit(ruling_planet),
        'best_hours': best_hours_formatted,
        'planet_mantra': get_planet_mantra(ruling_planet)
    })
    
    return recommendations


def get_planet_mantra(planet: str) -> str:
    """Возвращает мантру планеты"""
    mantras = {
        'Surya': 'ॐ सूर्याय नमः (Om Suryaya Namaha)',
        'Chandra': 'ॐ चन्द्राय नमः (Om Chandraya Namaha)',
        'Mangal': 'ॐ मंगलाय नमः (Om Mangalaya Namaha)', 
        'Budh': 'ॐ बुधाय नमः (Om Budhaya Namaha)',
        'Guru': 'ॐ गुरवे नमः (Om Gurave Namaha)',
        'Shukra': 'ॐ शुक्राय नमः (Om Shukraya Namaha)',
        'Shani': 'ॐ शनैश्चराय नमः (Om Shanaishcharaya Namaha)'
    }
    return mantras.get(planet, 'ॐ (Om)')


def get_monthly_planetary_route(city: str, start_date: datetime, birth_date: str = None,
                                user_numbers: Dict[str, int] = None, pythagorean_square: Dict[str, Any] = None,
                                fractal_behavior: List[int] = None, problem_numbers: List[int] = None,
                                name_numbers: Dict[str, int] = None, weekday_energy: Dict[str, float] = None,
                                janma_ank: int = None, modifiers_config: Dict[str, Any] = None,
                                monthly_route_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Генерирует планетарный маршрут на месяц с расчетом энергии планет
    """
    from vedic_numerology import calculate_enhanced_daily_planetary_energy, calculate_janma_ank, calculate_bhagya_ank, parse_birth_date, reduce_to_single_digit
    
    monthly_schedule = []
    current_date = start_date
    
    # Calculate destiny number and janma_ank if birth_date provided
    destiny_number = None
    if birth_date:
        try:
            day, month, year = parse_birth_date(birth_date)
            if janma_ank is None:
                janma_ank = calculate_janma_ank(day, month, year)
            destiny_number = calculate_bhagya_ank(day, month, year)
        except:
            pass
    
    for day in range(30):  # 30 дней месяца
        try:
            daily_schedule = get_vedic_day_schedule(city=city, date=current_date)
            
            if 'error' not in daily_schedule:
                # Calculate planetary energy for this day
                planetary_energies = {}
                total_energy = 0
                day_type = 'neutral'
                day_type_ru = 'Нейтральный'
                
                if birth_date and destiny_number is not None:
                    try:
                        planetary_energies = calculate_enhanced_daily_planetary_energy(
                            destiny_number=destiny_number,
                            date=current_date,
                            birth_date=birth_date,
                            user_numbers=user_numbers,
                            pythagorean_square=pythagorean_square,
                            fractal_behavior=fractal_behavior,
                            problem_numbers=problem_numbers,
                            name_numbers=name_numbers,
                            weekday_energy=weekday_energy,
                            janma_ank=janma_ank,
                            city=city,
                            modifiers_config=modifiers_config
                        )
                        
                        # Calculate total energy (sum of all planets)
                        total_energy = sum(planetary_energies.values())
                        
                        # Calculate average energy per planet (0-100%)
                        avg_energy_per_planet = total_energy / 9.0 if len(planetary_energies) > 0 else 0
                        
                        # Determine day type using advanced algorithm
                        day_type, day_type_ru, day_score = determine_day_type_advanced(
                            current_date=current_date,
                            birth_date=birth_date,
                            user_numbers=user_numbers,
                            planetary_energies=planetary_energies,
                            ruling_planet=daily_schedule.get('weekday', {}).get('ruling_planet', ''),
                            avg_energy_per_planet=avg_energy_per_planet,
                            modifiers_config=modifiers_config
                        )
                    except Exception as e:
                        print(f"Error calculating planetary energy for {current_date}: {e}")
                        day_score = 50.0  # Fallback score
                
                day_info = {
                    'date': current_date.strftime('%Y-%m-%d'),
                    'weekday': current_date.strftime('%A'),
                    'weekday_ru': ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'][current_date.weekday()],
                    'ruling_planet': daily_schedule.get('weekday', {}).get('ruling_planet', ''),
                    'rahu_kaal': daily_schedule.get('inauspicious_periods', {}).get('rahu_kaal', {}),
                    'abhijit_muhurta': daily_schedule.get('auspicious_periods', {}).get('abhijit_muhurta', {}),
                    'recommendations': daily_schedule.get('recommendations', {}),
                    'favorable_activities': daily_schedule.get('recommendations', {}).get('activities', []),
                    'avoid_activities': daily_schedule.get('recommendations', {}).get('avoid', []),
                    'planetary_energies': planetary_energies,
                    'total_energy': total_energy,
                    'avg_energy_per_planet': round(avg_energy_per_planet, 2) if 'avg_energy_per_planet' in locals() else None,
                    'day_type': day_type,
                    'day_type_ru': day_type_ru,
                    'day_score': day_score if 'day_score' in locals() else 50.0
                }
                monthly_schedule.append(day_info)
        except Exception as e:
            print(f"Error processing day {current_date}: {e}")
        
        current_date += timedelta(days=1)
    
    # Генерируем расширенную сводку месяца
    # Передаем modifiers_config для получения правильного favorable_day_threshold
    monthly_summary = get_monthly_summary(monthly_schedule, monthly_route_config, modifiers_config)
    
    # Добавляем анализ по неделям
    weekly_analysis = get_weekly_analysis(monthly_schedule, start_date, monthly_route_config)
    
    # Добавляем анализ сфер жизни
    life_spheres = analyze_life_spheres(monthly_schedule, user_numbers, pythagorean_square, monthly_route_config)
    
    # Добавляем тренды и прогнозы
    trends = calculate_monthly_trends(monthly_schedule, monthly_summary, monthly_route_config)
    
    # Добавляем лунные фазы
    lunar_phases = get_lunar_phases_for_month(start_date)
    
    # Добавляем планетарные транзиты
    planetary_transits = get_planetary_transits_for_month(monthly_schedule, monthly_route_config)
    
    return {
        'period': 'month',
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': (start_date + timedelta(days=29)).strftime('%Y-%m-%d'),
        'city': city,
        'total_days': len(monthly_schedule),
        'daily_schedule': monthly_schedule,
        'monthly_summary': monthly_summary,
        'weekly_analysis': weekly_analysis,
        'life_spheres': life_spheres,
        'trends': trends,
        'lunar_phases': lunar_phases,
        'planetary_transits': planetary_transits
    }


def get_weekly_planetary_route(city: str, start_date: datetime, birth_date: str = None,
                               user_numbers: Dict[str, int] = None, pythagorean_square: Dict[str, Any] = None,
                               fractal_behavior: List[int] = None, problem_numbers: List[int] = None,
                               name_numbers: Dict[str, int] = None, weekday_energy: Dict[str, float] = None,
                               janma_ank: int = None, modifiers_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Генерирует планетарный маршрут на неделю (7 дней) с расчетом энергии планет
    С детальным анализом каждого дня
    """
    from vedic_numerology import calculate_enhanced_daily_planetary_energy, calculate_janma_ank, calculate_bhagya_ank, parse_birth_date, reduce_to_single_digit
    
    weekly_schedule = []
    current_date = start_date
    
    # Calculate destiny number and janma_ank if birth_date provided
    destiny_number = None
    if birth_date:
        try:
            day, month, year = parse_birth_date(birth_date)
            if janma_ank is None:
                janma_ank = calculate_janma_ank(day, month, year)
            destiny_number = calculate_bhagya_ank(day, month, year)
        except:
            pass
    
    # Собираем данные за 7 дней
    for day_offset in range(7):
        try:
            daily_schedule = get_vedic_day_schedule(city=city, date=current_date)
            
            if 'error' not in daily_schedule:
                weekday_info = daily_schedule.get('weekday', {})
                ruling_planet = weekday_info.get('ruling_planet', 'Surya')
                
                # Базовая оценка благоприятности дня
                favorable_activities = daily_schedule.get('recommendations', {}).get('activities', [])
                avoid_activities = daily_schedule.get('recommendations', {}).get('avoid', [])
                favorable_rating = len(favorable_activities) - (len(avoid_activities) * 0.5)
                
                # Calculate planetary energy for this day
                planetary_energies = {}
                total_energy = 0
                avg_energy_per_planet = 0
                day_type = 'neutral'
                day_type_ru = 'Нейтральный'
                color_class = 'blue'
                
                if birth_date and destiny_number is not None:
                    try:
                        planetary_energies = calculate_enhanced_daily_planetary_energy(
                            destiny_number=destiny_number,
                            date=current_date,
                            birth_date=birth_date,
                            user_numbers=user_numbers,
                            pythagorean_square=pythagorean_square,
                            fractal_behavior=fractal_behavior,
                            problem_numbers=problem_numbers,
                            name_numbers=name_numbers,
                            weekday_energy=weekday_energy,
                            janma_ank=janma_ank,
                            city=city,
                            modifiers_config=modifiers_config
                        )
                        
                        # Calculate total energy (sum of all planets)
                        total_energy = sum(planetary_energies.values())
                        
                        # Calculate average energy per planet (0-100%)
                        avg_energy_per_planet = total_energy / 9.0 if len(planetary_energies) > 0 else 0
                        
                        # Determine day type using advanced algorithm
                        day_type, day_type_ru, day_score = determine_day_type_advanced(
                            current_date=current_date,
                            birth_date=birth_date,
                            user_numbers=user_numbers,
                            planetary_energies=planetary_energies,
                            ruling_planet=daily_schedule.get('weekday', {}).get('ruling_planet', ''),
                            avg_energy_per_planet=avg_energy_per_planet,
                            modifiers_config=modifiers_config
                        )
                        color_class = 'green' if day_type == 'favorable' else 'red'
                    except Exception as e:
                        print(f"Error calculating planetary energy for {current_date}: {e}")
                        # Fallback to old logic
                        day_score = 50.0  # Default score
                        if favorable_rating >= 3:
                            day_type = 'favorable'
                            day_type_ru = 'Благоприятный'
                            color_class = 'green'
                            day_score = 60.0
                        elif favorable_rating <= 1:
                            day_type = 'challenging'
                            day_type_ru = 'Сложный'
                            color_class = 'red'
                            day_score = 30.0
                        else:
                            day_score = 50.0
                else:
                    # Fallback to old logic if no birth_date
                    day_score = 50.0  # Default score
                    if favorable_rating >= 3:
                        day_type = 'favorable'
                        day_type_ru = 'Благоприятный'
                        color_class = 'green'
                        day_score = 60.0
                    elif favorable_rating <= 1:
                        day_type = 'challenging'
                        day_type_ru = 'Сложный'
                        color_class = 'red'
                        day_score = 30.0
                    else:
                        day_score = 50.0
                
                day_info = {
                    'date': current_date.strftime('%Y-%m-%d'),
                    'weekday': current_date.weekday(),
                    'weekday_name': weekday_info.get('name_ru', ''),
                    'ruling_planet': ruling_planet,
                    'planet_sanskrit': weekday_info.get('ruling_planet', ''),
                    'day_type': day_type,
                    'day_type_ru': day_type_ru,
                    'color_class': color_class,
                    'favorable_rating': round(favorable_rating, 1),
                    'day_score': round(day_score, 1) if 'day_score' in locals() else 50.0,
                    'rahu_kaal': daily_schedule.get('inauspicious_periods', {}).get('rahu_kaal', {}),
                    'gulika_kaal': daily_schedule.get('inauspicious_periods', {}).get('gulika_kaal', {}),
                    'favorable_activities': favorable_activities[:5],  # Топ 5
                    'avoid_activities': avoid_activities[:5],  # Топ 5
                    'best_hours': daily_schedule.get('recommendations', {}).get('best_hours', []),
                    'mantra': daily_schedule.get('mantra', ''),
                    'colors': daily_schedule.get('recommendations', {}).get('colors', []),
                    'planetary_energies': planetary_energies,
                    'total_energy': total_energy,
                    'avg_energy_per_planet': round(avg_energy_per_planet, 2)
                }
                
                weekly_schedule.append(day_info)
        except Exception as e:
            print(f"Error processing day {current_date}: {e}")
        
        current_date += timedelta(days=1)
    
    # Генерируем сводку недели
    weekly_summary = get_weekly_summary(weekly_schedule, birth_date)
    
    return {
        'period': 'week',
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': (start_date + timedelta(days=6)).strftime('%Y-%m-%d'),
        'city': city,
        'daily_schedule': weekly_schedule,
        'weekly_summary': weekly_summary
    }


def get_weekly_summary(weekly_schedule: List[Dict], birth_date: str = None) -> Dict[str, Any]:
    """
    Генерирует сводку недели с ключевыми рекомендациями
    """
    # Подсчитываем типы дней
    favorable_days = [d for d in weekly_schedule if d['day_type'] in ['favorable', 'highly_favorable']]
    challenging_days = [d for d in weekly_schedule if d['day_type'] == 'challenging']
    neutral_days = [d for d in weekly_schedule if d['day_type'] == 'neutral']
    
    # Подсчитываем планеты
    planet_distribution = {}
    for day in weekly_schedule:
        planet = day['ruling_planet']
        planet_distribution[planet] = planet_distribution.get(planet, 0) + 1
    
    # Определяем лучший и худший дни
    best_day = max(weekly_schedule, key=lambda x: x['favorable_rating']) if weekly_schedule else None
    worst_day = min(weekly_schedule, key=lambda x: x['favorable_rating']) if weekly_schedule else None
    
    # Средняя оценка недели
    avg_rating = sum(d['favorable_rating'] for d in weekly_schedule) / len(weekly_schedule) if weekly_schedule else 0
    
    # Определяем общую энергетику недели
    if avg_rating >= 2.5:
        week_energy = 'Высокая'
        week_description = 'Неделя благоприятна для активных действий и начинаний'
    elif avg_rating >= 1.5:
        week_energy = 'Средняя'
        week_description = 'Неделя требует баланса между действием и осторожностью'
    else:
        week_energy = 'Низкая'
        week_description = 'Неделя требует осторожности и завершения начатых дел'
    
    # Ключевые рекомендации
    key_recommendations = []
    if favorable_days:
        key_recommendations.append({
            'type': 'positive',
            'title': 'Благоприятные дни',
            'dates': [d['date'] for d in favorable_days],
            'advice': 'Используйте эти дни для важных начинаний, подписания договоров и принятия решений'
        })
    
    if challenging_days:
        key_recommendations.append({
            'type': 'warning',
            'title': 'Сложные дни',
            'dates': [d['date'] for d in challenging_days],
            'advice': 'Будьте осторожны, избегайте рисков и важных начинаний'
        })
    
    # Рекомендации по планированию
    planning_advice = []
    if best_day:
        planning_advice.append(f"Лучший день недели: {best_day['weekday_name']} ({best_day['date']})")
    if worst_day:
        planning_advice.append(f"Будьте осторожны: {worst_day['weekday_name']} ({worst_day['date']})")
    
    return {
        'week_energy': week_energy,
        'week_description': week_description,
        'average_rating': round(avg_rating, 1),
        'favorable_days_count': len(favorable_days),
        'challenging_days_count': len(challenging_days),
        'neutral_days_count': len(neutral_days),
        'planet_distribution': planet_distribution,
        'best_day': best_day,
        'worst_day': worst_day,
        'key_recommendations': key_recommendations,
        'planning_advice': planning_advice
    }


def get_quarterly_planetary_route(city: str, start_date: datetime, birth_date: str = None,
                                  user_numbers: Dict[str, int] = None, pythagorean_square: Dict[str, Any] = None,
                                  fractal_behavior: List[int] = None, problem_numbers: List[int] = None,
                                  name_numbers: Dict[str, int] = None, weekday_energy: Dict[str, float] = None,
                                  janma_ank: int = None, modifiers_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Генерирует планетарный маршрут на квартал (90 дней) с расчетом энергии планет
    """
    from vedic_numerology import calculate_enhanced_daily_planetary_energy, calculate_janma_ank, calculate_bhagya_ank, parse_birth_date, reduce_to_single_digit
    
    quarterly_schedule = []
    current_date = start_date
    
    # Calculate destiny number and janma_ank if birth_date provided
    destiny_number = None
    if birth_date:
        try:
            day, month, year = parse_birth_date(birth_date)
            if janma_ank is None:
                janma_ank = calculate_janma_ank(day, month, year)
            destiny_number = calculate_bhagya_ank(day, month, year)
        except:
            pass
    
    # Группируем по неделям для квартального обзора
    weeks = []
    week_data = []
    
    for day in range(90):  # 90 дней квартала
        try:
            daily_schedule = get_vedic_day_schedule(city=city, date=current_date)
            
            if 'error' not in daily_schedule:
                # Calculate planetary energy for this day
                planetary_energies = {}
                total_energy = 0
                day_type = 'neutral'
                day_type_ru = 'Нейтральный'
                
                if birth_date and destiny_number is not None:
                    try:
                        planetary_energies = calculate_enhanced_daily_planetary_energy(
                            destiny_number=destiny_number,
                            date=current_date,
                            birth_date=birth_date,
                            user_numbers=user_numbers,
                            pythagorean_square=pythagorean_square,
                            fractal_behavior=fractal_behavior,
                            problem_numbers=problem_numbers,
                            name_numbers=name_numbers,
                            weekday_energy=weekday_energy,
                            janma_ank=janma_ank,
                            city=city,
                            modifiers_config=modifiers_config
                        )
                        
                        # Calculate total energy (sum of all planets)
                        total_energy = sum(planetary_energies.values())
                        
                        # Calculate average energy per planet (0-100%)
                        avg_energy_per_planet = total_energy / 9.0 if len(planetary_energies) > 0 else 0
                        
                        # Determine day type based on average energy per planet
                        # Используем порог из конфигурации или значение по умолчанию 60%
                        favorable_threshold = modifiers_config.get('favorable_day_threshold', 60.0) if modifiers_config else 60.0
                        
                        if avg_energy_per_planet < favorable_threshold:
                            day_type = 'challenging'
                            day_type_ru = 'Неблагоприятный'
                        else:
                            day_type = 'favorable'
                            day_type_ru = 'Благоприятный'
                    except Exception as e:
                        print(f"Error calculating planetary energy for {current_date}: {e}")
                
                day_info = {
                    'date': current_date.strftime('%Y-%m-%d'),
                    'weekday': current_date.weekday(),
                    'ruling_planet': daily_schedule.get('weekday', {}).get('ruling_planet', ''),
                    'rahu_kaal': daily_schedule.get('inauspicious_periods', {}).get('rahu_kaal', {}),
                    'favorable_rating': len(daily_schedule.get('recommendations', {}).get('activities', [])),
                    'planetary_energies': planetary_energies,
                    'total_energy': total_energy,
                    'day_type': day_type,
                    'day_type_ru': day_type_ru,
                    'avg_energy_per_planet': round(avg_energy_per_planet, 2) if 'avg_energy_per_planet' in locals() else None
                }
                week_data.append(day_info)
                
                # Каждые 7 дней создаем неделю
                if len(week_data) == 7:
                    weeks.append({
                        'week_number': len(weeks) + 1,
                        'start_date': week_data[0]['date'],
                        'end_date': week_data[-1]['date'],
                        'days': week_data.copy(),
                        'best_days': [d for d in week_data if d.get('day_type') in ['favorable', 'highly_favorable']],
                        'challenging_days': [d for d in week_data if d.get('day_type') == 'challenging']
                    })
                    week_data = []
        except Exception as e:
            print(f"Error processing day {current_date}: {e}")
        
        current_date += timedelta(days=1)
    
    # Добавляем оставшиеся дни недели если есть
    if week_data:
        weeks.append({
            'week_number': len(weeks) + 1,
            'start_date': week_data[0]['date'],
            'end_date': week_data[-1]['date'],
            'days': week_data.copy(),
            'best_days': [d for d in week_data if d.get('day_type') in ['favorable', 'highly_favorable']],
            'challenging_days': [d for d in week_data if d.get('day_type') == 'challenging']
        })
    
    return {
        'period': 'quarter',
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': (start_date + timedelta(days=89)).strftime('%Y-%m-%d'),
        'city': city,
        'total_weeks': len(weeks),
        'weekly_schedule': weeks,
        'quarterly_summary': get_quarterly_summary(weeks)
    }


def get_monthly_summary(monthly_schedule: List[Dict], monthly_route_config: Dict[str, Any] = None, modifiers_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Генерирует полную сводку месяца на основе планетарных энергий и типов дней
    """
    planet_days = {}
    best_days = []
    challenging_days = []
    total_favorable = 0
    total_challenging = 0
    
    # Собираем статистику по планетам и энергиям
    planet_energy_totals = {}
    planet_energy_counts = {}
    
    # Используем favorable_day_score_threshold из modifiers_config (как в determine_day_type_advanced)
    # Это обеспечивает согласованность с алгоритмом определения типа дня
    favorable_score_threshold = modifiers_config.get('favorable_day_score_threshold', 50.0) if modifiers_config else 50.0
    
    for day in monthly_schedule:
        # Подсчет дней по правящим планетам
        planet = day.get('ruling_planet', '').split('(')[0].strip()
        if planet:
            planet_days[planet] = planet_days.get(planet, 0) + 1
        
        # Определение лучших и сложных дней на основе day_score (как в determine_day_type_advanced)
        # Используем day_score для определения типа дня, чтобы совпадало с расчетом для каждого дня
        day_score = day.get('day_score')
        if day_score is None:
            # Если day_score отсутствует, используем day_type как fallback
            day_type = day.get('day_type', 'neutral')
            if day_type == 'favorable' or day_type == 'highly_favorable':
                day_score = 60.0  # Примерное значение для благоприятного дня
            elif day_type == 'challenging':
                day_score = 40.0  # Примерное значение для сложного дня
            else:
                day_score = 50.0  # Нейтральный день
        else:
            day_score = float(day_score) or 50.0
        
        avg_energy = day.get('avg_energy_per_planet', 0) or 0  # Для отображения
        
        # Используем пороги из конфигурации или значения по умолчанию
        best_score_threshold = (monthly_route_config or {}).get('best_day_threshold', 70.0)  # Порог для лучших дней в баллах
        
        # Определяем тип дня на основе day_score (точно так же, как в determine_day_type_advanced)
        # Используем тот же порог favorable_score_threshold
        if day_score >= favorable_score_threshold:
            total_favorable += 1
            # Лучшие дни - это дни с высоким баллом
            if day_score >= best_score_threshold:
                best_days.append({
                    'date': day['date'],
                    'energy': round(avg_energy, 1),
                    'score': round(day_score, 1),
                    'ruling_planet': planet,
                    'day_type': day.get('day_type_ru', 'Благоприятный')
                })
        else:
            # day_score < favorable_score_threshold - неблагоприятный день
            total_challenging += 1
            challenging_days.append({
                'date': day['date'],
                'energy': round(avg_energy, 1),
                'score': round(day_score, 1),
                'ruling_planet': planet,
                'day_type': day.get('day_type_ru', 'Неблагоприятный')
            })
        
        # Собираем статистику по энергиям планет
        planetary_energies = day.get('planetary_energies', {})
        for planet_key, energy in planetary_energies.items():
            if planet_key not in planet_energy_totals:
                planet_energy_totals[planet_key] = 0
                planet_energy_counts[planet_key] = 0
            planet_energy_totals[planet_key] += energy
            planet_energy_counts[planet_key] += 1
    
    # Вычисляем средние энергии планет
    planet_avg_energies = {}
    for planet_key in planet_energy_totals:
        if planet_energy_counts[planet_key] > 0:
            planet_avg_energies[planet_key] = round(
                planet_energy_totals[planet_key] / planet_energy_counts[planet_key], 
                1
            )
    
    # Определяем самую активную планету (с максимальной средней энергией)
    most_active_planet_key = max(planet_avg_energies.items(), key=lambda x: x[1])[0] if planet_avg_energies else 'surya'
    
    # Маппинг ключей планет на русские названия
    planet_names_ru = {
        'surya': 'Солнце',
        'chandra': 'Луна',
        'mangal': 'Марс',
        'budha': 'Меркурий',
        'guru': 'Юпитер',
        'shukra': 'Венера',
        'shani': 'Сатурн',
        'rahu': 'Раху',
        'ketu': 'Кету'
    }
    
    most_active_planet_ru = planet_names_ru.get(most_active_planet_key, 'Солнце')
    
    # Сортируем лучшие дни по баллам (от большего к меньшему)
    best_days_sorted = sorted(best_days, key=lambda x: x.get('score', 0), reverse=True)[:10]
    
    # Сортируем сложные дни по баллам (от меньшего к большему)
    challenging_days_sorted = sorted(challenging_days, key=lambda x: x.get('score', 100), reverse=False)[:10]
    
    # Генерируем рекомендации на основе статистики
    advice_parts = []
    if total_favorable > total_challenging:
        advice_parts.append(f"Месяц благоприятен для активных действий. У вас {total_favorable} благоприятных дней.")
    else:
        advice_parts.append(f"Месяц требует осторожности. У вас {total_challenging} сложных дней.")
    
    if best_days_sorted:
        advice_parts.append(f"Лучшие дни для важных решений: {', '.join([d['date'] for d in best_days_sorted[:5]])}.")
    
    if planet_avg_energies:
        top_planets = sorted(planet_avg_energies.items(), key=lambda x: x[1], reverse=True)[:3]
        top_planets_ru = [planet_names_ru.get(p[0], p[0]) for p in top_planets]
        advice_parts.append(f"Наиболее активные планеты: {', '.join(top_planets_ru)}.")
    
    advice = ' '.join(advice_parts) if advice_parts else 'Используйте планетарные ритмы для максимальной эффективности.'
    
    return {
        'planet_distribution': planet_days,
        'planet_avg_energies': planet_avg_energies,
        'best_days': [d['date'] for d in best_days_sorted],  # Только даты для совместимости
        'best_days_detailed': best_days_sorted,  # Детальная информация
        'challenging_days': [d['date'] for d in challenging_days_sorted],  # Только даты для совместимости
        'challenging_days_detailed': challenging_days_sorted,  # Детальная информация
        'total_favorable_days': total_favorable,
        'total_challenging_days': total_challenging,
        'recommendations': {
            'most_active_planet': most_active_planet_ru,
            'most_active_planet_key': most_active_planet_key,
            'advice': advice,
            'top_planets': [{'key': k, 'name': planet_names_ru.get(k, k), 'avg_energy': v} 
                          for k, v in sorted(planet_avg_energies.items(), key=lambda x: x[1], reverse=True)[:3]]
        }
    }


def get_quarterly_summary(weeks: List[Dict]) -> Dict[str, Any]:
    """
    Генерирует сводку квартала
    """
    all_best_days = []
    all_challenging_days = []
    planet_weeks = {}
    
    for week in weeks:
        all_best_days.extend(week.get('best_days', []))
        all_challenging_days.extend(week.get('challenging_days', []))
        
        # Определяем доминирующую планету недели
        week_planets = [day.get('ruling_planet', '').split('(')[0].strip() for day in week.get('days', [])]
        most_common = max(set(week_planets), key=week_planets.count) if week_planets else 'Солнце'
        planet_weeks[most_common] = planet_weeks.get(most_common, 0) + 1
    
    return {
        'total_best_days': len(all_best_days),
        'total_challenging_days': len(all_challenging_days),
        'best_weeks': [w for w in weeks if len(w.get('best_days', [])) >= 4],
        'challenging_weeks': [w for w in weeks if len(w.get('challenging_days', [])) >= 3],
        'planet_weeks_distribution': planet_weeks,
        'quarterly_advice': {
            'focus_weeks': [w['week_number'] for w in weeks if len(w.get('best_days', [])) >= 5][:5],
            'rest_weeks': [w['week_number'] for w in weeks if len(w.get('challenging_days', [])) >= 4][:3],
            'strategy': 'Планируйте крупные проекты на недели с высокой активностью, используйте сложные недели для отдыха и подготовки.'
        }
    }


def get_weekly_analysis(monthly_schedule: List[Dict], start_date: datetime, monthly_route_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Анализирует месяц по неделям (4-5 недель)
    """
    weeks = []
    current_week = []
    week_start = start_date
    
    for i, day in enumerate(monthly_schedule):
        day_date = datetime.strptime(day['date'], '%Y-%m-%d')
        current_week.append(day)
        
        # Новая неделя начинается в понедельник или если прошло 7 дней
        if len(current_week) == 7 or (day_date.weekday() == 0 and len(current_week) > 0):
            week_num = len(weeks) + 1
            week_end = day_date
            
            # Анализ недели
            favorable_days = [d for d in current_week if d.get('day_type') in ['favorable', 'highly_favorable']]
            challenging_days = [d for d in current_week if d.get('day_type') == 'challenging']
            avg_energy = sum([(d.get('avg_energy_per_planet') or 0) for d in current_week]) / len(current_week) if current_week else 0
            
            # Определяем доминирующую планету недели
            planets = [d.get('ruling_planet', '').split('(')[0].strip() for d in current_week if d.get('ruling_planet')]
            dominant_planet = max(set(planets), key=planets.count) if planets else 'Солнце'
            
            weeks.append({
                'week_number': week_num,
                'start_date': week_start.strftime('%Y-%m-%d'),
                'end_date': week_end.strftime('%Y-%m-%d'),
                'days': current_week.copy(),
                'favorable_days_count': len(favorable_days),
                'challenging_days_count': len(challenging_days),
                'avg_energy': round(avg_energy, 1),
                'dominant_planet': dominant_planet,
                'theme': get_week_theme(dominant_planet, avg_energy, monthly_route_config),
                'key_periods': get_key_periods_for_week(current_week, monthly_route_config),
                'recommendations': get_week_recommendations(favorable_days, challenging_days, avg_energy, monthly_route_config)
            })
            
            current_week = []
            week_start = day_date + timedelta(days=1)
    
    # Добавляем последнюю неделю, если она неполная
    if current_week:
        week_num = len(weeks) + 1
        favorable_days = [d for d in current_week if d.get('day_type') in ['favorable', 'highly_favorable']]
        challenging_days = [d for d in current_week if d.get('day_type') == 'challenging']
        avg_energy = sum([(d.get('avg_energy_per_planet') or 0) for d in current_week]) / len(current_week) if current_week else 0
        planets = [d.get('ruling_planet', '').split('(')[0].strip() for d in current_week if d.get('ruling_planet')]
        dominant_planet = max(set(planets), key=planets.count) if planets else 'Солнце'
        
        weeks.append({
            'week_number': week_num,
            'start_date': week_start.strftime('%Y-%m-%d'),
            'end_date': (week_start + timedelta(days=len(current_week) - 1)).strftime('%Y-%m-%d'),
            'days': current_week,
            'favorable_days_count': len(favorable_days),
            'challenging_days_count': len(challenging_days),
            'avg_energy': round(avg_energy, 1),
            'dominant_planet': dominant_planet,
            'theme': get_week_theme(dominant_planet, avg_energy, monthly_route_config),
                'key_periods': get_key_periods_for_week(current_week, monthly_route_config),
                'recommendations': get_week_recommendations(favorable_days, challenging_days, avg_energy, monthly_route_config)
        })
    
    # Используем пороги из конфигурации
    favorable_week_threshold = (monthly_route_config or {}).get('favorable_week_threshold', 60.0)
    challenging_week_threshold = (monthly_route_config or {}).get('challenging_week_threshold', 40.0)
    
    return {
        'weeks': weeks,
        'total_weeks': len(weeks),
        'favorable_weeks': [w for w in weeks if (w.get('avg_energy') or 0) >= favorable_week_threshold],
        'challenging_weeks': [w for w in weeks if (w.get('avg_energy') or 0) < challenging_week_threshold],
        'overall_theme': get_month_theme(weeks, monthly_route_config)
    }


def get_week_theme(planet: str, avg_energy: float, monthly_route_config: Dict[str, Any] = None) -> str:
    """Определяет тематику недели на основе доминирующей планеты"""
    themes = {
        'Surya': 'Энергия и лидерство',
        'Chandra': 'Эмоции и интуиция',
        'Mangal': 'Действие и решительность',
        'Budha': 'Коммуникация и обучение',
        'Guru': 'Мудрость и расширение',
        'Shukra': 'Красота и гармония',
        'Shani': 'Дисциплина и структура',
        'Rahu': 'Трансформация и перемены',
        'Ketu': 'Духовность и освобождение'
    }
    base_theme = themes.get(planet, 'Гармония и баланс')
    
    # Используем пороги из конфигурации
    high_energy_threshold = (monthly_route_config or {}).get('high_energy_week_threshold', 70.0)
    low_energy_threshold = (monthly_route_config or {}).get('low_energy_week_threshold', 40.0)
    
    if avg_energy >= high_energy_threshold:
        return f"{base_theme} — Высокая активность"
    elif avg_energy < low_energy_threshold:
        return f"{base_theme} — Период осторожности"
    else:
        return base_theme


def get_key_periods_for_week(week_days: List[Dict], monthly_route_config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Определяет ключевые периоды недели"""
    key_periods = []
    
    # Используем пороги из конфигурации
    best_threshold = (monthly_route_config or {}).get('best_day_threshold', 70.0)
    challenging_threshold = (monthly_route_config or {}).get('challenging_day_threshold', 40.0)
    
    # Ищем дни с максимальной и минимальной энергией
    if week_days:
        max_energy_day = max(week_days, key=lambda d: d.get('avg_energy_per_planet') or 0)
        min_energy_day = min(week_days, key=lambda d: d.get('avg_energy_per_planet') or 100)
        
        if (max_energy_day.get('avg_energy_per_planet') or 0) >= best_threshold:
            key_periods.append({
                'date': max_energy_day['date'],
                'type': 'peak',
                'description': 'Пик энергии — идеальное время для важных начинаний'
            })
        
        if (min_energy_day.get('avg_energy_per_planet') or 100) < challenging_threshold:
            key_periods.append({
                'date': min_energy_day['date'],
                'type': 'critical',
                'description': 'Критическая точка — требуется осторожность'
            })
    
    return key_periods


def get_week_recommendations(favorable_days: List[Dict], challenging_days: List[Dict], avg_energy: float, monthly_route_config: Dict[str, Any] = None) -> List[str]:
    """Генерирует рекомендации для недели"""
    recommendations = []
    avg_energy = avg_energy or 0  # Обрабатываем None
    
    # Используем пороги из конфигурации
    high_energy_threshold = (monthly_route_config or {}).get('high_energy_week_threshold', 70.0)
    low_energy_threshold = (monthly_route_config or {}).get('low_energy_week_threshold', 40.0)
    many_favorable_threshold = (monthly_route_config or {}).get('many_favorable_days_threshold', 5)
    several_challenging_threshold = (monthly_route_config or {}).get('several_challenging_days_threshold', 3)
    
    if avg_energy >= high_energy_threshold:
        recommendations.append("Неделя высокой энергии — используйте для активных действий и новых проектов")
    elif avg_energy < low_energy_threshold:
        recommendations.append("Неделя низкой энергии — фокус на восстановлении и планировании")
    else:
        recommendations.append("Сбалансированная неделя — сочетайте активность с отдыхом")
    
    if len(favorable_days) >= many_favorable_threshold:
        recommendations.append(f"Много благоприятных дней ({len(favorable_days)}) — планируйте важные дела")
    
    if len(challenging_days) >= several_challenging_threshold:
        recommendations.append(f"Несколько сложных дней ({len(challenging_days)}) — будьте осторожны")
    
    return recommendations


def get_month_theme(weeks: List[Dict], monthly_route_config: Dict[str, Any] = None) -> str:
    """Определяет общую тематику месяца"""
    if not weeks:
        return "Гармония и баланс"
    
    avg_month_energy = sum([(w.get('avg_energy') or 0) for w in weeks]) / len(weeks)
    dominant_planets = [w['dominant_planet'] for w in weeks]
    most_common_planet = max(set(dominant_planets), key=dominant_planets.count) if dominant_planets else 'Солнце'
    
    # Используем пороги из конфигурации
    month_high_threshold = (monthly_route_config or {}).get('month_high_energy_threshold', 65.0)
    month_low_threshold = (monthly_route_config or {}).get('month_low_energy_threshold', 45.0)
    
    if avg_month_energy >= month_high_threshold:
        return f"Месяц высокой активности под влиянием {most_common_planet}"
    elif avg_month_energy < month_low_threshold:
        return f"Месяц осторожности и переосмысления под влиянием {most_common_planet}"
    else:
        return f"Сбалансированный месяц под влиянием {most_common_planet}"


def analyze_life_spheres(monthly_schedule: List[Dict], user_numbers: Dict[str, int] = None, 
                        pythagorean_square: Dict[str, Any] = None, monthly_route_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Анализирует влияние месяца на различные сферы жизни
    """
    # Планеты, связанные с разными сферами
    sphere_planets = {
        'career_finance': ['Surya', 'Guru', 'Shani'],  # Солнце, Юпитер, Сатурн
        'relationships_family': ['Chandra', 'Shukra'],  # Луна, Венера
        'health_energy': ['Mangal', 'Surya'],  # Марс, Солнце
        'spiritual_growth': ['Ketu', 'Guru', 'Shani']  # Кету, Юпитер, Сатурн
    }
    
    sphere_analysis = {}
    
    for sphere, planets in sphere_planets.items():
        sphere_energies = []
        sphere_days = []
        
        for day in monthly_schedule:
            planetary_energies = day.get('planetary_energies', {})
            day_energy = 0
            planet_count = 0
            
            for planet_key in ['surya', 'chandra', 'mangal', 'budha', 'guru', 'shukra', 'shani', 'rahu', 'ketu']:
                planet_name = planet_key.capitalize()
                if planet_name in planets or (planet_key == 'surya' and 'Surya' in planets):
                    if planet_key in planetary_energies:
                        day_energy += planetary_energies[planet_key]
                        planet_count += 1
            
            if planet_count > 0:
                avg_sphere_energy = day_energy / planet_count
                sphere_energies.append(avg_sphere_energy)
                sphere_days.append({
                    'date': day['date'],
                    'energy': round(avg_sphere_energy, 1),
                    'day_type': day.get('day_type_ru', 'Нейтральный')
                })
        
        avg_sphere_energy = sum(sphere_energies) / len(sphere_energies) if sphere_energies else 0
        
        # Используем пороги из конфигурации
        sphere_best_threshold = (monthly_route_config or {}).get('sphere_best_days_threshold', 70.0)
        sphere_challenging_threshold = (monthly_route_config or {}).get('sphere_challenging_days_threshold', 40.0)
        
        sphere_analysis[sphere] = {
            'avg_energy': round(avg_sphere_energy, 1),
            'rating': get_sphere_rating(avg_sphere_energy, monthly_route_config),
            'best_days': sorted([d for d in sphere_days if d['energy'] >= sphere_best_threshold], 
                              key=lambda x: x['energy'], reverse=True)[:5],
            'challenging_days': sorted([d for d in sphere_days if d['energy'] < sphere_challenging_threshold], 
                                     key=lambda x: x['energy'])[:5],
            'recommendations': get_sphere_recommendations(sphere, avg_sphere_energy, monthly_route_config)
        }
    
    return {
        'career_finance': sphere_analysis['career_finance'],
        'relationships_family': sphere_analysis['relationships_family'],
        'health_energy': sphere_analysis['health_energy'],
        'spiritual_growth': sphere_analysis['spiritual_growth']
    }


def get_sphere_rating(energy: float, monthly_route_config: Dict[str, Any] = None) -> str:
    """Определяет рейтинг сферы жизни"""
    # Используем пороги из конфигурации
    excellent_threshold = (monthly_route_config or {}).get('sphere_excellent_threshold', 70.0)
    good_threshold = (monthly_route_config or {}).get('sphere_good_threshold', 55.0)
    satisfactory_threshold = (monthly_route_config or {}).get('sphere_satisfactory_threshold', 40.0)
    
    if energy >= excellent_threshold:
        return 'Отлично'
    elif energy >= good_threshold:
        return 'Хорошо'
    elif energy >= satisfactory_threshold:
        return 'Удовлетворительно'
    else:
        return 'Требует внимания'


def get_sphere_recommendations(sphere: str, energy: float, monthly_route_config: Dict[str, Any] = None) -> List[str]:
    """Генерирует рекомендации для сферы жизни"""
    recommendations = []
    
    # Используем пороги из конфигурации
    excellent_threshold = (monthly_route_config or {}).get('sphere_excellent_threshold', 70.0)
    attention_threshold = (monthly_route_config or {}).get('sphere_attention_threshold', 40.0)
    
    if sphere == 'career_finance':
        if energy >= excellent_threshold:
            recommendations.append("Отличное время для карьерных продвижений и финансовых операций")
            recommendations.append("Планируйте важные встречи и переговоры")
        elif energy < attention_threshold:
            recommendations.append("Период осторожности в финансовых вопросах")
            recommendations.append("Избегайте крупных инвестиций без тщательного анализа")
        else:
            recommendations.append("Стабильный период для работы и планирования")
    
    elif sphere == 'relationships_family':
        if energy >= excellent_threshold:
            recommendations.append("Благоприятное время для укрепления отношений")
            recommendations.append("Идеальный период для семейных мероприятий")
        elif energy < attention_threshold:
            recommendations.append("Требуется больше внимания к отношениям")
            recommendations.append("Избегайте конфликтов, фокус на понимании")
        else:
            recommendations.append("Гармоничный период в отношениях")
    
    elif sphere == 'health_energy':
        if energy >= excellent_threshold:
            recommendations.append("Высокий уровень энергии — время для активных действий")
            recommendations.append("Идеально для начала новых тренировок или оздоровительных программ")
        elif energy < attention_threshold:
            recommendations.append("Период восстановления — больше отдыха")
            recommendations.append("Избегайте перегрузок, фокус на восстановлении")
        else:
            recommendations.append("Стабильный уровень энергии")
    
    elif sphere == 'spiritual_growth':
        if energy >= excellent_threshold:
            recommendations.append("Период глубокого духовного роста")
            recommendations.append("Идеальное время для медитации и саморазвития")
        elif energy < attention_threshold:
            recommendations.append("Время для переосмысления и внутренней работы")
            recommendations.append("Фокус на внутреннем балансе")
        else:
            recommendations.append("Стабильный период для духовных практик")
    
    return recommendations


def calculate_monthly_trends(monthly_schedule: List[Dict], monthly_summary: Dict[str, Any], monthly_route_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Рассчитывает тренды и прогнозы на месяц
    """
    # Анализ энергий по дням
    energies = [(d.get('avg_energy_per_planet') or 0) for d in monthly_schedule]
    
    if not energies:
        return {
            'energy_trend': 'stable',
            'optimal_start_periods': [],
            'completion_periods': [],
            'planning_recommendations': []
        }
    
    # Определяем тренд энергии
    first_half = energies[:len(energies)//2]
    second_half = energies[len(energies)//2:]
    first_avg = sum(first_half) / len(first_half) if first_half else 0
    second_avg = sum(second_half) / len(second_half) if second_half else 0
    
    # Используем пороги из конфигурации
    trend_rising_threshold = (monthly_route_config or {}).get('trend_rising_threshold', 5.0)
    trend_declining_threshold = (monthly_route_config or {}).get('trend_declining_threshold', 5.0)
    optimal_start_threshold = (monthly_route_config or {}).get('optimal_start_energy_threshold', 65.0)
    optimal_start_min_days = (monthly_route_config or {}).get('optimal_start_min_days', 3)
    completion_min = (monthly_route_config or {}).get('completion_energy_min', 40.0)
    completion_max = (monthly_route_config or {}).get('completion_energy_max', 55.0)
    completion_min_days = (monthly_route_config or {}).get('completion_min_days', 2)
    
    if second_avg > first_avg + trend_rising_threshold:
        energy_trend = 'rising'
        trend_description = 'Энергия растет к концу месяца'
    elif second_avg < first_avg - trend_declining_threshold:
        energy_trend = 'declining'
        trend_description = 'Энергия снижается к концу месяца'
    else:
        energy_trend = 'stable'
        trend_description = 'Стабильный уровень энергии в течение месяца'
    
    # Оптимальные периоды для начинаний (дни с высокой энергией подряд)
    optimal_start_periods = []
    current_period = []
    
    for i, day in enumerate(monthly_schedule):
        energy = day.get('avg_energy_per_planet') or 0
        if energy >= optimal_start_threshold:
            current_period.append(day)
        else:
            if len(current_period) >= optimal_start_min_days:
                optimal_start_periods.append({
                    'start_date': current_period[0]['date'],
                    'end_date': current_period[-1]['date'],
                    'days_count': len(current_period),
                    'avg_energy': round(sum([(d.get('avg_energy_per_planet') or 0) for d in current_period]) / len(current_period), 1),
                    'description': f"Идеальный период для новых начинаний ({len(current_period)} дней)"
                })
            current_period = []
    
    # Проверяем последний период
    if len(current_period) >= optimal_start_min_days:
        optimal_start_periods.append({
            'start_date': current_period[0]['date'],
            'end_date': current_period[-1]['date'],
            'days_count': len(current_period),
            'avg_energy': round(sum([(d.get('avg_energy_per_planet') or 0) for d in current_period]) / len(current_period), 1),
            'description': f"Идеальный период для новых начинаний ({len(current_period)} дней)"
        })
    
    # Периоды для завершения проектов (дни с низкой энергией, подходящие для завершения)
    completion_periods = []
    current_period = []
    
    for day in monthly_schedule:
        energy = day.get('avg_energy_per_planet') or 0
        if completion_min <= energy < completion_max:  # Умеренная энергия для завершения
            current_period.append(day)
        else:
            if len(current_period) >= completion_min_days:
                completion_periods.append({
                    'start_date': current_period[0]['date'],
                    'end_date': current_period[-1]['date'],
                    'days_count': len(current_period),
                    'description': f"Подходящее время для завершения проектов ({len(current_period)} дней)"
                })
            current_period = []
    
    if len(current_period) >= completion_min_days:
        completion_periods.append({
            'start_date': current_period[0]['date'],
            'end_date': current_period[-1]['date'],
            'days_count': len(current_period),
            'description': f"Подходящее время для завершения проектов ({len(current_period)} дней)"
        })
    
    # Рекомендации по планированию
    planning_recommendations = []
    
    if energy_trend == 'rising':
        planning_recommendations.append("Энергия растет к концу месяца — планируйте важные дела на вторую половину")
    elif energy_trend == 'declining':
        planning_recommendations.append("Энергия снижается к концу месяца — важные дела лучше планировать на первую половину")
    
    if optimal_start_periods:
        planning_recommendations.append(f"Выявлено {len(optimal_start_periods)} оптимальных периодов для новых начинаний")
    
    if monthly_summary.get('total_favorable_days', 0) > monthly_summary.get('total_challenging_days', 0) * 2:
        planning_recommendations.append("Месяц благоприятен для активных действий — используйте возможности")
    
    return {
        'energy_trend': energy_trend,
        'trend_description': trend_description,
        'optimal_start_periods': optimal_start_periods[:5],  # Топ-5
        'completion_periods': completion_periods[:5],  # Топ-5
        'planning_recommendations': planning_recommendations
    }


def get_lunar_phases_for_month(start_date: datetime) -> List[Dict[str, Any]]:
    """
    Рассчитывает лунные фазы для месяца
    """
    try:
        from astral import moon
        
        lunar_phases = []
        current_date = start_date
        
        for i in range(30):
            try:
                phase = moon.phase(current_date)
                
                # Определяем фазу луны
                if phase < 1.0 or phase > 29.0:
                    phase_name = 'Новолуние'
                    phase_emoji = '🌑'
                elif 1.0 <= phase < 7.0:
                    phase_name = 'Растущая луна'
                    phase_emoji = '🌒'
                elif 7.0 <= phase < 14.0:
                    phase_name = 'Первая четверть'
                    phase_emoji = '🌓'
                elif 14.0 <= phase < 15.0:
                    phase_name = 'Полнолуние'
                    phase_emoji = '🌕'
                elif 15.0 <= phase < 22.0:
                    phase_name = 'Убывающая луна'
                    phase_emoji = '🌖'
                elif 22.0 <= phase < 29.0:
                    phase_name = 'Последняя четверть'
                    phase_emoji = '🌗'
                else:
                    phase_name = 'Новолуние'
                    phase_emoji = '🌑'
                
                # Добавляем только ключевые фазы (новолуние, полнолуние, четверти)
                if phase < 1.5 or 14.0 <= phase < 15.5 or 7.0 <= phase < 7.5 or 22.0 <= phase < 22.5:
                    lunar_phases.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'phase': phase_name,
                        'phase_emoji': phase_emoji,
                        'phase_value': round(phase, 1),
                        'influence': get_lunar_influence(phase_name)
                    })
            except:
                pass
            
            current_date += timedelta(days=1)
        
        return lunar_phases
    except ImportError:
        # Если astral не установлен, возвращаем базовую информацию
        return [
            {
                'date': start_date.strftime('%Y-%m-%d'),
                'phase': 'Расчет недоступен',
                'phase_emoji': '🌙',
                'influence': 'Установите библиотеку astral для расчета лунных фаз'
            }
        ]


def get_lunar_influence(phase_name: str) -> str:
    """Определяет влияние лунной фазы"""
    influences = {
        'Новолуние': 'Время новых начинаний и планирования',
        'Растущая луна': 'Период роста и развития',
        'Первая четверть': 'Время активных действий',
        'Полнолуние': 'Пик энергии, время реализации',
        'Убывающая луна': 'Период завершения и освобождения',
        'Последняя четверть': 'Время анализа и переосмысления'
    }
    return influences.get(phase_name, 'Влияние лунной фазы')


def get_planetary_transits_for_month(monthly_schedule: List[Dict], monthly_route_config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Определяет важные планетарные транзиты в течение месяца
    """
    transits = []
    
    # Ищем дни с особыми планетарными конфигурациями
    for i, day in enumerate(monthly_schedule):
        planetary_energies = day.get('planetary_energies', {})
        
        if not planetary_energies:
            continue
        
        # Используем пороги из конфигурации
        peak_threshold = (monthly_route_config or {}).get('transit_peak_threshold', 85.0)
        low_threshold = (monthly_route_config or {}).get('transit_low_threshold', 15.0)
        max_transits = (monthly_route_config or {}).get('max_transits_per_month', 20)
        
        # Ищем дни с очень высокой или очень низкой энергией конкретных планет
        for planet_key, energy in planetary_energies.items():
            if energy >= peak_threshold:  # Очень высокая энергия
                planet_names = {
                    'surya': 'Солнце', 'chandra': 'Луна', 'mangal': 'Марс',
                    'budha': 'Меркурий', 'guru': 'Юпитер', 'shukra': 'Венера',
                    'shani': 'Сатурн', 'rahu': 'Раху', 'ketu': 'Кету'
                }
                planet_name = planet_names.get(planet_key, planet_key)
                
                transits.append({
                    'date': day['date'],
                    'planet': planet_name,
                    'type': 'peak',
                    'energy': round(energy, 1),
                    'description': f'Пик энергии {planet_name} — благоприятное время для действий, связанных с этой планетой'
                })
            elif energy <= low_threshold:  # Очень низкая энергия
                planet_names = {
                    'surya': 'Солнце', 'chandra': 'Луна', 'mangal': 'Марс',
                    'budha': 'Меркурий', 'guru': 'Юпитер', 'shukra': 'Венера',
                    'shani': 'Сатурн', 'rahu': 'Раху', 'ketu': 'Кету'
                }
                planet_name = planet_names.get(planet_key, planet_key)
                
                transits.append({
                    'date': day['date'],
                    'planet': planet_name,
                    'type': 'low',
                    'energy': round(energy, 1),
                    'description': f'Низкая энергия {planet_name} — требуется осторожность в соответствующих сферах'
                })
    
    # Сортируем по дате и ограничиваем количество
    transits.sort(key=lambda x: x['date'])
    return transits[:max_transits]  # Топ-N транзитов


def determine_day_type_advanced(
    current_date: datetime,
    birth_date: str,
    user_numbers: Dict[str, int],
    planetary_energies: Dict[str, float],
    ruling_planet: str,
    avg_energy_per_planet: float,
    modifiers_config: Dict[str, Any] = None
) -> Tuple[str, str, float]:
    """
    Определяет тип дня (благоприятный/неблагоприятный) на основе комплексного анализа:
    1. Энергия планеты дня и её сопоставимость с текущим днём
    2. Коэффициенты дня, месяца, года рождения
    3. Личное число месяца, года
    4. Аналитика всех факторов
    """
    from numerology import reduce_to_single_digit, parse_birth_date
    
    if modifiers_config is None:
        modifiers_config = {}
    
    try:
        # Парсим дату рождения
        birth_day, birth_month, birth_year = parse_birth_date(birth_date)
        
        # Получаем текущие дату, месяц, год
        current_day = current_date.day
        current_month = current_date.month
        current_year = current_date.year
        
        # Вычисляем личные числа для текущей даты
        individual_year = reduce_to_single_digit(birth_day + birth_month + current_year)
        individual_month = reduce_to_single_digit(individual_year + current_month)
        individual_day = reduce_to_single_digit(individual_month + current_day)
        
        # Получаем персональные числа
        destiny_number = user_numbers.get('destiny_number', 0)
        soul_number = user_numbers.get('soul_number', 0)
        mind_number = user_numbers.get('mind_number', 0)
        ruling_number = user_numbers.get('ruling_number', 0)
        
        # Нормализуем название планеты дня
        planet_name_map = {
            'Surya': 'surya', 'Chandra': 'chandra', 'Mangal': 'mangal',
            'Budh': 'budha', 'Budha': 'budha', 'Guru': 'guru',
            'Shukra': 'shukra', 'Shani': 'shani', 'Rahu': 'rahu', 'Ketu': 'ketu'
        }
        ruling_planet_key = planet_name_map.get(ruling_planet, ruling_planet.lower() if ruling_planet else '')
        
        # Получаем энергию планеты дня
        ruling_planet_energy = planetary_energies.get(ruling_planet_key, 0) if ruling_planet_key else 0
        
        # Оценка факторов (0-100, где 100 - максимально благоприятно)
        score = 50  # Базовый балл
        
        # 1. Анализ энергии планеты дня
        # Если энергия планеты дня высокая (>70%), это благоприятно
        if ruling_planet_energy > 70:
            score += 15
        elif ruling_planet_energy > 50:
            score += 5
        elif ruling_planet_energy < 30:
            score -= 15
        elif ruling_planet_energy < 50:
            score -= 5
        
        # 2. Сопоставимость личного числа дня с числом судьбы
        if individual_day == destiny_number:
            score += 20
        elif abs(individual_day - destiny_number) <= 1:
            score += 10
        elif abs(individual_day - destiny_number) >= 5:
            score -= 10
        
        # 3. Сопоставимость личного числа месяца с числом ума
        if individual_month == mind_number:
            score += 15
        elif abs(individual_month - mind_number) <= 1:
            score += 7
        elif abs(individual_month - mind_number) >= 5:
            score -= 7
        
        # 4. Сопоставимость личного числа года с числом судьбы
        if individual_year == destiny_number:
            score += 15
        elif abs(individual_year - destiny_number) <= 1:
            score += 7
        elif abs(individual_year - destiny_number) >= 5:
            score -= 7
        
        # 5. Сопоставимость дня рождения с текущим днём
        birth_day_reduced = reduce_to_single_digit(birth_day)
        current_day_reduced = reduce_to_single_digit(current_day)
        if birth_day_reduced == current_day_reduced:
            score += 10
        elif abs(birth_day_reduced - current_day_reduced) >= 5:
            score -= 5
        
        # 6. Сопоставимость месяца рождения с текущим месяцем
        birth_month_reduced = reduce_to_single_digit(birth_month)
        current_month_reduced = reduce_to_single_digit(current_month)
        if birth_month_reduced == current_month_reduced:
            score += 8
        elif abs(birth_month_reduced - current_month_reduced) >= 5:
            score -= 4
        
        # 7. Сопоставимость года рождения (последняя цифра) с текущим годом
        birth_year_last = birth_year % 10
        current_year_last = current_year % 10
        if birth_year_last == current_year_last:
            score += 5
        elif abs(birth_year_last - current_year_last) >= 5:
            score -= 3
        
        # 8. Сопоставимость с правящим числом
        if individual_day == ruling_number or individual_month == ruling_number or individual_year == ruling_number:
            score += 12
        
        # 9. Общая средняя энергия планет (дополнительный фактор, но не основной)
        # Используем энергию планеты дня как дополнительный модификатор
        if avg_energy_per_planet > 70:
            score += 8
        elif avg_energy_per_planet > 60:
            score += 4
        elif avg_energy_per_planet < 40:
            score -= 8
        elif avg_energy_per_planet < 50:
            score -= 4
        
        # Ограничиваем score в диапазоне 0-100
        score = max(0, min(100, score))
        
        # Определяем тип дня на основе итогового score (баллов)
        # Порог благоприятности теперь в баллах, а не в процентах
        # По умолчанию: если score >= 50, день благоприятный
        favorable_score_threshold = modifiers_config.get('favorable_day_score_threshold', 50.0)
        
        if score >= favorable_score_threshold:
            return 'favorable', 'Благоприятный', round(score, 1)
        else:
            return 'challenging', 'Неблагоприятный', round(score, 1)
            
    except Exception as e:
        print(f"Error in determine_day_type_advanced: {e}")
        # В случае ошибки используем простой алгоритм на основе баллов
        # Если score не удалось вычислить, используем fallback на основе энергии
        favorable_score_threshold = modifiers_config.get('favorable_day_score_threshold', 50.0) if modifiers_config else 50.0
        # Fallback: если не удалось вычислить score, используем энергию как индикатор
        # Но это не должно происходить в нормальной работе
        favorable_threshold = modifiers_config.get('favorable_day_threshold', 60.0) if modifiers_config else 60.0
        fallback_score = 50.0 if avg_energy_per_planet >= favorable_threshold else 30.0
        if avg_energy_per_planet >= favorable_threshold:
            return 'favorable', 'Благоприятный', round(fallback_score, 1)
        else:
            return 'challenging', 'Неблагоприятный', round(fallback_score, 1)