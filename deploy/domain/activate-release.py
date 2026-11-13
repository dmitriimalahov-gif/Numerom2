#!/usr/bin/env python3
"""Restricted SSH receiver for audited NumerOM browser releases. No shell commands."""
import io,json,os,re,shutil,sys,tarfile,tempfile,time
from pathlib import Path,PurePosixPath
from urllib.request import Request,urlopen

ROOT=Path('/srv/numerom')
LIMIT=64*1024*1024

def safe_name(name):
    path=PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name:
        raise ValueError('Unsafe release path')
    if any(p.startswith('.') and p!='.nojekyll' for p in path.parts):
        raise ValueError('Hidden release file')
    if path.suffix.lower() in {'.pem','.key','.py','.sh','.map','.sqlite','.db'}:
        raise ValueError('Non-public release file')
    return path

def receive(sha,stream):
    if not re.fullmatch('[a-f0-9]{40}',sha):raise ValueError('Expected a commit SHA')
    data=stream.read(LIMIT+1)
    if len(data)>LIMIT:raise ValueError('Release archive too large')
    stage=Path(tempfile.mkdtemp(prefix='.staging-',dir=ROOT/'releases'))
    try:
        total=0
        with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as archive:
            members=archive.getmembers()
            if len(members)>10000:raise ValueError('Too many release files')
            for member in members:
                name=safe_name(member.name);target=stage/str(name)
                if member.isdir():target.mkdir(exist_ok=True,parents=True);continue
                if not member.isfile():raise ValueError('Links and devices are forbidden')
                total+=member.size
                if total>256*1024*1024:raise ValueError('Expanded release too large')
                target.parent.mkdir(exist_ok=True,parents=True)
                with archive.extractfile(member) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst)
                target.chmod(0o644)
        if not (stage/'index.html').is_file() or not (stage/'_expo').is_dir():raise ValueError('Incomplete web release')
        config=json.loads((stage/'runtime-config.json').read_text())
        if config.get('api')!='https://1.numer.om':raise ValueError('Unexpected API origin')
        if json.loads((stage/'release.json').read_text()).get('commit')!=sha:raise ValueError('Commit mismatch')
        with urlopen(Request('http://127.0.0.1:18804/api/health',headers={'CF-Connecting-IP':'127.0.0.1'}),timeout=10) as response:
            if response.status!=200:raise ValueError('API unavailable')
        stage.chmod(0o755)
        release=ROOT/'releases'/f'{sha}-{time.time_ns()}'
        stage.rename(release)
        current=ROOT/'current';previous=current.resolve() if current.is_symlink() else None
        pending=ROOT/f'.current-{os.getpid()}'
        pending.symlink_to(release);pending.replace(current)
        try:
            with urlopen('https://1.numer.om/release.json',timeout=15) as response:
                if json.load(response).get('commit')!=sha:raise ValueError('Public release verification failed')
        except Exception:
            if previous:
                pending.symlink_to(previous);pending.replace(current)
            raise
        print(json.dumps({'status':'deployed','commit':sha,'url':'https://1.numer.om'}))
    finally:
        if stage.exists():shutil.rmtree(stage)

if __name__=='__main__':
    try:receive(os.environ.get('SSH_ORIGINAL_COMMAND',''),sys.stdin.buffer)
    except Exception as error:
        print('Deployment failed: '+type(error).__name__,file=sys.stderr);sys.exit(1)
