"""Prepare narration from the exact compatibility interpretation shown in the report."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from domain.relationships import connection
from domain.narration import clip

METHOD='Совместимость в NumerOM. Сначала для каждого участника складываем день, месяц и год рождения как целые числа. Полученную сумму сводим сложением цифр, сохраняя одиннадцать, двадцать два и тридцать три. Затем находим расстояние между двумя итоговыми числами: из большего вычитаем меньшее. Из десяти вычитаем это расстояние. Если получается меньше единицы, оставляем единицу. В группе каждый участник сравнивается с основным; среднее значение объединяет эти индексы. Это условная шкала метода. Она помогает сопоставить акценты двух трактовок, а не измерить качество отношений. Выберите строку пары, чтобы услышать её смысл и вопрос для обсуждения.'

def entries():
    rows=[{'id':'relationship-method','section':'relationships','title':'Как рассчитана совместимость','text':METHOD}]
    for key,difference in [('same',0),('close',1),('different',3),('contrast',5)]:
        result=connection({'number':1},{'number':1+difference,'name':'Участник'})
        rows.append({'id':'relationship-'+key,'section':'relationships','title':result['title'],
                     'text':result['interpretation']+' '+result['focus']})
    return rows

def main():
    path=ROOT/'packages/project-knowledge/ru.json';source=json.loads(path.read_text())
    source['items']=[row for row in source['items'] if not row['id'].startswith('relationship-')]+entries()
    if 'backend/domain/relationships.py' not in source['sources']:source['sources'].append('backend/domain/relationships.py')
    path.write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n')
    jobs=ROOT/'backend/private/narration/jobs';jobs.mkdir(parents=True,exist_ok=True)
    for row in entries():
        item=clip(row['id'],row['section'],row['title'],row['text']);destination=jobs/(item['hash']+'.json')
        if not destination.exists():destination.write_text(json.dumps({**item,'scope':'project','lesson_title':'NumerOM'},ensure_ascii=False))
    print('Prepared 5 compatibility recordings without personal data')

if __name__=='__main__':main()
