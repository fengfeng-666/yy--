from collections.abc import AsyncIterator
from tempfile import TemporaryDirectory

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_application


@pytest_asyncio.fixture
async def test_client() -> AsyncIterator[AsyncClient]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    settings = get_settings()
    original_upload_dir = settings.upload_dir

    with TemporaryDirectory() as temp_upload_dir:
        settings.upload_dir = temp_upload_dir
        app = create_application()

        async def override_get_db_session() -> AsyncIterator[AsyncSession]:
            async with session_factory() as session:
                yield session

        app.dependency_overrides[get_db_session] = override_get_db_session

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver/api/v1",
        ) as client:
            yield client

        app.dependency_overrides.clear()
        settings.upload_dir = original_upload_dir

    await engine.dispose()


async def register_and_login(
    client: AsyncClient,
    *,
    username: str,
    password: str = "secret123",
) -> str:
    await client.post(
        "/auth/register",
        json={
            "username": username,
            "nickname": username,
            "password": password,
        },
    )
    login_response = await client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    return login_response.json()["data"]["tokens"]["access_token"]


async def create_family(client: AsyncClient, headers: dict[str, str]) -> None:
    response = await client.post("/families", json={"name": "YY私厨"}, headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_dish_crud_and_upload(test_client: AsyncClient) -> None:
    access_token = await register_and_login(test_client, username="dish_owner")
    headers = {"Authorization": f"Bearer {access_token}"}
    await create_family(test_client, headers)

    upload_response = await test_client.post(
        "/uploads/images",
        files={"file": ("mapo-tofu.png", b"fake-image-bytes", "image/png")},
        headers=headers,
    )
    assert upload_response.status_code == 200
    upload_data = upload_response.json()["data"]
    assert upload_data["path"].startswith("/uploads/families/1/dishes/")
    assert upload_data["url"].startswith("http://testserver/uploads/families/1/dishes/")

    create_dish_response = await test_client.post(
        "/dishes",
        json={
            "name": "麻婆豆腐",
            "description": "又香又下饭",
            "price": 22.5,
            "image_url": upload_data["path"],
            "is_available": True,
        },
        headers=headers,
    )
    assert create_dish_response.status_code == 200
    dish_body = create_dish_response.json()["data"]
    dish_id = dish_body["id"]
    assert dish_body["name"] == "麻婆豆腐"

    list_response = await test_client.get("/dishes", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 1

    update_dish_response = await test_client.patch(
        f"/dishes/{dish_id}",
        json={
            "name": "麻婆豆腐（微辣）",
            "description": "更适合日常晚餐",
            "price": 24,
            "image_url": upload_data["path"],
            "is_available": False,
        },
        headers=headers,
    )
    assert update_dish_response.status_code == 200
    assert update_dish_response.json()["data"]["is_available"] is False

    delete_dish_response = await test_client.delete(f"/dishes/{dish_id}", headers=headers)
    assert delete_dish_response.status_code == 200
