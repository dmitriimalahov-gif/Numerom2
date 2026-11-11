"""Bounded private employee imports and task coverage from entered skills only.

Names and birth dates identify directory entries. They are never inputs to
employment suitability, team compatibility, personality or overall scores.
"""
from copy import deepcopy
import csv
from datetime import date, datetime
from io import BytesIO, StringIO
import math
from pathlib import PurePosixPath
import re
import unicodedata
from zipfile import BadZipFile, ZIP_DEFLATED, ZIP_STORED, ZipFile

from defusedxml.ElementTree import iterparse
from defusedxml.common import DefusedXmlException
from openpyxl import load_workbook
from openpyxl.utils.cell import range_boundaries
from pydantic import BaseModel, ConfigDict, Field, StrictStr, ValidationError, field_validator
from xml.etree.ElementTree import ParseError

MAX_EMPLOYEES = 250
MAX_GROUPS = 50
MAX_GROUP_MEMBERS = 20
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_ARCHIVE_BYTES = 20 * 1024 * 1024
MAX_ENTRY_BYTES = 8 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 100
MAX_SHEET_ROWS = 1001  # Permit spacing without accepting unbounded sparse sheets.
MAX_SHEET_COLUMNS = 32
MAX_XML_NODES = 100000
MAX_PREVIEW_ISSUES = 1000


def _key(value: str) -> str:
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().split())


def _text(value, *, multiline=False):
    if not isinstance(value, str):
        raise ValueError('Укажите текст')
    value = unicodedata.normalize('NFC', value)
    allowed = {'\n', '\r', '\t'} if multiline else set()
    if any(unicodedata.category(char) in ('Cc', 'Cs', 'Cf') and char not in allowed for char in value):
        raise ValueError('Текст содержит недопустимые управляющие символы')
    return value.strip() if multiline else ' '.join(value.split())


def _labels(value, maximum):
    if not isinstance(value, list) or len(value) > maximum:
        raise ValueError(f'Укажите список: не более {maximum} значений')
    result, seen = [], set()
    for item in value:
        label = _text(item)
        if not 1 <= len(label) <= 80:
            raise ValueError('Каждое значение должно содержать от 1 до 80 символов')
        key = _key(label)
        if key not in seen:
            seen.add(key)
            result.append(label)
    return result


def _hours(value, maximum):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError('Укажите число часов или оставьте поле пустым')
    if not 0 <= value <= maximum or not math.isfinite(value):
        raise ValueError(f'Часы должны быть от 0 до {maximum}')
    return value


def _birth_date(value):
    if value is None or value == '':
        return None
    if not isinstance(value, str):
        raise ValueError('Дата рождения: ДД.ММ.ГГГГ или ГГГГ-ММ-ДД')
    value = value.strip()
    for fmt, pattern in (('%d.%m.%Y', r'\d{2}\.\d{2}\.\d{4}'), ('%Y-%m-%d', r'\d{4}-\d{2}-\d{2}')):
        if re.fullmatch(pattern, value):
            try:
                parsed = datetime.strptime(value, fmt).date()
                if date(1900, 1, 1) <= parsed <= date.today():
                    return parsed.strftime('%d.%m.%Y')
            except ValueError:
                pass
    raise ValueError('Укажите существующую дату рождения с 1900 года по сегодня: ДД.ММ.ГГГГ')


class EmployeeInput(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    name: StrictStr = Field(min_length=1, max_length=80)
    surname: StrictStr = Field(min_length=1, max_length=80)
    birth_date: StrictStr | None = None
    department: StrictStr = Field(default='', max_length=120)
    role: StrictStr = Field(default='', max_length=120)
    skills: list[StrictStr] = Field(default_factory=list, max_length=30)
    experience: StrictStr = Field(default='', max_length=2000)
    interests: list[StrictStr] = Field(default_factory=list, max_length=20)
    hours_per_week: float | None = None

    @field_validator('name', 'surname', 'department', 'role', mode='before')
    @classmethod
    def clean_labels(cls, value):
        return _text(value)

    @field_validator('experience', mode='before')
    @classmethod
    def clean_experience(cls, value):
        return _text(value, multiline=True)

    @field_validator('birth_date', mode='before')
    @classmethod
    def normalize_birth(cls, value):
        return _birth_date(value)

    @field_validator('skills', mode='before')
    @classmethod
    def clean_skills(cls, value):
        return _labels(value, 30)

    @field_validator('interests', mode='before')
    @classmethod
    def clean_interests(cls, value):
        return _labels(value, 20)

    @field_validator('hours_per_week', mode='before')
    @classmethod
    def clean_hours(cls, value):
        return _hours(value, 168)


class GroupInput(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    name: StrictStr = Field(min_length=1, max_length=120)
    task: StrictStr = Field(min_length=1, max_length=2000)
    required_skills: list[StrictStr] = Field(default_factory=list, max_length=30)
    target_hours: float | None = None
    member_ids: list[StrictStr] = Field(default_factory=list, max_length=MAX_GROUP_MEMBERS)

    @field_validator('name', mode='before')
    @classmethod
    def clean_name(cls, value):
        return _text(value)

    @field_validator('task', mode='before')
    @classmethod
    def clean_task(cls, value):
        return _text(value, multiline=True)

    @field_validator('required_skills', mode='before')
    @classmethod
    def clean_skills(cls, value):
        return _labels(value, 30)

    @field_validator('target_hours', mode='before')
    @classmethod
    def clean_hours(cls, value):
        return _hours(value, 3360)

    @field_validator('member_ids', mode='before')
    @classmethod
    def clean_ids(cls, value):
        if not isinstance(value, list) or len(value) > MAX_GROUP_MEMBERS:
            raise ValueError('Выберите не более 20 сотрудников')
        if any(not isinstance(item, str) or not 1 <= len(item) <= 80 or _text(item) != item for item in value):
            raise ValueError('Недопустимый идентификатор сотрудника')
        if len(set(value)) != len(value):
            raise ValueError('Сотрудник не может повторяться в группе')
        return value


def employee_identity(employee):
    """Exact identity for duplicate detection, never a professional trait."""
    if isinstance(employee, EmployeeInput):
        employee = employee.model_dump()
    return (_key(employee['name']), _key(employee['surname']), _birth_date(employee.get('birth_date')))


_ALIASES = {
    'name': ('имя', 'name', 'firstname', 'first_name'),
    'surname': ('фамилия', 'surname', 'lastname', 'last_name'),
    'birth_date': ('дата рождения', 'датарождения', 'birth_date', 'birthdate', 'dateofbirth', 'dob'),
    'department': ('отдел', 'департамент', 'подразделение', 'department'),
    'role': ('должность', 'роль', 'role', 'position'),
    'skills': ('навыки', 'компетенции', 'skills'),
    'experience': ('опыт', 'опыт работы', 'experience'),
    'interests': ('интересы', 'профессиональные интересы', 'interests'),
    'hours_per_week': ('часов в неделю', 'часы в неделю', 'доступно часов в неделю', 'hours_per_week', 'weekly_hours', 'available_hours_per_week'),
}


def _header_key(value):
    return re.sub(r'[\s_-]+', '', _key(value))


HEADER_FIELDS = {_header_key(alias): field for field, aliases in _ALIASES.items() for alias in aliases}


class _ImportError(ValueError):
    def __init__(self, message, *, row=0, field='file', row_count=0):
        super().__init__(message)
        self.row, self.field, self.row_count = row, field, row_count


def _issue(row, field, message):
    return {'row': row, 'field': field, 'message': message}


def _preview(employees=None, issues=None, warnings=None, row_count=0, rows=None):
    if issues and len(issues) > MAX_PREVIEW_ISSUES:
        total = len(issues)
        issues = issues[:MAX_PREVIEW_ISSUES] + [_issue(0, 'file', f'Показаны первые {MAX_PREVIEW_ISSUES} ошибок из {total}. Исправьте таблицу по шаблону и повторите проверку')]
    return {'employees': employees or [], 'issues': issues or [], 'warnings': warnings or [],
            'row_count': row_count, 'valid': not issues, '_employee_rows': rows or []}


def _check_extent(reference):
    try:
        left, top, right, bottom = range_boundaries(reference)
        if any(value is None for value in (left, top, right, bottom)) or left < 1 or top < 1 or right > MAX_SHEET_COLUMNS or bottom > MAX_SHEET_ROWS:
            raise ValueError()
    except (ValueError, TypeError):
        raise _ImportError('Размер листа слишком велик. Оставьте до 1000 строк данных и 32 столбцов')


def _xlsx_preflight(content):
    """Inspect bounded ZIP/XML before openpyxl sees any workbook data."""
    with ZipFile(BytesIO(content)) as archive:
        items = archive.infolist()
        if len(items) > MAX_ARCHIVE_ENTRIES or sum(item.file_size for item in items) > MAX_ARCHIVE_BYTES:
            raise _ImportError('Содержимое XLSX слишком велико. Скопируйте таблицу в новый файл')
        names, node_count, sheet_count = set(), 0, 0
        for item in items:
            name = item.filename.casefold()
            path = PurePosixPath(name)
            if name in names or path.is_absolute() or '..' in path.parts or '\\' in name or item.flag_bits & 1:
                raise _ImportError('Архив XLSX имеет недопустимую структуру')
            names.add(name)
            if item.compress_type not in (ZIP_STORED, ZIP_DEFLATED) or item.file_size > MAX_ENTRY_BYTES or item.file_size > max(item.compress_size, 1) * 200:
                raise _ImportError('Архив XLSX слишком сильно сжат или содержит слишком большой элемент')
            if any(part in name for part in ('vbaproject', 'macrosheet', 'externallinks/', 'connections.xml', 'embeddings/', 'activex/')):
                raise _ImportError('Макросы, вложения и внешние связи не поддерживаются. Сохраните только значения в XLSX')
            if not name.endswith(('.xml', '.rels')):
                continue
            depth, worksheet_xml = 0, False
            with archive.open(item) as stream:
                for event, node in iterparse(stream, events=('start', 'end'), forbid_dtd=True, forbid_entities=True, forbid_external=True):
                    tag = node.tag.rsplit('}', 1)[-1]
                    if event == 'start':
                        depth += 1
                        if depth == 1:
                            worksheet_xml = tag == 'worksheet'
                        node_count += 1
                        if depth > 32 or node_count > MAX_XML_NODES:
                            raise _ImportError('Структура XLSX слишком сложная. Скопируйте только таблицу сотрудников')
                        if tag == 'Relationship' and node.attrib.get('TargetMode', '').casefold() == 'external':
                            raise _ImportError('Внешние ссылки не поддерживаются. Удалите ссылки и загрузите файл снова')
                        if tag == 'Relationship':
                            target = node.attrib.get('Target', '')
                            # openpyxl follows sheet targets even when their
                            # relationship Type is forged as an image. Require
                            # every related part to pass the XML preflight.
                            if PurePosixPath(target).suffix.casefold() != '.xml':
                                raise _ImportError('В файле есть неподдерживаемые связи. Скопируйте только значения в новый XLSX')
                        if tag in ('f', 'definedName'):
                            raise _ImportError('Формулы не поддерживаются. Замените их значениями и загрузите файл снова', field='formula')
                        if tag == 'sheet' and name == 'xl/workbook.xml':
                            sheet_count += 1
                            if sheet_count > 1:
                                raise _ImportError('Оставьте в файле один лист с сотрудниками')
                        # Related worksheet parts may live at arbitrary XML
                        # paths. Validate their contents, never the ZIP folder.
                        if worksheet_xml or node.tag.startswith('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'):
                            if tag == 'dimension':
                                _check_extent(node.attrib.get('ref', ''))
                            if tag == 'row':
                                try:
                                    if not 1 <= int(node.attrib.get('r', '0')) <= MAX_SHEET_ROWS:
                                        raise ValueError()
                                except ValueError:
                                    raise _ImportError('Номер строки выходит за допустимые пределы листа')
                            if tag == 'c':
                                _check_extent(node.attrib.get('r', ''))
                    else:
                        depth -= 1
                        node.clear()
        if sheet_count != 1:
            raise _ImportError('Файл должен содержать один лист с таблицей сотрудников')


def _xlsx_rows(content):
    _xlsx_preflight(content)
    book = load_workbook(BytesIO(content), read_only=True, data_only=False, keep_links=False, keep_vba=False)
    try:
        if len(book.worksheets) != 1:
            raise _ImportError('Оставьте в файле один лист с сотрудниками')
        sheet = book.worksheets[0]
        # Ignore potentially dishonest cached dimensions; preflight bounded every
        # actual row/cell coordinate, so this lazy iteration stays bounded.
        sheet.reset_dimensions()
        rows = []
        for row_index, cells in enumerate(sheet.iter_rows(), start=1):
            if row_index > MAX_SHEET_ROWS or len(cells) > MAX_SHEET_COLUMNS:
                raise _ImportError('Размер листа слишком велик')
            values = []
            for cell in cells:
                if cell.data_type in ('f', 'e'):
                    raise _ImportError('Замените формулы и ошибки ячеек готовыми значениями', row=row_index, field='formula')
                values.append(cell.value)
            rows.append((row_index, values))
        return rows
    finally:
        book.close()


def _csv_rows(content):
    try:
        text = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise _ImportError('Сохраните CSV в кодировке UTF-8 или используйте XLSX')
    if '\x00' in text:
        raise _ImportError('CSV содержит недопустимые символы')
    try:
        # Only the header determines the dialect. Multiline quoted evidence in
        # later records must not cause Sniffer to reject a valid CSV dialect.
        header = next((line for line in text.splitlines() if line.strip()), '')
        dialect = csv.Sniffer().sniff(header, delimiters=';,\t')
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ';'
    reader = csv.reader(StringIO(text, newline=''), delimiter=delimiter, strict=True)
    rows = []
    for row_index, row in enumerate(reader, start=1):
        if row_index > MAX_SHEET_ROWS or len(row) > MAX_SHEET_COLUMNS:
            raise _ImportError('Размер таблицы слишком велик: не более 1000 строк данных и 32 столбцов')
        rows.append((row_index, row))
    return rows


def _nonempty(value):
    return value is not None and (not isinstance(value, str) or bool(value.strip()))


def _cell_value(field, value):
    if not _nonempty(value):
        return None if field in ('birth_date', 'hours_per_week') else [] if field in ('skills', 'interests') else ''
    if field == 'birth_date' and isinstance(value, (datetime, date)):
        return value.strftime('%d.%m.%Y')
    if field in ('skills', 'interests'):
        if not isinstance(value, str):
            raise ValueError('Перечислите значения через точку с запятой')
        return [label.strip() for label in value.split(';') if label.strip()]
    if field == 'hours_per_week' and isinstance(value, str):
        if not re.fullmatch(r'\d+(?:[.,]\d{1,2})?', value.strip()):
            raise ValueError('Укажите число часов от 0 до 168')
        return float(value.strip().replace(',', '.'))
    return value


def _validation_message(detail):
    kind, context = detail['type'], detail.get('ctx', {})
    if kind == 'string_too_short':
        return f'Введите не менее {context["min_length"]} символа'
    if kind == 'string_too_long':
        return f'Допускается не более {context["max_length"]} символов'
    if kind == 'missing':
        return 'Заполните обязательное поле'
    if kind in ('string_type', 'list_type', 'float_type'):
        return 'Значение имеет неверный тип. Проверьте формат столбца'
    return detail['msg'].removeprefix('Value error, ')


def _parse_rows(rows):
    populated = [(row, values) for row, values in rows if any(_nonempty(value) for value in values)]
    if not populated:
        raise _ImportError('Файл пуст. Добавьте заголовки и хотя бы одного сотрудника')
    header_row, headers = populated[0]
    data_rows = populated[1:]
    row_count = len(data_rows)
    if row_count > MAX_EMPLOYEES:
        raise _ImportError('За один импорт допускается не более 250 сотрудников. Разделите таблицу', row=data_rows[MAX_EMPLOYEES][0], row_count=row_count)
    fields, issues = [], []
    for column, raw in enumerate(headers, start=1):
        if not _nonempty(raw):
            fields.append(None)
            continue
        field = HEADER_FIELDS.get(_header_key(raw)) if isinstance(raw, str) else None
        if field is None:
            issues.append(_issue(header_row, 'headers', f'Неизвестный заголовок в столбце {column}. Используйте шаблон'))
        elif field in fields:
            issues.append(_issue(header_row, field, 'Столбец повторяется. Оставьте один столбец для этого поля'))
        fields.append(field)
    for required in ('name', 'surname'):
        if required not in fields:
            issues.append(_issue(header_row, required, 'В таблице нужны столбцы «Имя» и «Фамилия»'))
    if issues:
        return _preview(issues=issues, row_count=row_count)
    if not data_rows:
        return _preview(issues=[_issue(header_row, 'file', 'Добавьте хотя бы одного сотрудника после заголовков')])
    employees, employee_rows, warnings = [], [], []
    seen, names = {}, {}
    for row_index, values in data_rows:
        payload, row_issues = {}, []
        for index, value in enumerate(values):
            field = fields[index] if index < len(fields) else None
            if field is None:
                if _nonempty(value):
                    row_issues.append(_issue(row_index, 'headers', f'В столбце {index + 1} есть значение без заголовка'))
                continue
            if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')):
                row_issues.append(_issue(row_index, field, 'Формулы не поддерживаются. Замените содержимое ячейки значением'))
                continue
            try:
                payload[field] = _cell_value(field, value)
            except ValueError as error:
                row_issues.append(_issue(row_index, field, str(error)))
        if not row_issues:
            try:
                normalized = EmployeeInput.model_validate(payload).model_dump()
            except ValidationError as error:
                for detail in error.errors(include_url=False, include_input=False):
                    message = _validation_message(detail)
                    row_issues.append(_issue(row_index, str(detail['loc'][0]), message))
            else:
                identity = employee_identity(normalized)
                if identity in seen:
                    row_issues.append(_issue(row_index, 'employee', f'Повтор сотрудника из строки {seen[identity]}: совпадают имя, фамилия и дата рождения'))
                else:
                    if identity[:2] in names:
                        warnings.append(_issue(row_index, 'employee', f'Имя и фамилия совпадают со строкой {names[identity[:2]]}. Проверьте, что это разные сотрудники'))
                    seen[identity] = row_index
                    names.setdefault(identity[:2], row_index)
                    employees.append(normalized)
                    employee_rows.append(row_index)
        issues.extend(row_issues)
    return _preview(employees, issues, warnings, row_count, employee_rows)


def parse_employee_file(filename: str, content: bytes) -> dict:
    """Return preview only; valid=False always prohibits committing any rows.

    `_employee_rows` is private service metadata aligned to `employees`. The API
    strips it after checking duplicates against the existing workspace.
    """
    try:
        if not isinstance(filename, str) or not isinstance(content, bytes):
            raise _ImportError('Передайте имя файла и его содержимое')
        if not content:
            raise _ImportError('Файл пуст')
        if len(content) > MAX_FILE_BYTES:
            raise _ImportError('Файл превышает 5 МиБ. Уменьшите таблицу')
        suffix = PurePosixPath(filename).suffix.casefold()
        if suffix == '.xls':
            raise _ImportError('Старый формат XLS не поддерживается. Сохраните файл как XLSX')
        if suffix not in ('.xlsx', '.csv'):
            raise _ImportError('Выберите XLSX без макросов или CSV в UTF-8')
        rows = _xlsx_rows(content) if suffix == '.xlsx' else _csv_rows(content)
        return _parse_rows(rows)
    except _ImportError as error:
        return _preview(issues=[_issue(error.row, error.field, str(error))], row_count=error.row_count)
    except (BadZipFile, DefusedXmlException, ParseError, csv.Error, ValueError, TypeError, KeyError, IndexError, OSError, RuntimeError, OverflowError):
        # Never expose library paths, XML payloads or employee contents as errors.
        return _preview(issues=[_issue(0, 'file', 'Не удалось прочитать таблицу. Сохраните только значения в новом XLSX или CSV UTF-8')])


def analyze_group(employees: list[dict], group: dict) -> dict:
    """Match manually selected employees' entered skills to explicit task needs."""
    if not isinstance(employees, list) or len(employees) > MAX_EMPLOYEES:
        raise ValueError('Недопустимый список сотрудников')
    task = GroupInput.model_validate({key: value for key, value in group.items() if key != 'id'})
    by_id = {}
    for person in employees:
        employee_id = person.get('id')
        if not isinstance(employee_id, str) or not employee_id or employee_id in by_id:
            raise ValueError('Недопустимый идентификатор сотрудника')
        normalized = EmployeeInput.model_validate({key: value for key, value in person.items() if key != 'id'}).model_dump()
        by_id[employee_id] = {'id': employee_id, **normalized}
    if any(employee_id not in by_id for employee_id in task.member_ids):
        raise ValueError('Один из выбранных сотрудников больше не доступен')
    members = [by_id[employee_id] for employee_id in task.member_ids]
    entered_skills = {person['id']: {_key(skill) for skill in person['skills']} for person in members}
    coverage = [{'skill': skill, 'employee_ids': [person['id'] for person in members if _key(skill) in entered_skills[person['id']]]} for skill in task.required_skills]
    missing_skills = [row['skill'] for row in coverage if not row['employee_ids']]
    missing_hours = [person['id'] for person in members if person['hours_per_week'] is None]
    available_hours = None if missing_hours else sum(person['hours_per_week'] for person in members)
    next_steps = []
    if not members:
        next_steps.append('Выберите сотрудников для группы, чтобы проверить покрытие требований задачи.')
    if not task.required_skills:
        next_steps.append('Укажите необходимые навыки задачи: без требований невозможно определить пробелы в составе группы.')
    if missing_skills:
        next_steps.append('Проверьте, у кого есть подтверждённый опыт по недостающим навыкам, или запланируйте обучение: ' + '; '.join(missing_skills) + '.')
    if missing_hours:
        next_steps.append('Уточните доступные часы у участников без данных. До этого общая ёмкость группы неизвестна.')
    elif task.target_hours is not None and available_hours < task.target_hours:
        next_steps.append(f'Согласуйте дополнительное время или сократите объём задачи: заявлено {available_hours:g} ч/нед., требуется {task.target_hours:g} ч/нед.')
    if members:
        next_steps.append('Подтвердите указанные навыки примерами выполненных работ. Совпадение названия навыка не подтверждает уровень владения.')
        next_steps.append('Распределите конкретные результаты между участниками и согласуйте сроки, ответственность и порядок проверки.')
    return {'name': task.name, 'task': task.task, 'member_count': len(members), 'coverage': coverage,
            'missing_skills': missing_skills, 'available_hours': available_hours, 'target_hours': task.target_hours,
            'missing_hours_data': missing_hours, 'next_steps': next_steps, 'members': deepcopy(members)}
