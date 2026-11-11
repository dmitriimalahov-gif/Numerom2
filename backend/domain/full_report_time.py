"""Daily time adapters: existing solar/route methods, explicit frozen location."""
from datetime import datetime, timedelta
import math

from fastapi import HTTPException

from domain.vedic_location import location_scope
from domain.vedic_report import user_context, profile_wisdom, wisdom_note, checked_schedule, normalize_day, PLANETS, KNOWLEDGE, TITLES
import vedic_time_calculations as legacy
from numerology import parse_birth_date
from vedic_numerology import calculate_bhagya_ank, calculate_enhanced_daily_planetary_energy


def clock(value):
    """«2026-10-24T07:35:28+03:00» → «07:35»: the report text and its voice read local clock time."""
    text = str(value or '')
    return text[11:16] if len(text) >= 16 and text[10] == 'T' else text


def monthly_route(birth_date, date, city, context, modifiers):
    """The app's «Маршрут на 30 дней» from the report date; the caller holds the frozen location scope."""
    route = legacy.get_monthly_planetary_route(city=city, start_date=date, birth_date=birth_date,
                                               **context, modifiers_config=modifiers)
    raw_days = route.get('daily_schedule', [])
    # The legacy loop skips a day it cannot compute; a purchased route never has gaps.
    if len(raw_days) != 30:
        raise ValueError('Incomplete monthly route')
    days = []
    for index, raw in enumerate(raw_days):
        day = date + timedelta(days=index)
        if raw.get('date') != day.strftime('%Y-%m-%d'):
            raise ValueError('Monthly route dates out of order')
        days.append(normalize_day(raw, day, checked_schedule(city, day)))
    return days


def monthly_section(days, header, modifiers, wisdom_line):
    from domain.full_report import _section, _value, _chart
    def meaning(day):
        top = max(day['energies'], key=lambda e: e['value'])
        low = min(day['energies'], key=lambda e: e['value'])
        rahu = next((p for p in day['periods'] if p['id'] == 'rahu_kaal'), None)
        return (f'{day["day_type_label"] or "Тип дня не определён"}. Управитель дня — {day["ruler"]}. '
                f'Выше всего: {top["title"]} {top["value"]}; ниже всего: {low["title"]} {low["value"]}.'
                + (f' Раху Кала {rahu["start"]}–{rahu["end"]}.' if rahu else ''))
    values = [_value(f'{day["date"][8:]}.{day["date"][5:7]} · {day["weekday"]}', day['average'], meaning(day), date=day['date'])
              for day in days]
    spoken = lambda day: f'{day["date"][8:]}.{day["date"][5:7]}.{day["date"][:4]} — {round(day["average"])}'
    ranked = sorted(days, key=lambda day: day['average'])
    teaching = KNOWLEDGE['vedic-monthly']
    section = _section('profile-monthly-route', TITLES['monthly'],
        [header, teaching['meaning'], teaching['focus'],
         'Шкала 0–100 — показатель символической модели проекта, не вероятность событий и не измерение физических сил.'],
        teaching['method'],
        ['Использованы сохранённые личные числа, квадрат, фрактал, задачи и доступные числа имени'
         + (' и действующие авторские настройки модификаторов.' if modifiers else '.'),
         wisdom_line,
         f'Средний показатель тридцати дней: {round(sum(d["average"] for d in days) / len(days))}.',
         'Самые высокие дни: ' + '; '.join(spoken(d) for d in ranked[:-4:-1]) + '.',
         'Самые низкие дни: ' + '; '.join(spoken(d) for d in ranked[:3]) + '.'],
        values, chart=_chart('series', values))
    # Thirty dated lines are for reading; the voice gives the method and the highest and lowest days.
    section['narration_values'] = False
    return section


def time_sections(birth_date, target, snapshot):
    from domain.full_report import _section, _value, _chart, _NUMBERS
    location = snapshot.get('current_location')
    if not isinstance(location, dict):
        return [], {}, [{'title':'Планетарные часы и дневной маршрут',
            'reason':'Текущий город не выбран однозначно из справочника. Город рождения не подставляется вместо текущего; координаты не угадываются.'}]
    from astral import Observer
    from astral.sun import sun
    import pytz
    lat, lon, zone = location['latitude'], location['longitude'], location['timezone']
    if not all(type(v) in (int,float) and math.isfinite(v) for v in (lat,lon)) or not -90<=lat<=90 or not -180<=lon<=180:
        raise ValueError('Invalid frozen location')
    timezone=pytz.timezone(zone)
    for date in (target, target+timedelta(days=1)):
        boundary=sun(Observer(lat,lon),date=date,tzinfo=timezone)
        if not boundary['sunrise']<boundary['sunset']:
            raise ValueError('Solar boundaries unavailable')
    date=datetime.combine(target,datetime.min.time())
    city=location['label']
    context=user_context(birth_date,snapshot['fields'])
    wisdom_line=wisdom_note(profile_wisdom(birth_date,snapshot['fields']),snapshot['fields'])
    # Orders paid before 24.10.2026 have no frozen modifiers and keep the defaults they were built with.
    modifiers=snapshot.get('planetary_modifiers') or {}
    month=None
    with location_scope(city,lat,lon,zone):
        schedule=checked_schedule(city,date)
        energies=calculate_enhanced_daily_planetary_energy(
            destiny_number=calculate_bhagya_ank(*parse_birth_date(birth_date)),date=date,birth_date=birth_date,
            city=city,modifiers_config=modifiers,**context)
        day=normalize_day({'planetary_energies':energies},date,schedule,include_hours=True)
        try:
            month=monthly_route(birth_date,date,city,context,modifiers)
        except (ValueError,KeyError,HTTPException):
            pass
    header=f'{target.isoformat()} · {city} · {zone}'
    digits={key:digit for key,_,digit in PLANETS}
    hours=[_value(f'{"Дневной" if i<12 else "Ночной"} час {i%12+1} · {h["title"]}',digits[h['planet']],
        f'{clock(h["start"])}–{clock(h["end"])}. '+_NUMBERS[digits[h['planet']]]['summary'],start=h['start'],end=h['end'],planet=h['planet'])
        for i,h in enumerate(day['hours'])]
    periods=[_value(p['title'],None,f'{p["start"]}–{p["end"]}. {p["meaning"]}') for p in day['periods']]
    values=[_value(p['title'],p['value'],_NUMBERS[p['digit']]['summary'],key=p['key']) for p in day['energies']]
    sections=[
        _section('profile-planetary-hours','Планетарные часы на дату отчёта',[header,KNOWLEDGE['vedic-schedule']['meaning']],
            KNOWLEDGE['vedic-schedule']['method'],
            [f'Восход: {clock(day["sunrise"])}; закат: {clock(day["sunset"])}; следующий восход: {clock(day.get("next_sunrise")) or "не указан"}.',
             'Дневной и ночной отрезки разделены на двенадцать частей; числа на схеме обозначают код планеты, а не оценку качества часа.'],
            hours,chart=_chart('series',hours)),
        _section('profile-solar-periods','Солнечные интервалы',[header],
            'Интервалы действующего ведического расписания для подтверждённых координат и часового пояса.',
            [f'Восход {day["sunrise"]}; закат {day["sunset"]}.'],periods),
        _section('profile-daily-route','Персональный маршрут на дату отчёта',
            [header,KNOWLEDGE['vedic-daily']['meaning'],'Шкала 0–100 — показатель символической модели проекта, не вероятность событий и не измерение физических сил.'],
            KNOWLEDGE['vedic-daily']['method'],
            ['Использованы сохранённые личные числа, квадрат, фрактал, задачи и доступные числа имени.',wisdom_line],
            values,chart=_chart('bars',values))]
    excluded=[{'title':'Недельный и квартальный маршруты',
         'reason':'Полный отчёт фиксирует маршрут на свою дату и тридцать дней вперёд. Другой горизонт и дату можно выбрать в отдельных интерактивных инструментах.'}]
    if month:
        sections.append(monthly_section(month,f'{month[0]["date"]} – {month[-1]["date"]} · {city} · {zone}',modifiers,wisdom_line))
    else:
        excluded.insert(0,{'title':TITLES['monthly'],
            'reason':'Для сохранённого места часть из тридцати дней не получила солнечных границ или полного расчёта; дни не пропускаются и не подставляются.'})
    return sections,{'location':location,'day':day,'month':month,'context':context},excluded
