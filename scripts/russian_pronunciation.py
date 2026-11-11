"""Local Russian stress preparation and a pinned Qwen stress adapter.

Only synthesis receives marks. Display text, calculations and ASR comparison
remain unchanged. A failed text-preservation check stops synthesis.
"""
from functools import lru_cache
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from domain.pronunciation import VERSION, ADAPTER_SHA256
RESOURCE = ROOT/'backend/private/pronunciation'/VERSION
ACUTE = '\u0301'
VOWELS = 'аеёиоуыэюя'
WORDS = re.compile(r'[А-Яа-яЁё\u0301]+')

# Unambiguous project terms only. Inflected homographs such as «числа» are
# deliberately absent: their stress depends on the sentence.
TERMS = {'нумером':'нумеро́м','пифагор':'пифаго́р','пифагора':'пифаго́ра',
    'пифагоров':'пифаго́ров','нумерология':'нумероло́гия','нумерологии':'нумероло́гии',
    'нумеролог':'нумеро́лог','нумеролога':'нумеро́лога','двигайтесь':'дви́гайтесь',
    'диагонали':'диагона́ли','диагональ':'диагона́ль','вертикали':'вертика́ли',
    'горизонтали':'горизонта́ли','ритме':'ри́тме','приоритеты':'приорите́ты'}
PHRASES = {'имени и даже адреса':'и́мени и да́же а́дреса',
    'свои личные числа':'свои́ ли́чные чи́сла',
    'что за ними стоит':'что за ни́ми стои́т'}

def unmark(text):
    return text.replace(ACUTE,'').replace('\u02ca','')

def canonical(text):
    return unmark(text).lower().replace('ё','е')

def stressed_like(marked, original):
    plain=unmark(marked)
    if canonical(plain)!=canonical(original):
        raise ValueError('Pronunciation would change the spoken word')
    letters=iter(unmark(original));out=[]
    for ch in marked:
        if ch==ACUTE:out.append(ch)
        else:
            old=next(letters)
            out.append(ch.upper() if old.isupper() else ch.lower())
    return ''.join(out)

def merge_marks(text, accented):
    """Keep original punctuation/case; reject dropped, added or changed words."""
    predicted=re.findall(r'[А-Яа-яЁё+\u0301]+',accented)
    originals=list(WORDS.finditer(text))
    if len(predicted)!=len(originals):raise ValueError('Accentizer changed word count')
    result=[];offset=0
    for m,word in zip(originals,predicted):
        word=re.sub(r'\+([А-Яа-яЁё])',lambda x:x[1]+ACUTE,word)
        if '+' in word or word.count(ACUTE)>1:raise ValueError('Invalid stress mark')
        if any(i==0 or word[i-1].lower() not in VOWELS for i,ch in enumerate(word) if ch==ACUTE):
            raise ValueError('Stress must follow a vowel')
        result.append(text[offset:m.start()])
        # Explicit author marks outrank model guesses.
        result.append(m[0] if ACUTE in m[0] else stressed_like(word,m[0]))
        offset=m.end()
    result.append(text[offset:])
    output=''.join(result)
    if canonical(output)!=canonical(text):raise ValueError('Accentizer changed the script')
    return output

@lru_cache(maxsize=1)
def accentizer():
    # These dependencies and ONNX weights are installed separately, never fetched
    # while serving a job. RUAccent.load() would download code, so initialize its
    # reviewed local components explicitly instead.
    sys.path.insert(0,str(RESOURCE/'python'))
    from ruaccent import RUAccent
    model=RUAccent();model.tiny_mode=True
    root=RESOURCE/'accentuator'
    def dictionary(name):
        with gzip.open(root/'dictionary'/name,'rt',encoding='utf8') as f:return json.load(f)
    model.omographs=dictionary('omographs.json.gz')
    model.yo_words=dictionary('yo_words.json.gz')
    model.yo_homographs=dictionary('yo_homographs.json.gz')
    model.accents=dictionary('accents.json.gz')
    model.omograph_model.load(str(root/'nn/nn_omograph/turbo3.1'))
    model.accent_model.load(str(root/'nn/nn_accent'))
    # CharTokenizer inherits Transformers defaults, which omit token_type_ids
    # in this runtime. The pinned character ONNX graph requires them. Let the
    # tokenizer build its own correctly shaped segment IDs (including BOS/EOS).
    model.accent_model.tokenizer.model_input_names = [
        item.name for item in model.accent_model.session.get_inputs()]
    model.yo_homograph_model.load(str(root/'nn/nn_yo_homograph_resolver'))
    return model

def prepare(text, model=None):
    model=model or accentizer()
    analysis=unmark(text).lower()
    predicted=model.process_all(analysis)
    try:
        output=merge_marks(text,predicted)
    except ValueError:
        # RUAccent deletes unsupported symbols, joining e.g. В−С into ВС.
        # Retry with those symbols as word boundaries, but merge onto the
        # untouched script and keep the same strict word-preservation check.
        # Successful existing preparations remain byte-for-byte unchanged.
        normalizer=getattr(model,'normalize',None)
        separated=normalizer.sub(' ',analysis) if isinstance(normalizer,re.Pattern) else analysis
        if separated==analysis:raise
        output=merge_marks(text,model.process_all(separated))
    originals=iter(WORDS.findall(text))
    def term(match):
        original=next(originals);key=unmark(match[0]).lower()
        return stressed_like(TERMS[key],match[0]) if ACUTE not in original and key in TERMS else match[0]
    output=WORDS.sub(term,output)
    # Match phrases on the unmarked sentence, then replace right-to-left so
    # offsets from accents never shift subsequent matches.
    for plain,marked in PHRASES.items():
        pattern=r'(?<![А-Яа-яЁё])'+''.join(re.escape(c)+(ACUTE+'?' if c.lower() in VOWELS else '') for c in plain)+r'(?![А-Яа-яЁё])'
        output=re.sub(pattern,lambda m:stressed_like(marked,m[0]),output,flags=re.I)
    # ё already carries stress. Monosyllables need no extra control token.
    output=WORDS.sub(lambda m:unmark(m[0]) if 'ё' in m[0].lower()
        or sum(c.lower() in VOWELS for c in m[0])<2 else m[0],output)
    return output

def apply_adapter(model, mx):
    """Merge only the 196 pinned talker LoRA matrices, once per loaded model."""
    if getattr(model,'numerom_pronunciation',None)==VERSION:return model
    path=RESOURCE/'adapter.safetensors'
    if hashlib.sha256(path.read_bytes()).hexdigest()!=ADAPTER_SHA256:
        raise ValueError('Russian stress adapter checksum mismatch')
    from mlx.utils import tree_flatten
    weights=dict(tree_flatten(model.parameters()));adapter=mx.load(str(path));updates=[]
    for name in sorted(adapter):
        if not name.endswith('.lora_A.weight'):continue
        module=name.removesuffix('.lora_A.weight')
        if not re.fullmatch(r'layers\.\d+\.(self_attn\.(q|k|v|o)_proj|mlp\.(gate|up|down)_proj)',module):
            raise ValueError('Unexpected stress adapter layer')
        a,b=adapter[name],adapter[module+'.lora_B.weight']
        key='talker.model.'+module+'.weight';w=weights[key]
        delta=b.astype(mx.float32)@a.astype(mx.float32)*2
        if delta.shape!=w.shape or not bool(mx.all(mx.isfinite(delta))):
            raise ValueError('Invalid stress adapter weights')
        updates.append((key,(w.astype(mx.float32)+delta).astype(w.dtype)))
    if len(updates)!=196 or len(adapter)!=392:raise ValueError('Incomplete stress adapter')
    model.load_weights(updates,strict=False);mx.eval(model.parameters())
    model.numerom_pronunciation=VERSION
    return model
