"""Solar intervals retain the city's clock and real elapsed time across DST."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vedic_time_calculations import calculate_planetary_hours, calculate_night_planetary_hours, get_vedic_day_schedule
from domain.vedic_report import normalize_day


class SolarTimezoneTests(unittest.TestCase):
    def assert_intervals(self, hours, start, end):
        self.assertEqual(len(hours), 12)
        boundaries = [(datetime.fromisoformat(item['start_time']), datetime.fromisoformat(item['end_time'])) for item in hours]
        self.assertTrue(all(a.utcoffset() is not None and b.utcoffset() is not None for a, b in boundaries))
        self.assertEqual(boundaries[0][0], start.replace(microsecond=0))
        self.assertEqual(boundaries[-1][1], end.replace(microsecond=0))
        self.assertEqual(boundaries[-1][1].strftime('%Y-%m-%d %H:%M:%S'), end.strftime('%Y-%m-%d %H:%M:%S'))
        duration = (end.astimezone(timezone.utc) - start.astimezone(timezone.utc)).total_seconds()/12
        for index, (a, b) in enumerate(boundaries):
            self.assertLessEqual(abs((b-a).total_seconds()-duration), 1)
            self.assertGreater(b, a)
            if index:
                self.assertEqual(a, boundaries[index-1][1])
        return boundaries

    def test_pytz_nights_end_at_actual_local_sunrise_after_both_dst_changes(self):
        tz = pytz.timezone('Europe/Chisinau')
        for start, end in [('2026-03-28T18:27:49','2026-03-29T06:50:16'), ('2026-10-24T18:01:16','2026-10-25T06:36:54')]:
            with self.subTest(start=start):
                sunset, sunrise = (tz.localize(datetime.fromisoformat(value)) for value in (start,end))
                hours=calculate_night_planetary_hours(sunset,sunrise,5)
                boundaries=self.assert_intervals(hours,sunset,sunrise)
                self.assertEqual([row['hour'] for row in hours],list(range(13,25)))
                self.assertEqual(set(row['period'] for row in hours),{'night'})
                self.assertEqual(len({value.utcoffset() for pair in boundaries for value in pair}),2)

    def test_zoneinfo_shared_timezone_does_not_turn_elapsed_night_into_wall_clock_duration(self):
        tz=ZoneInfo('Europe/Chisinau')
        start=datetime(2026,10,24,18,1,16,tzinfo=tz)
        end=datetime(2026,10,25,6,36,54,tzinfo=tz)
        self.assert_intervals(calculate_night_planetary_hours(start,end,5),start,end)

    def test_day_and_night_join_without_gaps_and_preserve_half_hour_zone(self):
        tz=pytz.timezone('Asia/Kolkata')
        sunrise=tz.localize(datetime(2026,10,18,6,2,11,123000))
        sunset=tz.localize(datetime(2026,10,18,17,50,49,456000))
        following=tz.localize(datetime(2026,10,19,6,2,35,789000))
        day=calculate_planetary_hours(sunrise,sunset,6)
        night=calculate_night_planetary_hours(sunset,following,6)
        self.assert_intervals(day,sunrise,sunset)
        self.assert_intervals(night,sunset,following)
        self.assertEqual(day[-1]['end_time'],night[0]['start_time'])
        self.assertTrue(all(row['start_time'].endswith('+05:30') for row in day+night))

    def test_naive_helper_call_remains_supported_without_fabricating_timezone(self):
        start,end=datetime(2026,10,18,6),datetime(2026,10,18,18)
        hours=calculate_planetary_hours(start,end,6)
        self.assertEqual(hours[0]['start_time'],'2026-10-18T06:00:00')
        self.assertEqual(hours[-1]['end_time'],'2026-10-18T18:00:00')

    def test_fresh_schedule_and_normalized_report_include_next_sunrise_anchor(self):
        tz=pytz.timezone('Europe/Chisinau')
        start=tz.localize(datetime(2026,10,24,7,35,0))
        sunset=tz.localize(datetime(2026,10,24,18,1,16))
        following=tz.localize(datetime(2026,10,25,6,36,54))
        with patch('vedic_time_calculations.get_city_timezone',return_value='Europe/Chisinau'), patch('vedic_time_calculations.get_sunrise_sunset',side_effect=[(start,sunset),(following,following+timedelta(hours=10))]):
            schedule=get_vedic_day_schedule('Синтетический город',datetime(2026,10,24))
        self.assertNotIn('error',schedule)
        self.assertEqual(schedule['sun_times']['next_sunrise'],following.isoformat())
        day=normalize_day({},datetime(2026,10,24),schedule,include_hours=True,require_energy=False)
        self.assertEqual(day['next_sunrise'],following.isoformat())
        self.assertEqual(day['hours'][-1]['end'],following.isoformat())
        self.assertEqual(day['sunrise'],'07:35')
        self.assertEqual(day['sunset'],'18:01')


if __name__ == '__main__':
    unittest.main()
