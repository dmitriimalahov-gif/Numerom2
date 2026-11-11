"""Publish bounded, non-personal narration texts for every supported tool result.

Shares the meaning with the report builder; no names/addresses are sent to TTS.
Safe to rerun: existing content-addressed recordings remain available.
"""
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from domain.number_tools import THEMES, TITLES, explanation
from domain.narration import clip

METHODS = {
 'name': 'Число имени. В этом расчёте используется имя и, если она указана, фамилия. Каждая буква получает число от одного до девяти по порядку своего алфавита. После девятки начинается новый цикл. Русская буква ё учитывается отдельно. Значения букв складываются. Затем складываются цифры суммы, пока не останется одна цифра или мастер-число: одиннадцать, двадцать два, тридцать три. В схеме можно проверить вклад каждой буквы. Итоговое число открывает трактовку самовыражения и общения.',
 'address': 'Числа адреса. Номер дома, номер квартиры и почтовый индекс рассматриваются отдельно. Из каждого значения берём только цифры и складываем их. Буквы корпуса и название улицы в сумму не входят. Результат сводится сложением цифр; одиннадцать, двадцать два и тридцать три сохраняются. Дом помогает рассмотреть общую атмосферу, квартира — личное пространство, индекс — окружение. Нажмите на нужный результат, чтобы услышать его смысл. Складывать три результата в одно число здесь не нужно.',
 'car': 'Число автомобиля рассчитывается по введённому номеру. Цифры берутся со своими значениями, буквы — по циклу от одного до девяти своего алфавита. Пробелы и дефисы пропускаются. Если вы указали цифры региона, они тоже входят в сумму. Далее складываем цифры результата, сохраняя одиннадцать, двадцать два и тридцать три. Под числом показана вся цепочка вычисления. Его трактовка предлагает тему для осмысления ваших поездок и связанных с ними привычек.',
}

def entries():
    rows=[]
    for kind, name in TITLES.items():
        rows.append({'id': f'tool-method-{kind}', 'section': 'tools', 'title': name + ': метод расчёта', 'text': METHODS[kind]})
        for value in THEMES:
            title, meaning, focus = explanation(kind, value)
            rows.append({'id': f'tool-{kind}-{value}', 'section': 'tools', 'title': f'{name} {value} · {title}', 'text': meaning + ' ' + focus})
    return rows

def main():
    path=ROOT/'packages/project-knowledge/ru.json'
    source=json.loads(path.read_text())
    source['items']=[row for row in source['items'] if not row['id'].startswith('tool-')] + entries()
    if 'backend/domain/number_tools.py' not in source['sources']:source['sources'].append('backend/domain/number_tools.py')
    path.write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n')
    jobs=ROOT/'backend/private/narration/jobs';jobs.mkdir(parents=True,exist_ok=True)
    for row in entries():
        item=clip(row['id'],row['section'],row['title'],row['text'])
        destination=jobs/(item['hash']+'.json')
        if not destination.exists():destination.write_text(json.dumps({**item,'scope':'project','lesson_title':'NumerOM'},ensure_ascii=False))
    print('Prepared',len(entries()),'contextual recordings; existing recordings unchanged')

if __name__=='__main__':main()
