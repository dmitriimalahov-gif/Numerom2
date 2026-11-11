"""The morning letter: at 8:00 in the city of the profile every registered user gets the number of their
personal day with a short word for it and local solar periods.

Runs as md.numerom.app.daily-email (scripts/send-daily-emails.py). Each pass looks for users whose local time is
between 8:00 and noon — a Mac asleep at 8:00 still sends that morning, never in the afternoon — and sends at most
one letter per user and local date. Every letter carries a link that turns the letters off.
"""
import asyncio
import html
import logging
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import pytz
from fastapi import HTTPException
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict, Field
from pymongo.errors import DuplicateKeyError

from auth import signing_key
from domain.personal_report import NUMBER_THEMES
from numerology import reduce_to_single_digit_always
from services.daily_periods import daily_periods
from services.mail import SMTPMailer
from services.report_delivery import app_url

log = logging.getLogger(__name__)
INTERVAL = 300
SEND_HOUR, LAST_HOUR = 8, 12
DEFAULT_ZONE = 'Europe/Chisinau'
AUDIENCE = 'numerom-daily-email'
MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
# Addresses that can never receive mail: test accounts and documentation domains.
NO_MAIL = re.compile(r'@(?:[^@]+\.)?(?:test|invalid|localhost|example)$|@example\.(?:com|org|net)$', re.IGNORECASE)


class DailyEmailChoice(BaseModel):
    model_config = ConfigDict(extra='forbid')
    token: str = Field(min_length=20, max_length=2048)
    subscribed: bool


def choice_token(user_id):
    """Turns the letters off or back on for one account; it opens nothing else, so it does not expire."""
    return jwt.encode({'sub': user_id, 'aud': AUDIENCE}, signing_key(), algorithm='HS256')


def personal_day(birth_date, today):
    """Personal year, month and day as in the full report: date of birth + the current year, month, day."""
    day, month, _ = (int(part) for part in birth_date.split('.'))
    year_number = reduce_to_single_digit_always(day + month + today.year)
    month_number = reduce_to_single_digit_always(year_number + today.month)
    day_number = reduce_to_single_digit_always(month_number + today.day)
    formulas = [f'{day} + {month} + {today.year} → {year_number}', f'{year_number} + {today.month} → {month_number}',
                f'{month_number} + {today.day} → {day_number}']
    steps = f'личный год {formulas[0]}; личный месяц {formulas[1]}; личный день {formulas[2]}'
    return year_number, month_number, day_number, steps, formulas


# The app's palette (mobile/src/lib/theme.ts) and system font; mail apps need every style inline.
INK, NAVY, MUTED, LINE, PALE, ACCENT, GREEN = '#20364E', '#183B62', '#61758B', '#DDE5EE', '#EAF1F9', '#356FA5', '#28705E'
FONT = "-apple-system,BlinkMacSystemFont,'Helvetica Neue',Helvetica,Arial,sans-serif"
LOGO_CID = 'numerom-logo@numerom'
ASSETS = Path(__file__).resolve().parents[1] / 'assets/email'
LOGO = ASSETS / 'numerom-logo.png'
# The planet of each number, as in the vedic section of the app (domain/vedic_report.py PLANETS);
# badges come from scripts/render-email-images.py.
PLANETS = {1: ('surya', 'Сурья', 'Солнце'), 2: ('chandra', 'Чандра', 'Луна'), 3: ('guru', 'Гуру', 'Юпитер'),
           4: ('rahu', 'Раху', 'северный лунный узел'), 5: ('budha', 'Будха', 'Меркурий'), 6: ('shukra', 'Шукра', 'Венера'),
           7: ('ketu', 'Кету', 'южный лунный узел'), 8: ('shani', 'Шани', 'Сатурн'), 9: ('mangal', 'Мангал', 'Марс')}


def periods_text(schedule, today, app):
    heading = f'Периоды дня · {today:%d.%m.%Y}'
    if not schedule.periods:
        return heading + '\n' + schedule.message + (f'\nПрофиль: {app.rstrip("/")}/profile/' if app else '')
    rows = '\n'.join(f'{p.title}: {p.start}–{p.end}. {p.meaning}' for p in schedule.periods)
    return (f'{heading}\n{schedule.city} · {schedule.zone}. Всё время местное.\n'
            f'Восход {schedule.sunrise} · Закат {schedule.sunset}\n\n{rows}\n'
            'Интервалы рассчитаны от восхода и заката по формулам раздела «Время» NumerOM.')


def periods_html(schedule, today, app):
    e = lambda value: html.escape(str(value), quote=True)
    heading = (f'<h2 style="margin:26px 0 8px;font:700 20px/26px {FONT};color:{NAVY}">'
               f'Периоды дня · {today:%d.%m.%Y}</h2>')
    if not schedule.periods:
        profile = (f' <a href="{e(app.rstrip("/") + "/profile/")}" style="color:{ACCENT}">Открыть профиль</a>') if app else ''
        return heading + f'<p style="margin:0;font:400 14px/21px {FONT};color:{MUTED}">{e(schedule.message)}{profile}</p>'
    rows = ''.join(
        f'<tr><td style="padding:14px 16px;border-top:1px solid {LINE}">'
        f'<div style="font:600 15px/22px {FONT};color:{NAVY}">{e(p.title)}</div>'
        f'<div style="font:700 22px/30px {FONT};color:{ACCENT}">{e(p.start)}–{e(p.end)}</div>'
        f'<div style="margin-top:3px;font:400 14px/21px {FONT};color:{INK}">{e(p.meaning)}</div>'
        '</td></tr>' for p in schedule.periods)
    return (heading
            + f'<p style="margin:0 0 12px;font:400 13px/20px {FONT};color:{MUTED};overflow-wrap:anywhere">'
            f'{e(schedule.city)} · {e(schedule.zone)}<br>Всё время местное. Восход {e(schedule.sunrise)} · Закат {e(schedule.sunset)}</p>'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F4F7FB;border-radius:16px">{rows}</table>'
            f'<p style="margin:10px 0 0;font:400 12px/18px {FONT};color:{MUTED}">'
            'Интервалы рассчитаны от восхода и заката по формулам раздела «Время» NumerOM.</p>')


def letter_html(name, today, numbers, theme, focus, month_theme, choice_url, app, schedule):
    year_number, month_number, day_number, _, formulas = numbers
    key, planet, meaning = PLANETS[day_number]
    e = lambda value: html.escape(str(value), quote=True)
    tiles = ''.join(
        f'<td width="33%" style="padding:0 4px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="background:{bg};border-radius:14px"><tr><td align="center" style="padding:12px 6px">'
        f'<div style="font:600 12px/16px {FONT};color:{MUTED}">{label}</div>'
        f'<div style="font:700 26px/32px {FONT};color:{NAVY}">{value}</div>'
        f'<div style="font:400 11px/15px {FONT};color:{MUTED}">{e(formula)}</div></td></tr></table></td>'
        for label, value, formula, bg in [('Личный год', year_number, formulas[0], '#F4F7FB'),
                                          ('Личный месяц', month_number, formulas[1], '#F4F7FB'),
                                          ('Личный день', day_number, formulas[2], PALE)])
    button = (f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:26px 0 6px"><tr>'
              f'<td style="background:{NAVY};border-radius:14px"><a href="{e(app)}" style="display:inline-block;padding:15px 26px;'
              f'font:600 15px/20px {FONT};color:#FFFFFF;text-decoration:none">Открыть NumerOM</a></td></tr></table>') if app else ''
    return f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light"><title>Ваш личный день</title></head>
<body style="margin:0;padding:0;background:#F4F7FB">
<div style="display:none;max-height:0;overflow:hidden">Сегодня ваш личный день — {day_number}. {e(focus)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F4F7FB"><tr><td align="center" style="padding:28px 12px 32px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px">
<tr><td align="center" style="padding:0 0 18px"><img src="cid:{LOGO_CID}" width="128" height="102" alt="NumerOM — Numbers Reveal" style="display:block;border:0"></td></tr>
<tr><td style="background:#FFFFFF;border:1px solid {LINE};border-radius:23px;padding:28px 24px">
<div style="font:700 11px/16px {FONT};letter-spacing:1.7px;text-transform:uppercase;color:{ACCENT}">Ваш личный день · {today.day} {MONTHS[today.month - 1]}</div>
<h1 style="margin:10px 0 20px;font:700 28px/34px {FONT};letter-spacing:-0.6px;color:{NAVY}">Доброе утро{", " + e(name) if name else ""}!</h1>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PALE};border-radius:22px"><tr><td align="center" style="padding:22px 16px 20px">
<div style="font:700 11px/16px {FONT};letter-spacing:1.7px;text-transform:uppercase;color:{ACCENT}">Число вашего дня</div>
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:10px auto 6px"><tr>
<td valign="middle" style="padding-right:16px"><img src="cid:{planet_cid(key)}" width="64" height="64" alt="{planet}" style="display:block;border:0"></td>
<td valign="middle" style="font:700 80px/84px {FONT};letter-spacing:-2px;color:{NAVY}">{day_number}</td></tr></table>
<div style="font:700 24px/30px {FONT};color:{NAVY}">{planet}</div>
<div style="font:400 14px/20px {FONT};color:{MUTED}">{meaning} · планета вашего дня</div>
</td></tr></table>
<p style="margin:20px 0 0;font:600 18px/26px {FONT};color:{NAVY}">Этот день связан с {e(theme)}.</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:20px;background:#E8F4EE;border-radius:16px"><tr><td style="padding:16px 18px">
<div style="font:700 11px/16px {FONT};letter-spacing:1.4px;text-transform:uppercase;color:{GREEN}">Напутствие</div>
<div style="margin-top:6px;font:400 16px/24px {FONT};color:{INK}">{e(focus)}</div></td></tr></table>
<p style="margin:20px 0 0;font:400 15px/23px {FONT};color:{MUTED}"><b style="color:{NAVY}">Фон месяца.</b> Личный месяц {month_number} — время, связанное с {e(month_theme)}.</p>
<div style="margin:22px 0 8px;font:600 13px/18px {FONT};color:{NAVY}">Как посчитано</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 -4px"><tr>{tiles}</tr></table>
{periods_html(schedule, today, app)}
{button}
<p style="margin:18px 0 0;font:400 12px/18px {FONT};color:{MUTED}">Числа описывают символику дня и служат материалом для самонаблюдения, а не предсказанием.</p>
</td></tr>
<tr><td align="center" style="padding:20px 18px 0;font:400 12px/19px {FONT};color:{MUTED}">Хорошего дня! · NumerOM<br>
Вы получаете это письмо как зарегистрированный пользователь NumerOM.<br>
<a href="{e(choice_url)}" style="color:{ACCENT}">Отключить утренние письма</a></td></tr>
</table></td></tr></table></body></html>'''


def planet_cid(key):
    return f'planet-{key}@numerom'


def morning_letter(user, today, choice_url, app=''):
    """Subject, plain text, the app-styled HTML and its pictures (content id → file) of one morning letter."""
    numbers = personal_day(user['birth_date'], today)
    _, month_number, day_number, steps, _ = numbers
    theme, focus = NUMBER_THEMES[day_number]
    month_theme = NUMBER_THEMES[month_number][0]
    name = str(user.get('name') or '').strip()
    key, planet, meaning = PLANETS[day_number]
    schedule = daily_periods(user.get('city'), today)
    subject = f'Ваш личный день {today:%d.%m}: {day_number} · {planet}'
    body = (f'Доброе утро{", " + name if name else ""}!\n\n'
            f'Сегодня, {today.day} {MONTHS[today.month - 1]}, ваш личный день — {day_number}. Планета дня — {planet} ({meaning}).\n\n'
            f'Этот день связан с {theme}. {focus}\n\n'
            f'Фон месяца — личный месяц {month_number}: время, связанное с {month_theme}.\n\n'
            f'Как посчитано: {steps}.\n\n'
            f'{periods_text(schedule, today, app)}\n\n'
            'Числа описывают символику дня и служат материалом для самонаблюдения, а не предсказанием.\n\n'
            + (f'Открыть NumerOM: {app}\n\n' if app else '')
            + 'Хорошего дня!\nNumerOM\n\n'
            f'—\nВы получаете это письмо как зарегистрированный пользователь NumerOM. '
            f'Отключить утренние письма: {choice_url}\n')
    images = {LOGO_CID: LOGO, planet_cid(key): ASSETS / 'planets' / f'{key}.png'}
    return subject, body, letter_html(name, today, numbers, theme, focus, month_theme, choice_url, app, schedule), images


@lru_cache(maxsize=512)
def city_zone(city):
    """The time zone of the profile's city; Chisinau when the city is missing or ambiguous."""
    try:
        from services.geography import city_index
        zone = (city_index.resolve_unique(city) or {}).get('timezone') if city else None
        return pytz.timezone(zone).zone if zone else DEFAULT_ZONE
    except Exception:
        return DEFAULT_ZONE


def valid_birth_date(value):
    try:
        return bool(re.fullmatch(r'\d{2}\.\d{2}\.\d{4}', value or '')) and bool(datetime.strptime(value, '%d.%m.%Y'))
    except ValueError:
        return False


class DailyEmail:
    def __init__(self, db, mailer=None, clock=lambda: datetime.now(timezone.utc), zone=city_zone):
        self.db, self.mailer, self.clock, self.zone = db, mailer or SMTPMailer(), clock, zone

    async def choose(self, body: DailyEmailChoice):
        """The link from a letter: turns the letters off (or back on) without signing in."""
        try:
            claims = jwt.decode(body.token, signing_key(), algorithms=['HS256'], audience=AUDIENCE)
            user_id = claims['sub']
            if not isinstance(user_id, str):
                raise ValueError()
        except (JWTError, KeyError, ValueError):
            raise HTTPException(400, 'Ссылка из письма повреждена. Откройте её из последнего письма NumerOM.')
        found = await self.db.users.find_one_and_update({'id': user_id}, {'$set': {'daily_email': body.subscribed}},
                                                        projection={'email': 1})
        if not found:
            raise HTTPException(404, 'Аккаунт не найден.')
        email = found.get('email') or ''
        local, _, domain = email.partition('@')
        return {'subscribed': body.subscribed, 'email': (local[:1] + '•••@' + domain) if domain else ''}

    async def due(self):
        """Users whose morning it is and who have not had today's letter."""
        now = self.clock()
        rows = await self.db.users.find(
            {'email': {'$type': 'string'}, 'birth_date': {'$type': 'string'}, 'is_disabled': {'$ne': True}, 'daily_email': {'$ne': False}},
            {'_id': 0, 'id': 1, 'email': 1, 'birth_date': 1, 'name': 1, 'city': 1}).to_list(10000)
        for user in rows:
            if not user.get('id') or '@' not in user['email'] or NO_MAIL.search(user['email'].strip()) or not valid_birth_date(user['birth_date']):
                continue
            local = now.astimezone(pytz.timezone(self.zone(user.get('city') or '')))
            if SEND_HOUR <= local.hour < LAST_HOUR:
                yield user, local.date()

    async def send(self, user, today):
        """Claims the user's letter for the date first, so two passes never send it twice."""
        key = f'{user["id"]}:{today.isoformat()}'
        try:
            await self.db.daily_emails.insert_one({'_id': key, 'user_id': user['id'], 'date': today.isoformat(), 'claimed_at': self.clock()})
        except DuplicateKeyError:
            return 0
        app = app_url()
        if not app:
            # Without the app address the letter has no way to turn it off; it waits for the configuration.
            await self.db.daily_emails.delete_one({'_id': key})
            log.warning('Morning letters wait for the public app address')
            return 0
        try:
            choice = f'{app}/daily-email/?token={choice_token(user["id"])}'
            subject, body, page, images = await asyncio.to_thread(morning_letter, user, today, choice, app + '/')
            await self.mailer.send_letter(user['email'], subject, body, unsubscribe=choice, html=page, images=images)
        except Exception:
            # The next pass, five minutes on, tries again until noon.
            await self.db.daily_emails.delete_one({'_id': key})
            log.warning('Morning letter deferred')
            return 0
        await self.db.daily_emails.update_one({'_id': key}, {'$set': {'sent_at': self.clock()}})
        return 1

    async def tick(self):
        sent = 0
        async for user, today in self.due():
            sent += await self.send(user, today)
        if sent:
            log.info('Morning letters sent: %s', sent)
        return sent

    async def run(self):
        while True:
            try:
                await self.tick()
            except Exception:
                log.warning('Morning letter pass failed; retrying')
            await asyncio.sleep(INTERVAL)
