"""Render both greeting videos, verify them, then install the complete mobile asset set."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from numerom_services import service_root
from report_generation_slot import report_generation_slot

SOURCE = Path(__file__).resolve().parents[1]
RUNTIME = service_root()


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    generated = SOURCE/'artifacts/author-greeting-ru-stress-v1'
    word = json.loads((generated/'author-word.json').read_text())
    if (word.get('voice') != 'dmitrii-conversation-v1' or word.get('tempo') != 1.2 or word.get('pronunciation')!='ru-stress-cf-v1'
            or word['audio_sha256'] != sha(generated/'author-word.m4a')
            or word.get('assembled_difference', 1) > .04 or len(word['sentences']) != 12):
        raise ValueError('Greeting is not the verified selected-voice recording')
    for a, b in zip(word['sentences'], word['sentences'][1:]):
        if not 0 <= a['start'] < a['end'] <= b['start'] < word['seconds']:
            raise ValueError('Invalid greeting timing')
    stage = RUNTIME/'artifacts/author-greeting-ru-stress-v1/assets/author'
    stage.mkdir(parents=True, exist_ok=True)
    illustrations = stage.parent/'illustrations'; illustrations.mkdir(exist_ok=True)
    for name in ('KVADRATW.png','123W.png','159W.png'):
        shutil.copy2(SOURCE/'mobile/assets/illustrations'/name, illustrations/name)
    for name in ('author-word.json','author-word.m4a'):
        shutil.copy2(generated/name, stage/name)
    node = Path.home()/'.nvm/versions/node/v22.22.2/bin/node'
    compositor = RUNTIME/'video/node_modules/@remotion/compositor-darwin-arm64'
    verified = {}
    print('WAIT: shared slot for two greeting videos', flush=True)
    with report_generation_slot(RUNTIME/'backend/private/runtime/report-generation.lock'):
        for vertical in (False, True):
            name = 'author-word-vertical.mp4' if vertical else 'author-word.mp4'
            path = stage/name
            print('RENDER', name, flush=True)
            subprocess.run([str(node), str(RUNTIME/'video/render-author.mjs'), '--word', str(stage/'author-word.json'),
                '--output', str(path), *(['--vertical'] if vertical else [])], check=True, timeout=1800)
            info = json.loads(subprocess.check_output([str(compositor/'ffprobe'), '-v','error','-show_entries',
                'format=duration:stream=codec_type,width,height', '-of','json',str(path)],
                env={**os.environ, 'DYLD_LIBRARY_PATH': str(compositor)}))
            duration = float(info['format']['duration'])
            movie = next((s for s in info['streams'] if s['codec_type']=='video'), {})
            if (abs(duration-(word['seconds']+4)) > .2
                    or not any(s['codec_type']=='audio' for s in info['streams'])
                    or (movie.get('width'), movie.get('height')) != ((1080,1920) if vertical else (1280,720))):
                raise ValueError('Rendered greeting failed media validation')
            verified[name] = {'sha256':sha(path), 'seconds':duration, 'bytes':path.stat().st_size}
    destination = SOURCE/'mobile/assets/author'
    backup = generated/'previous-assets'
    if not backup.exists(): shutil.copytree(destination, backup)
    for name in ('author-word.json','author-word.m4a','author-word.wav','author-word.mp4','author-word-vertical.mp4'):
        original = stage/name if name.endswith('.mp4') else generated/name
        pending = destination/(name+'.pending'); shutil.copy2(original, pending); pending.replace(destination/name)
    receipt = {'installed_at': time.time(), 'voice':word['voice'], 'audio_sha256':word['audio_sha256'], 'videos':verified}
    (generated/'installation.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print('INSTALLED selected greeting audio and both synchronized videos', flush=True)


if __name__ == '__main__': main()
