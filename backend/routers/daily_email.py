from fastapi import APIRouter
from services.daily_email import DailyEmail, DailyEmailChoice


def create_daily_email_router(db, service=None):
    router = APIRouter(prefix='/api', tags=['daily-email'])
    service = service or DailyEmail(db)

    # Opened from a letter without signing in: the signed token names the account.
    @router.post('/public/daily-email')
    async def choose(body: DailyEmailChoice):
        return await service.choose(body)

    return router
