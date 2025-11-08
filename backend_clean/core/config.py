"""
Конфигурация приложения

Исходный код перенесён из:
- backend/server.py (строки 50-95)
- backend/.env

Дата переноса: 2025-10-09
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """
    Настройки приложения загружаются из .env файла

    Использует Pydantic Settings для валидации и type hints
    """

    # ===========================================
    # MongoDB настройки
    # Источник: backend/.env строки 1-3
    # ===========================================
    MONGO_URL: str = Field(
        default="mongodb://localhost:27017",
        description="URL подключения к MongoDB"
    )
    MONGODB_DATABASE: str = Field(
        default="numerom",
        description="Имя базы данных MongoDB"
    )

    # ===========================================
    # JWT настройки
    # Источник: backend/.env строки 5-8
    # ===========================================
    JWT_SECRET_KEY: str = Field(
        default="your-super-secret-jwt-key-change-this-in-production",
        description="Секретный ключ для JWT токенов"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="Алгоритм шифрования JWT"
    )
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Время жизни access token в минутах"
    )

    # ===========================================
    # Stripe настройки
    # Источник: backend/.env строки 10-13
    # ===========================================
    STRIPE_PUBLIC_KEY: Optional[str] = Field(
        default="pk_test_your_stripe_public_key",
        description="Публичный ключ Stripe"
    )
    STRIPE_SECRET_KEY: Optional[str] = Field(
        default="sk_test_your_stripe_secret_key",
        description="Секретный ключ Stripe"
    )
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(
        default="whsec_your_webhook_secret",
        description="Секрет для Stripe webhooks"
    )

    # ===========================================
    # Настройки приложения
    # Источник: backend/.env строки 15-17
    # ===========================================
    APP_URL: str = Field(
        default="http://localhost:3000",
        description="URL фронтенда"
    )
    BACKEND_URL: str = Field(
        default="http://localhost:8000",
        description="URL бэкенда"
    )

    # ===========================================
    # Супер администратор
    # Источник: backend/.env строки 19-21
    # ===========================================
    SUPER_ADMIN_EMAIL: str = Field(
        default="dmitrii.malahov@gmail.com",
        description="Email суперадминистратора (создаётся при первом запуске)"
    )
    SUPER_ADMIN_PASSWORD: str = Field(
        default="756bvy67H",
        description="Пароль суперадминистратора"
    )

    # ===========================================
    # Пути для загрузок
    # Источник: backend/server.py строки 86-95
    # ===========================================
    UPLOAD_ROOT: Path = Field(
        default=Path("uploads"),
        description="Корневая папка для загрузок"
    )

    # Конфигурация Pydantic Settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # ===========================================
    # Вычисляемые свойства
    # ===========================================

    @property
    def materials_dir(self) -> Path:
        """Папка для материалов"""
        return self.UPLOAD_ROOT / "materials"

    @property
    def consultations_dir(self) -> Path:
        """Папка для консультаций"""
        return self.UPLOAD_ROOT / "consultations"

    @property
    def consultations_video_dir(self) -> Path:
        """Папка для видео консультаций"""
        return self.consultations_dir / "videos"

    @property
    def consultations_pdf_dir(self) -> Path:
        """Папка для PDF консультаций"""
        return self.consultations_dir / "pdfs"

    @property
    def consultations_subtitles_dir(self) -> Path:
        """Папка для субтитров консультаций"""
        return self.consultations_dir / "subtitles"

    @property
    def lessons_dir(self) -> Path:
        """Папка для уроков"""
        return self.UPLOAD_ROOT / "lessons"

    @property
    def lessons_video_dir(self) -> Path:
        """Папка для видео уроков"""
        return self.lessons_dir / "videos"

    @property
    def lessons_pdf_dir(self) -> Path:
        """Папка для PDF уроков"""
        return self.lessons_dir / "pdfs"

    @property
    def tmp_dir(self) -> Path:
        """Временная папка"""
        return self.UPLOAD_ROOT / "tmp"

    @property
    def stripe_api_key(self) -> Optional[str]:
        """Alias для STRIPE_SECRET_KEY"""
        return self.STRIPE_SECRET_KEY

    @property
    def payment_demo_mode(self) -> bool:
        """
        Режим демо-платежей (если нет настоящего Stripe ключа)
        Источник: backend/server.py строка 65
        """
        return (
            not self.STRIPE_SECRET_KEY
            or self.STRIPE_SECRET_KEY == 'sk_test_dummy_key_for_testing'
        )

    def create_upload_directories(self) -> None:
        """
        Создать все необходимые папки для загрузок

        Источник: backend/server.py строки 101-109
        """
        directories = [
            self.materials_dir,
            self.consultations_dir,
            self.consultations_video_dir,
            self.consultations_pdf_dir,
            self.consultations_subtitles_dir,
            self.lessons_dir,
            self.lessons_video_dir,
            self.lessons_pdf_dir,
            self.tmp_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# ===========================================
# Константы для платежей
# Источник: backend/server.py строки 67-79
# ===========================================

PAYMENT_PACKAGES = {
    'one_time': 0.99,              # 0,99€ = 10 баллов + месяц доступа
    'monthly': 9.99,               # 9,99€ = 150 баллов + месяц доступа
    'annual': 66.6,                # 66,6€ = 500 баллов + год доступа
    'master_consultation': 666.0   # 666€ = 10000 баллов + персональная консультация
}

SUBSCRIPTION_CREDITS = {
    'one_time': 10,                # 10 баллов за 0,99€
    'monthly': 150,                # 150 баллов за 9,99€
    'annual': 1000,                # 1000 баллов за 66,6€
    'master_consultation': 10000   # 10000 баллов за 666€ + консультация
}


# ===========================================
# Singleton instance
# ===========================================

# Определяем путь к .env относительно этого файла
ROOT_DIR = Path(__file__).parent.parent
ENV_FILE = ROOT_DIR / '.env'

# Создаём экземпляр настроек
# При импорте автоматически загружаются значения из .env
settings = Settings(_env_file=str(ENV_FILE) if ENV_FILE.exists() else None)


# ===========================================
# Экспорт для удобства
# ===========================================

__all__ = [
    'settings',
    'Settings',
    'PAYMENT_PACKAGES',
    'SUBSCRIPTION_CREDITS',
]
