"""Narrate only fixed preference themes, never personal answers."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from domain.assessment import METHOD, THEMES, narration
from domain.narration import clip


def entries():
    return [{'id':'assessment-method','section':'assessment','title':'Как разобраны ответы опроса','text':METHOD}] + [
        {'id':f'assessment-result-{n}','section':'assessment','title':title,'text':narration(n)} for n,(title,meaning,focus) in THEMES.items()]


def main():
    path=ROOT/'packages/project-knowledge/ru.json';source=json.loads(path.read_text())
    source['items']=[row for row in source['items'] if not row['id'].startswith('assessment-')]+entries()
    if 'backend/domain/assessment.py' not in source['sources']:source['sources'].append('backend/domain/assessment.py')
    path.write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n')
    jobs=ROOT/'backend/private/narration/jobs';jobs.mkdir(parents=True,exist_ok=True)
    for row in entries():
        item=clip(row['id'],row['section'],row['title'],row['text']);destination=jobs/(item['hash']+'.json')
        try:
            with destination.open('x') as file:json.dump({**item,'scope':'project','lesson_title':'Самонаблюдение'},file,ensure_ascii=False)
        except FileExistsError:pass
    print('Prepared 10 fixed assessment recordings without personal answers')

if __name__=='__main__':main()
