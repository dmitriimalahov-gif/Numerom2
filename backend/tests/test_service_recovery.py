import importlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock
import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'backend'))
import runtime_config as signing
import numerom_services as services
import numerom_watchdog as watchdog
from routers.health import create_health_router
from public_gateway import create_public_gateway

class ServiceRecoveryTests(unittest.TestCase):
    def setUp(self):
        # No test may move the real account's webhook through the runtime path.
        self.stripe_sync = patch.object(watchdog, 'sync_test_webhook', return_value='ready').start()
        self.addCleanup(patch.stopall)

    def test_health_checks_database_and_never_exposes_errors(self):
        db=type('DB',(),{'command':AsyncMock(return_value={'ok':1})})()
        app=FastAPI();app.include_router(create_health_router(db));client=TestClient(app)
        self.assertEqual(client.get('/api/health').json(),{'status':'ok','service':'numerom'})
        db.command.side_effect=RuntimeError('private connection string')
        result=client.get('/api/health')
        self.assertEqual(result.status_code,503)
        self.assertNotIn('private',result.text)

    def test_public_health_is_allowed_without_opening_user_routes(self):
        async def upstream(request): return httpx.Response(200,json={'status':'ok','service':'numerom'})
        client=TestClient(create_public_gateway(['https://dmitriimalahov-gif.github.io'],transport=httpx.MockTransport(upstream)))
        self.assertEqual(client.get('/api/health').status_code,200)
        self.assertEqual(client.post('/api/health').status_code,404)
        self.assertEqual(client.get('/api/user/profile-v2').status_code,401)

    def test_launch_agents_restart_services_without_touching_helper(self):
        for name,args in services.specifications().items():
            plist=services.service_plist(name,args)
            self.assertTrue(plist['Label'].startswith('md.numerom.app.'))
            self.assertNotIn('helper',plist['Label'])
            self.assertTrue(plist['RunAtLoad'])
            if name=='watchdog': self.assertEqual(plist['StartInterval'],60)
            else: self.assertTrue(plist['KeepAlive'])
            # Media workers must not run under launchd's default background throttling.
            if name in ('report-voice','report-video'): self.assertEqual((plist['ProcessType'],plist['Nice']),('Interactive',5))

    def test_voice_service_processes_lessons_and_guides_as_well_as_reports(self):
        command=services.specifications()['report-voice']
        self.assertNotIn('--only-prefix',command)
        self.assertNotIn('--lesson-prefix',command)
        self.assertIn('--watch',command)
        self.assertIn('--reuse-models',command)
        self.assertNotIn('--low-memory',command)

    def test_watchdog_restarts_after_three_failed_checks_without_publishing_dead_endpoint(self):
        state={}
        with patch.object(watchdog,'probe',return_value='unreachable'),patch.object(watchdog,'restart') as restart,patch.object(watchdog,'publish_config') as publish:
            watchdog.check(state);watchdog.check(state);restart.assert_not_called()
            watchdog.check(state);restart.assert_called_once_with('api');publish.assert_not_called()

    def test_database_outage_does_not_loop_restart_alive_api(self):
        state={}
        with patch.object(watchdog,'probe',return_value='database_unavailable'),patch.object(watchdog,'restart') as restart,patch.object(watchdog,'publish_config') as publish:
            for _ in range(5):watchdog.check(state)
            restart.assert_not_called();publish.assert_not_called()
            self.assertEqual(state['waiting_for'],'database')
            self.assertFalse(state['public_ready'])

    def test_database_recovery_replays_startup_once_before_publication(self):
        state={'waiting_for':'database','public_ready':False}
        with patch.object(watchdog,'probe',return_value='ready'), \
                patch.object(watchdog,'restart') as restart, \
                patch.object(watchdog,'tunnel_url',return_value='https://new.trycloudflare.com'), \
                patch.object(watchdog,'update_environment',return_value=False), \
                patch.object(watchdog,'sign_config'), \
                patch.object(watchdog,'publish_config') as publish, \
                patch.object(watchdog,'config_is_live',return_value=True):
            watchdog.check(state)
            restart.assert_called_once_with('api')
            publish.assert_not_called()
            self.assertFalse(state['public_ready'])
            self.assertNotIn('waiting_for',state)
            watchdog.check(state)
            restart.assert_called_once_with('api')
            publish.assert_called_once()
            self.assertTrue(state['public_ready'])

    def test_rotated_live_endpoint_is_signed_and_published_and_deployment_rechecked(self):
        state={}
        with patch.object(watchdog,'probe',return_value='ready'),patch.object(watchdog,'tunnel_url',return_value='https://new.trycloudflare.com'),patch.object(watchdog,'update_environment',side_effect=[True,False]),patch.object(watchdog,'restart') as restart,patch.object(watchdog,'sign_config') as sign,patch.object(watchdog,'publish_config') as publish,patch.object(watchdog,'config_is_live',side_effect=[False,True]):
            watchdog.check(state);self.assertFalse(state['deployment_verified'])
            watchdog.check(state);self.assertTrue(state['deployment_verified'])
            self.assertEqual(state['published'],'https://new.trycloudflare.com')
            restart.assert_called_once_with('api');self.assertEqual(publish.call_count,2)
            sign.assert_called_with('https://new.trycloudflare.com')
            self.stripe_sync.assert_called_with('https://new.trycloudflare.com')
            self.assertEqual(state['stripe_webhook'], 'ready')

    def test_stripe_failure_does_not_block_endpoint_recovery_and_is_retried(self):
        state={}
        self.stripe_sync.side_effect = [RuntimeError('secret must never be logged'), 'ready']
        with patch.object(watchdog,'probe',return_value='ready'), \
                patch.object(watchdog,'tunnel_url',return_value='https://new.trycloudflare.com'), \
                patch.object(watchdog,'update_environment',return_value=False), \
                patch.object(watchdog,'sign_config'), patch.object(watchdog,'publish_config') as publish, \
                patch.object(watchdog,'config_is_live',return_value=True):
            watchdog.check(state)
            self.assertTrue(state['public_ready']); publish.assert_called_once()
            self.assertEqual(state['stripe_webhook'], 'retry:RuntimeError')
            self.assertNotIn('secret', json.dumps(state))
            watchdog.check(state)
            self.assertEqual(state['stripe_webhook'], 'ready')
            self.assertEqual(self.stripe_sync.call_count, 2)

    def test_signer_preserves_key_and_only_emits_public_information(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with patch.object(signing,'KEY',root/'private/key.pem'),patch.object(signing,'TRUST',root/'trust.json'),patch.object(signing,'CONFIG',root/'public/config.json'):
                first=signing.sign_config('https://old.example.org');key=signing.KEY.read_bytes()
                second=signing.sign_config('https://new.example.org')
                self.assertGreater(second['iat'],first['iat']);self.assertEqual(signing.KEY.read_bytes(),key)
                self.assertEqual(set(second),{'v','api','iat','sig'})
                self.assertEqual(os.stat(signing.KEY).st_mode&0o777,0o600)
                signing.CONFIG.write_text(json.dumps({**second,'sig':'00'*64}))
                self.assertNotEqual(signing.sign_config(second['api'])['sig'],'00'*64)
                signing.KEY.unlink()
                with self.assertRaises(RuntimeError):signing.initialize()

    def test_build_receives_public_config_but_not_runtime_signing_key(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'source';live=root/'live'
            with patch.object(signing,'KEY',live/'private/key.pem'),patch.object(signing,'TRUST',live/'trust.json'),patch.object(signing,'CONFIG',live/'public/config.json'):
                expected=signing.sign_config('https://api.example.org')
                signing.copy_public_config(source)
                self.assertEqual(json.loads((source/'mobile/public/runtime-config.json').read_text()),expected)
                self.assertEqual(list(source.rglob('*.pem')),[])
                (source/'mobile/src/lib/endpointTrust.json').write_text('{}')
                with self.assertRaises(RuntimeError):signing.copy_public_config(source)

if __name__=='__main__':unittest.main()
