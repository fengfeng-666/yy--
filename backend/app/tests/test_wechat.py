from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_application
from app.services.wechat import get_wechat_client


class FakeWechatClient:
    async def code_to_session(self, code: str) -> dict[str, str]:
        assert code == "valid-login-code"
        return {"openid": "openid-test-user", "unionid": "unionid-test-user"}


@pytest_asyncio.fixture
async def wechat_client() -> AsyncIterator[AsyncClient]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    app = create_application()

    async def override_get_db_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_wechat_client] = lambda: FakeWechatClient()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver/api/v1"
    ) as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_wechat_login_is_idempotent_and_can_grant_subscriptions(
    wechat_client: AsyncClient,
) -> None:
    first = await wechat_client.post(
        "/auth/wechat/login",
        json={"code": "valid-login-code", "nickname": "小厨"},
    )
    second = await wechat_client.post(
        "/auth/wechat/login",
        json={"code": "valid-login-code"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"]["user"]["id"] == second.json()["data"]["user"]["id"]
    token = second.json()["data"]["tokens"]["access_token"]

    grant = await wechat_client.post(
        "/notifications/subscriptions/grant",
        json={"event_types": ["new_order", "order_accepted"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert grant.status_code == 200
    assert grant.json()["data"] == [
        {"event_type": "new_order", "available_count": 1},
        {"event_type": "order_accepted", "available_count": 1},
    ]

    grant_again = await wechat_client.post(
        "/notifications/subscriptions/grant",
        json={"event_types": ["new_order"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert grant_again.status_code == 200
    assert grant_again.json()["data"][0]["available_count"] == 2


@pytest.mark.asyncio
async def test_subscription_grant_rejects_unknown_event(wechat_client: AsyncClient) -> None:
    login = await wechat_client.post(
        "/auth/wechat/login",
        json={"code": "valid-login-code"},
    )
    token = login.json()["data"]["tokens"]["access_token"]
    response = await wechat_client.post(
        "/notifications/subscriptions/grant",
        json={"event_types": ["unknown_event"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
