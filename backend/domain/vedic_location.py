"""Validated coordinates and an isolated location scope for legacy formula calls."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import lru_cache

import pytz
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field


class LocationInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    latitude: float = Field(strict=True, ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(strict=True, ge=-180, le=180, allow_inf_nan=False)


@lru_cache(maxsize=1)
def _timezone_finder():
    from timezonefinder import TimezoneFinder
    return TimezoneFinder()


def resolve_timezone(location: LocationInput):
    try:
        zone = _timezone_finder().timezone_at(lat=location.latitude, lng=location.longitude)
        if not zone:
            raise ValueError('Unknown timezone')
        pytz.timezone(zone)
    except Exception:
        raise HTTPException(422, 'Не удалось определить часовой пояс места. Баллы не списаны.') from None
    return zone


_coordinates = ContextVar('vedic_request_coordinates', default=None)


def current_coordinates(city):
    current = _coordinates.get()
    return current[1] if current is not None and current[0] == city else None


@contextmanager
def location_scope(city, latitude, longitude, timezone):
    token = _coordinates.set((city, (latitude, longitude, timezone)))
    try:
        yield
    finally:
        _coordinates.reset(token)
