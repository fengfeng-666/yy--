import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


def test_settings_defaults() -> None:
    settings = get_settings()
    assert settings.api_v1_prefix == "/api/v1"


def test_settings_build_database_url_from_parts() -> None:
    settings = Settings(
        _env_file=None,
        database_url=None,
        db_host="db",
        db_port=5432,
        db_name="yy_kitchen",
        db_user="postgres",
        db_password="password",
    )
    assert (
        settings.sqlalchemy_database_url
        == "postgresql+asyncpg://postgres:password@db:5432/yy_kitchen"
    )


def test_settings_prefer_explicit_database_url() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://user:pwd@custom:5432/app",
    )
    assert settings.sqlalchemy_database_url == "postgresql+asyncpg://user:pwd@custom:5432/app"


def test_settings_escape_database_credentials() -> None:
    settings = Settings(
        _env_file=None,
        database_url=None,
        db_host="db",
        db_port=5432,
        db_name="yy kitchen",
        db_user="yy@user",
        db_password="p@ss/word",
    )

    assert (
        settings.sqlalchemy_database_url
        == "postgresql+asyncpg://yy%40user:p%40ss%2Fword@db:5432/yy%20kitchen"
    )


def test_settings_accept_secure_production_configuration() -> None:
    settings = Settings(
        _env_file=None,
        app_env="production",
        debug=False,
        db_password="a-strong-database-password",
        jwt_secret_key="a" * 64,
        cors_origins=[],
    )

    assert settings.app_env == "production"
    assert settings.debug is False


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"debug": True}, "必须关闭 DEBUG"),
        ({"jwt_secret_key": "short"}, "JWT_SECRET_KEY"),
        ({"jwt_secret_key": "CHANGE_ME_GENERATE_A_RANDOM_64_HEX_VALUE"}, "JWT_SECRET_KEY"),
        ({"db_password": "password"}, "数据库密码"),
        ({"db_password": "CHANGE_ME_USE_A_LONG_RANDOM_PASSWORD"}, "数据库密码"),
        ({"cors_origins": ["*"]}, "不能使用通配符"),
    ],
)
def test_settings_reject_insecure_production_configuration(
    overrides: dict[str, object],
    message: str,
) -> None:
    production_settings: dict[str, object] = {
        "_env_file": None,
        "app_env": "production",
        "debug": False,
        "db_password": "a-strong-database-password",
        "jwt_secret_key": "a" * 64,
        "cors_origins": [],
    }
    production_settings.update(overrides)

    with pytest.raises(ValidationError, match=message):
        Settings(**production_settings)
