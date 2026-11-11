import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import numerom_services

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts/deploy-service-runtime.py'
spec = importlib.util.spec_from_file_location('deploy_runtime', SCRIPT)
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class RuntimeDeploymentTests(unittest.TestCase):
    def fixture(self, root):
        source = root / 'checkout'
        for relative, text in {
            'backend/server.py': 'server v1', 'backend/.env': 'private config',
            'backend/private/order.json': 'original order', 'backend/uploads/lesson.pdf': 'lesson',
            'scripts/numerom_services.py': 'service', 'packages/knowledge/ru.json': '{}',
            'video/src/scene.jsx': 'scene', 'video/node_modules/example/index.js': 'dependency',
            'mobile/public/runtime-config.json': '{}', 'mobile/src/lib/endpointTrust.json': '{}',
        }.items():
            target = source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        return source

    def test_second_deploy_updates_code_but_preserves_runtime_data_and_secrets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self.fixture(root)
            destination = root / 'runtime'
            runtime.deploy(source, destination, True, False)
            (destination / 'backend/private/order.json').write_text('new live order')
            (destination / 'backend/.env').write_text('live config')
            (source / 'backend/server.py').write_text('server v2')
            runtime.deploy(source, destination, False, False)
            self.assertEqual((destination / 'backend/server.py').read_text(), 'server v2')
            self.assertEqual((destination / 'backend/private/order.json').read_text(), 'new live order')
            self.assertEqual((destination / 'backend/.env').read_text(), 'live config')
            self.assertEqual((source / 'backend/private/order.json').read_text(), 'original order')
            with self.assertRaises(ValueError):
                runtime.deploy(source, destination, True, False)

    def test_dependency_symlinks_can_be_copied_again_after_interruption(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=self.fixture(root);destination=root/'runtime'
            link=source/'video/node_modules/example/entry.js'
            link.symlink_to('index.js')
            runtime.deploy(source,destination,False,False)
            (destination/'video/.dependencies-copied').unlink()
            runtime.deploy(source,destination,False,False)
            copied=destination/'video/node_modules/example/entry.js'
            self.assertTrue(copied.is_symlink())
            self.assertEqual(copied.read_text(),'dependency')

    def test_active_runtime_cannot_be_reseeded_from_stale_checkout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=self.fixture(root);first=root/'first';second=root/'second'
            runtime.deploy(source,first,True,False);runtime.activate(source,first)
            (first/'backend/private/order.json').write_text('live order')
            with self.assertRaisesRegex(ValueError,'authoritative'):
                runtime.deploy(source,second,True,False)
            self.assertFalse(second.exists())
            self.assertEqual((first/'backend/private/order.json').read_text(),'live order')
            self.assertEqual(numerom_services.service_root(source),first.resolve())

    def test_unrelated_destination_and_nested_checkout_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self.fixture(root)
            unrelated = root / 'other'
            unrelated.mkdir()
            (unrelated / 'keep').write_text('untouched')
            with self.assertRaises(ValueError):
                runtime.deploy(source, unrelated, False, False)
            with self.assertRaises(ValueError):
                runtime.deploy(source, source / 'runtime', False, False)
            self.assertEqual((unrelated / 'keep').read_text(), 'untouched')

    def test_activation_requires_initialized_copy_and_writes_private_pointer(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self.fixture(root)
            destination = root / 'runtime'
            runtime.deploy(source, destination, False, False)
            with self.assertRaises(ValueError):
                runtime.activate(source, destination)
            runtime.deploy(source, destination, True, False)
            runtime.activate(source, destination)
            pointer = source / 'backend/private/runtime/service-location.json'
            self.assertEqual(json.loads(pointer.read_text())['root'], str(destination.resolve()))
            self.assertEqual(pointer.stat().st_mode & 0o777, 0o600)
            self.assertEqual(numerom_services.service_root(source), destination.resolve())
            pointer.chmod(0o666)
            with self.assertRaises(RuntimeError):
                numerom_services.service_root(source)

    def test_desktop_launcher_uses_active_runtime_but_keeps_source_frontend(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination=Path(temporary)/'runtime'
            python=destination/'backend/.service-venv/bin/python'
            with patch.object(numerom_services,'ROOT',destination), patch.object(numerom_services,'PYTHON',python):
                spec=importlib.util.spec_from_file_location('start_local_test',SCRIPT.parent/'start-local.py')
                launcher=importlib.util.module_from_spec(spec)
                spec.loader.exec_module(launcher)
            self.assertEqual(launcher.SERVICE_ROOT,destination)
            self.assertEqual(launcher.LOGS,destination/'backend/private/runtime')
            self.assertEqual(launcher.PYTHON,python)
            self.assertEqual(launcher.ROOT,SCRIPT.parent.parent)

    def test_missing_pointer_preserves_original_checkout(self):
        with tempfile.TemporaryDirectory() as temporary:
            source=self.fixture(Path(temporary))
            self.assertEqual(numerom_services.service_root(source), source)


if __name__ == '__main__':
    unittest.main()
