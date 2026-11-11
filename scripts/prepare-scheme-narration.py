"""Queue exact reviewed explanations of the original NumerOM schemes.

The source is shared with mobile. Only scheme entries are replaced in the
project catalog; existing content-addressed audio is never overwritten.
"""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from domain.narration import clip


def entries(source):
    rows = []
    for entry in [source['method'], *source['entries']]:
        narration = entry['narration']
        key, text = narration['id'], narration['text']
        if not re.fullmatch(r'scheme-[a-z0-9_-]+', key):
            raise ValueError('Invalid scheme narration ID')
        if not isinstance(text, str) or not 1 <= len(text.strip()) <= 20000:
            raise ValueError('Invalid scheme narration text: ' + key)
        rows.append({'id': key, 'section': 'schemes', 'title': entry['title'], 'text': text.strip()})
    if len({row['id'] for row in rows}) != len(rows):
        raise ValueError('Duplicate scheme narration ID')
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', help='Queue only one sample; catalog still includes all reviewed entries')
    args = parser.parse_args()
    source_path = ROOT / 'packages/scheme-knowledge/ru.json'
    rows = entries(json.loads(source_path.read_text()))
    if args.only and args.only not in {row['id'] for row in rows}:
        raise ValueError('Sample is not in the reviewed source')
    path = ROOT / 'packages/project-knowledge/ru.json'
    source = json.loads(path.read_text())
    source['items'] = [row for row in source['items'] if not row['id'].startswith('scheme-')] + rows
    relative = source_path.relative_to(ROOT).as_posix()
    if relative not in source['sources']:
        source['sources'].append(relative)
    path.write_text(json.dumps(source, ensure_ascii=False, indent=2) + '\n')
    jobs = ROOT / 'backend/private/narration/jobs'
    jobs.mkdir(parents=True, exist_ok=True)
    count = 0
    for row in rows:
        if args.only and row['id'] != args.only:
            continue
        item = clip(row['id'], row['section'], row['title'], row['text'])
        destination = jobs / (item['hash'] + '.json')
        try:
            with destination.open('x') as file:
                json.dump({**item, 'scope': 'project', 'lesson_title': 'Авторские схемы NumerOM'}, file, ensure_ascii=False)
        except FileExistsError:
            pass
        count += 1
    print('Prepared', count, 'scheme recordings; existing recordings unchanged')


if __name__ == '__main__':
    main()
