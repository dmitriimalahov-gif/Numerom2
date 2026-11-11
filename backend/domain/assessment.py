"""The project's ten preference questions, with server-owned interpretation."""
import hashlib
from typing import Annotated, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator
from quiz_data import NUMEROLOGY_QUIZ, calculate_quiz_results

TITLE = 'Опрос для самонаблюдения'
DESCRIPTION = 'Десять вопросов о ваших привычках и предпочтениях. Выберите ближайший вам вариант.'
METHOD = ('У каждого варианта ответа есть числовое соответствие от одного до девяти. '
    'После десяти вопросов считаем, сколько раз выбрано каждое число. '
    'Главная тема соответствует самому частому числу. Если таких чисел несколько, '
    'сначала показываем то, которое раньше встретилось в ответах, а рядом перечисляем остальные. '
    'Сумма значений показана отдельно: она не является оценкой. В разборе можно увидеть '
    'связь каждого выбранного ответа с числом и сравнить рекомендации со своим опытом.')
THEMES = {
    1: ('Инициатива', 'В ответах заметна тяга к самостоятельным решениям и ясной цели. Посмотрите, где личная инициатива помогает делу, а где полезно разделить ответственность.', 'Выберите одну задачу, в которой вы готовы сделать первый шаг и услышать обратную связь.'),
    2: ('Сотрудничество', 'Ваши выборы чаще обращены к отношениям, поддержке и согласованию. Чуткость помогает понять другого; ясное выражение своих потребностей делает общение взаимным.', 'Назовите одну свою потребность, которую стоит спокойно обсудить с близким человеком.'),
    3: ('Самовыражение', 'В выбранных ответах звучит интерес к творчеству, общению и новым формам. Чтобы вдохновение приносило результат, полезно завершать небольшие, понятные шаги.', 'Найдите простую форму для одной идеи: короткий текст, разговор или небольшой законченный проект.'),
    4: ('Устойчивость', 'Ваши ответы чаще связаны с порядком, надёжностью и последовательностью. Эти качества поддерживают долгую работу, а гибкость помогает менять план, когда меняются условия.', 'Отметьте одну полезную привычку и одно правило, которое уже можно пересмотреть.'),
    5: ('Исследование', 'Вы чаще выбираете свободу, разнообразие и новый опыт. Любознательность расширяет возможности; выбранные границы помогают сохранить внимание и завершать начатое.', 'Запланируйте один небольшой эксперимент и заранее выберите признаки, по которым оцените результат.'),
    6: ('Забота', 'В ответах выделяются внимание к близким, поддержка и ответственность. Забота становится устойчивой, когда в ней остаётся место вашим собственным силам и потребностям.', 'Спросите себя, какую помощь вы готовы предложить, а какую ответственность пора разделить.'),
    7: ('Осмысление', 'Ваши выборы чаще обращены к знаниям, тишине и поиску смысла. Размышление помогает увидеть детали; практическая проверка превращает вывод в полезный опыт.', 'Выберите один важный вопрос и небольшой шаг, которым можно проверить свой ответ на него.'),
    8: ('Организация', 'В ответах заметно внимание к результату, самостоятельности и разумному устройству дел. Соотнесите достижение цели с тем, сколько времени и сил она требует.', 'Определите один измеримый шаг к цели и ресурс, который нужно беречь на этом пути.'),
    9: ('Участие', 'Ваши ответы чаще связаны с общим смыслом, сочувствием и помощью. Широкий взгляд полезно соединять с конкретным действием и понятными личными границами.', 'Выберите дело, в котором ваше участие принесёт пользу без обещаний сверх ваших возможностей.'),
}


def question_rows():
    return sorted(NUMEROLOGY_QUIZ['questions'], key=lambda row: row['id'])


def option_id(question, index):
    return hashlib.sha256(f"numerom-assessment-v1:{question['id']}:{index}:{question['options'][index]['text']}".encode()).hexdigest()[:20]


def public_questions():
    return [{'id': str(q['id']), 'question': q['question'], 'options': [
        {'id': option_id(q, i), 'text': option['text']} for i, option in enumerate(q['options'])]} for q in question_rows()]


class AssessmentRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    kind: Literal['assessment']
    request_id: UUID
    expected_cost: int = Field(strict=True, ge=0, le=1000000)
    answers: dict[Annotated[StrictStr, Field(pattern=r'^(?:[1-9]|10)$')], Annotated[StrictStr, Field(pattern=r'^[a-f0-9]{20}$')]] = Field(min_length=10, max_length=10)

    @field_validator('request_id')
    @classmethod
    def v4(cls, value):
        if value.version != 4:
            raise ValueError('request_id must be UUIDv4')
        return value

    @field_validator('answers')
    @classmethod
    def actual_choices(cls, values):
        expected = {str(q['id']): {option_id(q, i) for i in range(len(q['options']))} for q in question_rows()}
        if set(values) != set(expected) or any(value not in expected[key] for key, value in values.items()):
            raise ValueError('Выберите один вариант в каждом из десяти вопросов')
        return values


def narration(number):
    title, meaning, focus = THEMES[number]
    return f'Тема ваших ответов: {title.lower()}. {meaning} {focus}'


def build_assessment(data):
    chosen = []
    for q in question_rows():
        index = next(i for i in range(len(q['options'])) if option_id(q, i) == data.answers[str(q['id'])])
        option = q['options'][index]
        chosen.append({'question_id': str(q['id']), 'question': q['question'], 'answer': option['text'], 'number': option['value']})
    legacy = calculate_quiz_results([{'value': row['number']} for row in chosen])
    number = legacy['dominant_number']
    frequencies = [{'number': value, 'count': legacy['frequencies'].get(value, 0)} for value in range(1, 10)]
    maximum = max(row['count'] for row in frequencies)
    leaders = [row['number'] for row in frequencies if row['count'] == maximum]
    title, interpretation, focus = THEMES[number]
    legacy = {**legacy, 'frequencies': {str(key): value for key, value in legacy['frequencies'].items()}}
    return {'version': 1, 'kind': 'assessment', 'title': TITLE, 'theme': title, 'number': number,
        'interpretation': interpretation, 'focus': focus, 'frequencies': frequencies,
        'leaders': leaders, 'total': legacy['total_score'], 'answers': chosen,
        'recommendations': legacy['recommendations'], 'method': METHOD,
        'tie_note': 'Частоты совпали. Основной показана тема, которая раньше встретилась в ответах.' if len(leaders)>1 else None,
        'narration_id': f'assessment-result-{number}', 'legacy': legacy}
