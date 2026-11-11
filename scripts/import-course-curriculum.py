"""Validate offline; preview or insert reviewed lessons without changing existing work."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from domain.course_curriculum import load_packages, import_plan, install_packages


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--validate-only', action='store_true')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    packages = load_packages()
    print(json.dumps({'validated': len(packages), 'theory_blocks': sum(len(p['lesson']['theory']) for p in packages),
                      'exercises': sum(len(p['lesson']['exercises']) for p in packages),
                      'questions': sum(len(p['lesson']['quiz']['questions']) for p in packages),
                      'challenge_days': sum(p['lesson']['challenge']['duration_days'] for p in packages)}, ensure_ascii=False))
    if args.validate_only:
        return
    from dotenv import load_dotenv
    from pymongo import MongoClient
    from bson import json_util
    load_dotenv(ROOT / 'backend/.env')
    with MongoClient(os.environ['MONGO_URL'], serverSelectionTimeoutMS=5000) as client:
        db = client[os.environ['MONGODB_DATABASE']]
        plan = import_plan(db.lessons_v2, packages)
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        if not args.apply:
            return
        if any(row['action'] == 'conflict' for row in plan):
            raise SystemExit('Conflict: existing lessons were preserved. Inspect differences before updating.')
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        backup = ROOT / 'backend/private/course-imports' / stamp
        backup.mkdir(parents=True, mode=0o700)
        # Course content only. No account data, student responses or diary records.
        snapshot = backup / 'lessons-before.json'
        snapshot.write_text(json_util.dumps(list(db.lessons_v2.find({})), ensure_ascii=False, indent=2))
        snapshot.chmod(0o600)
        (backup / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2))
        try:
            result = install_packages(db.lessons_v2, packages)
        except Exception as error:
            after = import_plan(db.lessons_v2, packages)
            inserted = sum(before['action'] == 'insert' and current['action'] == 'unchanged'
                           for before, current in zip(plan, after))
            failure = {'status': 'incomplete', 'error_type': type(error).__name__,
                       'inserted': inserted, 'after': after}
            (backup / 'result.json').write_text(json.dumps(failure, ensure_ascii=False, indent=2))
            raise SystemExit(f'Import incomplete; {inserted} new lessons are present. Existing content was not overwritten. Inspect {backup}') from error
        (backup / 'result.json').write_text(json.dumps({'status': 'complete', 'plan': result}, ensure_ascii=False, indent=2))
        print(json.dumps({'inserted': sum(r['action'] == 'insert' for r in result),
                          'unchanged': sum(r['action'] == 'unchanged' for r in result),
                          'backup': str(backup)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
