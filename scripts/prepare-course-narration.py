"""Queue the new curriculum only, preserving every other narration job."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from domain.course_curriculum import load_packages, import_plan
from domain.narration import lesson_clips


def main():
    from dotenv import load_dotenv
    from pymongo import MongoClient
    load_dotenv(ROOT / 'backend/.env')
    packages = load_packages()
    with MongoClient(os.environ['MONGO_URL'], serverSelectionTimeoutMS=5000) as client:
        db = client[os.environ['MONGODB_DATABASE']]
        if any(row['action'] != 'unchanged' for row in import_plan(db.lessons_v2, packages)):
            raise SystemExit('Install and verify the current lessons before preparing narration.')
        jobs = ROOT / 'backend/private/narration/jobs'
        jobs.mkdir(parents=True, exist_ok=True)
        rows = []
        for package in packages:
            lesson = package['lesson']
            clips = lesson_clips(lesson)
            for clip in clips:
                destination = jobs / (clip['hash'] + '.json')
                payload = {**clip, 'scope': 'lesson', 'lesson_id': lesson['id'], 'lesson_title': lesson['title']}
                if not destination.exists():
                    temp = destination.with_suffix('.tmp')
                    temp.write_text(json.dumps(payload, ensure_ascii=False))
                    temp.replace(destination)
            rows.append({'lesson_id': lesson['id'], 'clips': len(clips)})
        print(json.dumps({'lessons': rows, 'queued': sum(r['clips'] for r in rows)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
