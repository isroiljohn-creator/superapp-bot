"""Application settings — loaded from environment variables."""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Telegram
    BOT_TOKEN: str
    WEBAPP_URL: str = ""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/superapp"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Payments — Click
    CLICK_MERCHANT_ID: str = ""
    CLICK_SERVICE_ID: str = ""
    CLICK_SECRET_KEY: str = ""

    # Payments — Payme
    PAYME_MERCHANT_ID: str = ""
    PAYME_SECRET_KEY: str = ""

    # Bot settings
    ADMIN_IDS_STR: str = ""
    PRIVATE_GROUP_ID: int = 0
    CLUB_PRICE: int = 97_000  # UZS

    @property
    def ADMIN_IDS(self) -> List[int]:
        if not self.ADMIN_IDS_STR:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS_STR.split(",") if x.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
