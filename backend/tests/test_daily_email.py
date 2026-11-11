"""Morning letters: the personal day, the 8:00 window in the profile's city, one letter a day, the off switch."""
import os
import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from public_gateway import _route, _valid_body
import email
from services.daily_email import DailyEmail, DailyEmailChoice, choice_token, morning_letter, personal_day, PLANETS
from services.mail import SMTPMailer

CHISINAU = {'latitude': 47.0105, 'longitude': 28.8638, 'timezone': 'Europe/Chisinau'}


class Cursor:
    def __init__(self, rows):
        self.rows = rows

    async def to_list(self, length):
        return list(self.rows)


class Users:
    def __init__(self, rows):
        self.rows = rows

    def find(self, query, projection=None):
        return Cursor([row for row in self.rows if row.get('daily_email') is not False and not row.get('is_disabled')])

    async def find_one_and_update(self, query, update, projection=None):
        for row in self.rows:
            if row['id'] == query['id']:
                row.update(update['$set'])
                return row
        return None


class Letters:
    def __init__(self):
        self.rows = {}

    async def insert_one(self, row):
        if row['_id'] in self.rows:
            raise DuplicateKeyError('duplicate')
        self.rows[row['_id']] = dict(row)

    async def delete_one(self, query):
        self.rows.pop(query['_id'], None)

    async def update_one(self, query, update):
        self.rows[query['_id']].update(update['$set'])


class Db:
    def __init__(self, users):
        self.users, self.daily_emails = Users(users), Letters()


class Mailer:
    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    async def send_letter(self, email, subject, body, unsubscribe, html=None, images=None):
        if self.fail:
            raise RuntimeError('smtp down')
        self.sent.append((email, subject, body, unsubscribe, html, images))


def user(**changes):
    return {'id': 'u1', 'email': 'anna@gmail.com', 'birth_date': '10.01.1982', 'name': 'Анна', 'city': 'Кишинэу, Молдова', **changes}


class LetterTests(unittest.TestCase):
    def setUp(self):
        location = patch('services.daily_periods.city_index.resolve_unique', return_value=CHISINAU)
        location.start(); self.addCleanup(location.stop)

    def test_personal_day_follows_the_full_report_formula(self):
        # 10 + 1 + 2026 = 2037 → 3; 3 + 10 = 13 → 4; 4 + 26 = 30 → 3
        self.assertEqual(personal_day('10.01.1982', date(2026, 10, 26))[:3], (3, 4, 3))

    def test_letter_names_the_day_and_its_planet_explains_the_count_and_can_be_turned_off(self):
        subject, body, page, images = morning_letter(user(), date(2026, 10, 26), 'https://app.test/daily-email/?token=t', 'https://app.test/')
        self.assertEqual(subject, 'Ваш личный день 26.10: 3 · Гуру')
        self.assertIn('Доброе утро, Анна!', body)
        self.assertIn('Сегодня, 26 октября, ваш личный день — 3. Планета дня — Гуру (Юпитер).', body)
        self.assertIn('творчеством, общением и передачей знаний', body)
        self.assertIn('личный день 4 + 26 → 3', body)
        self.assertIn('Отключить утренние письма: https://app.test/daily-email/?token=t', body)
        self.assertIn('Доброе утро!', morning_letter(user(name=''), date(2026, 10, 26), 'x')[1])

    def test_styled_letter_shows_the_day_large_with_the_planet_badge(self):
        subject, body, page, images = morning_letter(user(name='<Анна>'), date(2026, 10, 25), 'https://app.test/daily-email/?token=t&x=1', 'https://app.test/')
        self.assertIn('font:700 80px', page)
        self.assertIn('>2</td>', page)
        self.assertIn('Чандра', page)
        self.assertIn('Луна · планета вашего дня', page)
        self.assertIn('src="cid:planet-chandra@numerom"', page)
        self.assertIn('&lt;Анна&gt;', page, 'names stay text')
        self.assertIn('href="https://app.test/daily-email/?token=t&amp;x=1"', page)
        self.assertEqual(sorted(images), ['numerom-logo@numerom', 'planet-chandra@numerom'])
        self.assertTrue(all(path.is_file() for path in images.values()))
        for key, _, _ in PLANETS.values():
            self.assertTrue((images['numerom-logo@numerom'].parent / 'planets' / f'{key}.png').is_file(), key)

    def test_the_mail_carries_text_html_and_pictures_inside(self):
        _, body, page, images = morning_letter(user(), date(2026, 10, 25), 'https://app.test/off', 'https://app.test/')
        sent = []
        class Smtp:
            def __init__(self, *args, **kwargs): pass
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def ehlo(self): pass
            def starttls(self, context=None): pass
            def login(self, *args): pass
            def send_message(self, message): sent.append(message)
        with patch.dict(os.environ, {'SMTP_HOST': 'smtp.test', 'SMTP_FROM': 'hello@numerom.test', 'SMTP_PORT': '587'}), \
                patch('services.mail.smtplib.SMTP', Smtp):
            SMTPMailer()._send('anna@gmail.com', 'Тема', body, {'List-Unsubscribe': '<https://app.test/off>'}, page, images)
        message = email.message_from_bytes(sent[0].as_bytes())
        self.assertEqual(message['List-Unsubscribe'], '<https://app.test/off>')
        kinds = [part.get_content_type() for part in message.walk()]
        self.assertEqual(kinds, ['multipart/alternative', 'text/plain', 'multipart/related', 'text/html', 'image/png', 'image/png'])
        self.assertEqual(sorted(part['Content-ID'] for part in message.walk() if part.get_content_type() == 'image/png'),
                         ['<numerom-logo@numerom>', '<planet-chandra@numerom>'])

    def test_periods_and_sun_times_are_in_both_versions_and_city_is_escaped(self):
        _, text, page, _ = morning_letter(user(city='<Город>'), date(2026, 10, 28), 'https://app.test/off')
        for title in ('Раху-кала', 'Ямаганта', 'Гулика-кала', 'Абхиджит-мухурта', 'Восход', 'Закат', 'Europe/Chisinau', '28.10.2026'):
            self.assertIn(title, text)
            self.assertIn(title, page)
        self.assertIn('&lt;Город&gt;', page)
        self.assertNotIn('<Город>', page)
        from services.daily_periods import daily_periods
        for period in daily_periods('<Город>', date(2026, 10, 28)).periods:
            self.assertIn(f'{period.start}–{period.end}', text)
            self.assertIn(f'{period.start}–{period.end}', page)

    def test_without_current_city_letter_keeps_personal_day_and_links_to_profile(self):
        _, text, page, _ = morning_letter(user(city='', birth_city='Кишинэу'), date(2026, 10, 28),
                                           'https://app.test/off', 'https://app.test/numerom-app/')
        for value in (text, page):
            self.assertIn('текущий город', value)
            self.assertIn('https://app.test/numerom-app/profile/', value)
            self.assertNotIn('Восход', value)
        self.assertIn('ваш личный день — 5', text)


class ServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        secret = patch.dict(os.environ, {'SECRET_KEY': 'synthetic-daily-email-test-key-' * 3, 'PUBLIC_APP_URL': 'https://app.numerom.test'})
        secret.start(); self.addCleanup(secret.stop)
        location = patch('services.daily_periods.city_index.resolve_unique', return_value=CHISINAU)
        location.start(); self.addCleanup(location.stop)

    def service(self, users, at, mailer=None, zones=None):
        zones = zones or {}
        return DailyEmail(Db(users), mailer or Mailer(), clock=lambda: at, zone=lambda city: zones.get(city, 'Europe/Chisinau'))

    async def test_letters_go_out_at_eight_in_the_profile_city_once_a_day(self):
        users = [user(), user(id='u2', email='li@gmail.com', city='Токио, Япония'), user(id='u3', email='qa@numerom.test'),
                 user(id='u4', email='off@gmail.com', daily_email=False), user(id='u5', email='bad@gmail.com', birth_date='31.02.1990')]
        # 06:10 UTC: 08:10 in Chisinau (UTC+2 after 25.10), 15:10 in Tokyo.
        service = self.service(users, datetime(2026, 10, 26, 6, 10, tzinfo=timezone.utc), zones={'Токио, Япония': 'Asia/Tokyo'})
        self.assertEqual(await service.tick(), 1)
        self.assertEqual([letter[0] for letter in service.mailer.sent], ['anna@gmail.com'])
        self.assertEqual(await service.tick(), 0, 'one letter per user and day')
        self.assertIn('u1:2026-10-26', service.db.daily_emails.rows)

    async def test_nothing_is_sent_before_eight_or_after_noon(self):
        for hour in (5, 10):  # 07:00 and 12:00 in Chisinau
            service = self.service([user()], datetime(2026, 10, 26, hour, 0, tzinfo=timezone.utc))
            self.assertEqual(await service.tick(), 0)

    async def test_a_failed_send_is_retried_by_the_next_pass(self):
        at = datetime(2026, 10, 26, 6, 0, tzinfo=timezone.utc)
        broken = self.service([user()], at, Mailer(fail=True))
        self.assertEqual(await broken.tick(), 0)
        self.assertEqual(broken.db.daily_emails.rows, {}, 'the claim is released')
        broken.mailer.fail = False
        self.assertEqual(await broken.tick(), 1)

    async def test_a_letter_preparation_error_releases_the_claim_for_retry(self):
        service = self.service([user()], datetime(2026, 10, 28, 6, 0, tzinfo=timezone.utc))
        with patch('services.daily_email.morning_letter', side_effect=RuntimeError('preparation failed')):
            self.assertEqual(await service.tick(), 0)
        self.assertEqual(service.db.daily_emails.rows, {})
        self.assertEqual(await service.tick(), 1)

    async def test_far_east_morning_uses_next_local_calendar_date_for_solar_periods(self):
        tokyo = {'latitude': 35.6762, 'longitude': 139.6503, 'timezone': 'Asia/Tokyo'}
        # 23:10 UTC on the 28th is 08:10 on the 29th in Tokyo.
        service = self.service([user(city='Токио')], datetime(2026, 10, 28, 23, 10, tzinfo=timezone.utc),
                               zones={'Токио': 'Asia/Tokyo'})
        with patch('services.daily_periods.city_index.resolve_unique', return_value=tokyo):
            self.assertEqual(await service.tick(), 1)
        self.assertIn('u1:2026-10-29', service.db.daily_emails.rows)
        self.assertIn('Периоды дня · 29.10.2026', service.mailer.sent[0][2])
        self.assertIn('Asia/Tokyo', service.mailer.sent[0][2])

    async def test_unavailable_solar_calculation_still_delivers_the_personal_day(self):
        service = self.service([user()], datetime(2026, 10, 28, 6, 0, tzinfo=timezone.utc))
        with patch('services.daily_periods.city_index.resolve_unique', side_effect=OSError('no cities')):
            self.assertEqual(await service.tick(), 1)
        self.assertIn('Времена периодов сегодня недоступны', service.mailer.sent[0][2])
        self.assertIn('ваш личный день — 5', service.mailer.sent[0][2])

    async def test_the_link_turns_letters_off_and_on_without_signing_in(self):
        users = [user()]
        service = self.service(users, datetime(2026, 10, 26, 6, 0, tzinfo=timezone.utc))
        result = await service.choose(DailyEmailChoice(token=choice_token('u1'), subscribed=False))
        self.assertEqual(result, {'subscribed': False, 'email': 'a•••@gmail.com'})
        self.assertEqual(await service.tick(), 0)
        await service.choose(DailyEmailChoice(token=choice_token('u1'), subscribed=True))
        self.assertEqual(await service.tick(), 1)
        letter = service.mailer.sent[0]
        self.assertTrue(letter[3].startswith('https://app.numerom.test/daily-email/?token='))
        with self.assertRaises(HTTPException) as caught:
            await service.choose(DailyEmailChoice(token=choice_token('u1')[:-3] + 'abc', subscribed=False))
        self.assertEqual(caught.exception.status_code, 400)

    def test_gateway_passes_only_the_choice(self):
        self.assertEqual(_route('POST', '/api/public/daily-email'), 'public')
        self.assertIsNone(_route('GET', '/api/public/daily-email'))
        self.assertTrue(_valid_body('/api/public/daily-email', {'token': 'x' * 30, 'subscribed': False}))
        for body in [{'token': 'x' * 30}, {'token': 'x' * 30, 'subscribed': False, 'email': 'a@b.c'}, {'token': 'short', 'subscribed': True}]:
            self.assertFalse(_valid_body('/api/public/daily-email', body))


if __name__ == '__main__':
    unittest.main()
