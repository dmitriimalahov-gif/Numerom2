"""Server-made report PDFs: gateway contract, isolation guard, cache, owner-bound links; Chrome is replaced by a stub."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from fastapi import FastAPI, HTTPException
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from auth import get_current_user
from public_gateway import _route, _valid_body
from routers.report_pdf import create_report_pdf_router
from services.report_pdf import MAX_HTML, ReportPdf, ReportPdfRequest, guarded, file_name, link_name

HTML = '<!doctype html><html><head><meta charset="utf-8"><title>Отчёт</title></head><body><h1>Отчёт</h1></body></html>'


def token_of(created):
    return created['url'].split('/report-pdf/')[1].split('/')[0]


class Users:
    def __init__(self, **users):
        self.users = users

    async def find_one(self, query, projection=None):
        return self.users.get(query['id'])


class Db:
    def __init__(self, **users):
        self.users = Users(**users)


class GatewayTests(unittest.TestCase):
    def test_only_the_upload_and_signed_download_pass(self):
        self.assertEqual(_route('POST', '/api/report-pdf'), 'pdf')
        for method in ('GET', 'HEAD'):
            self.assertEqual(_route(method, '/api/student/report-pdf/signed.example.token'), 'media')
        self.assertIsNone(_route('GET', '/api/report-pdf'))
        self.assertIsNone(_route('POST', '/api/student/report-pdf/signed.example.token'))
        self.assertIsNone(_route('GET', '/api/student/report-pdf/../../secret'))
        # The file name may end the link; it never opens another path.
        self.assertEqual(_route('GET', '/api/student/report-pdf/signed.example.token/10.01.1982-Ivan-Petrov.pdf'), 'media')
        for path in ['/api/student/report-pdf/../secret.pdf', '/api/student/report-pdf/token/../x.pdf',
                     '/api/student/report-pdf/token/name.html', '/api/student/report-pdf/token/a/b.pdf']:
            self.assertIsNone(_route('GET', path), path)

    def test_body_is_html_only(self):
        self.assertTrue(_valid_body('/api/report-pdf', {'html': HTML}))
        self.assertTrue(_valid_body('/api/report-pdf', {'html': HTML, 'filename': '10.01.1982 Иван Петров — полный разбор'}))
        for body in [{}, {'html': ''}, {'html': HTML, 'url': 'https://example.com'}, {'html': 'x' * (MAX_HTML + 1)}, {'html': 5},
                     {'html': HTML, 'filename': ''}, {'html': HTML, 'filename': 'x' * 121}]:
            self.assertFalse(_valid_body('/api/report-pdf', body))


class GuardTests(unittest.TestCase):
    def test_policy_goes_first_in_head_or_in_front(self):
        result = guarded(HTML)
        self.assertLess(result.index("default-src 'none'"), result.index('<meta charset'))
        self.assertTrue(guarded('<p>без head</p>').startswith('<meta http-equiv="Content-Security-Policy"'))


class ServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        secret = patch.dict(os.environ, {'SECRET_KEY': 'synthetic-report-pdf-test-key-' * 3}); secret.start(); self.addCleanup(secret.stop)
        self.renders = []
        def renderer(html, target):
            self.renders.append(html); target.mkdir(parents=True, exist_ok=True)
            (target / 'report.pdf').write_bytes(b'%PDF-1.4 synthetic')
        self.db = Db(owner={'id': 'owner', 'auth_version': 2})
        self.service = ReportPdf(self.db, self.root, 'https://api.numerom.test', renderer)

    async def test_same_document_renders_once_and_link_opens_it(self):
        first = await self.service.create('owner', ReportPdfRequest(html=HTML))
        second = await self.service.create('owner', ReportPdfRequest(html=HTML))
        self.assertEqual(len(self.renders), 1)
        self.assertTrue(first['url'].startswith('https://api.numerom.test/api/student/report-pdf/'))
        path, name = await self.service.resolve(token_of(second))
        self.assertEqual(path.read_bytes(), b'%PDF-1.4 synthetic')
        self.assertEqual(name, 'NumerOM-report.pdf')

    async def test_the_file_is_named_after_the_person_and_date(self):
        created = await self.service.create('owner', ReportPdfRequest(html=HTML, filename='10.01.1982 Дмитрий Малахов — полный разбор'))
        self.assertEqual(created['filename'], '10.01.1982 Дмитрий Малахов — полный разбор.pdf')
        self.assertTrue(created['url'].endswith('/10.01.1982-Dmitriy-Malakhov-polnyy-razbor.pdf'))
        self.assertEqual((await self.service.resolve(token_of(created)))[1], '10.01.1982 Дмитрий Малахов — полный разбор.pdf')
        self.assertEqual(len(self.renders), 1, 'the name does not change the cached document')

    def test_names_cannot_leave_the_file_or_break_the_link(self):
        self.assertEqual(file_name('../../etc/passwd'), 'etc passwd')
        self.assertEqual(file_name('a\r\nb:"c"'), 'a b c')
        self.assertEqual(file_name('  ...  '), 'NumerOM-report')
        self.assertEqual(link_name('Отчёт «Ёлка»'), 'Otchet-Elka.pdf')
        self.assertEqual(link_name('—'), 'NumerOM-report.pdf')

    async def test_links_are_bound_to_the_account_session(self):
        token = token_of(await self.service.create('owner', ReportPdfRequest(html=HTML)))
        for broken in [token[:-2] + 'xx', 'not.a.token']:
            with self.assertRaises(HTTPException) as caught:
                await self.service.resolve(broken)
            self.assertEqual(caught.exception.status_code, 401)
        self.db.users.users['owner']['auth_version'] = 3
        with self.assertRaises(HTTPException) as caught:
            await self.service.resolve(token)
        self.assertEqual(caught.exception.status_code, 401)

    async def test_failed_render_and_missing_public_address_are_reported(self):
        def broken(html, target):
            raise RuntimeError('chrome exited')
        with self.assertRaises(HTTPException) as caught:
            await ReportPdf(self.db, self.root, 'https://api.numerom.test', broken).create('owner', ReportPdfRequest(html=HTML))
        self.assertEqual(caught.exception.status_code, 503)
        with self.assertRaises(HTTPException) as caught:
            await ReportPdf(self.db, self.root, 'http://api.numerom.test', broken).create('owner', ReportPdfRequest(html=HTML))
        self.assertEqual(caught.exception.status_code, 503)
        with self.assertRaises(HTTPException) as caught:
            await self.service.create('stranger', ReportPdfRequest(html=HTML))
        self.assertEqual(caught.exception.status_code, 401)

    async def test_route_returns_an_inline_pdf(self):
        app = FastAPI(); app.dependency_overrides[get_current_user] = lambda: {'user_id': 'owner'}
        app.include_router(create_report_pdf_router(self.db, self.service))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='https://test.invalid') as client:
            created = await client.post('/api/report-pdf', json={'html': HTML, 'filename': '10.01.1982 Иван Петров'})
            self.assertEqual(created.status_code, 200)
            for path in [created.json()['url'].split('/api/')[1], 'student/report-pdf/' + token_of(created.json())]:
                opened = await client.get('/api/' + path)
                self.assertEqual(opened.status_code, 200)
                self.assertEqual(opened.headers['content-type'], 'application/pdf')
                self.assertEqual(opened.headers['content-disposition'], "inline; filename*=UTF-8''10.01.1982%20%D0%98%D0%B2%D0%B0%D0%BD%20%D0%9F%D0%B5%D1%82%D1%80%D0%BE%D0%B2.pdf")
            self.assertEqual((await client.post('/api/report-pdf', json={'html': HTML, 'extra': 1})).status_code, 422)


if __name__ == '__main__':
    unittest.main()
