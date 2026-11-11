"""Owner-private Business 250 directory and evidence-based team workspaces.

One Mongo document makes each revision atomic, including group references and
the bounded import receipt. Original upload bytes never leave parser memory.
"""
import base64
import binascii
import hashlib
import json
import unicodedata
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool

from domain.business import (
    EmployeeInput, GroupInput, MAX_EMPLOYEES, MAX_GROUPS, MAX_GROUP_MEMBERS,
    MAX_FILE_BYTES, analyze_group, employee_identity, parse_employee_file,
)

IMPORT_HISTORY_LIMIT = 64
MAX_BASE64_LENGTH = 4 * ((MAX_FILE_BYTES + 2) // 3)
PACKAGE = {'id': 'business-250', 'title': 'NumerOM Business 250',
           'max_employees': MAX_EMPLOYEES, 'mode': 'pilot', 'price': 0}
WORKSPACE_FIELDS = ('id', 'company_name', 'revision', 'employees', 'groups', 'created_at', 'updated_at')
CONFLICT = 'Данные изменены на другом устройстве. Обновите раздел и повторите действие.'


class RequestModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class ActivateRequest(RequestModel):
    company_name: StrictStr = Field(min_length=1, max_length=160)

    @field_validator('company_name', mode='before')
    @classmethod
    def company_not_blank(cls, value):
        if not isinstance(value, str):
            raise ValueError('Укажите название компании текстом')
        if any(unicodedata.category(char) in ('Cc', 'Cs', 'Cf') for char in value):
            raise ValueError('Название содержит недопустимые управляющие символы')
        value = ' '.join(unicodedata.normalize('NFC', value).split())
        if not value:
            raise ValueError('Укажите название компании')
        return value


class PreviewRequest(RequestModel):
    filename: StrictStr = Field(min_length=1, max_length=255)
    content_base64: StrictStr = Field(min_length=1, max_length=MAX_BASE64_LENGTH)


class RevisionRequest(RequestModel):
    expected_revision: int = Field(strict=True, ge=0)


class ImportRequest(RevisionRequest):
    request_id: StrictStr = Field(min_length=8, max_length=128, pattern=r'^[A-Za-z0-9_-]+$')
    employees: list[EmployeeInput] = Field(min_length=1, max_length=MAX_EMPLOYEES)


class EmployeeWrite(RevisionRequest):
    employee: EmployeeInput


class GroupWrite(RevisionRequest):
    group: GroupInput
    id: StrictStr | None = Field(default=None, min_length=1, max_length=128, pattern=r'^[A-Za-z0-9_-]+$')


def public_workspace(row):
    return {field: deepcopy(row[field]) for field in WORKSPACE_FIELDS} if row else None


def envelope(row):
    return {'package': dict(PACKAGE), 'workspace': public_workspace(row)}


def _fingerprint(request):
    data = request.model_dump(exclude={'request_id'})
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _receipt(row, request_id, fingerprint):
    for receipt in row.get('import_history', []):
        if receipt['request_id'] == request_id:
            if receipt['fingerprint'] != fingerprint:
                raise HTTPException(409, 'Этот идентификатор импорта уже использован для других данных')
            return True
    return False


def _ensure_unique(employees):
    identities = set()
    for employee in employees:
        key = employee_identity(employee)
        if key in identities:
            raise HTTPException(422, 'Повтор сотрудника: имя, фамилия и дата рождения уже есть в списке')
        identities.add(key)


class BusinessService:
    def __init__(self, db):
        self.db = db
        self.workspaces = db.business_workspaces

    async def _user(self, uid):
        user = await self.db.users.find_one({'id': uid}, {'id': 1, 'is_disabled': 1})
        if not user or user.get('is_disabled'):
            raise HTTPException(401, 'Требуется вход в действующий аккаунт')

    async def _workspace(self, uid, required=True):
        await self._user(uid)
        # The account is the only selector: client-supplied employee and group
        # identifiers can never change the workspace owner.
        row = await self.workspaces.find_one({'_id': uid})
        if required and row is None:
            raise HTTPException(403, 'Сначала подключите пакет Business 250')
        return row

    async def read(self, uid):
        return envelope(await self._workspace(uid, required=False))

    async def activate(self, uid, request):
        await self._user(uid)
        now = datetime.now(timezone.utc).isoformat()
        row = {'_id': uid, 'id': str(uuid4()), 'company_name': request.company_name,
               'revision': 0, 'employees': [], 'groups': [], 'import_history': [],
               'created_at': now, 'updated_at': now}
        # Default _id index makes concurrent activation idempotent. Pilot
        # activation never touches Stripe, user balance or credit history.
        try:
            await self.workspaces.update_one({'_id': uid}, {'$setOnInsert': row}, upsert=True)
        except DuplicateKeyError:
            pass
        return envelope(await self._workspace(uid))

    async def preview(self, uid, request):
        row = await self._workspace(uid)
        try:
            content = base64.b64decode(request.content_base64, validate=True)
        except (ValueError, binascii.Error):
            raise HTTPException(422, 'Файл передан в неверном формате')
        if len(content) > MAX_FILE_BYTES:
            raise HTTPException(413, 'Размер файла не должен превышать 5 МБ')
        preview = await run_in_threadpool(parse_employee_file, request.filename, content)
        employee_rows = preview.pop('_employee_rows', list(range(2, 2 + len(preview['employees']))))
        # Cross-workspace duplicates are checked only after row validation: the
        # parser retains its exact original row numbers for invalid files.
        if preview['valid']:
            existing = {employee_identity(item) for item in row['employees']}
            existing_names = {identity[:2] for identity in existing}
            for index, employee in zip(employee_rows, preview['employees']):
                identity = employee_identity(employee)
                if identity in existing:
                    preview['issues'].append({'row': index, 'field': 'name',
                                              'message': 'Этот сотрудник уже есть в компании'})
                elif identity[:2] in existing_names:
                    preview['warnings'].append({'row': index, 'field': 'name',
                                                'message': 'В компании уже есть такое имя и фамилия. Проверьте, что это другой человек.'})
            if len(row['employees']) + len(preview['employees']) > MAX_EMPLOYEES:
                preview['issues'].append({'row': 0, 'field': 'file',
                                          'message': f'В компании может быть не более {MAX_EMPLOYEES} сотрудников; сейчас {len(row["employees"])}.'})
            preview['valid'] = not preview['issues']
        return preview

    async def _commit(self, uid, old, expected_revision, changes):
        if old['revision'] != expected_revision:
            raise HTTPException(409, CONFLICT)
        row = {**old, **changes, 'revision': expected_revision + 1,
               'updated_at': datetime.now(timezone.utc).isoformat()}
        result = await self.workspaces.replace_one({'_id': uid, 'revision': expected_revision}, row)
        if not result.matched_count:
            raise HTTPException(409, CONFLICT)
        return {'workspace': public_workspace(row)}

    async def import_employees(self, uid, request):
        row = await self._workspace(uid)
        fingerprint = _fingerprint(request)
        if _receipt(row, request.request_id, fingerprint):
            return {'workspace': public_workspace(row)}
        if row['revision'] != request.expected_revision:
            raise HTTPException(409, CONFLICT)
        employees = row['employees'] + [{**item.model_dump(), 'id': str(uuid4())} for item in request.employees]
        if len(employees) > MAX_EMPLOYEES:
            raise HTTPException(422, f'В компании может быть не более {MAX_EMPLOYEES} сотрудников')
        _ensure_unique(employees)
        history = (row.get('import_history', []) + [{'request_id': request.request_id, 'fingerprint': fingerprint}])[-IMPORT_HISTORY_LIMIT:]
        try:
            return await self._commit(uid, row, request.expected_revision, {'employees': employees, 'import_history': history})
        except HTTPException as error:
            if error.status_code != 409:
                raise
            latest = await self._workspace(uid)
            if _receipt(latest, request.request_id, fingerprint):
                return {'workspace': public_workspace(latest)}
            raise

    async def edit_employee(self, uid, employee_id, request):
        row = await self._workspace(uid)
        if not any(item['id'] == employee_id for item in row['employees']):
            raise HTTPException(404, 'Сотрудник не найден')
        employees = [{**request.employee.model_dump(), 'id': employee_id} if item['id'] == employee_id else item for item in row['employees']]
        _ensure_unique(employees)
        return await self._commit(uid, row, request.expected_revision, {'employees': employees})

    async def remove_employee(self, uid, employee_id, request):
        row = await self._workspace(uid)
        if not any(item['id'] == employee_id for item in row['employees']):
            raise HTTPException(404, 'Сотрудник не найден')
        employees = [item for item in row['employees'] if item['id'] != employee_id]
        groups = [{**group, 'member_ids': [member for member in group['member_ids'] if member != employee_id]} for group in row['groups']]
        return await self._commit(uid, row, request.expected_revision, {'employees': employees, 'groups': groups})

    async def save_group(self, uid, request):
        row = await self._workspace(uid)
        group = request.group.model_dump()
        if len(group['member_ids']) > MAX_GROUP_MEMBERS or len(group['member_ids']) != len(set(group['member_ids'])):
            raise HTTPException(422, 'Выберите до 20 разных сотрудников')
        if not set(group['member_ids']).issubset({item['id'] for item in row['employees']}):
            raise HTTPException(422, 'В группе есть сотрудник, которого нет в вашей компании')
        if request.id:
            if not any(item['id'] == request.id for item in row['groups']):
                raise HTTPException(404, 'Группа не найдена')
            groups = [{**group, 'id': request.id} if item['id'] == request.id else item for item in row['groups']]
        else:
            if len(row['groups']) >= MAX_GROUPS:
                raise HTTPException(422, f'Можно сохранить не более {MAX_GROUPS} групп')
            groups = row['groups'] + [{**group, 'id': str(uuid4())}]
        return await self._commit(uid, row, request.expected_revision, {'groups': groups})

    async def remove_group(self, uid, group_id, request):
        row = await self._workspace(uid)
        if not any(item['id'] == group_id for item in row['groups']):
            raise HTTPException(404, 'Группа не найдена')
        return await self._commit(uid, row, request.expected_revision,
                                  {'groups': [item for item in row['groups'] if item['id'] != group_id]})

    async def report(self, uid, group_id):
        row = await self._workspace(uid)
        group = next((item for item in row['groups'] if item['id'] == group_id), None)
        if not group:
            raise HTTPException(404, 'Группа не найдена')
        return {'report': analyze_group(row['employees'], group)}

    async def template(self, uid):
        await self._workspace(uid)
        return {'filename': 'numerom-business-template.csv',
                'content': '\ufeffИмя;Фамилия;Дата рождения;Отдел;Должность;Навыки;Опыт;Интересы;Часов в неделю\r\n'
                           'Тестовый;Сотрудник;15.05.1990;Пример отдела;Пример должности;Excel;Вымышленный пример — замените своими данными;Анализ данных;20\r\n'}
