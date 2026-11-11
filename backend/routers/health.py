"""Minimal readiness signal without server, account or database details."""
import asyncio
from fastapi import APIRouter
from fastapi.responses import JSONResponse

def create_health_router(db):
    router = APIRouter()

    @router.get('/api/health')
    async def health():
        try:
            await asyncio.wait_for(db.command('ping'), timeout=2)
            return JSONResponse({'status': 'ok', 'service': 'numerom'}, headers={'Cache-Control': 'no-store'})
        except Exception:
            return JSONResponse({'status': 'unavailable', 'service': 'numerom'}, status_code=503,
                                headers={'Cache-Control': 'no-store'})
    return router
