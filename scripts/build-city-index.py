#!/usr/bin/env python3
"""Build NumerOM's offline GeoNames cities500 index from the original downloads.

Usage: python scripts/build-city-index.py --cities cities500.zip --regions
admin1CodesASCII.txt --countries countryInfo.txt --output backend/data/geography/cities.sqlite
No network access or personal data. GeoNames data: CC BY 4.0.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import unicodedata
import zipfile


def normalized(value):
    return ' '.join(re.findall(r'[^\W_]+', ''.join(c for c in unicodedata.normalize('NFKD', value.casefold().replace('ё', 'е')) if not unicodedata.combining(c))))


def build(cities, regions, countries, output):
    countries_map = {p[0]: p[4] for line in countries.read_text().splitlines() if not line.startswith('#') and len(p := line.split('\t')) > 4}
    regions_map = {p[0]: p[1] for line in regions.read_text().splitlines() if len(p := line.split('\t')) > 2}
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.building')
    temporary.unlink(missing_ok=True)
    with sqlite3.connect(temporary) as db:
        db.executescript('''CREATE TABLE cities(id TEXT PRIMARY KEY,name TEXT,country TEXT,country_code TEXT,region TEXT,label TEXT,latitude REAL,longitude REAL,timezone TEXT,population INTEGER,aliases TEXT);
        CREATE VIRTUAL TABLE search USING fts5(terms,content='',tokenize='unicode61 remove_diacritics 2');''')
        with zipfile.ZipFile(cities) as archive:
            with archive.open('cities500.txt') as source:
                for raw in source:
                    p = raw.decode('utf-8').rstrip('\n').split('\t')
                    if len(p) < 19 or p[6] != 'P': continue
                    name, country, region = p[1], countries_map.get(p[8], p[8]), regions_map.get(f'{p[8]}.{p[10]}', '')
                    label = ', '.join(dict.fromkeys(v for v in (name, region, country) if v))
                    aliases = sorted(set(normalized(v) for v in [p[1], p[2], *p[3].split(',')] if v and len(v) <= 200))
                    row = (p[0], name, country, p[8], region, label, float(p[4]), float(p[5]), p[17], int(p[14] or 0), '\n'.join(aliases))
                    cursor = db.execute('INSERT INTO cities VALUES (?,?,?,?,?,?,?,?,?,?,?)', row)
                    terms = ' '.join(sorted(set(' '.join(aliases + [normalized(region), normalized(country), p[8].lower()]).split())))
                    db.execute('INSERT INTO search(rowid,terms) VALUES (?,?)', (cursor.lastrowid, terms))
        db.execute("INSERT INTO search(search) VALUES ('optimize')")
        count = db.execute('SELECT count(*) FROM cities').fetchone()[0]
    temporary.replace(output)
    manifest = {'source': 'https://download.geonames.org/export/dump/', 'license': 'CC BY 4.0', 'attribution': 'GeoNames', 'dataset': 'cities500', 'rows': count,
                'sources_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (cities, regions, countries)}}
    output.with_suffix('.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'rows': count, 'bytes': output.stat().st_size}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for field in ('cities', 'regions', 'countries', 'output'): parser.add_argument('--' + field, required=True, type=Path)
    args = parser.parse_args()
    build(args.cities, args.regions, args.countries, args.output)
