from fastapi import APIRouter, Depends
from auth import get_current_user
from domain.telegram import TelegramLaunch, TelegramRegistration, TelegramLink, TelegramInvoice, verify_init_data
from services.telegram import TelegramAccounts
from services.telegram_payments import TelegramPayments
from domain.full_report_purchase import FullReportCheckout


def create_telegram_router(db, accounts=None):
    router = APIRouter(prefix='/api', tags=['telegram'])
    accounts = accounts or TelegramAccounts(db)
    payments = TelegramPayments(db, accounts)

    @router.post('/auth/telegram/login')
    async def login(body: TelegramLaunch):
        return await accounts.login(body)

    @router.post('/auth/telegram/register')
    async def register(body: TelegramRegistration):
        return await accounts.register(body)

    @router.post('/auth/telegram/link')
    async def link(body: TelegramLink):
        return await accounts.link(body)

    @router.post('/telegram/menu')
    async def menu(body: TelegramLaunch, user=Depends(get_current_user)):
        identity = verify_init_data(body.init_data, accounts.config)
        linked = await accounts.find(identity['id'])
        from fastapi import HTTPException
        if not linked or linked['id'] != user['user_id']:
            raise HTTPException(403, 'Аккаунт Telegram не совпадает с текущим входом.')
        await accounts.menu(identity['id'])
        return {'ok': True}

    @router.get('/telegram/payments/catalog')
    async def catalog(user=Depends(get_current_user)):
        return await payments.catalog(user['user_id'])

    @router.post('/telegram/payments/invoice')
    async def invoice(body: TelegramInvoice, user=Depends(get_current_user)):
        return await payments.create(user['user_id'], body)

    @router.get('/telegram/payments/orders/{order_id}')
    async def status(order_id: str, user=Depends(get_current_user)):
        return await payments.status(user['user_id'], order_id)

    @router.get('/telegram/full-reports/catalog')
    async def report_catalog(user=Depends(get_current_user)):
        return await payments.report_catalog(user['user_id'])

    @router.post('/telegram/full-reports/checkout')
    async def report_checkout(body: FullReportCheckout, user=Depends(get_current_user)):
        return await payments.create_report(user['user_id'], body)

    return router
