from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from pydantic import Field, model_validator
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

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.app_env.lower() not in {"production", "prod"}:
            return self

        if self.debug:
            raise ValueError("生产环境必须关闭 DEBUG")

        weak_secret_markers = ("replace", "change-me", "change_me", "changeme")
        normalized_secret = self.jwt_secret_key.lower()
        if len(self.jwt_secret_key.encode("utf-8")) < 32 or any(
            marker in normalized_secret for marker in weak_secret_markers
        ):
            raise ValueError("生产环境 JWT_SECRET_KEY 必须是至少 32 字节的随机密钥")

        normalized_db_password = self.db_password.lower()
        if not self.database_url and (
            normalized_db_password in {"password", "postgres"}
            or any(marker in normalized_db_password for marker in weak_secret_markers)
        ):
            raise ValueError("生产环境必须配置强数据库密码")

        if "*" in self.cors_origins:
            raise ValueError("生产环境 CORS_ORIGINS 不能使用通配符")

        return self

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{quote(self.db_user, safe='')}:{quote(self.db_password, safe='')}"
            f"@{self.db_host}:{self.db_port}/{quote(self.db_name, safe='')}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
