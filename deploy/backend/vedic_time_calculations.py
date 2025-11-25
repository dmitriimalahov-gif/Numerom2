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
                                janma_ank: int = None, modifiers_config: Dict[str, Any] = None) -> Dict[str, Any]:
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
                        
                        # Determine day type based on average energy per planet
                        # < 40% - сложный день, 40-65% - благоприятный, > 65% - очень благоприятный
                        if avg_energy_per_planet < 40:
                            day_type = 'challenging'
                            day_type_ru = 'Сложный'
                        elif avg_energy_per_planet <= 65:
                            day_type = 'favorable'
                            day_type_ru = 'Благоприятный'
                        else:
                            day_type = 'highly_favorable'
                            day_type_ru = 'Очень благоприятный'
                    except Exception as e:
                        print(f"Error calculating planetary energy for {current_date}: {e}")
                
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
                    'day_type': day_type,
                    'day_type_ru': day_type_ru
                }
                monthly_schedule.append(day_info)
        except Exception as e:
            print(f"Error processing day {current_date}: {e}")
        
        current_date += timedelta(days=1)
    
    return {
        'period': 'month',
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': (start_date + timedelta(days=29)).strftime('%Y-%m-%d'),
        'city': city,
        'total_days': len(monthly_schedule),
        'daily_schedule': monthly_schedule,
        'monthly_summary': get_monthly_summary(monthly_schedule)
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
                        
                        # Determine day type based on average energy per planet
                        # < 40% - сложный день, 40-60% - благоприятный, > 60% - очень благоприятный
                        if avg_energy_per_planet < 40:
                            day_type = 'challenging'
                            day_type_ru = 'Сложный'
                            color_class = 'red'
                        elif avg_energy_per_planet <= 60:
                            day_type = 'favorable'
                            day_type_ru = 'Благоприятный'
                            color_class = 'green'
                        else:
                            day_type = 'highly_favorable'
                            day_type_ru = 'Очень благоприятный'
                            color_class = 'green'
                    except Exception as e:
                        print(f"Error calculating planetary energy for {current_date}: {e}")
                        # Fallback to old logic
                        if favorable_rating >= 3:
                            day_type = 'favorable'
                            day_type_ru = 'Благоприятный'
                            color_class = 'green'
                        elif favorable_rating <= 1:
                            day_type = 'challenging'
                            day_type_ru = 'Сложный'
                            color_class = 'red'
                else:
                    # Fallback to old logic if no birth_date
                    if favorable_rating >= 3:
                        day_type = 'favorable'
                        day_type_ru = 'Благоприятный'
                        color_class = 'green'
                    elif favorable_rating <= 1:
                        day_type = 'challenging'
                        day_type_ru = 'Сложный'
                        color_class = 'red'
                
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
                    'rahu_kaal': daily_schedule.get('inauspicious_periods', {}).get('rahu_kaal', {}),
                    'gulika_kaal': daily_schedule.get('inauspicious_periods', {}).get('gulika_kaal', {}),
                    'favorable_activities': favorable_activities[:5],  # Топ 5
                    'avoid_activities': avoid_activities[:5],  # Топ 5
                    'best_hours': daily_schedule.get('recommendations', {}).get('best_hours', []),
                    'mantra': daily_schedule.get('mantra', ''),
                    'colors': daily_schedule.get('recommendations', {}).get('colors', []),
                    'planetary_energies': planetary_energies,
                    'total_energy': total_energy
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
                        # < 40% - сложный день, 40-65% - благоприятный, > 65% - очень благоприятный
                        if avg_energy_per_planet < 40:
                            day_type = 'challenging'
                            day_type_ru = 'Сложный'
                        elif avg_energy_per_planet <= 65:
                            day_type = 'favorable'
                            day_type_ru = 'Благоприятный'
                        else:
                            day_type = 'highly_favorable'
                            day_type_ru = 'Очень благоприятный'
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
                    'day_type_ru': day_type_ru
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


def get_monthly_summary(monthly_schedule: List[Dict]) -> Dict[str, Any]:
    """
    Генерирует сводку месяца
    """
    planet_days = {}
    best_days = []
    challenging_days = []
    
    for day in monthly_schedule:
        planet = day.get('ruling_planet', '').split('(')[0].strip()
        if planet:
            planet_days[planet] = planet_days.get(planet, 0) + 1
        
        if len(day.get('favorable_activities', [])) >= 3:
            best_days.append(day['date'])
        elif len(day.get('avoid_activities', [])) >= 3:
            challenging_days.append(day['date'])
    
    return {
        'planet_distribution': planet_days,
        'best_days': best_days[:10],  # Топ 10 лучших дней
        'challenging_days': challenging_days[:10],  # Топ 10 сложных дней
        'total_favorable_days': len(best_days),
        'total_challenging_days': len(challenging_days),
        'recommendations': {
            'most_active_planet': max(planet_days.items(), key=lambda x: x[1])[0] if planet_days else 'Солнце',
            'advice': 'Используйте лучшие дни для важных начинаний и будьте осторожны в сложные периоды.'
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