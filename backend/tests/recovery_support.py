"""Small Mongo-like test adapter. Production code never depends on this module."""
import copy
import re
from types import SimpleNamespace
from pymongo.errors import DuplicateKeyError

def field(document, key):
    value = document
    for part in key.split('.'):
        if not isinstance(value, dict): return None
        value = value.get(part)
    return value

def matches(document, query):
    for key, wanted in query.items():
        if key == '$or':
            if not any(matches(document, q) for q in wanted): return False
            continue
        actual = field(document, key)
        if isinstance(wanted, dict):
            for op, value in wanted.items():
                if op == '$ne' and actual == value: return False
                if op == '$gt' and (actual is None or actual <= value): return False
                if op == '$lte' and (actual is None or actual > value): return False
                if op == '$exists' and ((actual is not None) != value): return False
                if op == '$regex' and not re.search(value, actual or '', re.I if wanted.get('$options') == 'i' else 0): return False
        elif actual != wanted: return False
    return True

def apply(document, update):
    for key, value in update.get('$set', {}).items(): document[key] = copy.deepcopy(value)
    for key, value in update.get('$inc', {}).items(): document[key] = document.get(key, 0) + value
    for key in update.get('$unset', {}): document.pop(key, None)

class Collection:
    def __init__(self, documents=()): self.documents = copy.deepcopy(list(documents))
    async def find_one(self, query, projection=None):
        for d in self.documents:
            if matches(d, query): return copy.deepcopy(d)
        return None
    async def update_one(self, query, update, upsert=False):
        result = await self.find_one_and_update(query, update, upsert=upsert)
        return SimpleNamespace(matched_count=int(result is not None))
    async def find_one_and_update(self, query, update, upsert=False, return_document=False):
        for d in self.documents:
            if matches(d, query):
                old = copy.deepcopy(d); apply(d, update)
                return copy.deepcopy(d) if return_document else old
        if upsert:
            if any(d.get('_id') == query.get('_id') for d in self.documents): raise DuplicateKeyError('duplicate')
            d = {k:v for k,v in query.items() if not isinstance(v,dict)}
            d.update(copy.deepcopy(update.get('$setOnInsert', {}))); apply(d,update); self.documents.append(d)
            return copy.deepcopy(d) if return_document else None
        return None
    async def insert_one(self, document): self.documents.append(copy.deepcopy(document))
    async def create_index(self, *args, **kwargs): return 'test-index'

class Mailbox:
    configured = True
    def __init__(self): self.messages = []; self.fail = False
    async def send_reset(self, email, url):
        if self.fail: raise OSError('synthetic mail failure')
        self.messages.append({'email': email, 'url': url})
    async def send_changed(self, email): self.messages.append({'email': email, 'changed': True})
