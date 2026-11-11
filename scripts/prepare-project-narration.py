"""Reconcile visible course/guide text additively against the active runtime queue.

Never retire report jobs or overwrite a queued voice choice. --retry-reviewed
archives only failures of currently visible lesson/guide clips; verified audio stays.
"""
import argparse
from collections import Counter
import fcntl
import json
import os
from pathlib import Path
import sys
import time
from dotenv import load_dotenv
from pymongo import MongoClient
from numerom_services import service_root

ROOT=service_root()
sys.path.insert(0,str(ROOT/'backend'))
from domain.narration import lesson_clips,clip
from domain.report_audio import ready_audio
from services.report_files import read_json,write_json


def prepare_current(lessons,entries,root,retry=False):
    root=Path(root);jobs=root/'jobs';jobs.mkdir(parents=True,exist_ok=True,mode=0o700)
    current=[]
    for lesson in lessons:
        current.extend({**item,'scope':'lesson','lesson_id':lesson['id'],'lesson_title':lesson['title']}
                       for item in lesson_clips(lesson))
    for entry in entries:
        current.append({**clip(entry['id'],entry['section'],entry['title'],entry['text']),
                        'scope':'project','lesson_title':'NumerOM'})
    counts=Counter();seen=set();current_by_source={}
    descriptor=os.open(jobs/'.queue.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    with os.fdopen(descriptor,'r+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        for item in current:
            current_by_source[(item['scope'],item.get('lesson_id'),item['id'])]=item['hash']
            key=item['hash']
            if key in seen:continue
            seen.add(key);cache=root/'clips'/key;path=jobs/(key+'.json');saved=read_json(path)
            if saved:
                if saved.get('hash')!=key or saved.get('text')!=item['text']:
                    raise ValueError('Existing narration job differs from current content')
                # Old jobs retain their voice and all other metadata byte for byte.
            else:
                if path.exists():raise ValueError('Unreadable narration job; inspection required')
                write_json(path,item);counts['queued_new']+=1
            if ready_audio(cache,key):counts['ready']+=1;continue
            failure=cache/'failed.json'
            if failure.exists() and retry:
                failure.rename(cache/('failed-before-reconcile-'+str(time.time_ns())+'.json'))
                counts['retried']+=1
            counts['review' if failure.exists() else 'pending']+=1
        # Historical audio remains playable, but obsolete text/voice jobs must
        # not consume automatic retries after a current replacement is queued.
        for path in jobs.glob('*.json'):
            old=read_json(path)
            if not old or old.get('scope') not in ('project','lesson'):continue
            replacement=current_by_source.get((old['scope'],old.get('lesson_id'),old.get('id')))
            if replacement and replacement!=old.get('hash') and old.get('superseded_by')!=replacement:
                write_json(path,{**old,'superseded_by':replacement});counts['superseded']+=1
    return {'total':len(seen),**counts}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--retry-reviewed',action='store_true')
    args=parser.parse_args();load_dotenv(ROOT/'backend/.env')
    with MongoClient(os.environ['MONGO_URL'],serverSelectionTimeoutMS=5000) as client:
        lessons=list(client[os.environ['MONGODB_DATABASE']].lessons_v2.find({'is_active':True}).sort('order',1))
    entries=json.loads((ROOT/'packages/project-knowledge/ru.json').read_text())['items']
    print(json.dumps(prepare_current(lessons,entries,ROOT/'backend/private/narration',args.retry_reviewed)))

if __name__=='__main__':main()
