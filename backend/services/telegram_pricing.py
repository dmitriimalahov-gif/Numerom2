"""Current Stars prices; existing invoices retain their persisted amount."""
from fastapi import HTTPException
from domain.payments import PACKAGES
from domain.telegram import TelegramConfig

COLLECTION = 'telegram_stars_config'
PRODUCT_LABELS = {key: f'{value["title"]} · {value["credits"]} баллов' for key, value in PACKAGES.items()}
PRODUCT_LABELS['full_report'] = 'Полный персональный разбор'
MAX_STARS = 100000


def default_prices(config=None):
    prices = (config or TelegramConfig()).prices
    return {key: prices.get(key, 0) for key in PRODUCT_LABELS}


def validate_prices(values):
    if not values or set(values) - set(PRODUCT_LABELS):
        raise HTTPException(422, 'Неизвестная или отсутствующая цена Telegram Stars')
    for key, value in values.items():
        if type(value) is not int or not 0 <= value <= MAX_STARS:
            raise HTTPException(422, f'{PRODUCT_LABELS[key]}: укажите целое число от 0 до {MAX_STARS}')
    return values


async def current_prices(db, config):
    row = await getattr(db, COLLECTION).find_one({'is_active': True})
    # Once saved in the admin panel, missing/zero values disable new sales.
    # Never fall back to an old environment price for an explicitly disabled product.
    values = default_prices(config) if row is None else {key: row.get(key, 0) for key in PRODUCT_LABELS}
    validate_prices(values)
    return {key: value for key, value in values.items() if value > 0}
