"""City-only reverse geocoding. No account writes or persistent location history.

One process-wide upstream slot enforces the public Nominatim pilot limit.
The bounded, short-lived cache holds rounded grid keys and city labels only.
urllib avoids HTTP-client INFO/debug request-URL logging of coordinates.
"""
from collections import OrderedDict
import json
import os
import ssl
import threading
import time
from urllib.error import URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPSHandler, HTTPRedirectHandler, ProxyHandler, Request, build_opener

import certifi
from fastapi import HTTPException
from domain.vedic_location import LocationInput, resolve_timezone


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _fetch_city(latitude, longitude):
    endpoint = os.environ.get('NUMEROM_GEOCODER_URL', 'https://nominatim.openstreetmap.org/reverse')
    parsed = urlsplit(endpoint)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise HTTPException(503, 'Сервис определения города временно недоступен.')
    query = urlencode({'format': 'jsonv2', 'lat': latitude, 'lon': longitude,
                       'zoom': 10, 'addressdetails': 1, 'layer': 'address', 'accept-language': 'ru'})
    request = Request(endpoint + '?' + query, headers={
        'User-Agent': 'NumerOM/1.0 (https://1.numer.om/)',
        'Accept': 'application/json'})
    opener = build_opener(ProxyHandler({}), _NoRedirect(),
                         HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
    try:
        with opener.open(request, timeout=8) as response:
            content = response.read(65537)
        if len(content) > 65536:
            raise ValueError('Oversized response')
        data = json.loads(content)
    except (URLError, OSError, ValueError):
        raise HTTPException(503, 'Не удалось определить город. Попробуйте позже или введите его вручную.') from None
    address = data.get('address') if isinstance(data, dict) else None
    if not isinstance(address, dict):
        raise HTTPException(422, 'Рядом не найден населённый пункт. Укажите город вручную.')
    city = next((address[key] for key in ('city', 'town', 'village', 'municipality') if isinstance(address.get(key), str) and address[key].strip()), '')
    country = address.get('country', '')
    if not isinstance(country, str):
        country = ''
    label = ', '.join((city.strip(), country.strip()))
    if not city or not country.strip() or len(label) > 120 or any(ord(c) < 32 for c in label) or not any(c.isalpha() for c in city):
        raise HTTPException(422, 'Не удалось получить название города и страны. Укажите город вручную.')
    return label


class ReverseGeocoder:
    def __init__(self, *, fetch=None, clock=time.monotonic, ttl=600, capacity=128):
        self.fetch = fetch or _fetch_city
        self.clock, self.ttl, self.capacity = clock, ttl, capacity
        self.cache = OrderedDict()
        self.cache_lock = threading.Lock()
        self.upstream = threading.Lock()
        self.last_started = float('-inf')

    def city(self, location: LocationInput):
        # A city suggestion needs no street precision; exact input is never cached.
        key = (round(location.latitude, 3), round(location.longitude, 3))
        now = self.clock()
        with self.cache_lock:
            cached = self.cache.get(key)
            if cached and now - cached[0] < self.ttl:
                self.cache.move_to_end(key)
                return cached[1]
            self.cache.pop(key, None)
        if not self.upstream.acquire(blocking=False):
            raise HTTPException(429, 'Определение города занято. Повторите через несколько секунд.', headers={'Retry-After': '2'})
        try:
            now = self.clock()
            if now - self.last_started < 1:
                raise HTTPException(429, 'Повторите определение города через несколько секунд.', headers={'Retry-After': '2'})
            self.last_started = now
            label = self.fetch(*key)
            with self.cache_lock:
                self.cache[key] = (self.clock(), label)
                while len(self.cache) > self.capacity:
                    self.cache.popitem(last=False)
            return label
        finally:
            self.upstream.release()


_geocoder = ReverseGeocoder()


def resolve_location(location: LocationInput):
    timezone = resolve_timezone(location)
    return {'city': _geocoder.city(location), **location.model_dump(), 'timezone': timezone}
