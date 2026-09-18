import logging
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

log = logging.getLogger("hirely.config")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HIRELY_", env_file=".env", extra="ignore")

    database_url: str
    redis_url: Optional[str] = None
    public_base_url: str = "http://localhost:8081"
    secret_key: str = Field(min_length=32)
    bot_api_tokens: str = ""
    media_dir: str = "/data/media"
    display_tz: str = "Asia/Tashkent"
    # nginx must *set* (not append) this header; with Cloudflare use cf-connecting-ip.
    client_ip_header: str = "x-real-ip"
    cookie_secure: bool = True
    admin_session_hours: int = 12
    bootstrap_admin_email: Optional[str] = None
    bootstrap_admin_password: Optional[str] = None
    max_upload_mb: int = 6
    event_queue_size: int = 50000

    @field_validator("database_url")
    @classmethod
    def _driver(cls, v: str) -> str:
        for prefix in ("postgresql://", "postgres://"):
            if v.startswith(prefix):
                return "postgresql+asyncpg://" + v[len(prefix):]
        return v

    @property
    def api_tokens(self) -> List[str]:
        tokens = [t.strip() for t in self.bot_api_tokens.split(",") if t.strip()]
        good = [t for t in tokens if len(t) >= 24]
        if len(good) != len(tokens):
            log.warning("Ignoring bot API tokens shorter than 24 chars")
        return good

    @property
    def base_url(self) -> str:
        return self.public_base_url.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
