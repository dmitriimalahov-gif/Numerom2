"""Select a continuous, transcribed reference from the owner's new recording."""
from __future__ import annotations
import gc
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ['HF_HUB_OFFLINE']='1'
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
ROOT=Path(__file__).resolve().parents[1]
LAB=ROOT/'backend/private/voice-lab-new-recording-2026-11-07'
SLOT=Path.home()/'Library/Application Support/NumerOM/runtime/backend/private/runtime/report-generation.lock'
sys.path.insert(0,'/Users/brandbox/Developer/helper-voice/local')
from report_generation_slot import report_generation_slot
from audio_clean import highpass,soft_edges,loudness
from make_my_voice import pick_window
import generate_local as voice
from mlx_whisper import transcribe
from mlx_whisper.transcribe import ModelHolder


def main():
    source=LAB/'original.wav'
    audio,sr=voice.sf.read(source,dtype='float32')
    print('WAIT: reference transcription slot',flush=True)
    with report_generation_slot(SLOT):
        transcript=LAB/'transcript.json'
        if transcript.exists():result=json.loads(transcript.read_text())
        else:
            print('TRANSCRIBE: new recording',flush=True)
            result=transcribe(voice.to16k(audio,sr),path_or_hf_repo=voice.WHISPER,language='ru',
                             initial_prompt='Дмитрий. Нумером. Число души, число ума, число судьбы. Горизонтали, вертикали, диагонали.')
            transcript.write_text(json.dumps(result,ensure_ascii=False,indent=2));transcript.chmod(0o600)
        # Prefer a connected explanation near the start, before number lists.
        spoken=[s for s in result['segments'] if 0<=s['start'] and s['end']<=90]
        start,end,text=pick_window(spoken)
        selected=audio[max(0,round((start-.15)*sr)):min(len(audio),round((end+.25)*sr))]
        selected=soft_edges(highpass(selected,sr,hz=55),sr,head=.14,tail=.3,fade_in=.015,fade_out=.055,threshold=.002)
        selected=loudness(selected,rms_db=-20,peak_db=-2)
        reference=LAB/'reference-natural.wav'
        voice.sf.write(reference,selected,sr);reference.chmod(0o600)
        check=transcribe(voice.to16k(selected,sr),path_or_hf_repo=voice.WHISPER,language='ru',initial_prompt='Нумером. Дмитрий.')
        heard=check['text'].strip()
        (LAB/'reference-natural.txt').write_text(heard);(LAB/'reference-natural.txt').chmod(0o600)
        meta={'recording_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'span_seconds':[start,end],
              'reference_seconds':round(len(selected)/sr,3),'transcript':heard,'original_segment_text':text,
              'highpass_hz':55,'noise_reduction':False,'gate':False,'profile':'numerom-dmitrii-v4-new-recording-preview'}
        (LAB/'reference-provenance.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
        (LAB/'reference-provenance.json').chmod(0o600)
        ModelHolder.model=None;ModelHolder.model_path=None;gc.collect();voice.mx.clear_cache()
        print('REFERENCE READY',json.dumps(meta,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
