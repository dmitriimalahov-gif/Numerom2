import sys, unittest, uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
from starlette.testclient import TestClient
from public_gateway import _route,_valid_body,create_public_gateway

class MobileAdminGateway(unittest.TestCase):
    def test_only_explicit_new_admin_routes_are_open(self):
        for path in ('analytics','challenge-notes','settings/planetary-energy','settings/monthly-route','settings/telegram-stars'):
            self.assertEqual(_route('GET','/api/admin/mobile/'+path),'read')
        for path in ('lessons/import','lessons/import/preview','lessons/lesson-1/archive','consultations/c-1/archive','settings/planetary-energy','settings/monthly-route','settings/telegram-stars'):
            self.assertEqual(_route('POST','/api/admin/mobile/'+path),'write')
        for method,path in (('DELETE','lessons/l'),('POST','analytics'),('POST','settings/secrets'),('GET','settings/secrets'),('POST','reports/anything/retry')):
            self.assertIsNone(_route(method,'/api/admin/mobile/'+path))

    def test_import_and_archive_use_their_own_bounded_models(self):
        meta={'request_id':str(uuid.uuid4()),'revision':0,'reason':'Обновление программы'}
        self.assertTrue(_valid_body('/api/admin/mobile/lessons/import/preview',{'text':'Тема урока'}))
        self.assertFalse(_valid_body('/api/admin/mobile/lessons/import/preview',{'text':'x'*200001}))
        self.assertTrue(_valid_body('/api/admin/mobile/lessons/import',{**meta,'text':'Тема','fingerprint':'a'*64}))
        self.assertFalse(_valid_body('/api/admin/mobile/lessons/import',{**meta,'text':'Тема','user_id':'other'}))
        self.assertTrue(_valid_body('/api/admin/mobile/lessons/l/archive',meta))
        self.assertFalse(_valid_body('/api/admin/mobile/consultations/c/archive',{**meta,'delete_files':True}))

    def test_settings_and_reviews_keep_strict_types(self):
        meta={'request_id':str(uuid.uuid4()),'revision':0,'reason':'Настройка'}
        self.assertTrue(_valid_body('/api/admin/mobile/settings/planetary-energy',{**meta,'values':{'friend_planet_bonus':0.1,'anti_cyclicity_enabled':True}}))
        self.assertFalse(_valid_body('/api/admin/mobile/settings/planetary-energy',{**meta,'values':{'friend_planet_bonus':'0.1'}}))
        body={**meta,'admin_comment':'Принято','expected_answer':'a'*64,'points_earned':100}
        self.assertTrue(_valid_body('/api/admin/mobile/responses/r',body))
        self.assertFalse(_valid_body('/api/admin/mobile/responses/r',{**body,'points_earned':101}))
        self.assertFalse(_valid_body('/api/admin/mobile/responses/r',{**body,'points_earned':True}))

    def test_stars_prices_have_bounded_whole_numbers_and_no_secrets(self):
        meta={'request_id':str(uuid.uuid4()),'revision':0,'reason':'Новые цены'}
        path='/api/admin/mobile/settings/telegram-stars'
        self.assertTrue(_valid_body(path,{**meta,'values':{'one_time':0,'full_report':100000}}))
        for values in ({'one_time':-1},{'one_time':100001},{'one_time':True},
                       {'one_time':1.5},{'one_time':'10'},{'bot_token':0},{}):
            with self.subTest(values=values):
                self.assertFalse(_valid_body(path,{**meta,'values':values}))

class MobileAdminForwarding(unittest.TestCase):
    def setUp(self):
        self.forwarded = []
        self.status = 200
        def upstream(request):
            self.forwarded.append(request)
            return httpx.Response(self.status, json={'detail': 'private upstream diagnostic'})
        self.client = TestClient(create_public_gateway(
            ['https://1.numer.om'], transport=httpx.MockTransport(upstream)))
        self.addCleanup(self.client.close)
        self.auth = {'Authorization': 'Bearer synthetic-admin'}

    def test_mobile_admin_filters_reach_upstream_unchanged(self):
        cases = {
            'reports': {'q': 'Иван', 'page': '2', 'page_size': '10', 'state': 'paid'},
            'lessons': {'q': 'Урок', 'page': '1', 'page_size': '25', 'archived': 'active'},
            'consultations': {'q': '', 'page': '3', 'page_size': '25', 'archived': 'all'},
            'responses': {'q': 'Анна', 'page': '1', 'page_size': '25', 'reviewed': 'pending', 'lesson_id': 'l-1', 'user_id': ''},
            'challenge-notes': {'page': '1', 'page_size': '25', 'lesson_id': 'l-1', 'user_id': 'u-1'},
        }
        for kind, params in cases.items():
            with self.subTest(kind=kind):
                response = self.client.get('/api/admin/mobile/' + kind, params=params, headers=self.auth)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(dict(self.forwarded[-1].url.params), params)
                self.assertEqual(self.forwarded[-1].headers['authorization'], self.auth['Authorization'])

    def test_invalid_filters_never_reach_upstream(self):
        cases = [('reports', 'page=0'), ('reports', 'page=10001'), ('reports', 'page_size=21'),
                 ('reports', 'page=1&page=2'), ('reports', 'state=unknown'), ('reports', 'user_id=victim'),
                 ('lessons', 'q=' + 'x'*101), ('lessons', 'archived=deleted'),
                 ('consultations', 'page_size=101'), ('responses', 'reviewed=no'),
                 ('responses', 'lesson_id=../private'), ('challenge-notes', 'sort=secret')]
        for kind, query in cases:
            with self.subTest(kind=kind, query=query):
                result = self.client.get('/api/admin/mobile/' + kind + '?' + query, headers=self.auth)
                self.assertEqual(result.status_code, 422)
        self.assertEqual(self.forwarded, [])
        self.assertEqual(self.client.get('/api/admin/mobile/reports?page=1').status_code, 401)

    def test_readiness_does_not_disclose_upstream_failure(self):
        self.status = 503
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {'status': 'unavailable', 'service': 'numerom'})
        self.assertEqual(response.headers['cache-control'], 'no-store')
        result = self.client.get('/api/admin/mobile/reports', headers=self.auth)
        self.assertEqual(result.status_code, 502)
        self.assertNotIn('private', result.text)

if __name__=='__main__':unittest.main()
