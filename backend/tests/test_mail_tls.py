import ssl
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

class MailTLS(unittest.TestCase):
    def test_python_without_system_certificates_uses_trusted_bundle_and_keeps_verification(self):
        from services.mail import smtp_tls_context
        empty=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.assertEqual(len(empty.get_ca_certs()),0)
        with patch('services.mail.ssl.create_default_context',return_value=empty): context=smtp_tls_context()
        self.assertGreater(len(context.get_ca_certs()),0)
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode,ssl.CERT_REQUIRED)
