from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="YY私厨")
    app_env: str = Field(default="development")
    debug: bool = Field(default=True)
    api_v1_prefix: str = Field(default="/api/v1")
    docs_url: str = Field(default="/docs")
    openapi_url: str = Field(default="/openapi.json")

    database_url: str | None = Field(default=None)
    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5433)
    db_name: str = Field(default="yy_kitchen")
    db_user: str = Field(default="postgres")
    db_password: str = Field(default="password")

    jwt_secret_key: str = Field(default="replace-with-strong-secret")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=30)

    upload_dir: str = Field(default="uploads")
    max_upload_size_mb: int = Field(default=10)
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5174"])

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
