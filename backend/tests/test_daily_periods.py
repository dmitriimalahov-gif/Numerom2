"""Morning periods use the current city, local calendar date and project formulas."""
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import pytz
from astral import Observer
from astral.sun import sunrise, sunset

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from domain.vedic_location import location_scope
from services.daily_periods import daily_periods, _at_location
from vedic_time_calculations import get_vedic_day_schedule

CHISINAU = {'latitude': 47.0105, 'longitude': 28.8638, 'timezone': 'Europe/Chisinau'}
TOKYO = {'latitude': 35.6762, 'longitude': 139.6503, 'timezone': 'Asia/Tokyo'}


class DailyPeriodsTests(unittest.TestCase):
    def setUp(self):
        _at_location.cache_clear()

    def test_all_seven_weekdays_match_the_app_schedule_without_network_geocoding(self):
        with patch('services.daily_periods.city_index.resolve_unique', return_value=CHISINAU), \
                patch('vedic_time_calculations.Nominatim', side_effect=AssertionError('No network geocoding')):
            for offset in range(7):
                day = date(2026, 10, 26) + timedelta(days=offset)
                with self.subTest(day=day):
                    result = daily_periods('Кишинэу, Молдова', day)
                    with location_scope('Кишинэу, Молдова', **CHISINAU):
                        schedule = get_vedic_day_schedule('Кишинэу, Молдова', datetime.combine(day, datetime.min.time()))
                    expected = {**schedule['inauspicious_periods'], **schedule['auspicious_periods']}
                    self.assertEqual(result.sunrise, schedule['sun_times']['sunrise'])
                    self.assertEqual(result.sunset, schedule['sun_times']['sunset'])
                    self.assertEqual(len(result.periods), 4)
                    for p, key in zip(result.periods, ['rahu_kaal', 'yamaghanta', 'gulika_kaal', 'abhijit_muhurta']):
                        self.assertEqual((p.start, p.end), (expected[key]['start'], expected[key]['end']))

    def test_timezone_and_dst_are_derived_from_the_city_and_target_date(self):
        for location, day in [(CHISINAU, date(2026, 3, 29)), (CHISINAU, date(2026, 10, 25)),
                              (TOKYO, date(2026, 10, 29))]:
            with self.subTest(location=location, day=day), \
                    patch('services.daily_periods.city_index.resolve_unique', return_value=location):
                result = daily_periods('Выбранный город', day)
                zone = pytz.timezone(location['timezone'])
                observer = Observer(location['latitude'], location['longitude'])
                rise = sunrise(observer, date=day, tzinfo=zone)
                setting = sunset(observer, date=day, tzinfo=zone)
                middle = rise.astimezone(timezone.utc) + (setting - rise) / 2
                self.assertEqual(result.zone, location['timezone'])
                self.assertEqual(result.sunrise, rise.strftime('%H:%M'))
                self.assertEqual(result.periods[-1].start, (middle - timedelta(minutes=24)).astimezone(zone).strftime('%H:%M'))

    def test_city_changes_the_intervals(self):
        with patch('services.daily_periods.city_index.resolve_unique', side_effect=[CHISINAU, TOKYO]):
            one = daily_periods('Кишинэу', date(2026, 10, 28))
            two = daily_periods('Токио', date(2026, 10, 28))
        self.assertNotEqual(one.periods, two.periods)
        self.assertNotEqual(one.sunrise, two.sunrise)

    def test_unknown_or_ambiguous_city_prompts_for_location_without_solar_calculation(self):
        with patch('services.daily_periods.city_index.resolve_unique', return_value=None), \
                patch('services.daily_periods.sunrise', side_effect=AssertionError('No guessed coordinates')):
            for city in (None, '', 'Неизвестный город', 'Springfield'):
                result = daily_periods(city, date(2026, 10, 28))
                self.assertFalse(result.periods)
                self.assertIn('текущий город', result.message)
                self.assertEqual(result.sunrise, '')

    def test_polar_day_and_night_do_not_fall_back_to_six_and_eighteen(self):
        location = {'latitude': 78.2232, 'longitude': 15.6267, 'timezone': 'Arctic/Longyearbyen'}
        with patch('services.daily_periods.city_index.resolve_unique', return_value=location):
            for day in (date(2026, 6, 21), date(2026, 12, 21)):
                result = daily_periods('Longyearbyen', day)
                self.assertFalse(result.periods)
                self.assertEqual((result.sunrise, result.sunset), ('', ''))
                self.assertIn('полярном', result.message)

    def test_invalid_city_data_or_unavailable_index_does_not_break_the_letter(self):
        for changes in ({'latitude': float('nan')}, {'longitude': 999}, {'timezone': 'Invalid/Zone'}):
            with patch('services.daily_periods.city_index.resolve_unique', return_value={**CHISINAU, **changes}):
                self.assertFalse(daily_periods('Кишинэу', date(2026, 10, 28)).periods)
        with patch('services.daily_periods.city_index.resolve_unique', side_effect=OSError('index unavailable')):
            self.assertFalse(daily_periods('Кишинэу', date(2026, 10, 28)).periods)


if __name__ == '__main__':
    unittest.main()
