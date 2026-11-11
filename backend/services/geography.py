"""Read-only, offline city suggestions. No external requests or location history."""
from functools import lru_cache
from contextlib import closing
import json
from pathlib import Path
import re
import sqlite3
import unicodedata

DATA = Path(__file__).resolve().parents[1] / 'data/geography/cities.sqlite'
COUNTRIES = DATA.with_name('countries.json')


def normalize(value):
    return ' '.join(re.findall(r'[^\W_]+', ''.join(c for c in unicodedata.normalize('NFKD', value.casefold().replace('ё', 'е')) if not unicodedata.combining(c))))


@lru_cache(maxsize=1)
def country_names():
    """Country code → normalized CLDR names (scripts/build-country-names.py); GeoNames has English only."""
    try:
        names = json.loads(COUNTRIES.read_text(encoding='utf-8'))['names']
    except (OSError, ValueError, KeyError):
        return {}
    return {code: frozenset(normalize(name) for name in values) for code, values in names.items()}


class CityIndex:
    def __init__(self, path=DATA): self.path = Path(path)

    def connection(self):
        db = sqlite3.connect(self.path.resolve().as_uri() + '?mode=ro', uri=True, timeout=2)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def public(row):
        return {key: row[key] for key in ('id', 'name', 'country', 'country_code', 'region', 'label', 'latitude', 'longitude', 'timezone')}

    def lookup(self, identifier):
        if not re.fullmatch(r'[0-9]{1,12}', str(identifier)): return None
        with closing(self.connection()) as db:
            row = db.execute('SELECT * FROM cities WHERE id=?', (str(identifier),)).fetchone()
        return self.public(row) if row else None

    @lru_cache(maxsize=128)
    def search(self, query):
        clean = normalize(query)
        if not 2 <= len(clean) <= 80: return []
        words = clean.split()[:6]
        expression = ' AND '.join('"' + token + '"*' for token in words)
        with closing(self.connection()) as db:
            rows = db.execute('SELECT c.* FROM search JOIN cities c ON c.rowid=search.rowid WHERE search MATCH ? ORDER BY c.population DESC LIMIT 256', (expression,)).fetchall()
        rows.sort(key=lambda row: (clean not in row['aliases'].split('\n'), -row['population'], row['label']))
        return [self.public(row) for row in rows[:12]]

    def _rows(self, clean, limit):
        expression = ' AND '.join('"' + token + '"' for token in clean.split()[:6])
        with closing(self.connection()) as db:
            return db.execute('SELECT c.* FROM search JOIN cities c ON c.rowid=search.rowid WHERE search MATCH ? LIMIT ?', (expression, limit)).fetchall()

    def resolve_unique(self, query):
        """Only exact, unambiguous names/labels; never guess between same-name towns."""
        clean = normalize(query)
        if not clean or len(clean) > 200: return None
        found = [row for row in self._rows(clean, 1000) if clean in row['aliases'].split('\n') or clean in (normalize(row['label']), normalize(row['name'] + ', ' + row['country']))]
        if len(found) != 1 and ',' in query:
            # «Кишинэу, Молдова» or «Springfield, Illinois»: the city part must be an exact alias and
            # every further part must name that city's country (in any CLDR language) or its region.
            city, *rest = [normalize(part) for part in query.split(',')]
            rest, names = [part for part in rest if part], country_names()
            rows = self._rows(city, 5001) if city and rest else []
            places = lambda row: {normalize(row['country']), row['country_code'].lower(), normalize(row['region'])} | names.get(row['country_code'], frozenset())
            # A truncated candidate list could hide a second same-name town: refuse rather than guess.
            found = [] if len(rows) > 5000 else [row for row in rows if city in row['aliases'].split('\n') and all(part in places(row) for part in rest)]
        return self.public(found[0]) if len(found) == 1 else None


city_index = CityIndex()
