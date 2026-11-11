"""No network: the Stripe TEST setup never echoes the key and saves nothing on failure."""
import io
import json
import stat
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
import stripe_test_environment as setup

KEY = 'sk_test_' + 'A1b2C3' * 6


class FakeStripe:
    def __init__(self, live=False, fail=None):
        self.calls, self.live, self.fail = [], live, fail

    def __call__(self, method, path, key, data=None):
        self.calls.append((method, path, data))
        if self.fail and path.startswith(self.fail):
            raise RuntimeError('Invalid API Key provided')
        if path == '/balance': return {'livemode': self.live}
        if path == '/account': return {'id': 'acct_test_numerom'}
        if method == 'POST' and path == '/webhook_endpoints': return {'id': 'we_new', 'secret': 'whsec_created'}
        return {'id': path.rsplit('/', 1)[1]}


class StripeTestEnvironment(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(); self.addCleanup(folder.cleanup)
        self.env = Path(folder.name)/'.env'
        self.env.write_text("STRIPE_SECRET_KEY='rkcs_test_expired'\nSTRIPE_WEBHOOK_SECRET='whsec_old'\n"
                            "STRIPE_MODE='test'\nSTRIPE_SANDBOX_EXPIRES_AT='2026-10-23'\n"
                            "PUBLIC_API_URL='https://new.trycloudflare.com'\nSMTP_USER='owner@example.org'\n")
        self.state = Path(folder.name)/'stripe/runtime.json'
        self.state.parent.mkdir()
        self.state.write_text(json.dumps({'account_id': 'acct_sandbox', 'webhook_id': 'we_old', 'expires_at': '2026-10-23'}))
        for name, value in (('ENV', self.env), ('STATE', self.state), ('SANDBOX', self.state.parent/'sandbox-cli.toml')):
            patcher = patch.object(setup, name, value); patcher.start(); self.addCleanup(patcher.stop)
        self.restart = patch.object(setup, 'restart').start(); self.addCleanup(patch.stopall)

    def run_setup(self, stripe, key=KEY, email=''):
        output = io.StringIO()
        with patch.object(setup, 'stripe_call', stripe), patch.object(setup, 'getpass', return_value=key), \
                patch('builtins.input', return_value=email), redirect_stdout(output):
            setup.connect()
        return output.getvalue()

    def settings(self):
        from dotenv import dotenv_values
        return dotenv_values(self.env)

    def test_replaces_expired_sandbox_registers_webhook_and_restarts_api(self):
        stripe = FakeStripe()
        printed = self.run_setup(stripe)
        values = self.settings()
        self.assertEqual((values['STRIPE_SECRET_KEY'], values['STRIPE_WEBHOOK_SECRET'], values['STRIPE_MODE']),
                         (KEY, 'whsec_created', 'test'))
        self.assertNotIn('STRIPE_SANDBOX_EXPIRES_AT', values)
        self.assertEqual(values['PUBLIC_API_URL'], 'https://new.trycloudflare.com')
        created = stripe.calls[-1]
        self.assertEqual(created[:2], ('POST', '/webhook_endpoints'))
        self.assertEqual(created[2]['url'], 'https://new.trycloudflare.com/api/webhook/stripe')
        self.assertEqual(created[2]['enabled_events[]'], setup.EVENTS)
        saved = json.loads(self.state.read_text())
        self.assertEqual((saved['account_id'], saved['webhook_id'], saved['mode']), ('acct_test_numerom', 'we_new', 'test'))
        self.assertNotIn('expires_at', saved)
        self.assertEqual(stat.S_IMODE(self.state.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.env.stat().st_mode), 0o600)
        self.restart.assert_called_once_with('api')
        self.assertNotIn(KEY, printed)
        self.assertNotIn('whsec_created', printed)

    def test_rerun_after_tunnel_change_moves_the_same_webhook(self):
        self.run_setup(FakeStripe())
        self.env.write_text(self.env.read_text().replace('new.trycloudflare.com', 'next.trycloudflare.com'))
        stripe = FakeStripe()
        self.run_setup(stripe)
        self.assertEqual(stripe.calls[-1], ('POST', '/webhook_endpoints/we_new',
                                            {'url': 'https://next.trycloudflare.com/api/webhook/stripe'}))
        self.assertEqual(self.settings()['STRIPE_WEBHOOK_SECRET'], 'whsec_created')
        self.assertEqual(json.loads(self.state.read_text())['url'], 'https://next.trycloudflare.com/api/webhook/stripe')

    def test_live_malformed_or_rejected_keys_change_nothing(self):
        before = (self.env.read_text(), self.state.read_text())
        cases = [(FakeStripe(), 'sk_live_' + 'A1b2C3' * 6), (FakeStripe(), 'rkcs_test_whatever'),
                 (FakeStripe(live=True), KEY), (FakeStripe(fail='/balance'), KEY), (FakeStripe(fail='/webhook_endpoints'), KEY)]
        for stripe, key in cases:
            with self.subTest(key=key[:8], live=stripe.live, fail=stripe.fail), self.assertRaises(SystemExit):
                self.run_setup(stripe, key)
            self.assertEqual((self.env.read_text(), self.state.read_text()), before)
        self.restart.assert_not_called()

    def test_enter_recreates_sandbox_as_on_16_october(self):
        sandbox_key = 'rkcs_test_' + 'Z9y8X7' * 6
        claim = 'https://dashboard.stripe.com/onboard_sandbox/new'
        stripe = FakeStripe()
        with patch.object(setup, 'create_sandbox', return_value=(sandbox_key, '2026-10-30', claim, 'acct_sandbox_new')) as create:
            printed = self.run_setup(stripe, '')
        create.assert_called_once_with('owner@example.org')
        # A claimable sandbox key cannot read /balance or /account; the CLI profile names the account.
        self.assertEqual([call[:2] for call in stripe.calls], [('POST', '/webhook_endpoints')])
        values = self.settings()
        self.assertEqual((values['STRIPE_SECRET_KEY'], values['STRIPE_WEBHOOK_SECRET']), (sandbox_key, 'whsec_created'))
        self.assertEqual(values['STRIPE_SANDBOX_EXPIRES_AT'], '2026-10-30')
        saved = json.loads(self.state.read_text())
        self.assertEqual((saved['account_id'], saved['expires_at'], saved['claim_url']), ('acct_sandbox_new', '2026-10-30', claim))
        self.assertIn(claim, printed)
        self.assertNotIn(sandbox_key, printed)
        self.restart.assert_called_once_with('api')

    def write_sandbox(self, expires):
        (self.state.parent/'sandbox-cli.toml').write_text(
            "[numerom-credits]\naccount_id = 'acct_sandbox_cli'\nsandbox_claim_url = 'https://dashboard.stripe.com/onboard_sandbox/cli'\n"
            f"sandbox_expires_at = '{expires}'\ntest_mode_api_key = 'rkcs_test_{'Q1w2E3' * 6}'\n")

    def test_valid_sandbox_is_reused_without_questions_or_a_new_one(self):
        self.write_sandbox('2999-01-01')
        stripe = FakeStripe()
        output = io.StringIO()
        with patch.object(setup, 'stripe_call', stripe), patch.object(setup, 'create_sandbox') as create, \
                patch.object(setup, 'getpass') as asked, redirect_stdout(output):
            setup.connect(reuse=True)
        create.assert_not_called(); asked.assert_not_called()
        values = self.settings()
        self.assertEqual(values['STRIPE_SECRET_KEY'], 'rkcs_test_' + 'Q1w2E3' * 6)
        self.assertEqual(values['STRIPE_SANDBOX_EXPIRES_AT'], '2999-01-01')
        self.assertEqual(json.loads(self.state.read_text())['account_id'], 'acct_sandbox_cli')
        self.assertIn('https://dashboard.stripe.com/onboard_sandbox/cli', output.getvalue())
        self.restart.assert_called_once_with('api')

    def test_expired_sandbox_is_not_reused(self):
        self.write_sandbox('2026-10-23')
        before = self.env.read_text()
        with patch.object(setup, 'stripe_call', FakeStripe()), self.assertRaises(SystemExit):
            setup.connect(reuse=True)
        self.assertEqual(self.env.read_text(), before)

    def test_failed_sandbox_creation_changes_nothing(self):
        before = (self.env.read_text(), self.state.read_text())
        with patch.object(setup, 'create_sandbox', side_effect=OSError('stripe not found')), self.assertRaises(SystemExit):
            self.run_setup(FakeStripe(), '')
        self.assertEqual((self.env.read_text(), self.state.read_text()), before)
        self.restart.assert_not_called()

    def test_watchdog_moves_existing_test_webhook_once_without_rotating_secrets(self):
        self.run_setup(FakeStripe())
        before = self.env.read_text()
        target = 'https://rotated.trycloudflare.com/api/webhook/stripe'
        with patch.object(setup, 'stripe_call', return_value={
                'id': 'we_new', 'url': target, 'livemode': False, 'status': 'enabled'}) as call:
            self.assertEqual(setup.sync_test_webhook('https://rotated.trycloudflare.com'), 'ready')
            self.assertEqual(setup.sync_test_webhook('https://rotated.trycloudflare.com'), 'ready')
            call.assert_called_once_with('POST', '/webhook_endpoints/we_new', KEY, {'url': target})
        self.assertEqual(self.env.read_text(), before)
        self.assertEqual(json.loads(self.state.read_text())['url'], target)
        # Only the initial interactive setup restarts the API.
        self.restart.assert_called_once_with('api')

    def test_watchdog_never_creates_sandbox_or_modifies_live_or_expired_environment(self):
        with patch.object(setup, 'stripe_call') as call, patch.object(setup, 'create_sandbox') as create:
            self.assertEqual(setup.sync_test_webhook('https://new.trycloudflare.com'), 'sandbox_expired')
            self.env.write_text(self.env.read_text().replace("STRIPE_MODE='test'", "STRIPE_MODE='live'"))
            self.assertEqual(setup.sync_test_webhook('https://new.trycloudflare.com'), 'not_test')
            call.assert_not_called(); create.assert_not_called()

    def test_failed_webhook_move_keeps_old_address_for_retry(self):
        self.run_setup(FakeStripe())
        before = (self.env.read_text(), self.state.read_text())
        for response in [RuntimeError('private Stripe error'), {'id': 'we_new', 'livemode': True}]:
            with self.subTest(response=type(response).__name__):
                with patch.object(setup, 'stripe_call', side_effect=response if isinstance(response, Exception) else None,
                                  return_value=response), self.assertRaises(RuntimeError):
                    setup.sync_test_webhook('https://rotated.trycloudflare.com')
                self.assertEqual((self.env.read_text(), self.state.read_text()), before)

    def test_watchdog_rejects_unsafe_origin_without_sending_secrets(self):
        self.run_setup(FakeStripe())
        with patch.object(setup, 'stripe_call') as call:
            for origin in ['http://unsafe.example', 'https://user:pass@example.org', 'https://example.org/path']:
                with self.subTest(origin=origin), self.assertRaises(ValueError):
                    setup.sync_test_webhook(origin)
            call.assert_not_called()


if __name__ == '__main__':
    unittest.main()
