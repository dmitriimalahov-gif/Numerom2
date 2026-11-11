"""Provider migration contracts; temporary artifacts and mocked HTTP only."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

import test_report_insights as fixtures
from services.report_files import digest, folder, read_json, write_json
from services.report_insights import ReportInsights, VERSION, compose

STRATA = {'NUMEROM_REPORT_OLLAMA_BASE_URL': 'http://127.0.0.1:11437/',
          'NUMEROM_REPORT_OLLAMA_MODEL': 'qwen3.8-flash-next-iq3_s',
          'NUMEROM_REPORT_TRANSPORT_PROVIDER': 'strata'}

class StrataTransport(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = fixtures.report()
        self.service = ReportInsights(self.root)

    def http(self):
        client, requests = fixtures.LocalGeneration.inference_client(self, self.source)
        context = AsyncMock()
        context.__aenter__.return_value = client
        return client, requests, context

    async def test_strata_uses_bridge_and_preserves_legacy_checkpoint_for_rollback(self):
        target = folder(self.root, digest(VERSION, self.source))
        write_json(target / 'checkpoint.json', {'legacy': 'accepted work retained'})
        before = (target / 'checkpoint.json').read_bytes()
        client, requests, context = self.http()
        with patch.dict(os.environ, STRATA), patch('services.report_insights.httpx.AsyncClient', return_value=context):
            generated = await self.service.generate(self.source)
        self.assertEqual(generated.get('transport_provider'), 'strata')
        self.assertEqual(generated['provider'], 'ollama')  # native protocol/cache compatibility
        self.assertEqual(generated['model'], 'qwen3.8-flash-next-iq3_s')
        self.assertEqual(generated['result'], fixtures.result_for(self.source))
        self.assertTrue(all(call.args[0] == 'http://127.0.0.1:11437/api/chat' for call in client.post.call_args_list))
        self.assertTrue(all(request['model'] == 'qwen3.8-flash-next-iq3_s' for request in requests))
        self.assertEqual((target / 'checkpoint.json').read_bytes(), before)
        self.assertEqual(read_json(target / 'checkpoint-strata.json')['transport_provider'], 'strata')
        client.post.side_effect = AssertionError('accepted Strata checkpoint must not repeat inference')
        with patch.dict(os.environ, STRATA), patch('services.report_insights.httpx.AsyncClient', return_value=context):
            resumed = await self.service.generate(self.source)
        self.assertEqual(resumed['eval_count'], 0)
        self.assertEqual(resumed['result'], generated['result'])

    async def test_strata_provenance_survives_ready_cache_and_composition(self):
        target = folder(self.root, digest(VERSION, self.source))
        write_json(target / 'ready.json', {'key': target.name, 'provider': 'ollama',
            'transport_provider': 'strata', 'model': 'qwen3.8-flash-next-iq3_s', 'result': fixtures.result_for(self.source)})
        report, state = self.service.enrich(self.source)
        self.assertEqual(state, 'ready')
        self.assertEqual(report['interpretation'].get('transport_provider'), 'strata')
        self.assertIn('Strata', report['sections'][0]['method'])
        self.assertNotIn('локальной', report['sections'][0]['method'])
        self.assertNotIn('Ollama', report['sections'][0]['method'])

    async def test_legacy_cache_keeps_exact_old_report_when_environment_changes(self):
        target = folder(self.root, digest(VERSION, self.source))
        result = fixtures.result_for(self.source)
        write_json(target / 'ready.json', {'key': target.name, 'provider': 'ollama', 'model': 'qwen3.5:9b', 'result': result})
        old = compose(self.source, result, 'qwen3.5:9b')
        with patch.dict(os.environ, STRATA):
            report, state = self.service.enrich(self.source)
        self.assertEqual((report, state), (old, 'ready'))
        self.assertNotIn('transport_provider', report['interpretation'])

    async def test_configuration_rejects_nonlocal_url_credentials_and_unknown_provider(self):
        client, _, context = self.http()
        invalid = [{'NUMEROM_REPORT_OLLAMA_BASE_URL': value} for value in
            ['https://remote.invalid', 'http://user:secret@127.0.0.1:11437',
             'http://127.0.0.1:11437/path', 'http://127.0.0.1:11437/?token=secret']]
        invalid.append({'NUMEROM_REPORT_TRANSPORT_PROVIDER': 'unknown'})
        for extra in invalid:
            with self.subTest(extra=extra), patch.dict(os.environ, {**STRATA, **extra}), \
                    patch('services.report_insights.httpx.AsyncClient', return_value=context), self.assertRaises(ValueError):
                await self.service.generate(self.source)
        self.assertEqual(client.post.call_count, 0)
