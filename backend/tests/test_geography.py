import asyncio
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import AsyncMock, patch
import httpx
from fastapi import FastAPI
from models import UserProfileUpdate
from services.accounts import AccountService
from services.geography import CityIndex, normalize
from routers.geography import create_geography_router
from auth import get_current_user


class CityIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory();self.path=Path(self.temp.name)/'cities.sqlite'
        with sqlite3.connect(self.path) as db:
            db.executescript("CREATE TABLE cities(id TEXT PRIMARY KEY,name TEXT,country TEXT,country_code TEXT,region TEXT,label TEXT,latitude REAL,longitude REAL,timezone TEXT,population INTEGER,aliases TEXT); CREATE VIRTUAL TABLE search USING fts5(terms,content='');")
            rows=[('1','Chișinău','Moldova','MD','Chișinău','Chișinău, Moldova',47.,28.,'Europe/Chisinau',500000,'chisinau\nкишинев'),('2','Springfield','United States','US','Illinois','Springfield, Illinois, United States',39.,-89.,'America/Chicago',100000,'springfield'),('3','Springfield','United States','US','Missouri','Springfield, Missouri, United States',37.,-93.,'America/Chicago',200000,'springfield')]
            for row in rows:
                cursor=db.execute('INSERT INTO cities VALUES (?,?,?,?,?,?,?,?,?,?,?)',row)
                db.execute('INSERT INTO search(rowid,terms) VALUES (?,?)',(cursor.lastrowid,normalize(row[10]+' '+row[5])))
        self.index=CityIndex(self.path)
    def tearDown(self):self.temp.cleanup()
    def test_aliases_accents_and_cyrillic_without_external_calls(self):
        for name in ['Chișinău','chisinau','Кишинёв','Кишинев']:
            self.assertEqual(self.index.search(name)[0]['id'],'1')
        self.assertEqual(self.index.lookup('1')['timezone'],'Europe/Chisinau')
    def test_same_name_towns_require_region_and_no_guessed_resolution(self):
        self.assertEqual(len(self.index.search('Springfield')),2)
        self.assertIsNone(self.index.resolve_unique('Springfield'))
        self.assertEqual(self.index.resolve_unique('Springfield, Illinois, United States')['id'],'2')
    def test_city_with_country_written_in_russian_is_verified_not_guessed(self):
        # Profile cities are free text «Город, Страна»; GeoNames keeps country names only in English.
        for query in ['Кишинёв, Молдова','Кишинев, Молдавия','Chișinău, Moldova','Кишинев, MD','Springfield, Illinois','Springfield, Иллинойс']:
            expected=None if query.endswith('Иллинойс') else ('2' if query.startswith('Springfield') else '1')
            self.assertEqual((self.index.resolve_unique(query) or {}).get('id'),expected,query)
        for query in ['Кишинев, Россия','Кишинев, Молдова, Иллинойс','Springfield, США',', Молдова']:
            self.assertIsNone(self.index.resolve_unique(query),query)
    def test_queries_are_bounded_and_readonly(self):
        before=self.path.read_bytes()
        for query in ['x','x'*81,'" OR 1=1 --','*',"') DROP TABLE cities;"]:
            self.index.search(query)
        self.assertEqual(before,self.path.read_bytes())
        self.assertIsNone(self.index.lookup('../1'))
        self.assertEqual(self.index.search('x'*81),[])


class GeographyBoundaryTests(unittest.IsolatedAsyncioTestCase):
    async def test_authentication_and_no_store(self):
        app=FastAPI();app.include_router(create_geography_router())
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
            response=await client.get('/api/geography/cities?q=Paris')
            self.assertIn(response.status_code,(401,403))
            app.dependency_overrides[get_current_user]=lambda:{'user_id':'owner'}
            with patch('routers.geography.city_index.search',return_value=[]) as search:
                response=await client.get('/api/geography/cities?q=Paris')
                self.assertEqual(response.status_code,200);self.assertEqual(response.headers['cache-control'],'private, no-store')
                self.assertEqual(response.json()['items'],[]);search.assert_called_once_with('Paris')
                self.assertEqual((await client.get('/api/geography/cities',params={'q':'x'*81})).status_code,422)
    async def test_selected_city_is_canonical_and_manual_edit_clears_identifier(self):
        users=AsyncMock();users.find_one.return_value={'id':'owner','birth_city':'Old','birth_city_id':'1'}
        service=AccountService(type('DB',(),{'users':users})())
        with patch('services.geography.city_index.lookup',return_value={'label':'City, Region, Country'}):
            await service.update_profile('owner',UserProfileUpdate(birth_city='forged label',birth_city_id='2'))
        update=users.update_one.call_args.args[1]['$set']
        self.assertEqual(update['birth_city'],'City, Region, Country');self.assertEqual(update['birth_city_id'],'2')
        await service.update_profile('owner',UserProfileUpdate(birth_city='Manual village'))
        update=users.update_one.call_args.args[1]['$set'];self.assertEqual(update['birth_city_id'],'')
        self.assertNotIn('city',update)


if __name__=='__main__':unittest.main()
