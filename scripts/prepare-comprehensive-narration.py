"""Queue fixed report explanations without private birth dates or results."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from domain.narration import clip


def main():
    source_path = ROOT / 'packages/comprehensive-knowledge/ru.json'
    entries = [
        {'id': row['id'], 'section': 'comprehensive', 'title': row['title'], 'text': row['text']}
        for row in json.loads(source_path.read_text())['items']
    ]
    if len(entries) != 6 or len({row['id'] for row in entries}) != 6 or any(
        not row['id'].startswith('comprehensive-') or not row['text'].strip()
        for row in entries
    ):
        raise ValueError('Expected six report explanations')
    path = ROOT / 'packages/project-knowledge/ru.json'
    source = json.loads(path.read_text())
    source['items'] = [row for row in source['items'] if not row['id'].startswith('comprehensive-')] + entries
    if 'packages/comprehensive-knowledge/ru.json' not in source['sources']:
        source['sources'].append('packages/comprehensive-knowledge/ru.json')
    path.write_text(json.dumps(source, ensure_ascii=False, indent=2) + '\n')
    jobs = ROOT / 'backend/private/narration/jobs'
    jobs.mkdir(parents=True, exist_ok=True)
    for row in entries:
        item = clip(row['id'], row['section'], row['title'], row['text'])
        destination = jobs / (item['hash'] + '.json')
        try:
            with destination.open('x') as file:
                json.dump({**item, 'scope': 'project', 'lesson_title': 'Полный разбор'}, file, ensure_ascii=False)
        except FileExistsError:
            pass
    print('Prepared 6 report explanations without personal dates')


if __name__ == '__main__':
    main()
