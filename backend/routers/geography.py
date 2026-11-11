import sqlite3
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from auth import get_current_user
from services.geography import city_index


def create_geography_router():
    router = APIRouter(prefix='/api/geography', tags=['geography'])

    @router.get('/cities')
    def cities(q: str = Query('', max_length=80), user=Depends(get_current_user)):
        try: items = city_index.search(q.strip())
        except (OSError, sqlite3.Error):
            raise HTTPException(503, 'Поиск городов временно недоступен. Город можно указать вручную.') from None
        return JSONResponse({'items': items, 'attribution': 'GeoNames · CC BY 4.0', 'source': 'https://www.geonames.org/'}, headers={'Cache-Control': 'private, no-store'})

    return router
