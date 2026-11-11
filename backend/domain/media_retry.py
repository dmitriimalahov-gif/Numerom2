"""Persistent media recovery: bounded work per attempt, no permanent exhaustion."""
import math

MAX_DELAY = 6 * 3600

def delay(failures):
    if type(failures) is not int or failures < 1:
        raise ValueError('Invalid media failure count')
    return min(MAX_DELAY, 300 * 2 ** min(failures - 1, 7))

def scheduled(record, field):
    value = record.get(field) if isinstance(record, dict) else None
    return type(value) in (int, float) and math.isfinite(value) and value >= 0

