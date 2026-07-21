from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_current_user
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_application


@pytest_asyncio.fixture
async def test_client() -> AsyncIterator[AsyncClient]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    app = create_application()

    async def override_get_db_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides.pop(get_current_user, None)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver/api/v1") as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_register_login_and_me(test_client: AsyncClient) -> None:
    register_response = await test_client.post(
        "/auth/register",
        json={
            "username": "chef01",
            "nickname": "主厨",
            "password": "secret123",
        },
    )

    assert register_response.status_code == 200
    register_body = register_response.json()
    assert register_body["message"] == "注册成功"
    assert register_body["data"]["user"]["username"] == "chef01"
    assert register_body["data"]["tokens"]["access_token"]

    duplicate_response = await test_client.post(
        "/auth/register",
        json={
            "username": "chef01",
            "nickname": "重复用户",
            "password": "secret123",
        },
    )
    assert duplicate_response.status_code == 409

    login_response = await test_client.post(
        "/auth/login",
        json={"username": "chef01", "password": "secret123"},
    )
    assert login_response.status_code == 200

    access_token = login_response.json()["data"]["tokens"]["access_token"]
    me_response = await test_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["data"]["nickname"] == "主厨"


@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_401(test_client: AsyncClient) -> None:
    await test_client.post(
        "/auth/register",
        json={
            "username": "chef02",
            "password": "secret123",
        },
    )

    response = await test_client.post(
        "/auth/login",
        json={"username": "chef02", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["message"] == "用户名或密码错误"
