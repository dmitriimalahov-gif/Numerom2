"""Immutable one-time report price and bounded checkout input."""
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StrictStr, StrictBool, Field, field_validator, model_validator

INTEGRATION = 'numerom-full-report-v1'
AMOUNT_TOTAL = 666
CURRENCY = 'eur'
TITLE = 'Полный личный разбор'
DESCRIPTION = 'Расчёты по дате и заполненным данным профиля, авторские схемы, смысловой разбор, практики, озвучка и персональный MP4. Разовая оплата.'


class FullReportPreview(BaseModel):
    model_config = ConfigDict(extra='forbid')
    birth_date: StrictStr
    use_profile: StrictBool = False

    @field_validator('birth_date')
    @classmethod
    def valid_date(cls, value):
        try:
            parsed = datetime.strptime(value, '%d.%m.%Y').date()
        except ValueError:
            raise ValueError('Укажите существующую дату в формате ДД.ММ.ГГГГ')
        if parsed.strftime('%d.%m.%Y') != value or not date(1900, 1, 1) <= parsed <= date.today():
            raise ValueError('Дата рождения должна быть между 01.01.1900 и сегодняшним днём')
        return value


class FullReportCheckout(FullReportPreview):
    request_id: UUID
    client: Literal['mobile', 'web'] = 'mobile'
    profile_fingerprint: StrictStr | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')

    @field_validator('request_id')
    @classmethod
    def uuid4(cls, value):
        if value.version != 4:
            raise ValueError('UUIDv4 required')
        return value

    @model_validator(mode='after')
    def profile_confirmation(self):
        if bool(self.profile_fingerprint) != self.use_profile:
            raise ValueError('Сначала проверьте состав данных профиля перед оплатой')
        return self


class FullReportProfileExtension(BaseModel):
    model_config = ConfigDict(extra='forbid')
    profile_fingerprint: StrictStr = Field(pattern=r'^[a-f0-9]{64}$')
    expected_revision: int = Field(strict=True, ge=1, le=1000)
