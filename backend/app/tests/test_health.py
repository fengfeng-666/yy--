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
