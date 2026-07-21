from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver/api/v1") as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()


async def register_and_login(
    client: AsyncClient,
    *,
    username: str,
    password: str = "secret123",
    nickname: str | None = None,
) -> str:
    await client.post(
        "/auth/register",
        json={
            "username": username,
            "nickname": nickname or username,
            "password": password,
        },
    )
    login_response = await client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    return login_response.json()["data"]["tokens"]["access_token"]


@pytest.mark.asyncio
async def test_create_family_and_query_members(test_client: AsyncClient) -> None:
    access_token = await register_and_login(test_client, username="chef_owner", nickname="主厨")
    headers = {"Authorization": f"Bearer {access_token}"}

    create_response = await test_client.post(
        "/families",
        json={
            "name": "YY私厨",
            "description": "只属于我们的两人食堂",
        },
        headers=headers,
    )

    assert create_response.status_code == 200
    body = create_response.json()
    assert body["data"]["family"]["name"] == "YY私厨"
    assert body["data"]["family"]["invite_code"]

    current_response = await test_client.get("/families/current", headers=headers)
    assert current_response.status_code == 200
    assert current_response.json()["data"]["owner_id"] == 1

    members_response = await test_client.get("/families/current/members", headers=headers)
    assert members_response.status_code == 200
    assert members_response.json()["data"][0]["role"] == "owner"


@pytest.mark.asyncio
async def test_join_family_and_limit_members(test_client: AsyncClient) -> None:
    owner_token = await register_and_login(test_client, username="owner")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    create_response = await test_client.post(
        "/families",
        json={"name": "YY私厨"},
        headers=owner_headers,
    )
    invite_code = create_response.json()["data"]["family"]["invite_code"]

    member_token = await register_and_login(test_client, username="member")
    member_headers = {"Authorization": f"Bearer {member_token}"}
    join_response = await test_client.post(
        "/families/join",
        json={"invite_code": invite_code},
        headers=member_headers,
    )
    assert join_response.status_code == 200

    third_token = await register_and_login(test_client, username="third")
    third_headers = {"Authorization": f"Bearer {third_token}"}
    full_response = await test_client.post(
        "/families/join",
        json={"invite_code": invite_code},
        headers=third_headers,
    )
    assert full_response.status_code == 409
    assert full_response.json()["message"] == "当前家庭人数已满"
