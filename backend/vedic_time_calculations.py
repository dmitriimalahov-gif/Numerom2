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
    Рассчитывает планетарные часы дня
    """
    day_duration = sunset - sunrise
    hour_duration = day_duration / 12  # День делится на 12 планетарных часов
    
    # Планеты в порядке по дням недели (понедельник -> Луна, вторник -> Марс, ..., воскресенье -> Солнце)
    planets_order = ['Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Sun']
    
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
        
        planetary_hours.append({
            "hour": i + 1,
            "planet": planet,
            "planet_sanskrit": get_planet_sanskrit(planet),
            "start_time": hour_start,
            "end_time": hour_end,
            "is_favorable": is_favorable_time(planet, hour_start)
        })
    
    return planetary_hours


def get_planet_sanskrit(planet: str) -> str:
    """Возвращает санскритское название планеты"""
    sanskrit_names = {
        'Sun': 'Surya (सूर्य)',
        'Moon': 'Chandra (चन्द्र)', 
        'Mars': 'Mangal (मंगल)',
        'Mercury': 'Budha (बुध)',
        'Jupiter': 'Guru (गुरु)',
        'Venus': 'Shukra (शुक्र)',
        'Saturn': 'Shani (शनि)'
    }
    return sanskrit_names.get(planet, planet)


def is_favorable_time(planet: str, time: datetime) -> bool:
    """
    Определяет, является ли время благоприятным
    Простая логика: некоторые планеты благоприятнее в определенное время
    """
    hour = time.hour
    
    favorable_hours = {
        'Sun': [6, 7, 8, 9, 10, 11, 12, 13],  # Утро и полдень
        'Moon': [18, 19, 20, 21, 22],         # Вечер
        'Mars': [6, 7, 8, 14, 15, 16],        # Утро и послеполуденное время
        'Mercury': [9, 10, 11, 15, 16, 17],   # Середина утра и после обеда
        'Jupiter': [6, 7, 8, 9, 10, 11],      # Утренние часы
        'Venus': [16, 17, 18, 19, 20],        # Вечерние часы  
        'Saturn': [14, 15, 16, 17]            # Послеполуденное время
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
        
        # Рассчитываем все временные периоды
        rahu_start, rahu_end = calculate_rahu_kaal(sunrise, sunset, weekday)
        gulika_start, gulika_end = calculate_gulika_kaal(sunrise, sunset, weekday)
        yama_start, yama_end = calculate_yamaghanta(sunrise, sunset, weekday)
        abhijit_start, abhijit_end = calculate_abhijit_muhurta(sunrise, sunset)
        
        # Планетарные часы
        planetary_hours = calculate_planetary_hours(sunrise, sunset, weekday)
        
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
                "ruling_planet": get_planet_sanskrit(['Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Sun'][weekday])
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
    day_planets = ['Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Sun']
    ruling_planet = day_planets[weekday]
    
    # Общие рекомендации по дню недели
    day_recommendations = {
        'Sun': {
            'activities': ['Лидерство', 'Принятие важных решений', 'Публичные выступления', 'Работа с властью'],
            'avoid': ['Споры с начальством', 'Эгоистичные поступки'],
            'colors': ['Золотой', 'Оранжевый', 'Красный'],
            'gems': ['Рубин', 'Гранат']
        },
        'Moon': {
            'activities': ['Семейные дела', 'Забота о близких', 'Интуитивные решения', 'Творчество'],
            'avoid': ['Конфликты в семье', 'Важные финансовые решения'],
            'colors': ['Белый', 'Серебристый', 'Молочный'],
            'gems': ['Жемчуг', 'Лунный камень']
        },
        'Mars': {
            'activities': ['Спорт', 'Активные действия', 'Решение проблем', 'Защита интересов'],
            'avoid': ['Агрессивное поведение', 'Конфликты'],
            'colors': ['Красный', 'Алый'],
            'gems': ['Коралл', 'Красная яшма']
        },
        'Mercury': {
            'activities': ['Обучение', 'Коммуникации', 'Торговля', 'Путешествия'],
            'avoid': ['Обман', 'Поверхностные суждения'],
            'colors': ['Зеленый', 'Изумрудный'],
            'gems': ['Изумруд', 'Зеленый турмалин']
        },
        'Jupiter': {
            'activities': ['Духовная практика', 'Образование', 'Благотворительность', 'Мудрые советы'],
            'avoid': ['Материализм', 'Невежество'],
            'colors': ['Желтый', 'Золотистый'],
            'gems': ['Желтый сапфир', 'Топаз']
        },
        'Venus': {
            'activities': ['Искусство', 'Красота', 'Романтика', 'Финансы'],
            'avoid': ['Излишества', 'Поверхностность'],
            'colors': ['Розовый', 'Белый', 'Пастельные тона'],
            'gems': ['Алмаз', 'Белый сапфир']
        },
        'Saturn': {
            'activities': ['Планирование', 'Дисциплина', 'Упорный труд', 'Структурирование'],
            'avoid': ['Лень', 'Откладывание дел'],
            'colors': ['Синий', 'Черный', 'Фиолетовый'],
            'gems': ['Синий сапфир', 'Аметист']
        }
    }
    
    # Лучшие часы для активности
    favorable_hours = [hour for hour in planetary_hours if hour['is_favorable']]
    
    recommendations = day_recommendations.get(ruling_planet, {})
    recommendations.update({
        'ruling_planet': get_planet_sanskrit(ruling_planet),
        'best_hours': [f"{h['start_time'].strftime('%H:%M')}-{h['end_time'].strftime('%H:%M')} ({h['planet_sanskrit']})" 
                      for h in favorable_hours[:3]],  # Топ-3 часа
        'planet_mantra': get_planet_mantra(ruling_planet)
    })
    
    return recommendations


def get_planet_mantra(planet: str) -> str:
    """Возвращает мантру планеты"""
    mantras = {
        'Sun': 'ॐ सूर्याय नमः (Om Suryaya Namaha)',
        'Moon': 'ॐ चन्द्राय नमः (Om Chandraya Namaha)',
        'Mars': 'ॐ मंगलाय नमः (Om Mangalaya Namaha)', 
        'Mercury': 'ॐ बुधाय नमः (Om Budhaya Namaha)',
        'Jupiter': 'ॐ गुरवे नमः (Om Gurave Namaha)',
        'Venus': 'ॐ शुक्राय नमः (Om Shukraya Namaha)',
        'Saturn': 'ॐ शनैश्चराय नमः (Om Shanaishcharaya Namaha)'
    }
    return mantras.get(planet, 'ॐ (Om)')


def get_monthly_planetary_route(city: str, start_date: datetime, birth_date: str = None) -> Dict[str, Any]:
    """
    Генерирует планетарный маршрут на месяц
    """
    monthly_schedule = []
    current_date = start_date
    
    for day in range(30):  # 30 дней месяца
        try:
            daily_schedule = get_vedic_day_schedule(city=city, date=current_date)
            
            if 'error' not in daily_schedule:
                day_info = {
                    'date': current_date.strftime('%Y-%m-%d'),
                    'weekday': current_date.strftime('%A'),
                    'weekday_ru': ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'][current_date.weekday()],
                    'ruling_planet': daily_schedule.get('weekday', {}).get('ruling_planet', ''),
                    'rahu_kaal': daily_schedule.get('inauspicious_periods', {}).get('rahu_kaal', {}),
                    'abhijit_muhurta': daily_schedule.get('auspicious_periods', {}).get('abhijit_muhurta', {}),
                    'recommendations': daily_schedule.get('recommendations', {}),
                    'favorable_activities': daily_schedule.get('recommendations', {}).get('activities', []),
                    'avoid_activities': daily_schedule.get('recommendations', {}).get('avoid', [])
                }
                monthly_schedule.append(day_info)
        except:
            pass
        
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


def get_quarterly_planetary_route(city: str, start_date: datetime, birth_date: str = None) -> Dict[str, Any]:
    """
    Генерирует планетарный маршрут на квартал (90 дней)
    """
    quarterly_schedule = []
    current_date = start_date
    
    # Группируем по неделям для квартального обзора
    weeks = []
    week_data = []
    
    for day in range(90):  # 90 дней квартала
        try:
            daily_schedule = get_vedic_day_schedule(city=city, date=current_date)
            
            if 'error' not in daily_schedule:
                day_info = {
                    'date': current_date.strftime('%Y-%m-%d'),
                    'weekday': current_date.weekday(),
                    'ruling_planet': daily_schedule.get('weekday', {}).get('ruling_planet', ''),
                    'rahu_kaal': daily_schedule.get('inauspicious_periods', {}).get('rahu_kaal', {}),
                    'favorable_rating': len(daily_schedule.get('recommendations', {}).get('activities', [])),
                }
                week_data.append(day_info)
                
                # Каждые 7 дней создаем неделю
                if len(week_data) == 7:
                    weeks.append({
                        'week_number': len(weeks) + 1,
                        'start_date': week_data[0]['date'],
                        'end_date': week_data[-1]['date'],
                        'days': week_data.copy(),
                        'best_days': [d for d in week_data if d['favorable_rating'] >= 3],
                        'challenging_days': [d for d in week_data if d['favorable_rating'] < 2]
                    })
                    week_data = []
        except:
            pass
        
        current_date += timedelta(days=1)
    
    # Добавляем оставшиеся дни недели если есть
    if week_data:
        weeks.append({
            'week_number': len(weeks) + 1,
            'start_date': week_data[0]['date'],
            'end_date': week_data[-1]['date'],
            'days': week_data.copy(),
            'best_days': [d for d in week_data if d['favorable_rating'] >= 3],
            'challenging_days': [d for d in week_data if d['favorable_rating'] < 2]
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