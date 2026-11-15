import unittest
from public_gateway import _route, _valid_body


class FullReportGateway(unittest.TestCase):
    def test_only_reviewed_report_routes_pass(self):
        order = 'a' * 64
        for path in ['/api/full-reports/catalog', '/api/full-reports/history', f'/api/full-reports/{order}', f'/api/full-reports/{order}/narration']:
            self.assertEqual(_route('GET', path), 'read')
        self.assertEqual(_route('POST', '/api/full-reports/checkout'), 'checkout')
        self.assertEqual(_route('POST', '/api/full-reports/preview'), 'read')
        self.assertEqual(_route('POST', f'/api/full-reports/{order}/extend-profile'), 'write')
        self.assertEqual(_route('GET', f'/api/full-reports/{order}/revisions/1'), 'read')
        self.assertIsNone(_route('GET', f'/api/full-reports/{order}/revisions/0'))
        self.assertIsNone(_route('POST', f'/api/full-reports/{order}/revisions/1'))
        self.assertEqual(_route('POST', f'/api/full-reports/{order}/cancel'), 'checkout')
        self.assertEqual(_route('POST', f'/api/full-reports/{order}/narration/full-report-summary/access'), 'write')
        self.assertEqual(_route('GET', f'/api/full-reports/{order}/video'), 'read')
        self.assertEqual(_route('POST', f'/api/full-reports/{order}/video'), 'write')
        self.assertEqual(_route('DELETE', f'/api/full-reports/{order}'), 'write')
        self.assertIsNone(_route('DELETE', '/api/full-reports/all'))
        for method in ('GET', 'HEAD'):
            self.assertEqual(_route(method, '/api/student/report-video/signed.example.token'), 'media')
        self.assertIsNone(_route('POST', '/api/student/report-video/signed.example.token'))
        self.assertIsNone(_route('GET', '/api/student/report-video/../../secret'))
        for method, path in [('GET','/api/full-reports/all'), ('POST',f'/api/full-reports/{order}/paid')]:
            self.assertIsNone(_route(method, path))

    def test_no_price_override_arbitrary_text_or_extra_fields(self):
        body = {'birth_date':'29.02.2000','request_id':'04df42a9-faca-478c-8040-35fe80fa2c7a','client':'mobile'}
        self.assertTrue(_valid_body('/api/full-reports/checkout', body))
        for change in [{'amount_total':1}, {'birth_date':'29.02.2001'}, {'client':'unknown'}]:
            self.assertFalse(_valid_body('/api/full-reports/checkout', {**body,**change}))
        path='/api/full-reports/'+'a'*64+'/narration/full-report-summary/access'
        self.assertTrue(_valid_body(path, {}))
        self.assertFalse(_valid_body(path, {'text':'client supplied text'}))
        path='/api/full-reports/'+'a'*64+'/video'
        self.assertTrue(_valid_body(path, {}))
        self.assertFalse(_valid_body(path, {'url': 'https://external.example/video'}))

    def test_profile_preview_and_extension_do_not_accept_client_calculations_or_price(self):
        preview='/api/full-reports/preview'
        self.assertTrue(_valid_body(preview, {'birth_date':'29.02.2000','use_profile':True}))
        self.assertFalse(_valid_body(preview, {'birth_date':'29.02.2000','user_id':'someone-else'}))
        path='/api/full-reports/'+'a'*64+'/extend-profile'
        body={'profile_fingerprint':'b'*64,'expected_revision':1}
        self.assertTrue(_valid_body(path, body))
        for change in ({'profile_fingerprint':'invalid'}, {'expected_revision':0}, {'amount_total':0}, {'report':{}}):
            self.assertFalse(_valid_body(path, {**body,**change}))


if __name__=='__main__':unittest.main()
