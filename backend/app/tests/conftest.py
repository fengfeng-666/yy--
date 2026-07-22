import pytest

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def use_secure_test_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-" + "a" * 52)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
