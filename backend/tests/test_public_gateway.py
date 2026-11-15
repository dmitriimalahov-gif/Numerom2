"""Public gateway HTTP policy with an isolated HTTP transport, no live requests."""
import sys
import unittest
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
from starlette.testclient import TestClient
from public_gateway import create_public_gateway

ORIGIN = 'https://1.numer.om'


class PublicGatewayContracts(unittest.TestCase):
    def test_new_paid_calculations_and_materials_have_reviewed_routes(self):
        from domain.assessment import public_questions
        from public_gateway import _route, _valid_body
        for name in ('personal','assessment'):
            self.assertEqual(_route('POST','/api/numerology/'+name),'relationships')
            self.assertIsNone(_route('DELETE','/api/numerology/'+name))
            self.assertFalse(_valid_body('/api/numerology/'+name,{'user_id':'victim'}))
        body={'kind':'assessment','request_id':str(uuid.uuid4()),'expected_cost':1,'answers':{q['id']:q['options'][0]['id'] for q in public_questions()}}
        self.assertTrue(_valid_body('/api/numerology/assessment',body))
        self.assertFalse(_valid_body('/api/numerology/assessment',{**body,'score':100}))
        self.assertEqual(self.client.post('/api/numerology/assessment',json=body).status_code,401)
        self.assertEqual(self.forwarded,[])
        self.assertEqual(self.client.post('/api/numerology/assessment',json=body,headers={'Authorization':'Bearer test'}).status_code,200)
        root='/api/admin/mobile/lessons/lesson/materials'
        self.assertEqual(_route('POST',root),'attachment_upload')
        self.assertEqual(_route('GET',root+'/file/access'),'read')
        self.assertIsNone(_route('DELETE',root+'/file'))
        self.assertFalse(_valid_body(root,{'name':'file.pdf','path':'/etc/passwd'}))
        self.assertFalse(_valid_body(root+'/file',{'user_id':'victim','is_active':True}))

    def setUp(self):
        self.forwarded = []
        self.clock = 0
        self.upstream_status = 200
        self.upstream_json = {'ok': True}
        async def upstream(request):
            self.forwarded.append(request)
            return httpx.Response(self.upstream_status, json=self.upstream_json, headers={
                'Access-Control-Allow-Origin': '*', 'Set-Cookie': 'private=hidden',
                'Location': 'https://untrusted.example/redirect',
            })
        self.transport = httpx.MockTransport(upstream)
        self.app = create_public_gateway([ORIGIN], transport=self.transport, clock=lambda: self.clock)
        self.client = TestClient(self.app)
        self.addCleanup(self.client.close)

    def test_profile_forwards_only_authorized_route_and_controls_response_headers(self):
        response = self.client.get('/api/user/profile-v2', headers={
            'Origin': ORIGIN, 'Authorization': 'Bearer synthetic-token',
            'X-Forwarded-For': 'attacker-spoof', 'Cookie': 'must-not-forward',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['access-control-allow-origin'], ORIGIN)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertNotIn('set-cookie', response.headers)
        self.assertNotIn('location', response.headers)
        self.assertEqual(str(self.forwarded[0].url), 'http://127.0.0.1:8000/api/user/profile-v2')
        self.assertEqual(self.forwarded[0].headers['authorization'], 'Bearer synthetic-token')
        self.assertNotIn('cookie', self.forwarded[0].headers)
        self.assertNotEqual(self.forwarded[0].headers.get('x-forwarded-for'), 'attacker-spoof')

    def test_admin_legacy_docs_uploads_and_unapproved_writes_are_hidden(self):
        for method, path in (
            ('GET', '/docs'), ('GET', '/openapi.json'), ('GET', '/api/admin/users'),
            ('POST', '/api/auth/login-v2'), ('GET', '/uploads/private.pdf'),
            ('POST', '/api/student/time-activity'),
            ('POST', '/api/student/challenge-progress'), ('DELETE', '/api/user/profile-v2'),
            ('GET', '/api/learning-v2/lessons/a%2fb'),
        ):
            with self.subTest(method=method, path=path):
                self.assertEqual(self.client.request(method, path).status_code, 404)
        self.assertEqual(self.forwarded, [])

    def test_guest_reads_shared_guide_narration_but_not_the_account_catalog(self):
        self.assertEqual(self.client.get('/api/public/narration/project').status_code, 200)
        self.assertEqual(str(self.forwarded[0].url), 'http://127.0.0.1:8000/api/public/narration/project')
        self.assertEqual(self.client.get('/api/public/narration/project?clip=soul').status_code, 422)
        self.assertEqual(self.client.get('/api/narration/project').status_code, 401)
        self.assertEqual(self.client.post('/api/public/narration/project').status_code, 404)
        self.assertEqual(len(self.forwarded), 1)

    def test_checkout_requires_login_and_server_owned_catalog(self):
        self.assertEqual(self.client.post('/api/payments/checkout/session').status_code,401)
        self.assertEqual(self.client.post('/api/payments/checkout/session',headers={'Authorization':'Bearer synthetic-token'},json={'package_type':'one_time','credits':999999}).status_code,422)
        self.assertEqual(self.forwarded, [])

    def test_saved_calculation_is_read_only_scoped_by_backend_identity(self):
        path = '/api/numerology/personal-numbers/latest'
        self.assertEqual(self.client.get(path).status_code, 401)
        auth = {'Authorization': 'Bearer synthetic-token'}
        self.assertEqual(self.client.get(path, headers=auth).status_code, 200)
        self.assertEqual(self.client.get(path+'?user_id=other', headers=auth).status_code, 422)
        self.assertEqual(self.client.post(path, headers=auth, json={}).status_code, 404)
        self.assertEqual(len(self.forwarded), 1)

    def test_only_exact_https_origins_and_known_preflight_headers_are_allowed(self):
        for invalid in ([], ['*'], ['http://public.example'], ['https://public.example/path']):
            with self.assertRaises(ValueError):
                create_public_gateway(invalid, transport=self.transport)
        self.assertEqual(self.client.get('/api/user/profile-v2', headers={'Origin': 'https://evil.example'}).status_code, 403)
        preflight = {'Origin': ORIGIN, 'Access-Control-Request-Method': 'GET',
                     'Access-Control-Request-Headers': 'authorization,content-type'}
        self.assertEqual(self.client.options('/api/user/profile-v2', headers=preflight).status_code, 204)
        self.assertEqual(self.client.options('/api/user/profile-v2', headers={**preflight, 'Access-Control-Request-Headers': 'x-evil'}).status_code, 403)
        self.assertEqual(self.forwarded, [])

    def test_registration_validates_whitelisted_fields_and_date_before_forwarding(self):
        valid = {'email': 'person@example.invalid', 'password': 'valid-password',
                 'full_name': 'Anna', 'birth_date': '02.03.1990'}
        for changes in ({'is_admin': True}, {'birth_date': '31.02.1990'}, {'password': 'x'}, {'email': 'not-an-email'}):
            self.clock += 3601
            self.assertEqual(self.client.post('/api/auth/register', json={**valid, **changes}).status_code, 422)
        self.clock += 3601
        self.assertEqual(self.client.post('/api/auth/register', json=valid).status_code, 200)
        self.assertEqual(len(self.forwarded), 1)

    def test_body_size_encoding_and_personal_date_are_checked_before_upstream(self):
        self.assertEqual(self.client.post('/api/auth/login', content=b'x' * 17000,
                                         headers={'Content-Type': 'application/json'}).status_code, 413)
        self.assertEqual(self.client.post('/api/auth/login', content=b'x', headers={
            'Content-Type': 'application/json', 'Content-Encoding': 'gzip'}).status_code, 415)
        auth = {'Authorization': 'Bearer synthetic-token'}
        self.assertEqual(self.client.post('/api/numerology/personal-numbers?birth_date=31.02.1990', headers=auth).status_code, 422)
        self.assertEqual(self.client.post('/api/numerology/personal-numbers?birth_date=02.03.1990&user_id=victim', headers=auth).status_code, 422)
        self.assertEqual(self.forwarded, [])
        self.assertEqual(self.client.post('/api/numerology/personal-numbers?birth_date=02.03.1990', headers=auth).status_code, 200)

    def test_login_rate_limit_does_not_forward_excess_attempt(self):
        payload = {'email': 'person@example.invalid', 'password': 'test-password'}
        for _ in range(8):
            self.assertEqual(self.client.post('/api/auth/login', json=payload).status_code, 200)
        self.assertEqual(self.client.post('/api/auth/login', json=payload).status_code, 429)
        self.assertEqual(len(self.forwarded), 8)
        self.clock = 61
        self.assertEqual(self.client.post('/api/auth/login', json=payload).status_code, 200)

    def test_redirects_and_internal_or_validation_errors_do_not_escape(self):
        for code in (302, 500):
            self.upstream_status = code
            self.upstream_json = {'detail': '/private/server/secret'}
            result = self.client.post('/api/auth/login', json={'email': 'person@example.invalid', 'password': 'password'})
            self.assertEqual(result.status_code, 502)
            self.assertNotIn('secret', result.text)
            self.assertNotIn('location', result.headers)
        self.upstream_status = 422
        self.upstream_json = {'detail': [{'input': 'password-secret', 'msg': 'invalid'}]}
        result = self.client.post('/api/auth/login', json={'email': 'person@example.invalid', 'password': 'password'})
        self.assertEqual(result.status_code, 422)
        self.assertNotIn('password-secret', result.text)

    def test_reviewed_learning_routes_and_credit_history_have_bounded_contracts(self):
        auth = {'Authorization': 'Bearer synthetic-token'}
        for path in ('/api/student/lesson-progress/lesson', '/api/student/quiz-attempts/lesson',
                     '/api/student/exercise-responses/lesson', '/api/student/lesson-files/lesson',
                     '/api/student/lesson-files/lesson/file/access', '/api/student/lesson-video/lesson/access',
                     '/api/user/credit-history?limit=20&offset=0'):
            self.assertEqual(self.client.get(path, headers=auth).status_code, 200, path)
        for query in ('limit=101', 'offset=-1', 'limit=1&limit=2', 'user_id=victim', 'offset=100001'):
            self.assertEqual(self.client.get('/api/user/credit-history?' + query, headers=auth).status_code, 422)
        self.assertEqual(self.client.post('/api/student/lesson-progress/lesson/theory', headers=auth, json={}).status_code, 200)
        quiz = {'lesson_id': 'lesson', 'quiz_id': 'quiz', 'answers': {'a': 'one'}, 'submission_id': str(uuid.uuid4())}
        self.assertEqual(self.client.post('/api/student/quiz-attempt', headers=auth, json=quiz).status_code, 200)
        self.assertEqual(self.client.post('/api/student/quiz-attempt', headers=auth, json={**quiz, 'passed': True}).status_code, 422)
        self.assertEqual(self.client.post('/api/student/exercise-response', headers=auth, json={
            'lesson_id': 'lesson', 'exercise_id': 'exercise', 'response_text': 'я' * 10000}).status_code, 200)

    def test_media_streams_range_without_bearer_or_upstream_redirects(self):
        async def media(request):
            self.forwarded.append(request)
            return httpx.Response(206, content=b'media-part', headers={
                'Content-Type': 'video/mp4', 'Content-Range': 'bytes 0-9/100',
                'Accept-Ranges': 'bytes', 'Content-Disposition': 'inline',
                'Set-Cookie': 'must-not-escape', 'Location': 'https://evil.invalid'})
        with TestClient(create_public_gateway([ORIGIN], transport=httpx.MockTransport(media))) as client:
            response = client.get('/api/student/media/signed.token.value', headers={'Range': 'bytes=0-9', 'Origin': ORIGIN})
            self.assertEqual(response.status_code, 206)
            self.assertEqual(response.content, b'media-part')
            self.assertEqual(response.headers['content-range'], 'bytes 0-9/100')
            self.assertEqual(self.forwarded[-1].headers['range'], 'bytes=0-9')
            self.assertNotIn('authorization', self.forwarded[-1].headers)
            self.assertNotIn('set-cookie', response.headers)
            self.assertNotIn('location', response.headers)
            self.assertEqual(client.get('/api/student/media/signed.token.value', headers={'Range': 'bytes=0-1,4-5'}).status_code, 422)

    def test_cloudflare_ip_is_only_trusted_for_configured_loopback_peer(self):
        def client_for(peer):
            app = create_public_gateway([ORIGIN], transport=self.transport, trust_cloudflare=True)
            async def with_peer(scope, receive, send):
                await app({**scope, 'client': (peer, 12345)}, receive, send)
            return TestClient(with_peer)
        headers = {'Authorization': 'Bearer synthetic-token', 'CF-Connecting-IP': '203.0.113.8',
                   'X-Forwarded-For': '192.0.2.9'}
        with client_for('127.0.0.1') as client:
            self.assertEqual(client.get('/api/user/profile-v2', headers=headers).status_code, 200)
            self.assertEqual(self.forwarded[-1].headers['x-forwarded-for'], '203.0.113.8')
            self.assertEqual(client.get('/api/user/profile-v2', headers={**headers, 'CF-Connecting-IP': 'malformed'}).status_code, 400)
        with client_for('198.51.100.7') as client:
            self.assertEqual(client.get('/api/user/profile-v2', headers=headers).status_code, 200)
            self.assertEqual(self.forwarded[-1].headers['x-forwarded-for'], '198.51.100.7')

    def test_media_size_and_redirect_guards_and_head(self):
        cases = [(200, {'Content-Length': str(512 * 1024 * 1024 + 1)}, 502),
                 (302, {'Location': 'https://evil.invalid'}, 502),
                 (200, {'Content-Length': '100', 'Content-Type': 'video/mp4'}, 200)]
        for code, headers, expected in cases:
            async def upstream(request):
                return httpx.Response(code, headers=headers)
            with TestClient(create_public_gateway([ORIGIN], transport=httpx.MockTransport(upstream))) as client:
                response = client.head('/api/student/media/signed.token.value')
                self.assertEqual(response.status_code, expected)
                self.assertEqual(response.content, b'')
                if expected == 200:
                    self.assertEqual(response.headers['content-length'], '100')
                self.assertNotIn('location', response.headers)

    def test_json_response_limit_is_enforced(self):
        with TestClient(create_public_gateway([ORIGIN], transport=self.transport, max_response_bytes=4)) as client:
            self.assertEqual(client.get('/api/user/profile-v2', headers={
                'Authorization': 'Bearer synthetic-token'}).status_code, 502)


if __name__ == '__main__':
    unittest.main()
