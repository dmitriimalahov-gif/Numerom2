"""Single local Helper/Qwen worker. Resumable, verified chunks, atomic ready files."""
from __future__ import annotations
import argparse
import difflib
import fcntl
import gc
import hashlib
import importlib.util
import importlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import time
from report_generation_slot import report_generation_slot
import voice_tempo
import russian_pronunciation
os.environ['HF_HUB_OFFLINE']='1'
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
from num2words import num2words

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from domain.report_audio import ready_audio
from services.report_files import read_json
HELPER=Path('/Users/brandbox/Developer/helper-voice')
MODEL='mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16'
# A job without 'voice' is new and uses Dmitrii's cloned voice (helper-voice
# local/make_my_voice.py). Jobs queued before 23.10.2026 are marked 'helper-male',
# so a partly voiced report or lesson keeps one voice in every chapter.
VOICE='dmitrii'
# Reference stem, cache profile, sampling temperature and helper-voice cleaning.
# Dmitrii's voice uses the settings chosen for it in helper-voice (--clean --temperature 0.75).
VOICES={'helper-male':('voice/helper_male_ref','numerom-helper-male-project-v1',.65,False),
    'dmitrii':('voice/dmitrii_ref','numerom-dmitrii-v2-clean',.75,True),
    'dmitrii-conversation-v1':(None,'dmitrii-speaker-identity-e8bbe873-tempo120-v1',.85,None)}
LEXICON=('Термины курса: Сурья, Чандра, Гуру, Раху, Кету, Шани, Шукра, Буддха, '
    'Джанма-анк, Атма-анк, Бхагья-анк, Нама-анк, Шакти-анк, '
    'Атри, Анусуйя, Адити, Чхайя, Сандья, Лакшми, Сарасвати, Дакша, Рохини, Кашьяпа, саттва, раджас, тамас, Муладхара, Свадхистхана, Манипура, Анахата, Вишуддха, '
    'Сурья Намаха, Шанайе Намаха, Мангалая Намаха, Кетаве Намаха, Буддхая Намаха, '
    'Ом Чандрайа намаха, Ом намо бхагаватэ Ваманадевайя, Ом брим Брихаспатайе намаха.')

LATIN_LETTERS={'A':'а','B':'бэ','C':'цэ','D':'дэ','E':'е','F':'эф','G':'гэ','H':'аш','I':'и','J':'йот','K':'ка',
    'L':'эль','M':'эм','N':'эн','O':'о','P':'пэ','Q':'ку','R':'эр','S':'эс','T':'тэ','U':'у','V':'вэ',
    'W':'дубль-вэ','X':'икс','Y':'игрек','Z':'зэт'}

def atomic(path,value):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2));temp.replace(path)

def save_generation(cache,generation):
    """Private diagnostics only; never a substitute for the audio quality gate."""
    path=cache/'generation.json';atomic(path,generation);path.chmod(0o600)

def begin_generation_cycle(cache):
    path=cache/'generation.json'
    previous=json.loads(path.read_text()) if path.exists() else {}
    cycle=previous.get('cycle',0)
    if not isinstance(cycle,int) or isinstance(cycle,bool) or cycle<0:
        raise ValueError('Invalid narration generation cycle')
    base_seed=secrets.randbits(32)
    # An explicit retry must not replay the previous cycle, even if entropy
    # happens to return the same value. Segment cache keys remain unchanged.
    if base_seed==previous.get('base_seed'):base_seed=(base_seed+1)%(2**32)
    history=previous.get('history',[])
    if not isinstance(history,list):raise ValueError('Invalid narration generation history')
    if cycle:
        history=[*history,{key:previous[key] for key in
            ('cycle','base_seed','started_at','completed_at','status') if key in previous}]
    generation={'version':1,'cycle':cycle+1,'base_seed':base_seed,'started_at':time.time(),
        'status':'working','attempts':[],'reused_segments':[],'history':history[-8:]}
    save_generation(cache,generation)
    return generation

from domain.media_retry import delay as retry_delay, scheduled
AUTO_RETRY_DELAY=300

def job_priority(job):
    """Every paid chapter precedes the bulk library refresh; rechecked per clip."""
    report={'full-report-summary':-6,'full-report-synthesis':-5,'full-report-personal':-4,'full-report-lines':-3.5}
    guides={'numbers':-3,'lines':-2,'methods':-1,'theory':0,'intro':1,'exercise':2,'quiz':3,'challenge':4,'guide':5}
    return (report.get(job['id'],-3.25) if job['id'].startswith('full-report-')
            else guides.get(job.get('section'),9),job.get('lesson_title',''),job['id'])


def ordered_jobs(root, jobs):
    """Give new overviews priority, then finish the nearest complete report.

    Alphabetical chapter order spread hundreds of chapters across all reports,
    keeping every video waiting. Rank remaining work without changing scripts
    or skipping unavailable/corrupt audio. Existing media jobs supply membership.
    """
    pending={j['hash'] for j in jobs if j.get('id','').startswith('full-report-')}
    groups={}
    if pending:
        for path in (root.parent/'report-video').glob('*/job.json'):
            saved=read_json(path) or {}
            report=saved.get('report')
            if not isinstance(report,dict):continue
            items=report.get('narration')
            if not isinstance(items,list) or not items:continue
            if any(not isinstance(x,dict) or not isinstance(x.get('hash'),str)
                   or not re.fullmatch('[a-f0-9]{64}',x['hash']) or not isinstance(x.get('text'),str) for x in items):continue
            members=pending.intersection(x['hash'] for x in items)
            if not members:continue
            remaining=sum(len(x['text']) for x in items if not ready_audio(root/'clips'/x['hash'],x['hash']))
            rank=(remaining,path.parent.name)
            for key in members:groups[key]=min(groups.get(key,rank),rank)
    focus=min(groups.values()) if groups else None
    previews={'full-report-summary','full-report-synthesis','full-report-personal','full-report-lines'}
    def priority(job):
        if job['id'] in previews:band=0
        elif focus is not None and groups.get(job['hash'])==focus:band=1
        elif job['id'].startswith('full-report-'):band=2
        else:band=3
        return (band,job_priority(job))
    return sorted(jobs,key=priority)

def automatic_retry_due(cache,now=None):
    path=cache/'automatic-retry.json'
    try:
        saved=json.loads(path.read_text())
        return (type(saved.get('used')) is int and saved['used']>=0
            and scheduled(saved,'after') and saved['after']<=(time.time() if now is None else now))
    except (OSError,ValueError,TypeError,AttributeError):return False

def reserve_automatic_retry(cache):
    # The worker's exclusive flock protects the persistent budget across restarts.
    path=cache/'automatic-retry.json';saved=json.loads(path.read_text())
    if not automatic_retry_due(cache):raise ValueError('Automatic narration retry is not due')
    saved.update(used=saved['used']+1,after=time.time()+retry_delay(saved['used']+2))
    atomic(path,saved);path.chmod(0o600)

def schedule_automatic_retry(cache):
    path=cache/'automatic-retry.json'
    try:saved=json.loads(path.read_text()) if path.exists() else {'used':0}
    except (OSError,ValueError):return
    if type(saved.get('used')) is not int or saved['used']<0:return
    saved['after']=time.time()+retry_delay(saved['used']+1)
    atomic(path,saved);path.chmod(0o600)

def generation_seed(generation,index,attempt):
    return (generation['base_seed']+index*13+attempt*101)%(2**32)

def reference(name):
    """Reference audio, transcript, hash, cache profile, temperature and cleaning; read per job so a re-recorded voice applies."""
    stem,profile,temperature,clean=VOICES[name]
    if name == 'dmitrii-conversation-v1':
        directory=ROOT/'backend/private/voice-profiles'/name
        settings=json.loads((directory/'profile.json').read_text())
        wav=directory/'reference.wav'
        digest=hashlib.sha256(wav.read_bytes()).hexdigest()
        if (settings.get('id')!=name or settings.get('mode')!='speaker_embedding'
                or settings.get('ref_text') is not None or settings.get('model')!=MODEL
                or digest!='e8bbe873b833a9916a83d31276424d76fc2b942bfa8bf58ee09d526cb367d2aa'
                or settings.get('reference_sha256')!=digest):
            raise ValueError('Selected conversation voice reference does not match its cache identity')
        return wav,None,digest,profile,temperature,clean
    wav=HELPER/(stem+'.wav')
    return wav,(HELPER/(stem+'.txt')).read_text().strip(),hashlib.sha256(wav.read_bytes()).hexdigest(),profile,temperature,clean

def spoken(text):
    # Spell the course's written notation without changing its arithmetic.
    # Restrict Cyrillic variable names to formulas/lists: ordinary А, в, с remain words.
    names={'А':'а','В':'вэ','С':'эс'}
    def operand(value):
        value=value.strip()
        return names.get(value,value)
    text=re.sub(r'\|\s*(ЧП\s*[1-4]|[АВС])\s*[−–-]\s*(ЧП\s*[1-4]|[АВС])\s*\|',
        lambda m:'модуль разности '+operand(m[1])+' и '+operand(m[2]),text)
    text=re.sub(r'\bА\s*,\s*В\s*,\s*С\b','а, вэ, эс',text)
    text=re.sub(r'\bЧП\s*([1-4])\b',r'число проблемы \1',text)
    text=re.sub(r'\bДДММ\b','день и месяц без разделителей',text)
    # A three-cell route is an ordered list, not a range or subtraction.
    text=re.sub(r'(?<![0-9–-])([1-9])[–-]([1-9])[–-]([1-9])(?![0-9–-])',r'\1, \2, \3',text)
    text=text.replace('×',' умножить на ')
    text=re.sub(r'−\s*(?=\d)','минус ',text)
    text=re.sub(r'[ \t]+',' ',text)
    ordinals={'1':'первая','2':'вторая','3':'третья','4':'четвёртая','5':'пятая','6':'шестая','7':'седьмая','8':'восьмая','9':'девятая'}
    text=re.sub(r'\b([1-9])-я\b',lambda m:ordinals[m[1]],text)
    # TTS cannot read a run of digits, and Whisper writes a spoken million as "1,983, 1982".
    # Five or more digits (the planet product 1983982, phones, codes) are read digit by digit;
    # the planet line then names each digit. The report text keeps the integer.
    digits=('ноль','один','два','три','четыре','пять','шесть','семь','восемь','девять')
    text=re.sub(r'\b\d{5,}\b',lambda m:', '.join(digits[int(d)] for d in m[0]),text)
    # A Latin-script name is spelled letter by letter (Абракадабра); the Russian model
    # drops a lone «M». Name each letter as in Russian school mathematics.
    text=re.sub(r'(?<![A-Za-z])([A-Z])(?![A-Za-z])',lambda m:LATIN_LETTERS[m[1]],text)
    text=re.sub(r'\b(\d{1,4})\b',lambda m:num2words(int(m[0]),lang='ru'),text)
    text=re.sub(r'\b[А-ЯЁ]{3,}\b',lambda m:m[0].lower(),text)
    text=re.sub(r'\bОМ\b','Ом',text)
    return text

def sentences(text):
    """Sentences of one segment for the fallback; fragments under three words join a neighbour."""
    out=[]
    for part in (p.strip() for p in re.split(r'(?<=[.!?])\s+',text)):
        if part and out and len(out[-1].split())<3:out[-1]+=' '+part
        elif part:out.append(part)
    if len(out)>1 and len(out[-1].split())<3:
        last=out.pop();out[-1]+=' '+last  # pop first: `out[-2] += out.pop()` writes to a shifted index
    return out

def segments(text,limit=330):
    # Break at sentence/list boundaries; preserve short headings with their sentence.
    sentences=re.split(r'(?<=[.!?;])\s+|\n+',spoken(text))
    chunks=[];current=''
    for sentence in sentences:
        if not sentence.strip():continue
        sentence=sentence.strip()
        if len(sentence)<=limit and re.search(r'\bОм\b',sentence,re.I):
            if current:chunks.append(current);current=''
            chunks.append(sentence);continue
        if sentence[-1] not in '.!?;':sentence+='.'
        if len(sentence)>limit:
            words=sentence.split();sentence=''
            for word in words:
                if len(sentence)+len(word)>limit-30:
                    if current:chunks.append(current);current=''
                    chunks.append(sentence);sentence=''
                sentence=(sentence+' '+word).strip()
        if current and len(current)+len(sentence)>limit:chunks.append(current);current=''
        current=(current+' '+sentence).strip()
    if current:chunks.append(current)
    return chunks

def comparison_words(text,voice):
    # ASR writes inflected numerals as digits ("одиннадцати" -> "11").
    # Compare their values without treating that spelling choice as a missing word.
    forms={'одна':'один','одно':'один','одного':'один','одной':'один','двух':'два','двум':'два','две':'два',
        'трех':'три','трем':'три','четырех':'четыре','пяти':'пять','шести':'шесть',
        'семи':'семь','восьми':'восемь','девяти':'девять','десяти':'десять','действия':'действие',
        'одиннадцати':'одиннадцать','двенадцати':'двенадцать','двадцати':'двадцать',
        'тридцати':'тридцать','пожертвования':'пожертвование','упайя':'упая','упайи':'упаи',
        'мулатхара':'муладхара','сватхистхана':'свадхистхана','вишудха':'вишуддха','вишутха':'вишуддха',
        'саттве':'сатве','саттва':'сатва'}
    # Whisper prints dates as digits: «десятое ... восемьдесят второго»
    # and «10 ... 1982» name the same date, despite case and ordinal endings.
    ordinals = {'перв': 1, 'втор': 2, 'трет': 3, 'четверт': 4, 'пят': 5, 'шест': 6,
        'седьм': 7, 'восьм': 8, 'девят': 9, 'десят': 10, 'одиннадцат': 11,
        'двенадцат': 12, 'тринадцат': 13, 'четырнадцат': 14, 'пятнадцат': 15,
        'шестнадцат': 16, 'семнадцат': 17, 'восемнадцат': 18, 'девятнадцат': 19,
        'двадцат': 20, 'тридцат': 30, 'сороков': 40, 'пятидесят': 50,
        'шестидесят': 60, 'семидесят': 70, 'восьмидесят': 80, 'девяност': 90}
    for stem, number in ordinals.items():
        for ending in ('ый','ой','ий','ое','ая','ую','ого','ому','ым','ом','ые','ых','им','ем','ья','ье','ьего','ьему','ьим'):
            forms[stem + ending] = num2words(number, lang='ru')
    # A spoken letter name ("эм") is often printed as the letter itself ("М").
    # Both sides map, so prepositions such as "в" stay equal to themselves.
    letters = {'б':'бэ','в':'вэ','г':'гэ','д':'дэ','ж':'жэ','з':'зэ','к':'ка','л':'эль','м':'эм','н':'эн','п':'пэ',
        'р':'эр','с':'эс','т':'тэ','ф':'эф','х':'ха','ц':'цэ','ч':'че','ш':'ша','щ':'ща'}
    words = [letters.get(word,forms.get(word,word)).replace('саттв','сатв') for word in voice.words(spoken(russian_pronunciation.unmark(text)))]
    return [word for index,word in enumerate(words)
        if not (word == 'один' and index + 1 < len(words) and words[index + 1] == 'тысяча')]


def local_whisper_model(repo):
    """Resolve the complete offline snapshot before spending time on synthesis."""
    from huggingface_hub import snapshot_download
    path=Path(snapshot_download(repo_id=repo,local_files_only=True))
    if not (path/'config.json').is_file() or not any((path/name).is_file() for name in ('weights.safetensors','weights.npz')):
        raise FileNotFoundError(f'Incomplete local Whisper model: {repo}')
    return str(path)


def model_memory_available():
    """Keep both models only on a roomy machine; unavailable telemetry fails low."""
    try:
        if sys.platform == 'darwin':
            total = int(subprocess.run(['/usr/sbin/sysctl', '-n', 'hw.memsize'],
                capture_output=True, text=True, check=True, timeout=2).stdout.strip())
            pressure = subprocess.run(['/usr/bin/memory_pressure', '-Q'],
                capture_output=True, text=True, check=True, timeout=2).stdout
            match = re.search(r'System-wide memory free percentage:\s*(\d+)%', pressure)
            if not match:return False
            available = total * int(match[1]) / 100
        elif sys.platform.startswith('linux'):
            info = dict(re.findall(r'^(MemTotal|MemAvailable):\s*(\d+)\s+kB',
                Path('/proc/meminfo').read_text(), re.M))
            total, available = int(info['MemTotal']) * 1024, int(info['MemAvailable']) * 1024
        else:return False
        return total >= 32 * 1024**3 and available >= 8 * 1024**3
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        return False


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--watch',action='store_true');parser.add_argument('--retry-failed',action='store_true')
    parser.add_argument('--auto-retry',action='store_true',help='Recover failures automatically with persistent backoff up to six hours')
    parser.add_argument('--only-prefix',default='',help='Process only clip IDs with this prefix')
    parser.add_argument('--lesson-prefix',default='',help='Process only lesson IDs with this prefix')
    parser.add_argument('--limit',type=int,default=0,help='Maximum number of clips in this invocation')
    memory = parser.add_mutually_exclusive_group()
    memory.add_argument('--low-memory',action='store_true',help='Unload TTS before recognition so both models do not share memory')
    memory.add_argument('--reuse-models',action='store_true',help='Reuse TTS and recognition within a chapter when memory permits; release both before unlocking')
    args=parser.parse_args();processed=0;attempted=set()
    root=ROOT/'backend/private/narration';root.mkdir(parents=True,exist_ok=True)
    lock=(root/'worker.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    print('WORKER STARTED; mode:', 'watch' if args.watch else 'batch', flush=True)
    # generate_local.py imports its sibling modules (audio_clean) by name.
    if str(HELPER/'local') not in sys.path:sys.path.insert(0,str(HELPER/'local'))
    spec=importlib.util.spec_from_file_location('helper_voice',HELPER/'local/generate_local.py')
    voice=importlib.util.module_from_spec(spec);spec.loader.exec_module(voice)
    whisper_cache=importlib.import_module('mlx_whisper.transcribe').ModelHolder
    whisper_model=local_whisper_model(voice.WHISPER)
    voice.mx.set_cache_limit(256*1024*1024)
    model=None
    while True:
        jobs=[]
        for path in (root/'jobs').glob('*.json'):
            key=path.stem
            if not re.fullmatch('[a-f0-9]{64}',key):continue
            cache=root/'clips'/key
            try:job=json.loads(path.read_text())
            except (OSError,ValueError):continue
            if job.get('hash')!=key or not isinstance(job.get('text'),str) or not 1<=len(job['text'])<=20000:continue
            if job.get('superseded_by'):continue
            if job.get('voice',VOICE) not in VOICES:continue
            # Superseded selected-voice jobs remain recoverable, but must not
            # generate new audio with the known stress problem.
            if job.get('voice')=='dmitrii-conversation-v1' and job.get('pronunciation')!=russian_pronunciation.VERSION:continue
            if not job.get('id','').startswith(args.only_prefix):continue
            if not job.get('lesson_id','').startswith(args.lesson_prefix):continue
            valid=ready_audio(cache,key)
            manual_retry=args.retry_failed and key not in attempted
            auto_retry=args.auto_retry and automatic_retry_due(cache)
            if valid or ((cache/'failed.json').exists() and not (manual_retry or auto_retry)):continue
            jobs.append(job)
        # A paid report starts with its overview, then personal numbers. The
        # common generation slot also excludes Ollama and Remotion while a chapter runs.
        jobs=ordered_jobs(root,jobs)
        if not jobs:
            if not args.watch:break
            if model is not None:model=None;gc.collect();voice.mx.clear_cache()
            time.sleep(3);continue
        for job in jobs:
            if args.limit and processed>=args.limit:return
            with report_generation_slot():
                processed+=1
                key=job['hash'];cache=root/'clips'/key;cache.mkdir(parents=True,exist_ok=True)
                if (cache/'failed.json').exists() and args.auto_retry and automatic_retry_due(cache):
                    reserve_automatic_retry(cache)
                attempted.add(key)
                atomic(cache/'working.json',{'started_at':time.time(),'id':job['id']})
                print('START',job.get('lesson_title',''),job['id'],flush=True)
                generation=None
                try:
                    ref,ref_text,ref_hash,profile,temperature,clean=reference(job.get('voice',VOICE))
                    pronunciation=job.get('pronunciation')==russian_pronunciation.VERSION
                    generation=begin_generation_cycle(cache)
                    reuse_models=args.reuse_models and model_memory_available()
                    performance={'mode':'reuse' if reuse_models else 'low' if args.low_memory or args.reuse_models else 'tts-only',
                        'tts_loads':0,'asr_loads':0,'tts_load_seconds':0.0,'synthesis_seconds':0.0,'recognition_seconds':0.0}
                    generation['performance']=performance
                    # A failed cycle changes delivery sampling, not the speaker,
                    # tempo, text or quality threshold. Previously good chunks stay.
                    if generation['cycle']>1 and job.get('voice')=='dmitrii-conversation-v1':
                        temperature=(.85,.65,.75)[(generation['cycle']-1)%3]
                    generation['temperature']=temperature
                    save_generation(cache,generation)
                    def attempts(text,index,offset,label):
                        """Up to three seeds for one text; the best (audio, difference, heard, cues, seed, attempt)."""
                        nonlocal model, reuse_models
                        best=None
                        for attempt in range(3):
                            if reuse_models and not model_memory_available():
                                reuse_models=False;performance['mode']='low-fallback'
                                model=None;whisper_cache.model=None;whisper_cache.model_path=None
                                gc.collect();voice.mx.clear_cache()
                            if model is None:
                                started=time.monotonic()
                                model=voice.load_model(MODEL)
                                if pronunciation:russian_pronunciation.apply_adapter(model,voice.mx)
                                performance['tts_loads']+=1
                                performance['tts_load_seconds']+=time.monotonic()-started
                            sr=model.sample_rate
                            print(f"SYNTH {job['id']} {label} try {attempt+1}",flush=True)
                            seed=generation_seed(generation,index,offset+attempt)
                            diagnostic={'segment':index+1,'attempt':offset+attempt+1,'seed':seed,'status':'synthesizing'}
                            generation['attempts'].append(diagnostic);save_generation(cache,generation)
                            voice.mx.random.seed(seed)
                            options={'text':text,'ref_audio':str(ref),'lang_code':'russian','temperature':temperature,'max_tokens':520}
                            if ref_text is None:
                                options.update(top_p=.95,top_k=50)
                            else:
                                options.update(ref_text=ref_text,top_p=.9)
                            started=time.monotonic()
                            result=list(model.generate(**options))
                            raw=voice.np.concatenate([voice.np.asarray(p.audio) for p in result]).astype(voice.np.float32)
                            audio=(raw if clean is None else
                                voice.soft_edges(voice.gate(voice.highpass(raw,sr),sr),sr) if clean else voice.polish(raw,sr))
                            del result;gc.collect();voice.mx.clear_cache()
                            performance['synthesis_seconds']+=time.monotonic()-started
                            if args.low_memory or (args.reuse_models and not reuse_models):
                                model=None;gc.collect();voice.mx.clear_cache()
                            started=time.monotonic()
                            if whisper_cache.model is None:performance['asr_loads']+=1
                            transcription=voice.mlx_whisper.transcribe(voice.to16k(audio,sr),path_or_hf_repo=whisper_model,language='ru',initial_prompt=LEXICON)
                            performance['recognition_seconds']+=time.monotonic()-started
                            heard=transcription['text'].strip()
                            # A bounded chapter may reuse both models on roomy Macs. The
                            # finally block always frees both before releasing the GPU slot.
                            if not reuse_models:
                                whisper_cache.model=None;whisper_cache.model_path=None
                            gc.collect()
                            difference=1-difflib.SequenceMatcher(None,comparison_words(text,voice),comparison_words(heard,voice)).ratio()
                            voice.mx.clear_cache()
                            diagnostic.update({'status':'recognized','difference':difference});save_generation(cache,generation)
                            if best is None or difference<best[1]:best=(audio,difference,heard,transcription.get('segments',[]),seed,offset+attempt+1)
                            print(f"CHECK {job['id']} {label} try {attempt+1}: {difference:.1%}",flush=True)
                            if difference<=.07:break
                        return best,sr
                    parts=[];checks=[];tempo=voice_tempo.TEMPO.get(job.get('voice',VOICE),1)
                    for index,text in enumerate(segments(job['text'],210 if job['section']=='quiz' else 330)):
                        if pronunciation:text=russian_pronunciation.prepare(text)
                        identity=[text,profile,MODEL,ref_hash]
                        if pronunciation:identity.append(russian_pronunciation.VERSION)
                        chunkhash=hashlib.sha256(json.dumps(identity).encode()).hexdigest()[:16]
                        wav=cache/f'{index}-{chunkhash}.wav';checkfile=wav.with_suffix('.json')
                        if wav.exists() and checkfile.exists():
                            check=json.loads(checkfile.read_text());audio,sr=voice.sf.read(wav,dtype='float32')
                            generation['reused_segments'].append({'segment':index+1,'chunk_hash':chunkhash,
                                'generation':check.get('generation')})
                            save_generation(cache,generation)
                        else:
                            best,sr=attempts(text,index,0,str(index+1))
                            pieces=sentences(text)
                            if best[1]>.07 and len(pieces)>1:
                                # A long repetitive list can lose an item in one pass. As in the
                                # helper-voice setup, read it sentence by sentence; the joined
                                # result passes the same check against the whole segment.
                                found=[]
                                for number,piece in enumerate(pieces):
                                    piece_best,sr=attempts(piece,index,3*(number+1),f'{index+1}.{number+1}')
                                    found.append(piece_best)
                                gap=voice.np.zeros(round(sr*.25),dtype=voice.np.float32)
                                joined,timing,offset=[],[],0.0
                                for piece_best in found:
                                    if joined:joined.append(gap);offset+=len(gap)/sr
                                    joined.append(piece_best[0])
                                    # Whisper may end a cue after the sentence audio; clip it to this
                                    # sentence so cues of neighbouring sentences never overlap.
                                    length=len(piece_best[0])/sr
                                    timing+=[{**c,'start':c['start']+offset,'end':min(c['end'],length)+offset} for c in piece_best[3]
                                             if isinstance(c.get('start'),(int,float)) and isinstance(c.get('end'),(int,float))
                                             and 0<=c['start']<min(c['end'],length)]
                                    offset+=length
                                heard=' '.join(piece_best[2] for piece_best in found)
                                difference=1-difflib.SequenceMatcher(None,comparison_words(text,voice),comparison_words(heard,voice)).ratio()
                                print(f"CHECK {job['id']} {index+1} by sentences: {difference:.1%}",flush=True)
                                if difference<best[1]:
                                    best=(voice.np.concatenate(joined),difference,heard,timing,found[0][4],'sentences')
                            audio,difference,heard,timing,seed,selected_attempt=best
                            selected={'cycle':generation['cycle'],'base_seed':generation['base_seed'],
                                'seed':seed,'attempt':selected_attempt}
                            if difference>.07:
                                voice.sf.write(cache/f'review-{index+1}.wav',audio,sr)
                                atomic(cache/f'review-{index+1}.json',{'generation':selected,'difference':difference})
                                (cache/f'review-{index+1}.json').chmod(0o600)
                                raise ValueError(f'Segment {index+1}: {difference:.1%}; expected {text}; heard {heard}')
                            duration=len(audio)/sr
                            cues=[{'start':max(0,float(c['start'])),'end':min(duration,float(c['end'])),'text':c['text'].strip()}
                                  for c in timing if isinstance(c.get('text'),str) and isinstance(c.get('start'),(int,float)) and isinstance(c.get('end'),(int,float))
                                  and 0<=c['start']<c['end'] and c['start']<duration]
                            check={'text':text,'heard':heard,'difference':difference,'seconds':duration,'cues':cues,
                                'generation':selected}
                            voice.sf.write(wav,audio,sr);atomic(checkfile,check)
                        # Cached segments stay at the recorded pace; the job's voice tempo applies when assembling.
                        audio=voice_tempo.stretch(audio,sr,tempo,voice.sf)
                        check=voice_tempo.faster(check,tempo,seconds=len(audio)/sr)
                        if parts:parts.append(voice.np.zeros(round(sr*.38),dtype=voice.np.float32))
                        parts.append(audio);checks.append(check)
                    complete=voice.np.concatenate(parts)
                    if clean or clean is None:complete=voice.loudness(complete)
                    master=cache/'master.wav';voice.sf.write(master,complete,sr)
                    output=cache/'audio.pending.m4a';output.unlink(missing_ok=True)
                    subprocess.run(['/usr/bin/afconvert','-f','m4af','-d','aac','-b','64000',str(master),str(output)],check=True)
                    output.replace(cache/'audio.m4a')
                    generation.update({'status':'ready','completed_at':time.time()});save_generation(cache,generation)
                    atomic(cache/'ready.json',{'hash':key,'seconds':round(len(complete)/sr,2),'bytes':(cache/'audio.m4a').stat().st_size,
                        'sha256':hashlib.sha256((cache/'audio.m4a').read_bytes()).hexdigest(),'profile':profile,'tempo':tempo,'segments':checks,
                        'pronunciation':job.get('pronunciation'),'pronunciation_review':'pending_human_listening'})
                    (cache/'failed.json').unlink(missing_ok=True)
                    (cache/'automatic-retry.json').unlink(missing_ok=True)
                    print('READY',job['id'],round(len(complete)/sr,1),'seconds',flush=True)
                except Exception as error:
                    if generation is not None:
                        generation.update({'status':'failed','completed_at':time.time()});save_generation(cache,generation)
                    atomic(cache/'failed.json',{'error':str(error),'at':time.time()});print('FAILED',job['id'],str(error),flush=True)
                    if args.auto_retry:schedule_automatic_retry(cache)
                finally:
                    # Drop model weights before giving the shared slot to Ollama or
                    # Remotion. --low-memory additionally unloads TTS before each ASR.
                    model=None
                    whisper_cache.model=None;whisper_cache.model_path=None
                    audio=parts=checks=complete=best=transcription=timing=result=None
                    gc.collect();voice.mx.clear_cache()
                    (cache/'working.json').unlink(missing_ok=True)
            # Re-read the queue between chapters so a newly purchased report's
            # overview does not wait behind an entire earlier course batch.
            break
    print('BATCH COMPLETE',flush=True)

if __name__=='__main__':main()
