"""Reviewed course packages: strict content checks and insert-only installation.

Answer keys stay in this server-side package. Existing lessons and student work
are never rewritten by the installer, including when a teacher edited a lesson.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from models import LessonV2

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'packages/course-curriculum'
EXPECTED = {'intro', '0', '4', '5', '6', '7', '8', '9'}
ID = re.compile(r'^[A-Za-z0-9_-]{1,128}$')


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_package(package, root=ROOT):
    require(package.get('schema_version') == 1, 'Unsupported curriculum schema')
    key = str(package.get('number'))
    require(key in EXPECTED, 'Unexpected lesson number')
    lesson = package['lesson']
    require(lesson.get('id') == 'numerom-course-' + key, 'Unstable lesson id')
    require(lesson.get('is_active') is True and lesson.get('level') == 1, 'Invalid lesson access')
    LessonV2.model_validate({**lesson, 'created_by': 'curriculum-import', 'updated_by': 'curriculum-import'})
    sources = package.get('sources', [])
    require(bool(sources) and bool(package.get('editorial_note', '').strip()), 'Missing provenance')
    source_ids = set()
    for source in sources:
        require(source['id'] not in source_ids, 'Duplicate source id')
        source_ids.add(source['id'])
        path = Path(source['path'])
        require(not path.is_absolute() and (root / path).resolve().is_relative_to(root.resolve()), 'Invalid source path')
        require((root / path).is_file(), f'Missing source: {path}')
        require(hashlib.sha256((root / path).read_bytes()).hexdigest() == source['sha256'], f'Source changed: {path}')
        require(all(type(p) is int and p > 0 for p in source.get('pages', [])), 'Invalid source pages')
    identifiers = [lesson['id'], lesson['quiz']['id'], lesson['challenge']['id']]
    for group in ('theory', 'exercises'):
        require(len(lesson[group]) >= (6 if group == 'theory' else 4), 'Incomplete ' + group)
        orders = [b.get('order') for b in lesson[group]]
        require(all(type(o) is int and o >= 0 for o in orders) and orders == sorted(set(orders)), 'Invalid block order')
        for block in lesson[group]:
            identifiers.append(block['id'])
            require(bool(block['title'].strip()), 'Missing block title')
            for ref in block.get('source_refs', []):
                require(ref['source_id'] in source_ids, 'Unknown source reference')
    require(all(b['content'].strip() for b in lesson['theory']), 'Empty theory')
    require(all(b['instructions'].strip() and b['expected_outcome'].strip() for b in lesson['exercises']), 'Empty practice')
    quiz = lesson['quiz']
    require(len(quiz['questions']) >= 8 and 1 <= quiz['passing_score'] <= 100, 'Incomplete quiz')
    for question in quiz['questions']:
        identifiers.append(question['id'])
        options = question['options']
        require(question.get('type') == 'multiple_choice', 'Unsupported quiz type')
        require(2 <= len(options) <= 6 and len(set(options)) == len(options) and all(o.strip() for o in options), 'Invalid quiz options')
        require(question['correct_answer'] in options and bool(question['explanation'].strip()), 'Invalid answer key')
    challenge = lesson['challenge']
    require(challenge['duration_days'] == 7 and [d['day'] for d in challenge['daily_tasks']] == list(range(1, 8)), 'Incomplete challenge')
    require(all(d['title'].strip() and d['description'].strip() and d['tasks'] and all(t.strip() for t in d['tasks']) for d in challenge['daily_tasks']), 'Empty challenge task')
    require(len(set(identifiers)) == len(identifiers) and all(ID.fullmatch(i) for i in identifiers), 'Invalid or duplicate identifier')
    return package


def load_packages(folder=PACKAGE, root=ROOT):
    packages = [validate_package(json.loads(p.read_text()), root) for p in sorted(folder.glob('lesson-*.json'))]
    require({str(p['number']) for p in packages} == EXPECTED and len(packages) == len(EXPECTED), 'Curriculum package is incomplete')
    return sorted(packages, key=lambda p: p['lesson']['order'])


def planned_document(package):
    return {**deepcopy(package['lesson']), 'curriculum': {
        'version': package['schema_version'], 'number': package['number'],
        'digest': digest(package), 'sources': deepcopy(package['sources']),
        'editorial_note': package['editorial_note']}}


def import_plan(collection, packages):
    rows = []
    for package in packages:
        expected = planned_document(package)
        existing = list(collection.find({'id': expected['id']}))
        if not existing:
            status = 'insert'
        elif len(existing) == 1 and all(existing[0].get(k) == v for k, v in expected.items()):
            status = 'unchanged'
        else:
            status = 'conflict'
        rows.append({'id': expected['id'], 'title': expected['title'], 'action': status})
    return rows


def install_packages(collection, packages):
    require(any(info.get('unique') is True and list(info.get('key', [])) == [('id', 1)]
                for info in collection.index_information().values()),
            'A unique lessons_v2.id index is required before installation')
    plan = import_plan(collection, packages)
    require(not any(row['action'] == 'conflict' for row in plan), 'Existing lesson differs; no lessons were changed')
    now = datetime.now(timezone.utc)
    for package, row in zip(packages, plan):
        if row['action'] != 'insert':
            continue
        document = {**planned_document(package), 'created_at': now, 'updated_at': now,
                    'created_by': 'curriculum-import', 'updated_by': 'curriculum-import'}
        # A repeated or interrupted import cannot create another copy or reset work.
        collection.update_one({'_id': document['id']}, {'$setOnInsert': document}, upsert=True)
    final = import_plan(collection, packages)
    require(all(row['action'] == 'unchanged' for row in final), 'Import conflict detected; inspect the saved plan')
    return plan
