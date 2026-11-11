"""Reconciliation keeps paid jobs, voice selection, and validated recordings."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('narration_prepare',ROOT/'scripts/prepare-project-narration.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.entries=[{'id':'guide','section':'guide','title':'Пример','text':'Учебный текст.'}]
        self.item=module.clip('guide','guide','Пример','Учебный текст.')
    def test_additive_queue_never_retires_report_or_changes_old_voice(self):
        jobs=self.root/'jobs';jobs.mkdir()
        paid=jobs/('b'*64+'.json');paid.write_text('{"scope":"full-report","private":"fixture"}')
        path=jobs/(self.item['hash']+'.json');path.write_text(json.dumps({**self.item,'voice':'helper-male'}))
        before={p:p.read_bytes() for p in [paid,path]}
        result=module.prepare_current([],self.entries,self.root)
        self.assertEqual(result,{'total':1,'pending':1})
        for p,data in before.items():self.assertEqual(p.read_bytes(),data)
    def test_retry_archives_only_current_failure(self):
        cache=self.root/'clips'/self.item['hash'];cache.mkdir(parents=True)
        (cache/'failed.json').write_text('{"error":"fixture"}');(cache/'passed.wav').write_bytes(b'old chunk')
        old=self.root/'clips'/('c'*64);old.mkdir();(old/'failed.json').write_text('{}')
        result=module.prepare_current([],self.entries,self.root,retry=True)
        self.assertEqual(result['retried'],1)
        self.assertEqual(len(list(cache.glob('failed-before-reconcile-*.json'))),1)
        self.assertEqual((cache/'passed.wav').read_bytes(),b'old chunk')
        self.assertTrue((old/'failed.json').exists())
    def test_ready_recording_survives_even_with_stale_failure(self):
        cache=self.root/'clips'/self.item['hash'];cache.mkdir(parents=True)
        audio=b'ftyp synthetic aac';(cache/'audio.m4a').write_bytes(audio)
        meta={'hash':self.item['hash'],'bytes':len(audio),'seconds':1,'sha256':hashlib.sha256(audio).hexdigest()}
        (cache/'ready.json').write_text(json.dumps(meta));(cache/'failed.json').write_text('{}')
        result=module.prepare_current([],self.entries,self.root,retry=True)
        self.assertEqual(result['ready'],1);self.assertNotIn('retried',result)
        self.assertEqual((cache/'audio.m4a').read_bytes(),audio)
    def test_changed_text_queues_new_identity_without_overwriting_old_job(self):
        module.prepare_current([],self.entries,self.root)
        self.entries[0]['text']='Обновлённый учебный текст.'
        result=module.prepare_current([],self.entries,self.root)
        self.assertEqual(result['queued_new'],1)
        self.assertEqual(len(list((self.root/'jobs').glob('*.json'))),2)

if __name__=='__main__':unittest.main()
