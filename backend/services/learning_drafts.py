"""Private unfinished learning work; saving never grades or completes anything."""
from typing import Annotated, Literal
from uuid import UUID
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictStr, ValidationError
from services.exercise_drafts import DraftWrite
from services.versioned_drafts import public, write_versioned
from services.student_learning import Identifier, require_student_lesson, _key
from services.challenge_diary import ChallengeDiary


class QuizWork(BaseModel):
    model_config=ConfigDict(extra='forbid')
    submission_id: UUID
    answers: dict[Identifier,Annotated[StrictStr,Field(max_length=4000)]]=Field(max_length=100)
    index: int=Field(strict=True,ge=0,le=99)
    stage: Literal['editing','submitting']='editing'


class QuizDraftWrite(DraftWrite):
    text: StrictStr | None=Field(max_length=450000)


class DiaryDraftWrite(DraftWrite):
    text: StrictStr | None=Field(max_length=4000)


class LearningDrafts:
    def __init__(self,db):self.db=db

    async def quiz(self,uid,lesson_id,quiz_id,request=None):
        _,lesson=await require_student_lesson(self.db,uid,lesson_id)
        quiz=lesson.get('quiz') or (lesson.get('content') or {}).get('quiz') or {}
        if (quiz.get('id') or lesson_id)!=quiz_id or not quiz.get('questions'):
            raise HTTPException(404,'Тест не найден')
        identity=_key(uid,'quiz',lesson_id,quiz_id)
        if request is None:return public(await self.db.learning_drafts.find_one({'_id':identity}))
        if request.text is not None:
            try:work=QuizWork.model_validate_json(request.text)
            except (ValidationError,ValueError):raise HTTPException(422,'Некорректный черновик теста')
            questions={q.get('id'):q for q in quiz['questions'] if isinstance(q,dict)}
            if None in questions or len(questions)!=len(quiz['questions']):
                raise HTTPException(409,'Преподаватель обновляет структуру теста')
            if work.submission_id.version!=4 or work.index>=len(questions) or set(work.answers)-set(questions):
                raise HTTPException(422,'Структура теста изменилась. Сохраните свой текст перед новой попыткой.')
            for key,answer in work.answers.items():
                q=questions[key]
                if answer and q.get('type','multiple_choice')!='text' and answer not in q.get('options',[]):
                    raise HTTPException(422,'Выберите вариант из текущего теста')
            if work.stage=='submitting' and (set(work.answers)!=set(questions) or any(not a.strip() for a in work.answers.values())):
                raise HTTPException(422,'Ответьте на все вопросы перед отправкой')
        return await write_versioned(self.db.learning_drafts,identity,request,{'user_id':uid,'kind':'quiz','lesson_id':lesson_id,'quiz_id':quiz_id})

    async def diary(self,uid,lesson_id,challenge_id,attempt_id,day,request=None):
        _,_,challenge,_,state,_=await ChallengeDiary(self.db).snapshot(uid,lesson_id,challenge_id)
        if str(attempt_id)!=state['attempt_id']:raise HTTPException(409,'Начата другая попытка практики. Ваш текст остаётся в поле.')
        if not 1<=day<=challenge['duration_days']:raise HTTPException(404,'День практики не найден')
        identity=_key(uid,'diary',lesson_id,challenge_id,str(attempt_id),str(day))
        if request is None:return public(await self.db.learning_drafts.find_one({'_id':identity}))
        return await write_versioned(self.db.learning_drafts,identity,request,{'user_id':uid,'kind':'diary','lesson_id':lesson_id,
            'challenge_id':challenge_id,'attempt_id':str(attempt_id),'day':day})
