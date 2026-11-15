"""Synthetic coordinates only; upstream geocoding is mocked in all tests."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import AsyncMock, Mock, patch
from urllib.error import URLError
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from starlette.testclient import TestClient
from public_gateway import create_public_gateway, _route, _valid_body
from auth import get_current_user
from domain import vedic_report as report
from domain.vedic_location import LocationInput, current_coordinates, location_scope
from routers.vedic_calculations import create_vedic_calculations_router
from services import vedic_location as resolver
from services.vedic_calculations import VedicCalculations


COORDS = {'latitude': 47.010501, 'longitude': 28.863801}


def data(**changes):
    return report.VedicRequest.model_validate({'kind': 'schedule', 'date': '2026-10-18',
        'city': 'Кишинёв, Молдова', 'birth_date': '', 'request_id': str(uuid.uuid4()),
        'expected_cost': 1, **changes})


class LocationValidation(unittest.TestCase):
    def test_strict_finite_ranges_and_server_owned_timezone(self):
        for field, value in [('latitude', True), ('latitude', '47.0'), ('latitude', 90.1),
                             ('latitude', -90.1), ('longitude', 180.1), ('longitude', -180.1),
                             ('latitude', float('nan')), ('longitude', float('inf'))]:
            with self.subTest(field=field, value=value), self.assertRaises(ValidationError):
                LocationInput.model_validate({**COORDS, field: value})
        for extra in ({'timezone': 'UTC'}, {'user_id': 'victim'}, {'accuracy': 20}):
            with self.assertRaises(ValidationError):LocationInput.model_validate({**COORDS, **extra})
        self.assertEqual(LocationInput(latitude=0, longitude=180).longitude, 180)
        with self.assertRaises(ValidationError):data(location={**COORDS, 'timezone': 'UTC'})

    def test_legacy_manual_fingerprint_unchanged_and_coordinates_in_new_fingerprint(self):
        manual = data()
        body = manual.model_dump(mode='json', exclude={'request_id'})
        self.assertNotIn('location', body)
        self.assertEqual(data(location=None, request_id=str(manual.request_id)).model_dump(mode='json', exclude={'request_id'}), body)
        self.assertEqual(data(location=COORDS).model_dump(mode='json')['location'], COORDS)

    def test_concurrent_scopes_never_poison_city_cache_and_reset_on_failure(self):
        city = 'Synthetic shared city'
        cached = (10, 20, 'Europe/Paris')
        barrier = threading.Barrier(2)
        def run(coords):
            with location_scope(city, *coords):
                barrier.wait(timeout=5)
                self.assertEqual(report.legacy.get_city_coordinates(city), coords)
                self.assertIsNone(current_coordinates('another city'))
            self.assertIsNone(current_coordinates(city))
            return report.legacy.get_city_coordinates(city)
        with patch.dict(report.legacy._city_cache, {city: cached}), ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(run, (47, 28, 'Europe/Chisinau'))
            second = pool.submit(run, (51, 0, 'Europe/London'))
            self.assertEqual(first.result(), cached);self.assertEqual(second.result(), cached)
            with self.assertRaises(RuntimeError), location_scope(city, 60, 30, 'Europe/Moscow'):
                raise RuntimeError('Synthetic failure')
            self.assertIsNone(current_coordinates(city))
            self.assertEqual(report.legacy._city_cache[city], cached)

    def test_actual_coordinates_drive_hours_for_all_periods_without_forward_geocoding(self):
        # A wrong existing city cache must not determine a GPS report's sun times.
        city = 'Кишинёв, Молдова'
        cached = (55.7558, 37.6173, 'Europe/Moscow')
        with patch.dict(report.legacy._city_cache, {city: cached}), patch.object(report.legacy, 'Nominatim', side_effect=AssertionError('No forward geocoding')):
            for kind in ('schedule', 'daily', 'weekly', 'monthly', 'quarterly'):
                result = report.build_vedic_report(data(kind=kind, location=COORDS, birth_date='10.01.1982'))
                self.assertEqual(result['location'], {**COORDS, 'timezone': 'Europe/Chisinau'})
                self.assertEqual(result['city'], city)
                with location_scope(city, COORDS['latitude'], COORDS['longitude'], 'Europe/Chisinau'):
                    expected = report.legacy.get_vedic_day_schedule(city, datetime(2026,10,18))
                self.assertEqual(result['days'][0]['sunrise'], expected['sun_times']['sunrise'])
                self.assertEqual(report.legacy._city_cache[city], cached)
                self.assertIsNone(current_coordinates(city))

    def test_invalid_zone_and_polar_location_fail_without_schedule_fallback(self):
        with patch('domain.vedic_location._timezone_finder') as finder:
            finder.return_value.timezone_at.return_value = None
            with self.assertRaises(HTTPException) as error:report.build_vedic_report(data(location=COORDS))
            self.assertEqual(error.exception.status_code, 422)
        with self.assertRaises(HTTPException) as error:report.build_vedic_report(data(location={'latitude':89,'longitude':0}))
        self.assertEqual(error.exception.status_code, 422)
        self.assertIsNone(current_coordinates('Кишинёв, Молдова'))


class ResolverTests(unittest.TestCase):
    def test_city_country_only_no_street_and_bounded_transport(self):
        body={'address': {'city':'Кишинёв','country':'Молдова','road':'Secret street','house_number':'45'}, 'lat':'0','lon':'0','display_name':'Secret street, 45'}
        class Response(io.BytesIO):
            pass
        opener=Mock();opener.open.return_value=Response(json.dumps(body).encode())
        with patch.object(resolver,'build_opener',return_value=opener):
            self.assertEqual(resolver._fetch_city(47.01,28.864),'Кишинёв, Молдова')
        args,kwargs=opener.open.call_args
        self.assertEqual(kwargs['timeout'],8)
        self.assertIn('zoom=10',args[0].full_url)
        self.assertIn('layer=address',args[0].full_url)
        self.assertIn('NumerOM',args[0].get_header('User-agent'))

    def test_missing_city_and_failure_never_fallback_to_street_or_leak_request(self):
        opener=Mock()
        for payload in ({'address':{'road':'Secret street','country':'Молдова'}}, {'address':{'city':'Кишинёв'}}, {'error':'No result'}):
            opener.open.return_value=io.BytesIO(json.dumps(payload).encode())
            with patch.object(resolver,'build_opener',return_value=opener),self.assertRaises(HTTPException) as error:
                resolver._fetch_city(47.01,28.864)
            self.assertEqual(error.exception.status_code,422)
            self.assertNotIn('Secret',error.exception.detail)
        opener.open.side_effect=URLError('secret-coordinate-url')
        with patch.object(resolver,'build_opener',return_value=opener),self.assertRaises(HTTPException) as error:
            resolver._fetch_city(47.01,28.864)
        self.assertEqual(error.exception.status_code,503)
        self.assertNotIn('secret',error.exception.detail)
        self.assertTrue(error.exception.__suppress_context__)

    def test_round_cache_bounded_ttl_and_one_request_per_second(self):
        now=[100.0];fetch=Mock(return_value='Кишинёв, Молдова')
        geocoder=resolver.ReverseGeocoder(fetch=fetch,clock=lambda:now[0],ttl=10,capacity=2)
        loc=LocationInput(**COORDS)
        self.assertEqual(geocoder.city(loc),'Кишинёв, Молдова')
        fetch.assert_called_once_with(47.011,28.864)
        self.assertEqual(geocoder.city(LocationInput(latitude=47.010502,longitude=28.863802)),'Кишинёв, Молдова')
        self.assertEqual(fetch.call_count,1)
        with self.assertRaises(HTTPException) as error:geocoder.city(LocationInput(latitude=48,longitude=29))
        self.assertEqual(error.exception.status_code,429)
        for lat in (48,49):
            now[0]+=1;geocoder.city(LocationInput(latitude=lat,longitude=29))
        self.assertEqual(len(geocoder.cache),2)
        now[0]+=11;geocoder.city(LocationInput(latitude=49,longitude=29))
        self.assertEqual(fetch.call_count,4)

    def test_parallel_upstream_is_bounded_and_lock_released_after_error(self):
        entered=threading.Event();release=threading.Event()
        def fetch(*args):
            entered.set();release.wait(5)
            raise HTTPException(503,'Synthetic failure')
        geocoder=resolver.ReverseGeocoder(fetch=fetch)
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(geocoder.city,LocationInput(**COORDS));self.assertTrue(entered.wait(5))
            with self.assertRaises(HTTPException) as error:geocoder.city(LocationInput(latitude=48,longitude=29))
            self.assertEqual(error.exception.status_code,429)
            release.set()
            with self.assertRaises(HTTPException):future.result()
        self.assertFalse(geocoder.upstream.locked());self.assertFalse(geocoder.cache)

    def test_exact_response_coordinates_and_timezone_are_not_provider_coordinates(self):
        with patch.object(resolver._geocoder,'city',return_value='Кишинёв, Молдова'):
            self.assertEqual(resolver.resolve_location(LocationInput(**COORDS)),{'city':'Кишинёв, Молдова',**COORDS,'timezone':'Europe/Chisinau'})


class LocationRoutes(unittest.IsolatedAsyncioTestCase):
    async def test_auth_no_writes_bad_finite_input_and_no_store(self):
        db=Mock();db.users.find_one=AsyncMock(return_value={'id':'student','credits_remaining':10})
        app=FastAPI();app.include_router(create_vedic_calculations_router(db))
        output={'city':'Кишинёв, Молдова',**COORDS,'timezone':'Europe/Chisinau'}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
            with patch('services.vedic_calculations.resolve_location',return_value=output) as resolve:
                self.assertEqual((await client.post('/api/numerology/vedic/location',json=COORDS)).status_code,401)
                resolve.assert_not_called();db.users.find_one.assert_not_called()
                app.dependency_overrides[get_current_user]=lambda:{'user_id':'student'}
                result=await client.post('/api/numerology/vedic/location',json=COORDS)
                self.assertEqual(result.status_code,200);self.assertEqual(result.json(),output)
                self.assertEqual(result.headers['cache-control'],'no-store')
                for raw in ('{"latitude":NaN,"longitude":28}', '{"latitude":90.1,"longitude":28}', '{"latitude":true,"longitude":28}', '{"latitude":47,"longitude":28,"timezone":"UTC"}'):
                    self.assertEqual((await client.post('/api/numerology/vedic/location',content=raw,headers={'Content-Type':'application/json'})).status_code,422)
                self.assertEqual(resolve.call_count,1)
                db.users.find_one.return_value={'id':'student','is_disabled':True}
                self.assertEqual((await client.post('/api/numerology/vedic/location',json=COORDS)).status_code,401)
        self.assertEqual({call[0] for call in db.mock_calls},{'users.find_one'})

    async def test_lookup_deadline_is_sanitized(self):
        db=Mock();db.users.find_one=AsyncMock(return_value={'id':'student'})
        def timeout(awaitable,**kwargs):
            awaitable.close()
            raise asyncio.TimeoutError()
        with patch('services.vedic_calculations.asyncio.wait_for',side_effect=timeout),self.assertRaises(HTTPException) as error:
            await VedicCalculations(db).location('student',LocationInput(**COORDS))
        self.assertEqual(error.exception.status_code,503)


class GatewayLocationTests(unittest.TestCase):
    def test_authenticated_post_only_and_strict_coordinate_contract(self):
        path='/api/numerology/vedic/location'
        self.assertEqual(_route('POST',path),'location')
        self.assertIsNone(_route('GET',path))
        for change in ({'latitude':'47'}, {'longitude':float('nan')}, {'timezone':'UTC'}, {'user_id':'other'}):
            self.assertFalse(_valid_body(path,{**COORDS,**change}))
        self.assertTrue(_valid_body('/api/numerology/vedic',data(location=COORDS).model_dump(mode='json')))
        forwarded=[]
        def upstream(request):
            forwarded.append(request)
            return httpx.Response(200,json={'city':'Кишинёв, Молдова',**COORDS,'timezone':'Europe/Chisinau'})
        with TestClient(create_public_gateway(['https://1.numer.om'],transport=httpx.MockTransport(upstream))) as client:
            self.assertEqual(client.post(path,json=COORDS).status_code,401)
            self.assertEqual(forwarded,[])
            auth={'Authorization':'Bearer synthetic-token'}
            self.assertEqual(client.post(path+'?latitude=47',json=COORDS,headers=auth).status_code,422)
            self.assertEqual(client.post(path,json={**COORDS,'timezone':'UTC'},headers=auth).status_code,422)
            result=client.post(path,json=COORDS,headers=auth)
            self.assertEqual(result.status_code,200)
            self.assertEqual(result.headers['cache-control'],'no-store')
            self.assertEqual(len(forwarded),1)
            self.assertEqual(forwarded[0].url.query,b'')
            self.assertEqual(json.loads(forwarded[0].content),COORDS)


@unittest.skipUnless(os.environ.get('NUMEROM_TEST_MONGO_URL'),'isolated Mongo required')
class LocationReceipts(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client=AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL']);self.db=self.client['numerom_test_location_'+uuid.uuid4().hex]
        await self.db.users.insert_one({'id':'student','credits_remaining':10})
        await self.db.credits_deduction_config.insert_one({'is_active':True,'vedic_daily':1})
        self.service=VedicCalculations(self.db)
    async def asyncTearDown(self):
        await self.client.drop_database(self.db.name);self.client.close()
    async def test_exact_receipt_replay_and_different_coordinates_conflict(self):
        request=data(location=COORDS)
        first=await self.service.calculate('student',request)
        self.assertEqual(first['results']['location'],{**COORDS,'timezone':'Europe/Chisinau'})
        with patch('services.vedic_calculations.build_vedic_report',side_effect=AssertionError('Replay must not rebuild')):
            self.assertEqual(await self.service.calculate('student',request),first)
        changed=data(request_id=request.request_id,location={**COORDS,'latitude':48})
        with self.assertRaises(HTTPException) as error:await self.service.calculate('student',changed)
        self.assertEqual(error.exception.status_code,409)
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],9)
        self.assertEqual(await self.db.credit_transactions.count_documents({}),1)
        self.assertEqual((await self.service.history('student'))['calculations'],[first])
    async def test_lookup_and_failed_location_do_not_bill_or_store(self):
        before=await self.db.users.find_one({'id':'student'})
        with patch('services.vedic_calculations.resolve_location',return_value={'city':'Кишинёв, Молдова',**COORDS,'timezone':'Europe/Chisinau'}):
            await self.service.location('student',LocationInput(**COORDS))
        with self.assertRaises(HTTPException):await self.service.calculate('student',data(location={'latitude':89,'longitude':0}))
        self.assertEqual(await self.db.users.find_one({'id':'student'}),before)
        self.assertEqual(await self.db.numerology_calculations.count_documents({}),0)
        self.assertEqual(await self.db.credit_transactions.count_documents({}),0)
    async def test_pre_gps_manual_receipt_fingerprint_replays_unchanged(self):
        request=data()
        body=request.model_dump(mode='json',exclude={'request_id'})
        self.assertNotIn('location',body)
        fingerprint=hashlib.sha256(json.dumps(body,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        with patch('services.vedic_calculations.build_vedic_report',return_value={'legacy':{},'version':1,'kind':'schedule'}):
            first=await self.service.calculate('student',request)
        user=await self.db.users.find_one({'id':'student'})
        self.assertEqual(user['vedic_requests'][first['id']],fingerprint)
        with patch('services.vedic_calculations.build_vedic_report',side_effect=AssertionError('Replay must not rebuild')):
            self.assertEqual(await self.service.calculate('student',data(request_id=request.request_id,location=None)),first)
