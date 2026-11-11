import asyncio
from datetime import datetime, timedelta
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from services.admin_reports import AdminReports, ReportRetry
from services.full_reports import FullReports
from services.report_insights import ReportInsights
from services.report_files import digest
from public_gateway import _route, _valid_body


class Contracts(unittest.TestCase):
    def test_gateway_and_bounded_retry_fields(self):
        path='/api/admin/mobile/reports/'+'a'*64+'/retry'
        body={'request_id':str(uuid.uuid4()),'expected_revision':1,'reason':'Повтор после исправления сервера'}
        self.assertEqual(_route('POST',path),'write')
        self.assertEqual(_route('GET','/api/admin/mobile/reports'),'read')
        self.assertIsNone(_route('DELETE',path))
        self.assertTrue(_valid_body(path,body))
        for patch in ({'amount_total':0},{'user_id':'victim'},{'expected_revision':True},{'expected_revision':0},{'reason':' '},{'request_id':str(uuid.uuid1())}):
            self.assertFalse(_valid_body(path,{**body,**patch}))

    def test_inspection_of_unprepared_report_does_not_create_queue(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)/'insights'
            service=AdminReports(SimpleNamespace(users=None),reports=SimpleNamespace(),insights=ReportInsights(root),movies=Mock())
            stages=service.stages({'state':'paid','report':{'version':1,'sections':[]}})
            self.assertEqual(stages['analysis']['status'],'preparing')
            self.assertFalse(root.exists())
            service.movies.state.assert_not_called()


@unittest.skipUnless(os.environ.get('NUMEROM_TEST_MONGO_URL'),'isolated Mongo required')
class AdminReportOperations(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client=AsyncIOMotorClient(os.environ['NUMEROM_TEST_MONGO_URL'],serverSelectionTimeoutMS=3000)
        self.db=self.client['numerom_test_admin_reports_'+uuid.uuid4().hex]
        await self.db.users.insert_many([{'id':'admin','is_admin':True},{'id':'student','name':'Anna','email':'anna@example.invalid','credits_remaining':17},{'id':'blocked','is_admin':True,'is_disabled':True}])
        self.movies=SimpleNamespace(status=AsyncMock(return_value={'status':'waiting_analysis'}))
        self.reports=SimpleNamespace(config=SimpleNamespace(live=False),revision_filter=FullReports.revision_filter)
        self.s=AdminReports(self.db,reports=self.reports,movies=self.movies)
        self.order={'_id':'a'*64,'user_id':'student','state':'paid','livemode':False,'revision':1,'birth_date':'01.02.1990','created_at':datetime.utcnow(),'amount_total':666,'currency':'eur','session_id':'private-session','profile_snapshot':{'private':'address'}}
        await self.db.full_report_orders.insert_one(dict(self.order))

    async def asyncTearDown(self):
        await self.client.drop_database(self.db.name)
        self.client.close()

    def body(self,**changes):
        return ReportRetry(**{'request_id':uuid.uuid4(),'expected_revision':1,'reason':'Сервер исправлен',**changes})

    async def test_roles_and_disabled_accounts_cannot_read_or_retry(self):
        for actor in ('student','blocked','missing'):
            for operation in (lambda:self.s.list(actor),lambda:self.s.retry(actor,self.order['_id'],self.body())):
                with self.assertRaises(HTTPException) as raised:await operation()
                self.assertEqual(raised.exception.status_code,403)
        self.movies.status.assert_not_awaited()
        self.assertNotIn('admin_retry',await self.db.full_report_orders.find_one({'_id':self.order['_id']}))

    async def test_pagination_search_and_no_private_report_content(self):
        for i in range(12):
            await self.db.full_report_orders.insert_one({**self.order,'_id':f'{i:064x}','created_at':datetime.utcnow()+timedelta(seconds=i)})
        page=await self.s.list('admin','Anna','paid',2,10)
        self.assertEqual((page['total'],len(page['reports'])),(13,3))
        row=page['reports'][0]
        self.assertEqual((row['amount_total'],row['user']['name']),(666,'Anna'))
        self.assertNotIn('session_id',row);self.assertNotIn('profile_snapshot',row)
        self.assertEqual(row['analysis']['status'],'not_started')
        self.movies.status.assert_not_awaited()
        self.assertEqual((await self.s.list('admin','does-not-exist'))['total'],0)

    async def test_retry_is_audited_idempotent_without_payment_or_credit_mutation(self):
        request=self.body()
        await self.s.retry('admin',self.order['_id'],request)
        await self.s.retry('admin',self.order['_id'],request)
        self.movies.status.assert_awaited_once_with('student',self.order['_id'],retry=True)
        row=await self.db.full_report_orders.find_one({'_id':self.order['_id']})
        self.assertEqual(row['admin_retry']['status'],'done')
        self.assertEqual(len(row['admin_audit']),1)
        self.assertEqual((row['amount_total'],row['state']),(666,'paid'))
        self.assertEqual((await self.db.users.find_one({'id':'student'}))['credits_remaining'],17)
        with self.assertRaises(HTTPException) as raised:
            await self.s.retry('admin',self.order['_id'],request.model_copy(update={'reason':'Иная причина'}))
        self.assertEqual(raised.exception.status_code,409)

    async def test_failure_retains_same_receipt_for_safe_retry_and_new_attempt_is_limited(self):
        request=self.body();self.movies.status.side_effect=[RuntimeError('transient'),{'status':'queued'}]
        with self.assertRaises(HTTPException) as raised:await self.s.retry('admin',self.order['_id'],request)
        self.assertEqual(raised.exception.status_code,503)
        with self.assertRaises(HTTPException) as raised:await self.s.retry('admin',self.order['_id'],self.body())
        self.assertEqual(raised.exception.status_code,429)
        await self.s.retry('admin',self.order['_id'],request)
        row=await self.db.full_report_orders.find_one({'_id':self.order['_id']})
        self.assertEqual((row['admin_retry']['status'],len(row['admin_audit'])),('done',1))

    async def test_wrong_revision_unpaid_other_mode_do_not_queue(self):
        for change in ({'revision':2},{'state':'pending'},{'livemode':True}):
            await self.db.full_report_orders.replace_one({'_id':self.order['_id']},{**self.order,**change})
            with self.assertRaises(HTTPException) as raised:await self.s.retry('admin',self.order['_id'],self.body())
            self.assertEqual(raised.exception.status_code,409)
        self.movies.status.assert_not_awaited()

    async def test_competing_admin_requests_only_claim_once(self):
        results=await asyncio.gather(*(self.s.retry('admin',self.order['_id'],self.body()) for _ in range(2)),return_exceptions=True)
        self.assertEqual(sum(isinstance(r,dict) for r in results),1)
        self.assertEqual(self.movies.status.await_count,1)
        self.assertEqual(len((await self.db.full_report_orders.find_one({'_id':self.order['_id']}))['admin_audit']),1)

if __name__=='__main__':unittest.main()
