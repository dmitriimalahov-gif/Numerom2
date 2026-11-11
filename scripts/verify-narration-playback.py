"""Exercise signed playback for real recordings in an isolated ASGI app.

No network listener, production token or database mutation is used. The fake
account is scoped to this process; output never contains signed media URLs.
"""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
import httpx
from fastapi import FastAPI
from auth import get_current_user
from routers.narration import create_narration_router


async def verify(prefix,output):
    os.environ['SECRET_KEY']='isolated-narration-playback-test-only-key'
    os.environ['PUBLIC_API_URL']='https://voice.example.invalid'
    user={'id':'voice-qa','auth_version':1}
    async def find(query):
        return dict(user) if query.get('id')=='voice-qa' else None
    db=SimpleNamespace(users=SimpleNamespace(find_one=AsyncMock(side_effect=find)))
    app=FastAPI();app.include_router(create_narration_router(db))
    app.dependency_overrides[get_current_user]=lambda:{'user_id':'voice-qa'}
    results=[]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='https://voice.example.invalid') as client:
        catalog=await client.get('/api/narration/project');catalog.raise_for_status()
        items=[row for row in catalog.json()['items'] if row['id'].startswith(prefix)]
        assert items,'No matching narration'
        for row in items:
            assert row['status']=='ready',row['id']
            path=urlsplit(row['url']).path
            response=await client.get(path,headers={'Range':'bytes=0-31'})
            assert response.status_code==206 and b'ftyp' in response.content
            assert 'no-store' in response.headers['cache-control']
            user['auth_version']=2
            revoked=await client.get(path);assert revoked.status_code==401
            user['auth_version']=1
            results.append({'id':row['id'],'hash':row['hash'],'seconds':row['seconds'],'range_status':response.status_code,'revoked_status':revoked.status_code})
    report={'recordings':results,'count':len(results),'seconds':round(sum(row['seconds'] for row in results),2),'environment':'isolated ASGI; real audio files; fake revocable account'}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='recordings'},ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prefix',required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();asyncio.run(verify(args.prefix,args.output))
