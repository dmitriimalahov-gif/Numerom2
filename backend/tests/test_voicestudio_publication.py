"""Only verified current sources may enter the normal authenticated media cache."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import unittest
import tempfile

SCRIPTS = Path(__file__).resolve().parents[2] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('voice_publisher', SCRIPTS / 'publish-voicestudio-narration.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


def publication(tmp_path):
    tmp_path = tmp_path.resolve()
    root = tmp_path / 'runtime'; batch = tmp_path / 'batch'
    catalog = root / 'packages/project-knowledge/ru.json'; catalog.parent.mkdir(parents=True)
    entry = {'id': 'learning', 'section': 'guide', 'title': 'Обучение', 'text': 'Прочитайте урок и выполните упражнение.'}
    catalog.write_text(json.dumps({'items': [entry]}, ensure_ascii=False))
    item = publisher.clip(entry['id'], entry['section'], entry['title'], entry['text'])
    key = 'a' * 64; folder = batch / 'cache' / key; folder.mkdir(parents=True)
    (batch / 'reference.wav').write_bytes(b'reference fixture')
    (folder / 'master.wav').write_bytes(b'master fixture')
    (folder / 'audio.m4a').write_bytes(b'audio fixture')
    config = {'publish_to_project': True, 'reference_sha256': publisher.sha(batch / 'reference.wav'),
              'model_revision': 'fixture', 'profile_id': 'fixture', 'max_word_difference': .04}
    meta = {'key': key, 'engine': 'omnivoice', 'model_revision': 'fixture', 'automatic_checks_passed': True,
            'voice_reference_sha256': config['reference_sha256'], 'seconds': 2,
            'bytes': (folder / 'audio.m4a').stat().st_size, 'sha256': publisher.sha(folder / 'audio.m4a'),
            'wav_sha256': publisher.sha(folder / 'master.wav'),
            'segments': [{'critical_ok': True, 'difference': 0, 'clipped_fraction': 0}]}
    publisher.atomic_json(batch / 'config.json', config); publisher.atomic_json(folder / 'ready.json', meta)
    target = {'scope': 'project', 'source_id': 'project-knowledge/ru.json', 'item_id': 'learning',
              'source_sha256': hashlib.sha256(item['text'].encode()).hexdigest()}
    return root, batch, key, target, item


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.publication = publication(Path(self.temporary.name))

    def test_verified_audio_enters_existing_playback_idempotently(self):
        root, batch, key, target, item = self.publication
        first = publisher.install(batch, key, [target], root=root)
        audio = root / 'backend/private/narration/clips' / item['hash'] / 'audio.m4a'
        before = audio.stat().st_mtime_ns
        publisher.install(batch, key, [target], root=root)
        assert audio.stat().st_mtime_ns == before
        assert first['placements'][0]['scope'] == 'project'
        assert publisher.ready_audio(audio.parent, item['hash'])['generation_cache_key'] == key


    def test_changed_source_is_not_published(self):
        root, batch, key, target, _ = self.publication
        target['source_sha256'] = 'b' * 64
        with self.assertRaisesRegex(ValueError, 'Current source differs'):
            publisher.install(batch, key, [target], root=root)
        assert not (root / 'backend/private/narration/clips').exists()


    def test_changed_voice_is_not_published(self):
        root, batch, key, target, _ = self.publication
        (batch / 'reference.wav').write_bytes(b'other voice')
        with self.assertRaisesRegex(AssertionError, ""):
            publisher.install(batch, key, [target], root=root)


    def test_corrupt_audio_is_not_published(self):
        root, batch, key, target, _ = self.publication
        (batch / 'cache' / key / 'audio.m4a').write_bytes(b'corrupted')
        with self.assertRaisesRegex(ValueError, 'Audio integrity'):
            publisher.install(batch, key, [target], root=root)


    def test_private_report_cannot_be_mapped_into_public_catalog(self):
        root, batch, key, target, _ = self.publication
        target['item_id'] = 'full-report-summary'
        with self.assertRaisesRegex(ValueError, 'Current source differs'):
            publisher.install(batch, key, [target], root=root)


if __name__ == "__main__":
    unittest.main()
