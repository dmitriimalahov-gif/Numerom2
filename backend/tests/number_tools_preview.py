"""Disposable browser QA: isolated Mongo container 27039 only, no production env."""
import os
from contextlib import asynccontextmanager

if os.environ.get('NUMEROM_TOOLS_QA') != '1':
    raise RuntimeError('Enable only for isolated browser QA')
os.environ['SECRET_KEY'] = 'isolated-tools-preview-signing-key-only'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from auth import get_password_hash
from models import User
from routers.accounts import create_accounts_router
from routers.number_tools import create_number_tools_router

mongo = AsyncIOMotorClient('mongodb://127.0.0.1:27039', serverSelectionTimeoutMS=4000)
db = mongo['numerom_tools_browser_qa']

@asynccontextmanager
async def lifespan(app):
    user = User(id='tools-qa',email='tools@example.invalid',
                password_hash=get_password_hash('preview-only'),full_name='Анна',
                name='Анна',birth_date='10.01.1982',credits_remaining=20)
    await db.users.update_one({'id':user.id},{'$setOnInsert':user.model_dump()},upsert=True)
    await db.lessons_v2.update_one({'id':'diary-test'},{'$setOnInsert':{
        'id':'diary-test','title':'Практика внимания','description':'Учебный пример для проверки дневника','is_active':True,'level':1,
        'theory':[{'title':'Наблюдение','content':'В течение дня обратите внимание на привычный способ принимать решения.'}],
        'challenge':{'id':'diary-challenge','title':'Два дня наблюдений','description':'Запишите опыт и отметьте выполненные задания.','duration_days':2,
                     'daily_tasks':[{'day':1,'title':'Замечать инициативу','description':'Вспомните одно решение, принятое самостоятельно.','tasks':['Запишите ситуацию.','Отметьте, что помогло действовать.']},
                                    {'day':2,'title':'Замечать сотрудничество','description':'Вспомните разговор, в котором вы нашли общее решение.','tasks':['Запишите, что вы услышали.','Отметьте свой вклад.']}]}
        }},upsert=True)
    await db.lessons_v2.update_one({'id':'diary-test'},{'$set':{
        'quiz':{'id':'qa-quiz','title':'Проверка наблюдений','passing_score':50,'questions':[
            {'id':'qa-one','type':'multiple_choice','question':'Сколько чисел от одного до девяти?','options':['Восемь','Девять'],'correct_answer':'Девять'},
            {'id':'qa-two','type':'multiple_choice','question':'Какой шаг помогает наблюдать опыт?','options':['Записать наблюдение','Пропустить заметку'],'correct_answer':'Записать наблюдение'}]},
        'exercises':[{'id':'qa-exercise','type':'text','title':'Моё наблюдение','description':'Опишите один пример из практики.'}]
    }})
    admin=User(id='mobile-admin',email='mobile-admin@example.invalid',password_hash=get_password_hash('preview-only'),full_name='Администратор проверки',birth_date='01.01.1980',is_admin=True,is_super_admin=True,credits_remaining=100)
    await db.users.update_one({'id':admin.id},{'$setOnInsert':admin.model_dump()},upsert=True)
    yield
    mongo.close()

app=FastAPI(lifespan=lifespan)
app.state.auth_db=db
app.add_middleware(CORSMiddleware,allow_origins=['http://127.0.0.1:5132'],allow_methods=['GET','POST','PATCH'],allow_headers=['Authorization','Content-Type'])
app.include_router(create_accounts_router(db))
app.include_router(create_number_tools_router(db))

# Fixture catalog exposes real texts without pretending that local HTTP playback
# validates the signed HTTPS media boundary (checked separately by service tests).
from auth import get_current_user
from fastapi import Depends
from domain.narration import clip
from pathlib import Path
import json
@app.get('/api/narration/project')
async def narration(user=Depends(get_current_user)):
    source=Path(__file__).resolve().parents[2]/'packages/project-knowledge/ru.json'
    return {'items':[{**clip(row['id'],row['section'],row['title'],row['text']), 'status':'missing','seconds':0}
                     for row in json.loads(source.read_text())['items']]}

from routers.challenge_diary import create_challenge_diary_router
from routers.exercise_drafts import create_exercise_drafts_router
from services.student_learning import StudentLearningService,TheoryRead
from domain.narration import lesson_clips
app.include_router(create_challenge_diary_router(db))
app.include_router(create_exercise_drafts_router(db))
@app.get('/api/learning-v2/lessons')
async def lessons(user=Depends(get_current_user)):
    return await StudentLearningService(db).lessons(user['user_id'])
@app.get('/api/learning-v2/lessons/{lesson_id}')
async def lesson(lesson_id:str,user=Depends(get_current_user)):
    return await StudentLearningService(db).lesson(user['user_id'],lesson_id)
@app.get('/api/student/lesson-progress/{lesson_id}')
async def progress(lesson_id:str,user=Depends(get_current_user)):
    return await StudentLearningService(db).progress(user['user_id'],lesson_id)
@app.post('/api/student/lesson-progress/{lesson_id}/theory')
async def theory(lesson_id:str,body:TheoryRead,user=Depends(get_current_user)):
    return await StudentLearningService(db).mark_theory(user['user_id'],lesson_id)
@app.get('/api/student/lesson-files/{lesson_id}')
async def files(lesson_id:str,user=Depends(get_current_user)):
    return await StudentLearningService(db).files(user['user_id'],lesson_id)
@app.get('/api/narration/lesson/{lesson_id}')
async def lesson_narration(lesson_id:str,user=Depends(get_current_user)):
    row=await StudentLearningService(db).lesson(user['user_id'],lesson_id)
    return {'items':[{**item,'status':'missing','seconds':0} for item in lesson_clips(row['lesson'])]}

from services.student_learning import ExerciseSubmission
@app.get('/api/student/exercise-responses/{lesson_id}')
async def exercise_responses(lesson_id:str,user=Depends(get_current_user)):
    return await StudentLearningService(db).exercise_responses(user['user_id'],lesson_id)
@app.post('/api/student/exercise-response')
async def exercise_response(body:ExerciseSubmission,user=Depends(get_current_user)):
    return await StudentLearningService(db).submit_exercise(user['user_id'],body)

from routers.learning_drafts import create_learning_drafts_router
from routers.passkeys import create_passkeys_router
from services.student_learning import QuizSubmission
app.include_router(create_learning_drafts_router(db))
app.include_router(create_passkeys_router(db,rp_id='127.0.0.1',origins=['http://127.0.0.1:5132']))
@app.get('/api/student/quiz-attempts/{lesson_id}')
async def attempts(lesson_id:str,user=Depends(get_current_user)):
    return await StudentLearningService(db).quiz_attempts(user['user_id'],lesson_id)
@app.post('/api/student/quiz-attempt')
async def submit_quiz(body:QuizSubmission,user=Depends(get_current_user)):
    return await StudentLearningService(db).submit_quiz(user['user_id'],body)

from routers.mobile_admin import create_mobile_admin_router
from routers.admin_management import create_admin_management_router
from routers.exercise_attachments import create_exercise_attachments_router
app.include_router(create_mobile_admin_router(db,materials_root='/tmp/numerom-completion-qa-materials',consultation_materials_root='/tmp/numerom-completion-qa-consultations'))
app.include_router(create_admin_management_router(db))
app.include_router(create_exercise_attachments_router(db,root='/tmp/numerom-completion-qa-attachments'))
from routers.personal_calculations import create_personal_calculations_router
from routers.vedic_calculations import create_vedic_calculations_router
from routers.assessment import create_assessment_router
from routers.personal_reports import create_personal_reports_router
app.include_router(create_personal_calculations_router(db))
app.include_router(create_vedic_calculations_router(db))
app.include_router(create_assessment_router(db))
app.include_router(create_personal_reports_router(db))
from routers.consultations import create_consultations_router
from services.consultations import Consultations
app.include_router(create_consultations_router(db,Consultations(db,root='/tmp/numerom-completion-qa-legacy-consultations',private_root='/tmp/numerom-completion-qa-consultations')))
