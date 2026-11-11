"""Learner-visible text only: no quiz keys, private responses, or hidden theory."""
import hashlib
import html
import json
import re
from domain.consultation import guide_text, STYLE, VOICE, VOICE_IDENTITY
from domain.pronunciation import VERSION as PRONUNCIATION

PROFILE = 'numerom-helper-male-project-v1'
DEFAULT_LABELS = {'what_is_numerology':'Что такое нумерология','cosmic_ship_story':'История',
    'planets_and_numbers':'Планеты и числа','what_is_topic':'О теме','main_story':'Основное',
    'key_concepts':'Ключевые понятия','practical_applications':'Применение'}

def obj(value): return value if isinstance(value, dict) else {}
def seq(value):
    if isinstance(value, str):
        try: return seq(json.loads(value))
        except (ValueError, TypeError): return []
    return value if isinstance(value, list) else []

def plain(value):
    if not isinstance(value, str): return ''
    value = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', '', value, flags=re.I|re.S)
    value = re.sub(r'</?(?:p|div|h[1-6]|li|br)[^>]*>', '\n', value, flags=re.I)
    return html.unescape(re.sub(r'<[^>]*>', '', value)).strip()

def oral(text):
    text = plain(text)
    text = re.sub(r'^\s*[•*]\s*', '', text, flags=re.M)
    text = re.sub(r'_{2,}', 'место для вашего ответа', text)
    for short, full in [('ЧЛГ','число личного года'),('ЧД','число души'),('ЧС','число судьбы')]:
        text = re.sub(r'\b'+short+r'\b', full, text)
    text = text.replace('→','; далее ').replace('+',' плюс ').replace('=',' равно ').replace('•',', ')
    text = text.replace('смело смотрите на первые лучи солнца','наблюдайте краски неба и окружающий пейзаж, избегая прямого взгляда на солнце')
    if 'С какой горизонталью' in text:
        text = re.sub(r'Вариант (\d+)\. (Первой|Второй|Третьей) \(([^)]+)\)\.',
            lambda m:f'Вариант {m[1]}. С {m[2].lower()} горизонталью. Тема: {m[3]}.',text)
    return re.sub(r'[ \t]+',' ',text).strip()

def clip(key, section, title, *parts, consultation=True, previous_pronunciation=False):
    text = '\n\n'.join(plain(p) for p in parts if plain(p))
    if not text: return None
    speech = oral(guide_text(key, section, plain(title), text) if consultation else text)
    # These existing course passages describe traditional symbolism, not physiology.
    if section == 'theory' and any(word in text for word in ['управляет сердцем','управляет жидкостями тела']):
        speech = ('В этом разделе урока рассматриваются традиционные соответствия планет и тела. '
                  'Это образы нумерологической традиции. По ним нельзя определять состояние здоровья. '
                  + ('Солнце здесь символизирует жизненный тонус, ясность и уверенность.' if 'сердцем' in text else
                     'Луна здесь символизирует изменчивость чувств, восприимчивость и потребность в заботе.'))
    identity = PROFILE+'\0'+STYLE+'\0'+VOICE_IDENTITY if consultation else PROFILE
    if consultation and not previous_pronunciation:identity+='\0'+PRONUNCIATION
    fingerprint = hashlib.sha256((identity+'\0'+text+'\0'+speech).encode()).hexdigest()
    return {'id':key,'section':section,'title':plain(title) or 'Материал','text':speech,'hash':fingerprint,
            'adapted':speech!=text, **({'style':STYLE, 'voice':VOICE} if consultation else {}),
            **({'pronunciation':PRONUNCIATION} if consultation and not previous_pronunciation else {})}

def lesson_clips(lesson, *, consultation=True, previous_pronunciation=False):
    out=[]
    def add(*args):
        item=clip(*args, consultation=consultation, previous_pronunciation=previous_pronunciation)
        if item: out.append(item)
    add('intro','intro',lesson.get('title'),lesson.get('title'),lesson.get('description'))
    content=obj(lesson.get('content')); blocks=[]
    for raw in seq(lesson.get('theory')):
        b=obj(raw)
        if plain(b.get('content')): blocks.append((b.get('title'),b.get('content')))
    theory=obj(content.get('theory')); labels=obj(content.get('theory_labels'))
    hidden=set(seq(obj(content.get('hidden_theory_fields')).get('fields')))
    for key,value in theory.items():
        if key!='full_text' and key not in hidden and plain(value):
            blocks.append((labels.get(key+'_label') or DEFAULT_LABELS.get(key,'Теоретический материал'),value))
    if not blocks and 'full_text' not in hidden and plain(theory.get('full_text')): blocks.append(('',theory['full_text']))
    for raw in seq(obj(content.get('custom_theory_blocks')).get('blocks')):
        b=obj(raw); body=b.get('content') or b.get('text')
        if b.get('hidden') is not True and plain(body): blocks.append((b.get('title'),body))
    for index,(title,body) in enumerate(blocks): add(f'theory-{index}','theory',title,title,body)
    for index,raw in enumerate(seq(lesson.get('exercises',content.get('exercises')))):
        b=obj(raw); instructions=b.get('instructions')
        if isinstance(instructions,list): instructions='\n'.join(plain(v) for v in instructions)
        add('exercise-'+str(b.get('id',index)),'exercise',b.get('title'),b.get('title'),b.get('description') or b.get('content'),instructions)
    quiz=obj(lesson.get('quiz',content.get('quiz')))
    for index,raw in enumerate(seq(quiz.get('questions'))):
        b=obj(raw)
        # Read exactly the visible question and every option; never correct_answer or explanation.
        options='\n'.join(f'Вариант {i+1}. {plain(v)}.' for i,v in enumerate(seq(b.get('options'))) if plain(v))
        add('quiz-'+str(b.get('id',index)),'quiz',f'Вопрос {index+1}',b.get('question'),options)
    challenge=obj(lesson.get('challenge',content.get('challenge')))
    if challenge: add('challenge-intro','challenge',challenge.get('title'),challenge.get('title'),challenge.get('description'))
    for index,raw in enumerate(seq(challenge.get('daily_tasks'))):
        b=obj(raw); title=f"День {b.get('day',index+1)}. {plain(b.get('title'))}"
        tasks='\n'.join(plain(t) if isinstance(t,str) else plain(obj(t).get('text') or obj(t).get('description')) for t in seq(b.get('tasks')))
        add('challenge-'+str(index),'challenge',title,title,b.get('description'),tasks)
    return out
