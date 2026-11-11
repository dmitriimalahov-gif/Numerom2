"""Check current published sources against private recordings; never prints tokens or quiz keys."""
import argparse
from collections import Counter,defaultdict
import hashlib
import json
import os
from pathlib import Path
import sys

from dotenv import load_dotenv
from pymongo import MongoClient

from numerom_services import service_root
ROOT=service_root()
sys.path.insert(0,str(ROOT/'backend'))
from domain.narration import clip,lesson_clips
from services.narration import DEFAULT_ROOT

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--require-ready',action='store_true');args=parser.parse_args()
    load_dotenv(ROOT/'backend/.env')
    client=MongoClient(os.environ['MONGO_URL'],serverSelectionTimeoutMS=5000)
    db=client[os.environ['MONGODB_DATABASE']]
    groups=[]
    for lesson in db.lessons_v2.find({'is_active':True}).sort('order',1):
        groups.append((lesson['title'],lesson_clips(lesson)))
    client.close()
    entries=json.loads((ROOT/'packages/project-knowledge/ru.json').read_text())['items']
    groups.append(('Пояснения NumerOM',[clip(e['id'],e['section'],e['title'],e['text']) for e in entries]))
    totals=Counter();sections=defaultdict(Counter);rows=[];problems=[];seconds=0;size=0
    for title,items in groups:
        counts=Counter()
        for item in items:
            folder=DEFAULT_ROOT/'clips'/item['hash'];meta=folder/'ready.json';audio=folder/'audio.m4a'
            state='pending'
            if meta.is_file() and audio.is_file():
                record=json.loads(meta.read_text());data=audio.read_bytes()
                valid=record['hash']==item['hash'] and record['bytes']==len(data) and record['sha256']==hashlib.sha256(data).hexdigest() and record['seconds']>0 and b'ftyp' in data[:32]
                valid=valid and all(c['difference']<=.07 for c in record['segments'])
                state='ready' if valid else 'invalid'
                if valid:seconds+=record['seconds'];size+=len(data)
            elif (folder/'failed.json').is_file():state='review'
            totals[state]+=1;counts[state]+=1;sections[item['section']][state]+=1
            if state!='ready':problems.append({'source':title,'id':item['id'],'state':state})
        rows.append({'source':title,'total':len(items),**counts})
    report={'total':sum(totals.values()),'status':dict(totals),'seconds':round(seconds,2),'bytes':size,'sources':rows,'sections':dict(sections),'remaining':problems}
    output=ROOT/'artifacts/voice-project/coverage.json';output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='remaining'},ensure_ascii=False,indent=2))
    if args.require_ready and problems:raise SystemExit(1)

if __name__=='__main__':main()
