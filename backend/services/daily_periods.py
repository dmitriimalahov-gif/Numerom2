"""Morning periods from the app's formulas and the current profile city.

Use only the offline city index and actual solar events. The legacy schedule's
network geocoder and estimated 06:00/18:00 fallback must not enter emails.
"""
from dataclasses import dataclass
from datetime import date, timezone
from functools import lru_cache
import logging
import math

import pytz
from astral import Observer
from astral.sun import sunrise, sunset

from services.geography import city_index
from vedic_time_calculations import (
    calculate_abhijit_muhurta, calculate_gulika_kaal,
    calculate_rahu_kaal, calculate_yamaghanta,
)

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Period:
    title: str
    start: str
    end: str
    meaning: str


@dataclass(frozen=True)
class DailyPeriods:
    city: str = ''
    zone: str = ''
    sunrise: str = ''
    sunset: str = ''
    periods: tuple[Period, ...] = ()
    message: str = ''


LOCATION_REQUIRED = DailyPeriods(message=(
    'Выберите текущий город в профиле NumerOM, чтобы получать местное время периодов. '
    'Для этого расчёта нужен город, где вы сейчас находитесь, а не город рождения.'
))
UNAVAILABLE = DailyPeriods(message=(
    'Времена периодов сегодня недоступны. Расчёт требует восхода и заката для вашего города; '
    'при полярном дне или ночи эти интервалы не определяются.'
))


@lru_cache(maxsize=1024)
def _at_location(today: date, latitude: float, longitude: float, zone_name: str):
    zone = pytz.timezone(zone_name)
    observer = Observer(latitude, longitude)
    # Separate events also work when there is no astronomical dawn/dusk.
    rise = sunrise(observer, date=today, tzinfo=zone)
    setting = sunset(observer, date=today, tzinfo=zone)
    if rise.date() != today or setting.date() != today or setting <= rise:
        raise ValueError('No usable daylight interval')
    # Divide elapsed time, then format in the city zone, including DST changes.
    start, end = rise.astimezone(timezone.utc), setting.astimezone(timezone.utc)
    weekday = today.weekday()
    intervals = (
        ('Раху-кала', calculate_rahu_kaal(start, end, weekday),
         'Пауза перед новым начинанием: перепроверьте детали и завершите текущие дела.'),
        ('Ямаганта', calculate_yamaghanta(start, end, weekday),
         'Время для спокойной рутины: снизьте спешку и обдумайте следующий шаг.'),
        ('Гулика-кала', calculate_gulika_kaal(start, end, weekday),
         'Время повторения: вернитесь к знакомой задаче и закрепите полезный навык.'),
        ('Абхиджит-мухурта', calculate_abhijit_muhurta(start, end),
         'Полуденное окно для сосредоточенного действия: выделите одну главную задачу.'),
    )
    periods = tuple(Period(title, left.astimezone(zone).strftime('%H:%M'),
                           right.astimezone(zone).strftime('%H:%M'), meaning)
                    for title, (left, right), meaning in intervals)
    return rise.strftime('%H:%M'), setting.strftime('%H:%M'), periods


def daily_periods(city, today: date) -> DailyPeriods:
    """A missing, ambiguous or unavailable location never acquires guessed times."""
    if not isinstance(city, str) or not city.strip():
        return LOCATION_REQUIRED
    try:
        location = city_index.resolve_unique(city)
        if not location:
            return LOCATION_REQUIRED
        lat, lon = float(location['latitude']), float(location['longitude'])
        if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError('Invalid city coordinates')
        zone = pytz.timezone(location['timezone']).zone
        rise, setting, periods = _at_location(today, lat, lon, zone)
        return DailyPeriods(city=city.strip(), zone=zone, sunrise=rise, sunset=setting, periods=periods)
    except Exception:
        # No personal data in logs; still deliver the rest of the morning letter.
        log.warning('Morning solar periods unavailable')
        return UNAVAILABLE
