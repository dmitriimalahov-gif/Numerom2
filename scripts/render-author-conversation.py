"""Local selected voice, natural paragraphs and measured sentence timings for the greeting."""
import difflib
import gc
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from domain.consultation import VOICE, VOICE_IDENTITY
from numerom_services import service_root
from report_generation_slot import report_generation_slot
import voice_tempo
import russian_pronunciation

SOURCE = ROOT/'packages/project-knowledge/author-word.json'
OUT = ROOT/'artifacts/author-greeting-ru-stress-v1'
PASS = .04


def words(text):
    # Exact alternative spellings of the product name, not phonetic fuzzing.
    text = re.sub(r'\b(?:NumerOM|Нумер\s*ОМ)\b', 'нумером', russian_pronunciation.unmark(text), flags=re.I)
    return re.findall(r'[а-я]+', text.lower().replace('ё', 'е'))


def sentences(text):
    return [part.strip() for part in re.split(r'(?<=[.!?])\s+', text) if part.strip()]


def sentence_timings(text, recognized, duration):
    """Match known script words to measured timestamps, never equal-length scenes."""
    measured = [(token, float(w['start']), float(w['end']))
                for segment in recognized['segments'] for w in segment.get('words', [])
                for token in words(w['word'])]
    expected = words(text)
    mapping = {}
    for block in difflib.SequenceMatcher(None, expected, [w[0] for w in measured], autojunk=False).get_matching_blocks():
        mapping.update({block.a+i: measured[block.b+i] for i in range(block.size)})
    offset, result = 0, []
    for sentence in sentences(text):
        size = len(words(sentence))
        matched = [mapping[i] for i in range(offset, offset+size) if i in mapping]
        if not matched or len(matched) < max(1, size-1):
            raise ValueError('Greeting sentence cannot be aligned to its spoken words')
        start, end = max(0, matched[0][1]), min(duration, matched[-1][2])
        if not start < end or result and start < result[-1]['end']:
            raise ValueError('Greeting sentence timings overlap or are empty')
        result.append({'text': sentence, 'start': start, 'end': end})
        offset += size
    return result


def main():
    source = json.loads(SOURCE.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location('project_voice', ROOT/'scripts/generate-project-voices.py')
    worker = importlib.util.module_from_spec(spec); spec.loader.exec_module(worker)
    reference, transcript, ref_hash, profile, temperature, clean = worker.reference(VOICE)
    assert transcript is None and clean is None and profile == VOICE_IDENTITY
    tempo = voice_tempo.TEMPO[VOICE]
    print('WAIT: shared NumerOM generation slot', flush=True)
    slot = service_root()/'backend/private/runtime/report-generation.lock'
    with report_generation_slot(slot):
        sys.path.insert(0, str(worker.HELPER/'local'))
        import generate_local as voice
        from mlx_whisper.transcribe import ModelHolder
        whisper = worker.local_whisper_model(voice.WHISPER)
        voice.mx.set_cache_limit(256*1024*1024)
        def recognize(audio, sr):
            result = voice.mlx_whisper.transcribe(voice.to16k(audio, sr), path_or_hf_repo=whisper,
                language='ru', word_timestamps=True, initial_prompt='Нумером.')
            ModelHolder.model = None; ModelHolder.model_path = None
            gc.collect(); voice.mx.clear_cache()
            return result
        parts, timing, checks, at = [], [], [], 0.0
        for index, paragraph in enumerate(source['paragraphs']):
            spoken = paragraph
            for written, said in source['speech'].items():
                spoken = re.sub(r'\b'+re.escape(written)+r'\b', said, spoken)
            marked=source.get('pronunciation',{}).get('paragraphs',[])
            if len(marked)!=len(source['paragraphs']) or russian_pronunciation.unmark(marked[index])!=spoken:
                raise ValueError('Greeting pronunciation must preserve the complete spoken script')
            spoken=marked[index]
            key = hashlib.sha256(json.dumps([spoken, ref_hash, profile, worker.MODEL,russian_pronunciation.VERSION], ensure_ascii=False).encode()).hexdigest()
            wav, metadata = OUT/f'{index}-{key[:16]}.wav', OUT/f'{index}-{key[:16]}.json'
            saved = json.loads(metadata.read_text()) if metadata.exists() else {}
            if wav.exists() and saved.get('key') == key and saved.get('difference', 1) <= PASS:
                audio, sr = voice.sf.read(wav, dtype='float32')
                check = saved
                print('REUSE paragraph', index+1, flush=True)
            else:
                best = None
                for attempt in range(3):
                    seed = 20261209 + index*37 + attempt*101
                    voice.mx.random.seed(seed)
                    model = voice.load_model(worker.MODEL);russian_pronunciation.apply_adapter(model,voice.mx);sr = model.sample_rate
                    print('SYNTH paragraph', index+1, 'attempt', attempt+1, flush=True)
                    generated = list(model.generate(text=spoken, ref_audio=str(reference), lang_code='russian',
                        temperature=temperature, top_p=.95, top_k=50, max_tokens=850))
                    audio = voice.np.concatenate([voice.np.asarray(p.audio) for p in generated]).astype('float32')
                    del model, generated
                    gc.collect(); voice.mx.clear_cache()
                    recognized = recognize(audio, sr)
                    difference = 1-difflib.SequenceMatcher(None, words(spoken), words(recognized['text'])).ratio()
                    print('CHECK', index+1, f'{difference:.1%}', flush=True)
                    check = {'key': key, 'text': spoken, 'heard': recognized['text'], 'difference': difference,
                        'recognition': recognized, 'seed': seed}
                    if best is None or difference < best[0]['difference']: best = (check, audio)
                    if difference <= PASS: break
                check, audio = best
                if check['difference'] > PASS:
                    voice.sf.write(OUT/f'review-{index+1}.wav', audio, sr)
                    raise ValueError(f'Greeting paragraph {index+1} failed word check: {check["heard"]}')
                assert voice.np.isfinite(audio).all() and .3 < len(audio)/sr < 60
                voice.sf.write(wav, audio, sr)
                metadata.write_text(json.dumps(check, ensure_ascii=False, indent=2))
            bounds = sentence_timings(spoken, check['recognition'], len(audio)/sr)
            written = sentences(paragraph)
            assert len(bounds) == len(written)
            audio = voice_tempo.stretch(audio, sr, tempo, voice.sf)
            if parts:
                pause = voice.np.zeros(round(sr*.3), dtype='float32')
                parts.append(pause); at += len(pause)/sr
            timing.extend({'paragraph': index, 'text': sentence,
                'start': round(at+bound['start']/tempo, 3), 'end': round(at+bound['end']/tempo, 3)}
                for sentence, bound in zip(written, bounds))
            parts.append(audio); at += len(audio)/sr
            checks.append({k: check[k] for k in ('text','heard','difference','seed')})
        complete = voice.loudness(voice.np.concatenate(parts))
        final = recognize(complete, sr)
        difference = 1-difflib.SequenceMatcher(None, words(' '.join(c['text'] for c in checks)), words(final['text'])).ratio()
        if difference > PASS: raise ValueError('Assembled greeting failed word check')
        master, encoded = OUT/'author-word.wav', OUT/'author-word.m4a'
        voice.sf.write(master, complete, sr)
        pending = OUT/'author-word.pending.m4a'; pending.unlink(missing_ok=True)
        subprocess.run(['/usr/bin/afconvert','-f','m4af','-d','aac','-b','64000',str(master),str(pending)], check=True)
        pending.replace(encoded)
        manifest = {k: source[k] for k in ('id','title','author','paragraphs')}
        manifest.update(seconds=round(len(complete)/sr, 3), sentences=timing, voice=VOICE, profile=profile,
            tempo=tempo, post_processing='level_matching_only; pitch_preserving_tempo',
            reference_sha256=ref_hash, audio_sha256=hashlib.sha256(encoded.read_bytes()).hexdigest(),
            worst_difference=max(c['difference'] for c in checks), assembled_difference=difference,
            checks=checks, pronunciation_review='pending_user_listening')
        manifest['pronunciation']=russian_pronunciation.VERSION
        (OUT/'author-word.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
        print('READY', encoded, manifest['seconds'], 'seconds; final word check', f'{difference:.1%}', flush=True)


if __name__ == '__main__': main()
