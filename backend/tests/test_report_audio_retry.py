"""Paid-report audio recovery uses only selected hashes and bounded retries."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from fastapi import HTTPException
from services.narration import NarrationService
from services.report_files import read_json, write_json


class ReportAudioRetryTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name).resolve();self.voice=NarrationService(None,root=self.root)

    def item(self,n):
        return {'id':f'full-report-section-{n}','hash':f'{n:064x}','text':f'Текст главы {n}.','title':'Глава'}

    def failed(self,item):
        target=self.voice.folder(item['hash']);write_json(target/'failed.json',{'error':'synthetic failure'})
        return target

    def ready(self,item):
        target=self.voice.folder(item['hash']);target.mkdir(parents=True,exist_ok=True)
        data=b'synthetic-aac';(target/'audio.m4a').write_bytes(data)
        write_json(target/'ready.json',{'hash':item['hash'],'seconds':2,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        return target

    def test_only_selected_failed_or_corrupt_hashes_are_requeued(self):
        selected,good,old=self.item(1),self.item(2),self.item(3)
        broken=self.ready(selected);(broken/'audio.m4a').write_bytes(b'X'*len(b'synthetic-aac'))
        ready=self.ready(good);held=self.failed(old)
        before=(ready/'ready.json').read_bytes();held_before=(held/'failed.json').read_bytes()
        self.assertEqual(self.voice.state(selected)['status'],'review')
        self.assertEqual(self.voice.retry_report([selected,good],'owned-order'),0)
        self.assertEqual(self.voice.state(selected)['status'],'preparing')
        self.assertEqual((ready/'ready.json').read_bytes(),before)
        self.assertEqual((held/'failed.json').read_bytes(),held_before)
        self.assertEqual([p.stem for p in (self.root/'jobs').glob('*.json')],[selected['hash']])

    def test_cooldown_and_three_attempts_per_hour_reset_without_lifetime_lockout(self):
        item=self.item(1);target=self.failed(item)
        for now in [1000,1060,1120]:
            self.failed(item)
            with patch('services.narration.time.time',return_value=now):
                self.assertEqual(self.voice.retry_report([item],'owned-order'),0)
        self.failed(item)
        for now in [1130,1200]:
            with patch('services.narration.time.time',return_value=now):
                self.assertEqual(self.voice.retry_report([item],'owned-order'),1)
                self.assertTrue((target/'failed.json').exists())
        with patch('services.narration.time.time',return_value=4721):
            self.assertEqual(self.voice.retry_report([item],'owned-order'),0)
        self.assertEqual(read_json(target/'retry.json')['attempts'],[4721])

    def test_ready_history_does_not_consume_pending_capacity(self):
        with patch('services.narration.QUEUE_LIMIT',2):
            for n in [1,2,3]:
                item=self.item(n);self.voice.enqueue(item,'full-report','owned');self.ready(item)
            self.voice.enqueue(self.item(4),'full-report','owned')
            self.voice.enqueue(self.item(5),'full-report','owned')
            with self.assertRaises(HTTPException) as failure:
                self.voice.enqueue(self.item(6),'full-report','owned')
            self.assertEqual(failure.exception.status_code,503)
        self.assertEqual(len(list((self.root/'jobs').glob('*.json'))),5)

    def test_corrupt_job_file_is_repaired_from_authorized_source(self):
        item=self.item(1);jobs=self.root/'jobs';jobs.mkdir()
        (jobs/(item['hash']+'.json')).write_text('{invalid')
        self.voice.enqueue(item,'full-report','owned')
        self.assertEqual(read_json(jobs/(item['hash']+'.json'))['text'],item['text'])

    def test_unrelated_course_scope_cannot_use_report_retry(self):
        item={**self.item(1),'id':'theory-1'};target=self.failed(item)
        with self.assertRaises(ValueError):self.voice.retry_report([item],'owned')
        self.assertTrue((target/'failed.json').exists())


if __name__=='__main__':unittest.main()
