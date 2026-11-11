"""Business gateway policy, synthetic transport only."""
import sys
import unittest
import base64
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
from starlette.testclient import TestClient
from public_gateway import create_public_gateway,_route

class BusinessGatewayTests(unittest.TestCase):
    def setUp(self):
        self.forwarded=[]
        self.clock=0
        async def upstream(request):
            self.forwarded.append(request)
            return httpx.Response(200,json={'ok':True})
        self.client=TestClient(create_public_gateway(['https://dmitriimalahov-gif.github.io'],transport=httpx.MockTransport(upstream),clock=lambda:self.clock))
        self.addCleanup(self.client.close)
        self.auth={'Authorization':'Bearer synthetic'}

    def test_exact_routes_and_methods_require_authentication(self):
        for method,path in [('GET','/api/business'),('GET','/api/business/template'),('POST','/api/business/activate'),('POST','/api/business/import/preview'),('POST','/api/business/import'),('POST','/api/business/groups'),('PATCH','/api/business/employees/a'),('POST','/api/business/employees/a/remove'),('POST','/api/business/groups/a/remove'),('GET','/api/business/groups/a/report')]:
            with self.subTest(path=path):self.assertEqual(self.client.request(method,path,json={} if method!='GET' else None).status_code,401)
        self.assertEqual(self.forwarded,[])
        for method,path in [('DELETE','/api/business'),('GET','/api/business/admin'),('PATCH','/api/business/groups/a'),('GET','/api/business/groups/a/report/extra')]:
            self.assertIsNone(_route(method,path))

    def test_cannot_supply_owner_or_bypass_revision(self):
        for path,body in [('/api/business/activate',{'company_name':'Synthetic','user_id':'victim'}),('/api/business/groups/a/remove',{}),('/api/business/import',{'employees':[],'expected_revision':0,'request_id':'testing-123','owner':'victim'})]:
            self.assertEqual(self.client.post(path,json=body,headers=self.auth).status_code,422)
        self.assertEqual(self.client.get('/api/business?user_id=victim',headers=self.auth).status_code,422)
        self.assertEqual(self.forwarded,[])
        self.assertEqual(self.client.post('/api/business/activate',json={'company_name':'Synthetic'},headers=self.auth).status_code,200)

    def test_file_preview_over_default_body_limit_is_forwarded_only_to_import(self):
        body={'filename':'test.csv','content_base64':base64.b64encode(b'Name;Surname\n'+b'A;B\n'*10000).decode()}
        self.assertEqual(self.client.post('/api/business/import/preview',json=body,headers=self.auth).status_code,200)
        self.assertEqual(len(self.forwarded),1)
        self.assertEqual(self.client.post('/api/business/activate',json=body,headers=self.auth).status_code,422)
        self.assertEqual(self.client.post('/api/auth/login',json=body).status_code,413)

    def test_file_size_and_rate_limit_are_bounded(self):
        self.assertEqual(self.client.post('/api/business/import/preview',content=b'x'*(8*1024*1024+1),headers={**self.auth,'Content-Type':'application/json'}).status_code,413)
        for _ in range(5):self.client.post('/api/business/import/preview',json={},headers=self.auth)
        self.assertEqual(self.client.post('/api/business/import/preview',json={},headers=self.auth).status_code,429)
        self.assertEqual(self.forwarded,[])

    def test_large_employee_edit_and_group_task_fit_bounded_reviewed_routes(self):
        employee={'name':'Тест','surname':'Фикстура','birth_date':None,'department':'','role':'','skills':[f'{i}'+('Я'*70) for i in range(30)],'interests':[f'{i}'+('Я'*70) for i in range(20)],'experience':'Я'*2000,'hours_per_week':None}
        self.assertEqual(self.client.patch('/api/business/employees/test',json={'employee':employee,'expected_revision':0},headers=self.auth).status_code,200)
        self.assertEqual(self.client.post('/api/business/groups',json={'expected_revision':0,'group':{'name':'Тест','task':'Я'*2000,'required_skills':employee['skills'],'target_hours':None,'member_ids':[]}},headers=self.auth).status_code,200)
