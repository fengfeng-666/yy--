from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.constants import ErrorCode
from app.core.exceptions import AppException
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_application
from app.services import chat as chat_service


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

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api/v1"
    ) as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()


async def register_and_login(client: AsyncClient, username: str) -> str:
    await client.post(
        "/auth/register",
        json={"username": username, "nickname": username, "password": "secret123"},
    )
    response = await client.post(
        "/auth/login",
        json={"username": username, "password": "secret123"},
    )
    return response.json()["data"]["tokens"]["access_token"]


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def create_family(client: AsyncClient, token: str, name: str = "YY私厨") -> str:
    response = await client.post(
        "/families",
        json={"name": name},
        headers=headers(token),
    )
    return response.json()["data"]["family"]["invite_code"]


async def join_family(client: AsyncClient, token: str, invite_code: str) -> None:
    response = await client.post(
        "/families/join",
        json={"invite_code": invite_code},
        headers=headers(token),
    )
    assert response.status_code == 200


async def send_message(client: AsyncClient, token: str, content: str) -> dict:
    response = await client.post(
        "/chat/messages",
        json={"content": content},
        headers=headers(token),
    )
    assert response.status_code == 200
    return response.json()["data"]


@pytest.mark.asyncio
async def test_chat_requires_authentication_and_family(test_client: AsyncClient) -> None:
    unauthenticated = await test_client.get("/chat/messages")
    assert unauthenticated.status_code == 401

    token = await register_and_login(test_client, "no_family")
    without_family = await test_client.get("/chat/messages", headers=headers(token))
    assert without_family.status_code == 404


@pytest.mark.asyncio
async def test_send_and_cursor_paginate_family_messages(test_client: AsyncClient) -> None:
    owner_token = await register_and_login(test_client, "chat_owner")
    invite_code = await create_family(test_client, owner_token)
    member_token = await register_and_login(test_client, "chat_member")
    await join_family(test_client, member_token, invite_code)

    first = await send_message(test_client, owner_token, "  今晚吃面吗？\n🍜  ")
    second = await send_message(test_client, member_token, "好呀")
    third = await send_message(test_client, owner_token, "加个煎蛋")
    fourth = await send_message(test_client, member_token, "收到 😄")

    assert first["content"] == "今晚吃面吗？\n🍜"
    assert first["sender"]["username"] == "chat_owner"

    latest_response = await test_client.get(
        "/chat/messages",
        params={"limit": 2},
        headers=headers(owner_token),
    )
    latest = latest_response.json()["data"]
    assert [item["id"] for item in latest["items"]] == [third["id"], fourth["id"]]
    assert latest["has_more"] is True

    older_response = await test_client.get(
        "/chat/messages",
        params={"before_id": third["id"], "limit": 2},
        headers=headers(owner_token),
    )
    older = older_response.json()["data"]
    assert [item["id"] for item in older["items"]] == [first["id"], second["id"]]
    assert older["has_more"] is False

    newer_response = await test_client.get(
        "/chat/messages",
        params={"after_id": first["id"], "limit": 2},
        headers=headers(owner_token),
    )
    newer = newer_response.json()["data"]
    assert [item["id"] for item in newer["items"]] == [second["id"], third["id"]]
    assert newer["has_more"] is True

    invalid_cursors = await test_client.get(
        "/chat/messages",
        params={"before_id": third["id"], "after_id": first["id"]},
        headers=headers(owner_token),
    )
    assert invalid_cursors.status_code == 400


@pytest.mark.asyncio
async def test_chat_message_content_validation(test_client: AsyncClient) -> None:
    token = await register_and_login(test_client, "validation_owner")
    await create_family(test_client, token)

    empty = await test_client.post(
        "/chat/messages",
        json={"content": "   \n  "},
        headers=headers(token),
    )
    too_long = await test_client.post(
        "/chat/messages",
        json={"content": "长" * 1001},
        headers=headers(token),
    )

    assert empty.status_code == 422
    assert too_long.status_code == 422


@pytest.mark.asyncio
async def test_unread_count_and_forward_only_read_cursor(test_client: AsyncClient) -> None:
    owner_token = await register_and_login(test_client, "unread_owner")
    invite_code = await create_family(test_client, owner_token)
    member_token = await register_and_login(test_client, "unread_member")
    await join_family(test_client, member_token, invite_code)

    first = await send_message(test_client, owner_token, "第一条")
    second = await send_message(test_client, owner_token, "第二条")

    owner_unread = await test_client.get("/chat/unread-count", headers=headers(owner_token))
    member_unread = await test_client.get("/chat/unread-count", headers=headers(member_token))
    assert owner_unread.json()["data"]["unread_count"] == 0
    assert member_unread.json()["data"]["unread_count"] == 2

    marked = await test_client.post(
        "/chat/read",
        json={"last_read_message_id": second["id"]},
        headers=headers(member_token),
    )
    assert marked.json()["data"]["unread_count"] == 0

    await test_client.post(
        "/chat/read",
        json={"last_read_message_id": first["id"]},
        headers=headers(member_token),
    )
    await send_message(test_client, owner_token, "第三条")
    after_backward_attempt = await test_client.get(
        "/chat/unread-count", headers=headers(member_token)
    )
    assert after_backward_attempt.json()["data"]["unread_count"] == 1

    reply = await send_message(test_client, member_token, "回复")
    owner_after_reply = await test_client.get(
        "/chat/unread-count", headers=headers(owner_token)
    )
    assert owner_after_reply.json()["data"]["unread_count"] == 1

    duplicate_mark = await test_client.post(
        "/chat/read",
        json={"last_read_message_id": reply["id"]},
        headers=headers(owner_token),
    )
    assert duplicate_mark.json()["data"]["unread_count"] == 0


@pytest.mark.asyncio
async def test_chat_is_isolated_by_family(test_client: AsyncClient) -> None:
    first_token = await register_and_login(test_client, "family_one")
    await create_family(test_client, first_token, "家庭一")
    message = await send_message(test_client, first_token, "家庭一的消息")

    second_token = await register_and_login(test_client, "family_two")
    await create_family(test_client, second_token, "家庭二")

    second_list = await test_client.get("/chat/messages", headers=headers(second_token))
    assert second_list.json()["data"]["items"] == []

    cross_family_read = await test_client.post(
        "/chat/read",
        json={"last_read_message_id": message["id"]},
        headers=headers(second_token),
    )
    assert cross_family_read.status_code == 404


@pytest.mark.asyncio
async def test_mark_message_read_returns_app_exception_when_retry_still_hits_integrity_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSession:
        async def commit(self) -> None:
            return None

        async def rollback(self) -> None:
            return None

    async def fake_get_chat_message(
        session: AsyncSession,
        *,
        family_id: int,
        message_id: int,
    ) -> object:
        return object()

    async def fake_get_chat_read_state(
        session: AsyncSession,
        *,
        family_id: int,
        user_id: int,
    ) -> None:
        return None

    async def fake_create_chat_read_state(
        session: AsyncSession,
        *,
        family_id: int,
        user_id: int,
        last_read_message_id: int,
    ) -> None:
        raise IntegrityError("insert into chat_read_states", None, Exception("duplicate key"))

    async def fake_advance_chat_read_state(
        session: AsyncSession,
        *,
        family_id: int,
        user_id: int,
        last_read_message_id: int,
    ) -> None:
        raise IntegrityError("update chat_read_states", None, Exception("still failing"))

    monkeypatch.setattr(chat_service, "get_chat_message", fake_get_chat_message)
    monkeypatch.setattr(chat_service, "get_chat_read_state", fake_get_chat_read_state)
    monkeypatch.setattr(chat_service, "create_chat_read_state", fake_create_chat_read_state)
    monkeypatch.setattr(chat_service, "advance_chat_read_state", fake_advance_chat_read_state)

    with pytest.raises(AppException) as exc_info:
        await chat_service.mark_message_read_for_user(
            FakeSession(),
            family_id=1,
            user_id=2,
            message_id=3,
        )

    assert exc_info.value.code == ErrorCode.INTERNAL_ERROR
    assert exc_info.value.status_code == 500
    assert exc_info.value.message == "标记消息已读失败，请稍后重试"
