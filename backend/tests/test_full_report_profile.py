"""Full-report profile math parity, exact inputs, and offline time boundaries."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from domain.full_report import build_full_report, _personal_sections, _date
from domain.full_report_profile import snapshot_profile, name_schemes
from domain.number_tools import ToolRequest, build_tools
from services.report_insights import generation_parts, evidence, SYNTHESIS_SKIP
from numerology import calculate_address_numerology

LOCATION = {'id':'618426','name':'Chisinau','label':'Chisinau, Moldova','latitude':47.0105,
            'longitude':28.8638,'timezone':'Europe/Chisinau'}


def snapshot(**changes):
    result=snapshot_profile({'name':'Dmitrii','surname':'Malahov','birth_date':'10.01.1982',
        'house_number':'12A','apartment_number':'34','postal_code':'2044','car_number':'ABC 123',
        'phone_number':'+373 (691) 83-398','city':'Chisinau','birth_city':'Kyiv','birth_city_id':'703448',**changes})
    result['current_location']=copy.deepcopy(LOCATION)
    return result


class ProfileReportMath(unittest.TestCase):
    def test_separate_methods_and_all_available_profile_sections(self):
        source=snapshot(); result=build_full_report('10.01.1982','2026-10-23',source)
        ids={s['id'] for s in result['sections']}
        expected={'profile-name','profile-wisdom','profile-vedic-name','profile-abracadabra','profile-human',
                  'profile-address','profile-car','profile-phone','profile-planetary-hours','profile-solar-periods','profile-daily-route'}
        self.assertTrue(expected <= ids)
        raw=result['raw']['profile']
        for kind,inputs in [('name',{'name':'Dmitrii','surname':'Malahov'}),('car',{'car_number':'ABC 123'})]:
            tool=build_tools(ToolRequest(kind=kind,request_id='00000000-0000-4000-8000-000000000001',expected_cost=0,inputs=inputs))
            self.assertEqual(raw[kind],tool)
        legacy=calculate_address_numerology(house_number='12A',apartment_number='34',postal_code='2044',street='')
        self.assertEqual(raw['address']['legacy'],legacy)
        self.assertIn('A=1',next(s for s in result['sections'] if s['id']=='profile-wisdom')['method'])
        self.assertIn('1 до 9',raw['name']['method'])
        self.assertEqual(len(raw['time']['day']['hours']),24)
        self.assertEqual(len(raw['time']['day']['energies']),9)
        self.assertEqual(result['profile_snapshot']['fields']['birth_city'],'Kyiv')
        self.assertEqual(raw['time']['location']['name'],'Chisinau')

    def test_all_profile_results_are_frozen_detached_and_serializable(self):
        source=snapshot(); before=copy.deepcopy(source)
        report=build_full_report('10.01.1982','2026-10-23',source)
        self.assertEqual(source,before)
        source['fields']['name']='Changed'
        self.assertEqual(report['profile_snapshot'],before)
        self.assertEqual(report,json.loads(json.dumps(report,allow_nan=False)))
        date_only=build_full_report('10.01.1982','2026-10-23')
        for key,value in date_only['raw'].items(): self.assertEqual(report['raw'][key],value)
        self.assertTrue(all(c['section']=='full-report' for c in report['narration']))
        self.assertTrue(all('full-report-'+s['id'] in {c['id'] for c in report['narration']} for s in report['sections']))

    def test_name_schemes_match_existing_javascript_core(self):
        for name,surname in [('Dmitrii','Malahov'),('Al','Smith'),("Anne-Marie","O’Neil"),('Иван','Иванов'),('ABCD','')]:
            code='const {nameSchemes}=require("./packages/numerology-core/name-schemes");process.stdout.write(JSON.stringify(nameSchemes(JSON.parse(process.argv[1]),"10.01.1982")))'
            actual=json.loads(subprocess.check_output(['node','-e',code,json.dumps({'name':name,'surname':surname})],cwd=Path(__file__).resolve().parents[2]))
            python=name_schemes(name,surname,_date('10.01.1982'))
            for key,value in python.items(): self.assertEqual(actual[key],value,(name,surname,key))

    def test_cyrillic_name_not_silently_transliterated_or_used_in_latin_schemes(self):
        result=build_full_report('10.01.1982','2026-10-23',snapshot(name='Иван',surname='Иванов'))
        ids={s['id'] for s in result['sections']}
        self.assertIn('profile-name',ids)
        self.assertNotIn('profile-wisdom',ids)
        self.assertNotIn('profile-abracadabra',ids)
        self.assertNotIn('profile-human',ids)
        self.assertNotIn('wisdom_number',result['raw']['profile']['time']['context']['user_numbers'])

    def test_apartment_and_index_do_not_require_invented_house(self):
        result=build_full_report('10.01.1982','2026-10-23',snapshot(house_number=''))
        values=next(s for s in result['sections'] if s['id']=='profile-address')['values']
        self.assertEqual([v['key'] for v in values],['apartment_number','postal_code'])
        self.assertEqual([v['value'] for v in values],[7,1])
        self.assertTrue(any(e['title']=='Номер дома' for e in result['excluded']))

    def test_phone_reduces_exact_entered_digits_without_guessing_country_or_preserving_master(self):
        for entered,digits,expected in [('+373 (691) 83-398','37369183398',6),('0011','0011',2),('119','119',2)]:
            report=build_full_report('10.01.1982','2026-10-23',snapshot(phone_number=entered))
            phone=report['raw']['profile']['phone']
            self.assertEqual(phone['source'],entered)
            self.assertEqual(phone['digits'],digits)
            self.assertEqual(phone['number'],expected)
            section=next(s for s in report['sections'] if s['id']=='profile-phone')
            self.assertIn('новое применение',section['method'])
        for entered in ['', '0000', 'abc123', '123 ext 4', '+12📞345']:
            report=build_full_report('10.01.1982','2026-10-23',snapshot(phone_number=entered))
            self.assertNotIn('phone',report['raw']['profile'])

    def test_time_does_not_use_birth_city_or_network_geocoding(self):
        source=snapshot();source['current_location']=None;source['birth_location']=LOCATION
        with patch('geopy.geocoders.Nominatim.geocode',side_effect=AssertionError('must stay offline')):
            result=build_full_report('10.01.1982','2026-10-23',source)
        self.assertFalse(any(s['id'].startswith('profile-planetary') for s in result['sections']))
        self.assertTrue(any('Текущий город' in s['reason'] for s in result['excluded']))
        source=snapshot()
        with patch('geopy.geocoders.Nominatim.geocode',side_effect=AssertionError('must stay offline')):
            result=build_full_report('10.01.1982','2026-10-23',source)
        self.assertEqual(result['raw']['profile']['time']['location'],LOCATION)

    def test_context_uses_actual_wisdom_and_matches_existing_route_arithmetic(self):
        source=snapshot();report=build_full_report('10.01.1982','2026-10-23',source)
        raw=report['raw']['profile'];context=raw['time']['context']
        self.assertEqual(context['user_numbers']['wisdom_number'],raw['name_personal']['wisdom_number'])
        self.assertNotEqual(context['user_numbers']['wisdom_number'],8)
        from domain.vedic_location import location_scope
        from vedic_numerology import calculate_enhanced_daily_planetary_energy,calculate_bhagya_ank
        from datetime import datetime
        with location_scope(LOCATION['label'],LOCATION['latitude'],LOCATION['longitude'],LOCATION['timezone']):
            expected=calculate_enhanced_daily_planetary_energy(destiny_number=calculate_bhagya_ank(10,1,1982),
                date=datetime(2026,10,23),birth_date='10.01.1982',city=LOCATION['label'],modifiers_config={},**context)
        self.assertEqual({v['key']:v['value'] for v in raw['time']['day']['energies']},expected)

    def test_expanded_insights_material_preserves_every_fact_and_meaning(self):
        report=build_full_report('10.01.1982','2026-10-23',snapshot())
        parts=generation_parts(report);packed=parts[0]['material'];actual={}
        self.assertEqual(packed['value_columns'],['ref','label','value','meaning_ref'])
        for section in packed['sections']:
            for row in section['values']:
                entry=dict(zip(packed['value_columns'],row))
                actual[entry['ref']]={'label':entry['label'],'value':entry['value'],'meaning':packed['meanings'][entry['meaning_ref']]}
        # Date-bound schedules have their own chapters and stay out of the synthesis prompt (num_ctx 16384).
        expected={ref:{k:value[k] for k in ('label','value','meaning')} for ref,value in evidence(report).items()}
        route={ref for ref in expected if ref.split(':')[0] in SYNTHESIS_SKIP}
        self.assertEqual(sum(ref.startswith('profile-monthly-route:') for ref in route),30)
        self.assertEqual(sum(ref.startswith('profile-planetary-hours:') for ref in route),24)
        self.assertEqual(actual,{ref:value for ref,value in expected.items() if ref not in route})
        self.assertFalse(route & set(parts[0]['response_schema']['$defs']['evidenceReference']['enum']))
        self.assertLess(len(json.dumps(packed,ensure_ascii=False,separators=(',',':'))),40000)
        ids=[s['id'] for part in parts[1:] if part['kind'] == 'chapters' for s in part['report']['sections']]
        self.assertEqual(ids,[s['id'] for s in report['sections']])
        shown={v['ref'] for part in parts[1:] if part['kind'] == 'chapters' for s in part['material']['sections'] for v in s['values']}
        self.assertTrue(route <= shown)

    def test_hours_are_written_as_local_clock_time_not_iso_timestamps(self):
        # «2026-10-24T07:35:28+03:00–…» was read aloud digit by digit in the paid audio.
        report=build_full_report('10.01.1982','2026-10-23',snapshot())
        hours=next(s for s in report['sections'] if s['id']=='profile-planetary-hours')
        self.assertRegex(hours['values'][0]['meaning'],r'^\d\d:\d\d–\d\d:\d\d\. ')
        self.assertNotRegex(' '.join(hours['steps']+[v['meaning'] for v in hours['values']]),r'\d{4}-\d\d-\d\dT')
        self.assertIn('T',hours['values'][0]['start'])

    def test_entered_name_puts_wisdom_and_full_name_number_into_the_personal_numbers(self):
        report=build_full_report('10.01.1982','2026-10-23',snapshot())
        personal=report['sections'][0]
        self.assertEqual([(v['key'],v['value']) for v in personal['values'][-2:]],[('wisdom',5),('full_name',1)])
        self.assertTrue(personal['steps'][-2].startswith('Число мудрости.'))
        named=next(s for s in report['sections'] if s['id']=='profile-wisdom')
        self.assertEqual([v['value'] for v in named['values']],[5,1])
        # Without a Latin name and surname nothing is invented; a date-only report keeps seven numbers.
        for source in (snapshot(name='Дмитрий',surname='Малахов'),None):
            plain=build_full_report('10.01.1982','2026-10-23',source)
            self.assertEqual(len(plain['sections'][0]['values']),7)

    def test_chapter_knowledge_never_hands_the_model_a_forbidden_sentence(self):
        # «Сопоставьте повторяющиеся темы и итоговое число» was copied into prose and failed every attempt.
        from services.report_insights import _sentence
        report=build_full_report('10.01.1982','2026-10-23',snapshot())
        knowledge=[sentence for part in generation_parts(report)[1:] if part['kind'] == 'chapters' for s in part['material']['sections'] for sentence in s['knowledge']]
        self.assertTrue(knowledge)
        for sentence in knowledge:
            _sentence(sentence,2000)
        self.assertNotIn('итоговое число',' '.join(knowledge))

    def test_thirty_day_route_from_report_date_uses_frozen_author_modifiers(self):
        import vedic_time_calculations as legacy
        source=snapshot();source['planetary_modifiers']={'friend_planet_bonus':0.11,'normalization_min':1,'normalization_max':95}
        seen=[]
        original=legacy.get_monthly_planetary_route
        def spy(**kwargs):
            seen.append(kwargs['modifiers_config']);return original(**kwargs)
        with patch('vedic_time_calculations.get_monthly_planetary_route',side_effect=spy), \
                patch('domain.full_report_time.calculate_enhanced_daily_planetary_energy',
                      wraps=__import__('vedic_numerology').calculate_enhanced_daily_planetary_energy) as daily:
            report=build_full_report('10.01.1982','2026-10-23',source)
        self.assertEqual(seen,[source['planetary_modifiers']])
        self.assertEqual(daily.call_args.kwargs['modifiers_config'],source['planetary_modifiers'])
        section=next(s for s in report['sections'] if s['id']=='profile-monthly-route')
        self.assertEqual(section['title'],'Маршрут на 30 дней')
        dates=[v['date'] for v in section['values']]
        from datetime import date,timedelta
        self.assertEqual(dates,[(date(2026,10,23)+timedelta(days=i)).isoformat() for i in range(30)])
        days=report['raw']['profile']['time']['month']
        self.assertEqual([v['value'] for v in section['values']],[d['average'] for d in days])
        self.assertTrue(all(len(d['energies'])==9 for d in days))
        self.assertEqual(section['chart']['type'],'series');self.assertEqual(len(section['chart']['items']),30)
        self.assertFalse(section['narration_values'])
        self.assertIn('авторские настройки модификаторов',section['steps'][0])
        self.assertIn('Chisinau, Moldova',section['paragraphs'][0])
        self.assertNotIn('Маршрут на 30 дней',[e['title'] for e in report['excluded']])

    def test_incomplete_month_is_excluded_and_never_padded(self):
        import vedic_time_calculations as legacy
        original=legacy.get_monthly_planetary_route
        def short(**kwargs):
            route=original(**kwargs);route['daily_schedule']=route['daily_schedule'][:29];return route
        with patch('vedic_time_calculations.get_monthly_planetary_route',side_effect=short):
            report=build_full_report('10.01.1982','2026-10-23',snapshot())
        ids={s['id'] for s in report['sections']}
        self.assertNotIn('profile-monthly-route',ids)
        self.assertTrue({'profile-planetary-hours','profile-daily-route'} <= ids)
        self.assertIn('Маршрут на 30 дней',[e['title'] for e in report['excluded']])

    def test_private_profile_fields_are_not_copied(self):
        result=snapshot_profile({'email':'private@example.test','password_hash':'secret','name':'A'*501,'surname':'A\nB','birth_city_id':'bad'})
        self.assertNotIn('email',result['fields']);self.assertNotIn('password_hash',result['fields'])
        self.assertEqual(result['fields']['name'],'');self.assertEqual(len(result['issues']),2)

if __name__=='__main__':unittest.main()
