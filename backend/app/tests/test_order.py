from collections.abc import AsyncIterator
from datetime import date

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
) -> str:
    await client.post(
        "/auth/register",
        json={"username": username, "nickname": username, "password": password},
    )
    response = await client.post("/auth/login", json={"username": username, "password": password})
    return response.json()["data"]["tokens"]["access_token"]


async def create_family(client: AsyncClient, token: str) -> str:
    response = await client.post(
        "/families",
        json={"name": "YY私厨"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.json()["data"]["family"]["invite_code"]


async def join_family(client: AsyncClient, token: str, invite_code: str) -> None:
    await client.post(
        "/families/join",
        json={"invite_code": invite_code},
        headers={"Authorization": f"Bearer {token}"},
    )


async def create_dish(client: AsyncClient, token: str) -> int:
    headers = {"Authorization": f"Bearer {token}"}
    category_response = await client.post(
        "/dish-categories",
        json={"name": "家常菜", "sort_order": 1},
        headers=headers,
    )
    category_id = category_response.json()["data"]["id"]
    dish_response = await client.post(
        "/dishes",
        json={
            "category_id": category_id,
            "name": "番茄炒蛋",
            "description": "适合晚餐",
            "price": 18,
            "is_available": True,
        },
        headers=headers,
    )
    return dish_response.json()["data"]["id"]


@pytest.mark.asyncio
async def test_create_list_detail_and_accept_order(test_client: AsyncClient) -> None:
    owner_token = await register_and_login(test_client, username="owner")
    invite_code = await create_family(test_client, owner_token)

    member_token = await register_and_login(test_client, username="member")
    await join_family(test_client, member_token, invite_code)

    dish_id = await create_dish(test_client, owner_token)

    create_response = await test_client.post(
        "/orders",
        json={
            "cook_id": 2,
            "planned_date": date.today().isoformat(),
            "planned_time": "19:00:00",
            "note": "少放一点糖",
            "items": [{"dish_id": dish_id, "quantity": 2}],
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert create_response.status_code == 200
    order_body = create_response.json()["data"]
    order_id = order_body["id"]
    assert order_body["status"] == "pending"
    assert order_body["items"][0]["dish"]["name"] == "番茄炒蛋"
    assert order_body["status_logs"][0]["to_status"] == "pending"

    owner_list = await test_client.get(
        "/orders",
        params={"role": "my_requested", "status": "pending"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert owner_list.status_code == 200
    assert len(owner_list.json()["data"]) == 1

    member_list = await test_client.get(
        "/orders",
        params={"role": "to_me", "status": "pending"},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert member_list.status_code == 200
    assert member_list.json()["data"][0]["id"] == order_id

    forbidden_accept = await test_client.post(
        f"/orders/{order_id}/accept",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert forbidden_accept.status_code == 403

    accept_response = await test_client.post(
        f"/orders/{order_id}/accept",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert accept_response.status_code == 200
    assert accept_response.json()["data"]["status"] == "accepted"
    assert len(accept_response.json()["data"]["status_logs"]) == 2

    detail_response = await test_client.get(
        f"/orders/{order_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["cook"]["username"] == "member"


@pytest.mark.asyncio
async def test_order_detail_is_isolated_by_family(test_client: AsyncClient) -> None:
    owner_token = await register_and_login(test_client, username="chef_a")
    invite_code = await create_family(test_client, owner_token)
    member_token = await register_and_login(test_client, username="chef_b")
    await join_family(test_client, member_token, invite_code)
    dish_id = await create_dish(test_client, owner_token)

    create_response = await test_client.post(
        "/orders",
        json={
            "cook_id": 2,
            "planned_date": date.today().isoformat(),
            "items": [{"dish_id": dish_id, "quantity": 1}],
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    order_id = create_response.json()["data"]["id"]

    outsider_token = await register_and_login(test_client, username="outsider")
    await create_family(test_client, outsider_token)

    outsider_detail = await test_client.get(
        f"/orders/{order_id}",
        headers={"Authorization": f"Bearer {outsider_token}"},
    )
    assert outsider_detail.status_code == 404
