"""Lossless TXT preview: preserve source, never invent quiz answer keys."""
import hashlib
import json
from fastapi import HTTPException


def lesson_preview(text):
    if not isinstance(text,str) or not text.strip() or len(text)>200000 or any(ord(c)<32 and c not in '\n\r\t' for c in text):
        raise HTTPException(422,'Добавьте текст UTF-8 до 200 000 символов без управляющих знаков')
    normalized=text.removeprefix('\ufeff').replace('\r\n','\n').replace('\r','\n')
    title=next((line.strip().lstrip('#').strip() for line in normalized.splitlines() if line.strip()),'Урок из TXT')
    warnings=['Весь текст сохранён в теории. Проверьте структуру, упражнения, тест и задания по дням в редакторе перед публикацией.']
    if len(title)>300:
        title=title[:300];warnings.append('Заголовок сокращён до 300 символов; полный текст сохранён в теории.')
    content_hash=hashlib.sha256(normalized.encode()).hexdigest()
    chunks=[];rest=normalized
    while rest:
        end=min(10000,len(rest))
        if end<len(rest):
            newline=rest.rfind('\n',0,end)
            if newline>5000:end=newline+1
        chunks.append(rest[:end]);rest=rest[end:]
    lesson={'title':title,'description':'Материал импортирован из TXT. Черновик для проверки преподавателем.',
            'level':1,'order':0,'is_active':False,'exercises':[],
            'theory':[{'id':'txt-'+hashlib.sha256((content_hash+':'+str(i)).encode()).hexdigest()[:32],
                       'title':'Материал' if len(chunks)==1 else 'Материал · часть '+str(i+1), 'content':chunk,'order':i} for i,chunk in enumerate(chunks)]}
    fingerprint=hashlib.sha256(json.dumps({'version':1,'lesson':lesson},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return {'lesson':lesson,'fingerprint':fingerprint,'warnings':warnings}
