"""Private, versioned exercise drafts. Saving does not submit or award points."""
from uuid import UUID
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictStr
from services.versioned_drafts import public, write_versioned
from services.student_learning import require_student_lesson, _key


class DraftWrite(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: UUID
    revision: int = Field(strict=True, ge=0)
    text: StrictStr | None = Field(max_length=10000)


class ExerciseDrafts:
    def __init__(self, db):
        self.db = db

    async def identity(self, uid, lesson_id, exercise_id):
        _, lesson = await require_student_lesson(self.db, uid, lesson_id)
        exercises = lesson.get('exercises') or (lesson.get('content') or {}).get('exercises') or []
        if exercise_id not in {row.get('id') for row in exercises if isinstance(row, dict)}:
            raise HTTPException(404, 'Упражнение не найдено')
        return _key(uid, lesson_id, exercise_id)

    async def read(self, uid, lesson_id, exercise_id):
        identity = await self.identity(uid, lesson_id, exercise_id)
        return public(await self.db.exercise_drafts.find_one({'_id': identity}))

    async def save(self, uid, lesson_id, exercise_id, request):
        identity = await self.identity(uid, lesson_id, exercise_id)
        return await write_versioned(self.db.exercise_drafts, identity, request, {'user_id':uid,'lesson_id':lesson_id,'exercise_id':exercise_id})
