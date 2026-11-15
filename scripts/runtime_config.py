"""Signed public endpoint configuration; its private key never leaves this Mac."""
import json
import os
import re
import time
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature, encode_dss_signature
from numerom_services import service_root

ROOT = service_root(Path(__file__).resolve().parents[1])
KEY = ROOT / 'backend/private/runtime/endpoint-signing.pem'
CONFIG = ROOT / 'mobile/public/runtime-config.json'
TRUST = ROOT / 'mobile/src/lib/endpointTrust.json'

def copy_public_config(checkout):
    """A source build receives only public config; the live key stays in runtime."""
    checkout = Path(checkout)
    target_trust = checkout / 'mobile/src/lib/endpointTrust.json'
    trust = json.loads(TRUST.read_text())
    if target_trust.exists() and json.loads(target_trust.read_text()) != trust:
        raise RuntimeError('Source build trust differs from the running installation')
    if target_trust.resolve() != TRUST.resolve():
        atomic_write(target_trust, json.dumps(trust, indent=2) + '\n', 0o644)
    target_config = checkout / 'mobile/public/runtime-config.json'
    if target_config.resolve() != CONFIG.resolve():
        atomic_write(target_config, CONFIG.read_text(), 0o644)

def valid_origin(value):
    return isinstance(value, str) and re.fullmatch(r'https://[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?', value) is not None

def atomic_write(path, data, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    with open(temporary, 'w', encoding='utf8') as stream:
        os.chmod(temporary, mode)
        stream.write(data)
    temporary.replace(path)

def initialize():
    if not KEY.exists():
        if TRUST.exists():
            raise RuntimeError('Signing key is missing; restore it instead of rotating the installed app trust key')
        KEY.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        key = ec.generate_private_key(ec.SECP256R1())
        with os.fdopen(os.open(KEY, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as stream:
            stream.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    key = serialization.load_pem_private_key(KEY.read_bytes(), password=None)
    public = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint).hex()
    trust = {'publicKey': public, 'configUrl': 'https://1.numer.om/runtime-config.json'}
    if TRUST.exists() and json.loads(TRUST.read_text()).get('publicKey') != public:
        raise RuntimeError('Existing app public key differs; refusing silent key rotation')
    atomic_write(TRUST, json.dumps(trust, indent=2) + '\n', 0o644)
    return key

def sign_config(api):
    if not valid_origin(api):
        raise ValueError('Expected an HTTPS origin')
    key = initialize()
    try:
        previous = json.loads(CONFIG.read_text())
        raw = bytes.fromhex(previous['sig'])
        if previous['v'] != 1 or len(raw) != 64 or not isinstance(previous['iat'], int):
            raise ValueError('Invalid configuration')
        key.public_key().verify(encode_dss_signature(int.from_bytes(raw[:32],'big'),int.from_bytes(raw[32:],'big')),
                                f"numerom-config:v1:{previous['api']}:{previous['iat']}".encode(),ec.ECDSA(hashes.SHA256()))
    except Exception:
        previous = {}
    if previous.get('api') == api:
        return previous
    issued = max(int(time.time()), previous.get('iat', 0) + 1)
    raw = key.sign(f'numerom-config:v1:{api}:{issued}'.encode(), ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(raw)
    result = {'v': 1, 'api': api, 'iat': issued, 'sig': (r.to_bytes(32, 'big') + s.to_bytes(32, 'big')).hex()}
    atomic_write(CONFIG, json.dumps(result, indent=2) + '\n', 0o644)
    return result

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('api')
    args = parser.parse_args()
    print(json.dumps(sign_config(args.api)))
