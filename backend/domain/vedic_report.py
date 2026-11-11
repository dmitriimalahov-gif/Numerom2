"""Versioned mobile views of existing NumerOM time/route calculations.

The legacy arithmetic is reused. Unknown coordinates and unavailable solar
boundaries are rejected before a paid receipt can be committed.
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal
from uuid import UUID
import json
import math
import re
import pytz
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator, model_validator, model_serializer
from domain.vedic_location import LocationInput, location_scope, resolve_timezone
import vedic_time_calculations as legacy
from numerology import calculate_personal_numbers, create_pythagorean_square, calculate_planetary_strength, parse_birth_date, reduce_to_single_digit
from vedic_numerology import calculate_janma_ank, calculate_bhagya_ank, calculate_enhanced_daily_planetary_energy
from domain.name_numbers import calculate_full_name_number
from domain.number_tools import ToolRequest, build_tools
from domain.personal_report import supported_profile_name, _reduction_steps

KINDS={'schedule':1,'daily':1,'weekly':7,'monthly':30,'quarterly':90}
PRICES={'schedule':'vedic_daily',**{kind:'planetary_'+kind for kind in ('daily','weekly','monthly','quarterly')}}
TITLES={'schedule':'Ведическое время','daily':'Маршрут на день','weekly':'Маршрут на 7 дней','monthly':'Маршрут на 30 дней','quarterly':'Маршрут на 90 дней'}
PLANETS=[('surya','Солнце',1),('chandra','Луна',2),('guru','Юпитер',3),('rahu','Раху',4),('budha','Меркурий',5),('shukra','Венера',6),('ketu','Кету',7),('shani','Сатурн',8),('mangal','Марс',9)]
PLANET_NAMES={key:title for key,title,_ in PLANETS}
RULERS=['chandra','mangal','budha','guru','shukra','shani','surya']
WEEKDAYS=['Понедельник','Вторник','Среда','Четверг','Пятница','Суббота','Воскресенье']
KNOWLEDGE={item['id']:item for item in json.loads((Path(__file__).resolve().parents[2]/'packages/vedic-knowledge/ru.json').read_text())['items']}

class VedicRequest(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    kind:Literal['schedule','daily','weekly','monthly','quarterly']
    date:StrictStr=Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    city:StrictStr=Field(min_length=2,max_length=120)
    location:LocationInput|None=None
    birth_date:StrictStr=''
    request_id:UUID
    expected_cost:int=Field(strict=True,ge=0,le=1000000)
    @model_serializer(mode='wrap')
    def stable_payload(self,handler):
        # Preserve fingerprints of manual-city receipts made before GPS support.
        body=handler(self)
        if self.location is None:body.pop('location',None)
        return body
    @field_validator('request_id')
    @classmethod
    def uuid4(cls,value):
        if value.version!=4:raise ValueError('Нужен UUIDv4 попытки')
        return value
    @field_validator('city')
    @classmethod
    def valid_city(cls,value):
        if any(ord(c)<32 for c in value) or not any(c.isalpha() for c in value):raise ValueError('Укажите название города')
        return value
    @model_validator(mode='after')
    def valid_dates(self):
        start=datetime.strptime(self.date,'%Y-%m-%d')
        if start.year<1900 or (start+timedelta(days=KINDS[self.kind]-1)).year>2099:raise ValueError('Дата должна быть между 1900 и 2099 годами')
        if self.birth_date:
            if not re.fullmatch(r'\d{2}\.\d{2}\.\d{4}',self.birth_date):raise ValueError('Дата рождения: ДД.ММ.ГГГГ')
            birth=datetime.strptime(self.birth_date,'%d.%m.%Y')
            if birth.year<1900 or birth>datetime.utcnow():raise ValueError('Проверьте дату рождения')
        elif self.kind!='schedule':raise ValueError('Для личного маршрута нужна дата рождения')
        return self


def checked_location(city,start,days,coordinates=None):
    try:
        from astral import Observer
        from astral.sun import sun
    except ImportError:
        raise HTTPException(503,'Сервис солнечных расчётов временно недоступен. Баллы не списаны.')
    if coordinates is not None:
        latitude,longitude,zone=coordinates.latitude,coordinates.longitude,resolve_timezone(coordinates)
    else:latitude,longitude,zone=legacy.get_city_coordinates(city)
    if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (latitude,longitude)) or not -90<=latitude<=90 or not -180<=longitude<=180 or (coordinates is None and latitude==0 and longitude==0):
        raise HTTPException(422,'Город не найден. Уточните название и страну. Баллы не списаны.')
    # Legacy UTC can mean timezonefinder failed. Confirm rather than bill a fallback.
    if zone=='UTC' and coordinates is None:
        try:
            from timezonefinder import TimezoneFinder
            zone=TimezoneFinder().timezone_at(lat=latitude,lng=longitude)
        except Exception:zone=None
        if not zone:raise HTTPException(422,'Не удалось определить часовой пояс города. Баллы не списаны.')
    try:
        timezone=pytz.timezone(zone)
        for offset in range(days+1):
            boundary=sun(Observer(latitude,longitude),date=(start+timedelta(days=offset)).date(),tzinfo=timezone)
            if not boundary['sunrise']<boundary['sunset']:raise ValueError('No solar boundaries')
    except Exception:
        raise HTTPException(422,'Для выбранного места и периода восход или закат недоступен. Баллы не списаны.')
    return {'latitude':latitude,'longitude':longitude,'timezone':zone}


def profile_wisdom(birth_date,profile):
    """Число мудрости = судьба + полное число имени (A=1 … Z=26) из латинских имени и фамилии профиля; 11, 22, 33
    сохраняются. Без такого имени — None: прежняя заглушка «судьба × 2» в маршрутах больше не используется."""
    parts=supported_profile_name((profile or {}).get('name') or '',(profile or {}).get('surname') or '')
    if not birth_date or not parts:return None
    destiny=calculate_personal_numbers(birth_date)['destiny_number'];full=calculate_full_name_number(*parts)
    value,_=_reduction_steps(destiny+full)
    return {'value':value,'destiny':destiny,'full_name_number':full,
            'calculation':f'{destiny} + {full} = {destiny+full}'+('' if destiny+full==value else f' → {value}')}


def profile_name_numbers(profile):
    """Числа имени действующим инструментом (циклическая таблица): имя, фамилия и оба вместе, как в полном отчёте."""
    name,surname=((profile or {}).get(key) or '' for key in ('name','surname'))
    names={}
    for key,value in [('first_name_number',name),('last_name_number',surname),('total_name_number',f'{name} {surname}' if name and surname else '')]:
        try:names[key]=build_tools(ToolRequest(kind='name',request_id='00000000-0000-4000-8000-000000000001',expected_cost=0,inputs={'name':value}))['items'][0]['number']
        except ValueError:pass
    if 'total_name_number' in names:names['full_name_number']=names['total_name_number']
    return names or None


def user_context(birth_date,profile=None):
    """Personal inputs of every planetary route: the route tools, the old site endpoints and the full report.
    `profile` holds the name and surname of the person whose birth date this is, or None."""
    if not birth_date:return {}
    day,month,year=parse_birth_date(birth_date)
    numbers=calculate_personal_numbers(birth_date)
    user_numbers={key:numbers.get(key) for key in ('soul_number','mind_number','destiny_number','ruling_number')}
    wisdom=profile_wisdom(birth_date,profile)
    if wisdom:user_numbers['wisdom_number']=wisdom['value']
    dr,mr,yr=map(reduce_to_single_digit,(day,month,year))
    soul,mind=user_numbers['soul_number'],user_numbers['mind_number']
    p1,p2=reduce_to_single_digit(abs(soul-mind)),reduce_to_single_digit(abs(soul-yr))
    name_numbers=profile_name_numbers(profile)
    strengths=calculate_planetary_strength(day,month,year).get('strength',{})
    names={'Солнце':'surya','Луна':'chandra','Марс':'mangal','Меркурий':'budha','Юпитер':'guru','Венера':'shukra','Сатурн':'shani'}
    return {'user_numbers':user_numbers,'pythagorean_square':create_pythagorean_square(day,month,year),
            'fractal_behavior':[dr,mr,yr,reduce_to_single_digit(day+month+year)],
            'problem_numbers':[p1,p2,reduce_to_single_digit(abs(p1-p2)),reduce_to_single_digit(abs(mind-yr))],
            'name_numbers':name_numbers,'weekday_energy':{names[key]:float(value) for key,value in strengths.items() if key in names},
            'janma_ank':22 if day+month+year==22 else calculate_janma_ank(day,month,year)}


def normalize_periods(schedule):
    titles={'rahu_kaal':'Раху Кала','gulika_kaal':'Гулика Кала','yamaghanta':'Ямаганта','abhijit_muhurta':'Абхиджит Мухурта'}
    source={**schedule.get('inauspicious_periods',{}),**schedule.get('auspicious_periods',{})}
    return [{'id':key,'title':title,'start':source[key]['start'],'end':source[key]['end'],'meaning':source[key]['description']} for key,title in titles.items() if key in source]


def checked_schedule(city,date):
    value=legacy.get_vedic_day_schedule(city,date)
    if 'error' in value or len(value.get('planetary_hours',[]))!=12 or len(value.get('night_hours',[]))!=12:raise HTTPException(503,'Не удалось получить полное расписание. Баллы не списаны.')
    return value


def normalize_day(raw,date,schedule,include_hours=False,require_energy=True):
    energies=raw.get('planetary_energies',{})
    if require_energy and (set(energies)!=set(PLANET_NAMES) or any(type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=100 for value in energies.values())):
        raise HTTPException(503,'Показатели планет получены не полностью. Баллы не списаны.')
    items=[{'key':key,'title':title,'digit':digit,'value':energies[key]} for key,title,digit in PLANETS if key in energies]
    hours=[]
    if include_hours:
        for hour in schedule['planetary_hours']+schedule['night_hours']:
            key={'Budh':'budha'}.get(hour['planet'],hour['planet'].lower())
            hours.append({'hour':hour['hour'],'planet':key,'title':PLANET_NAMES[key], 'start':hour['start_time'],'end':hour['end_time'],'period':hour['period']})
    return {'date':date.strftime('%Y-%m-%d'),'weekday':WEEKDAYS[date.weekday()],'ruler':PLANET_NAMES[RULERS[date.weekday()]],
            'energies':items,'average':round(sum(energies.values())/9,2) if items else None,
            'day_type':raw.get('day_type',''),'day_type_label':raw.get('day_type_ru',''),
            'sunrise':schedule['sun_times']['sunrise'],'sunset':schedule['sun_times']['sunset'],
            **({'next_sunrise':schedule['sun_times']['next_sunrise']} if schedule['sun_times'].get('next_sunrise') else {}),
            'periods':normalize_periods(schedule),'hours':hours,
            'activities':schedule.get('recommendations',{}).get('activities',[])}


def wisdom_note(wisdom,profile):
    if wisdom:return f'Число мудрости {wisdom["value"]} = судьба {wisdom["destiny"]} + полное число имени {wisdom["full_name_number"]}; учтено в показателях планет.'
    if profile is None:return 'Число мудрости не учтено: дата рождения не совпадает с профилем, поэтому имя профиля к ней не применяется.'
    return 'Число мудрости не учтено: для него нужны имя и фамилия латиницей в профиле. Заменяющее значение не подставляется.'


def build_vedic_report(data,*,profile=None,modifiers=None):
    start=datetime.strptime(data.date,'%Y-%m-%d');count=KINDS[data.kind]
    location=checked_location(data.city,start,count,data.location)
    # Every legacy helper (including energy modifiers) sees this same location.
    # ContextVar state is thread/task-local and never changes the global city cache.
    with location_scope(data.city,**location):
        return _build_vedic_report_at_location(data,start,count,location,profile=profile,modifiers=modifiers)


def _build_vedic_report_at_location(data,start,count,location,*,profile=None,modifiers=None):
    context=user_context(data.birth_date,profile)
    wisdom=profile_wisdom(data.birth_date,profile)
    full_name=((profile or {}).get('full_name') or ' '.join(filter(None,((profile or {}).get('name'),(profile or {}).get('surname'))))).strip()
    common={'city':data.city,'start_date':start,'birth_date':data.birth_date,**context,'modifiers_config':modifiers or {}}
    if data.kind in ('weekly','monthly','quarterly'):
        function={'weekly':legacy.get_weekly_planetary_route,'monthly':legacy.get_monthly_planetary_route,'quarterly':legacy.get_quarterly_planetary_route}[data.kind]
        route=function(**common)
        raw_days=[d for week in route.get('weekly_schedule',[]) for d in week['days']] if data.kind=='quarterly' else route.get('daily_schedule',[])
        if len(raw_days)!=count:raise HTTPException(503,'Маршрут получен не полностью. Баллы не списаны.')
    else:
        energies={}
        if data.kind=='daily':
            energies=calculate_enhanced_daily_planetary_energy(destiny_number=calculate_bhagya_ank(*parse_birth_date(data.birth_date)),date=start,birth_date=data.birth_date,city=data.city,**context,modifiers_config=modifiers or {})
        raw_days=[{'date':data.date,'planetary_energies':energies}]
    days=[]
    for index,raw in enumerate(raw_days):
        date=start+timedelta(days=index)
        if raw.get('date')!=date.strftime('%Y-%m-%d'):raise HTTPException(503,'Порядок дат маршрута нарушен. Баллы не списаны.')
        schedule=checked_schedule(data.city,date)
        days.append(normalize_day(raw,date,schedule,include_hours=count==1,require_energy=data.kind!='schedule'))
    teaching=KNOWLEDGE['vedic-'+data.kind]
    return {'version':1,'kind':data.kind,'title':TITLES[data.kind], 'city':data.city,'location':location,'timezone':location['timezone'],
            'start_date':data.date,'end_date':days[-1]['date'],'birth_date':data.birth_date,'profile_name':full_name,
            **({'wisdom':wisdom,'wisdom_note':wisdom_note(wisdom,profile)} if data.birth_date else {}),
            'days':days,'meaning':teaching['meaning'],'method':teaching['method'],'focus':teaching['focus'],'narration_id':teaching['id'],'legacy':{}}
