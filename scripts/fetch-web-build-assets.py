#!/usr/bin/env python3
"""Restore only checksum-pinned, already-public author videos for clean CI builds."""
import hashlib,json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parents[1]

def main():
    for item in json.loads((ROOT/'deploy/domain/public-build-assets.json').read_text()):
        target=ROOT/item['path'];url=urlsplit(item['url'])
        if (target.parent!=ROOT/'mobile/assets/author' or target.suffix!='.mp4'
            or url.scheme!='https' or url.netloc!='1.numer.om' or not url.path.startswith('/_build-assets/')):
            raise ValueError('Unexpected public asset')
        if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest()==item['sha256']:continue
        with urlopen(item['url'],timeout=45) as response:
            if response.geturl()!=item['url']:raise ValueError('Asset redirect not permitted')
            data=response.read(12*1024*1024+1)
        if len(data)>12*1024*1024 or hashlib.sha256(data).hexdigest()!=item['sha256']:
            raise ValueError('Public asset checksum mismatch')
        target.parent.mkdir(exist_ok=True,parents=True)
        temp=target.with_suffix('.pending');temp.write_bytes(data);temp.replace(target)
        print('Verified public build asset:',target.name)

if __name__=='__main__':main()
