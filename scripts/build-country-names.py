#!/usr/bin/env python3
"""Country names for «Город, Страна» in the offline city index (GeoNames keeps them only in English).

Usage: python scripts/build-country-names.py
Names come from Unicode CLDR as built into Node.js (Intl.DisplayNames): Russian, Ukrainian,
Romanian and English, long and short forms, plus a few colloquial Russian names. No network access.
"""
import json
from pathlib import Path
import sqlite3
import subprocess

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'backend/data/geography/cities.sqlite'
OUTPUT = INDEX.with_name('countries.json')
LANGUAGES = ('ru', 'uk', 'ro', 'en')
# Names people write that CLDR does not list as a display name.
COLLOQUIAL = {'BY': ['Белоруссия'], 'MD': ['Молдавия', 'Республика Молдова'], 'RU': ['Российская Федерация', 'РФ'],
              'US': ['Америка'], 'GB': ['Англия', 'Соединённое Королевство'], 'KR': ['Южная Корея'],
              'CZ': ['Чешская Республика'], 'AE': ['Объединённые Арабские Эмираты']}
NAMES = """
const [codes, languages] = JSON.parse(process.argv[1]);
const result = {};
for (const code of codes) {
  const names = new Set();
  for (const language of languages)
    for (const style of ['long', 'short']) {
      const name = new Intl.DisplayNames([language], {type: 'region', style, fallback: 'none'}).of(code);
      if (name) names.add(name);
    }
  result[code] = [...names];
}
process.stdout.write(JSON.stringify({icu: process.versions.icu, cldr: process.versions.cldr, names: result}));
"""


def main():
    with sqlite3.connect(INDEX.resolve().as_uri() + '?mode=ro', uri=True) as db:
        codes = sorted(code for (code,) in db.execute('SELECT DISTINCT country_code FROM cities') if code)
    data = json.loads(subprocess.run(['node', '-e', NAMES, json.dumps([codes, LANGUAGES])],
                                     check=True, capture_output=True, text=True).stdout)
    for code, extra in COLLOQUIAL.items():
        data['names'][code] = sorted(set(data['names'].get(code, [])) | set(extra))
    OUTPUT.write_text(json.dumps({'source': 'Unicode CLDR via Node.js Intl.DisplayNames', 'cldr': data['cldr'],
                                  'icu': data['icu'], 'languages': list(LANGUAGES), 'names': data['names']},
                                 ensure_ascii=False, indent=1, sort_keys=True) + '\n')
    print(json.dumps({'countries': len(data['names']), 'bytes': OUTPUT.stat().st_size}))


if __name__ == '__main__':
    main()
