from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.constants import ErrorCode
from app.core.exceptions import AppException
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_application
from app.schemas.ai_chat import ParsedAiRecommendation
from app.services import ai_chat as ai_chat_service
from app.services.ai_chat import build_system_prompt
from app.tests.test_chat import create_family, headers, join_family, register_and_login


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


def build_stub_result(summary: str = "适合做这几道菜") -> ParsedAiRecommendation:
    return ParsedAiRecommendation.model_validate(
        {
            "summary": summary,
            "recognized_ingredients": ["鸡蛋", "番茄", "葱"],
            "recommendations": [
                {
                    "dish_name": "番茄炒蛋",
                    "rating": 5,
                    "required_ingredients": ["番茄", "鸡蛋", "油", "盐"],
                    "matched_ingredients": ["番茄", "鸡蛋"],
                    "steps": ["番茄切块", "鸡蛋炒熟", "混合翻炒调味"],
                    "reason": "现有食材匹配度高，做法简单。",
                },
                {
                    "dish_name": "葱花煎蛋",
                    "rating": 4,
                    "required_ingredients": ["鸡蛋", "葱", "盐", "油"],
                    "matched_ingredients": ["鸡蛋", "葱"],
                    "steps": ["葱切碎", "鸡蛋打散", "小火煎熟"],
                    "reason": "冰箱里现有食材足够。",
                },
            ],
            "raw_model_output": '{"summary":"ok"}',
        }
    )


def test_build_system_prompt_avoids_unsolicited_fridge_copy() -> None:
    prompt = build_system_prompt([])

    assert "如果用户没有上传图片，不要主动提到冰箱" in prompt
    assert "recognized_ingredients 必须返回空数组" in prompt


async def create_family_with_dishes(client: AsyncClient, token: str) -> None:
    await create_family(client, token)
    response = await client.post(
        "/dishes",
        json={
            "name": "番茄炒蛋",
            "description": "家常快手菜",
            "price": 18,
            "is_available": True,
        },
        headers=headers(token),
    )
    assert response.status_code == 200
    response = await client.post(
        "/dishes",
        json={
            "name": "葱花煎蛋",
            "description": "适合早餐",
            "price": 12,
            "is_available": True,
        },
        headers=headers(token),
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_ai_chat_requires_authentication_and_family(test_client: AsyncClient) -> None:
    unauthenticated = await test_client.get("/ai-chat/messages")
    assert unauthenticated.status_code == 401

    token = await register_and_login(test_client, "ai_no_family")
    without_family = await test_client.get("/ai-chat/messages", headers=headers(token))
    assert without_family.status_code == 404


@pytest.mark.asyncio
async def test_list_ai_chat_messages_returns_empty_page(test_client: AsyncClient) -> None:
    token = await register_and_login(test_client, "ai_empty")
    await create_family_with_dishes(test_client, token)

    conversations = await test_client.get("/ai-chat/conversations", headers=headers(token))

    assert conversations.status_code == 200
    assert conversations.json()["data"] == {"items": []}


@pytest.mark.asyncio
async def test_ai_chat_creates_and_lists_conversations(
    test_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_generate_ai_recommendation(**_: object) -> ParsedAiRecommendation:
        return build_stub_result()

    monkeypatch.setattr(
        ai_chat_service,
        "generate_ai_recommendation",
        fake_generate_ai_recommendation,
    )

    token = await register_and_login(test_client, "ai_conversation_owner")
    await create_family_with_dishes(test_client, token)

    created = await test_client.post(
        "/ai-chat/messages",
        data={"content": "我现在有鸡蛋和番茄，推荐吃什么？"},
        headers=headers(token),
    )

    assert created.status_code == 200
    conversation = created.json()["data"]["conversation"]
    assert conversation["title"] == "我现在有鸡蛋和番茄，推荐吃什么？"

    conversations = await test_client.get("/ai-chat/conversations", headers=headers(token))
    assert conversations.status_code == 200
    items = conversations.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["id"] == conversation["id"]
    assert items[0]["last_message_preview"].startswith("适合做这几道菜")

    response = await test_client.get(
        "/ai-chat/messages",
        params={"conversation_id": conversation["id"]},
        headers=headers(token),
    )

    assert response.status_code == 200
    assert len(response.json()["data"]["items"]) == 2


@pytest.mark.asyncio
async def test_delete_ai_chat_conversation_success(
    test_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_generate_ai_recommendation(**_: object) -> ParsedAiRecommendation:
        return build_stub_result()

    monkeypatch.setattr(
        ai_chat_service,
        "generate_ai_recommendation",
        fake_generate_ai_recommendation,
    )

    token = await register_and_login(test_client, "ai_delete_owner")
    await create_family_with_dishes(test_client, token)

    created = await test_client.post(
        "/ai-chat/messages",
        data={"content": "帮我推荐一道下饭菜"},
        headers=headers(token),
    )
    assert created.status_code == 200
    conversation_id = created.json()["data"]["conversation"]["id"]

    deleted = await test_client.delete(
        f"/ai-chat/conversations/{conversation_id}",
        headers=headers(token),
    )
    assert deleted.status_code == 200
    assert deleted.json()["message"] == "AI 对话已删除"

    conversations = await test_client.get("/ai-chat/conversations", headers=headers(token))
    assert conversations.status_code == 200
    assert conversations.json()["data"]["items"] == []

    history = await test_client.get(
        "/ai-chat/messages",
        params={"conversation_id": conversation_id},
        headers=headers(token),
    )
    assert history.status_code == 404


@pytest.mark.asyncio
async def test_send_ai_chat_text_message_success(
    test_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_generate_ai_recommendation(**_: object) -> ParsedAiRecommendation:
        return build_stub_result()

    monkeypatch.setattr(
        ai_chat_service,
        "generate_ai_recommendation",
        fake_generate_ai_recommendation,
    )

    token = await register_and_login(test_client, "ai_text_owner")
    await create_family_with_dishes(test_client, token)

    response = await test_client.post(
        "/ai-chat/messages",
        data={"content": "我现在有鸡蛋和番茄，推荐吃什么？"},
        headers=headers(token),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user_message"]["role"] == "user"
    assert data["user_message"]["message_kind"] == "text"
    assert data["assistant_message"]["role"] == "assistant"
    assert data["assistant_message"]["message_kind"] == "recommendation"
    assert data["conversation"]["title"] == "我现在有鸡蛋和番茄，推荐吃什么？"
    assert (
        data["assistant_message"]["metadata_json"]["recommendations"][0]["dish_name"]
        == "番茄炒蛋"
    )
    history = await test_client.get(
        "/ai-chat/messages",
        params={"conversation_id": data["conversation"]["id"]},
        headers=headers(token),
    )
    assert len(history.json()["data"]["items"]) == 2


@pytest.mark.asyncio
async def test_send_ai_chat_message_with_fridge_image_success(
    test_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_generate_ai_recommendation(**_: object) -> ParsedAiRecommendation:
        return build_stub_result("根据冰箱图片，推荐这几道菜。")

    monkeypatch.setattr(
        ai_chat_service,
        "generate_ai_recommendation",
        fake_generate_ai_recommendation,
    )

    token = await register_and_login(test_client, "ai_image_owner")
    await create_family_with_dishes(test_client, token)

    response = await test_client.post(
        "/ai-chat/messages",
        data={"content": "这是我冰箱里的食材"},
        files={"image": ("fridge.png", b"fake-png-image", "image/png")},
        headers=headers(token),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user_message"]["message_kind"] == "fridge_image"
    assert (
        data["user_message"]["metadata_json"]["fridge_image"]["image_url"].startswith(
            "/uploads/families/1/ai/fridge/"
        )
        is True
    )
    assert data["assistant_message"]["metadata_json"]["recognized_ingredients"] == [
        "鸡蛋",
        "番茄",
        "葱",
    ]


@pytest.mark.asyncio
async def test_ai_chat_respects_family_isolation(
    test_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_generate_ai_recommendation(**_: object) -> ParsedAiRecommendation:
        return build_stub_result()

    monkeypatch.setattr(
        ai_chat_service,
        "generate_ai_recommendation",
        fake_generate_ai_recommendation,
    )

    owner_token = await register_and_login(test_client, "ai_family_owner")
    invite_code = await create_family(test_client, owner_token)
    await test_client.post(
        "/dishes",
        json={"name": "番茄炒蛋", "description": "家常菜", "price": 18, "is_available": True},
        headers=headers(owner_token),
    )
    member_token = await register_and_login(test_client, "ai_family_member")
    await join_family(test_client, member_token, invite_code)

    await test_client.post(
        "/ai-chat/messages",
        data={"content": "推荐一道菜"},
        headers=headers(owner_token),
    )

    member_history = await test_client.get("/ai-chat/messages", headers=headers(member_token))
    assert member_history.status_code == 422

    member_conversations = await test_client.get("/ai-chat/conversations", headers=headers(member_token))
    assert member_conversations.status_code == 200
    assert member_conversations.json()["data"]["items"] == []


@pytest.mark.asyncio
async def test_ai_chat_returns_provider_error(
    test_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_generate_ai_recommendation(**_: object) -> ParsedAiRecommendation:
        raise AppException(
            code=ErrorCode.INTERNAL_ERROR,
            message="AI 服务暂时不可用，请稍后再试",
            status_code=500,
        )

    monkeypatch.setattr(
        ai_chat_service,
        "generate_ai_recommendation",
        fake_generate_ai_recommendation,
    )

    token = await register_and_login(test_client, "ai_error_owner")
    await create_family_with_dishes(test_client, token)

    response = await test_client.post(
        "/ai-chat/messages",
        data={"content": "推荐一道菜"},
        headers=headers(token),
    )

    assert response.status_code == 500
    body = response.json()
    assert body["message"] == "AI 服务暂时不可用，请稍后再试"


@pytest.mark.asyncio
async def test_ai_chat_returns_parse_error(
    test_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_generate_ai_recommendation(**_: object) -> ParsedAiRecommendation:
        raise AppException(
            code=ErrorCode.INTERNAL_ERROR,
            message="AI 返回格式解析失败，请稍后再试",
            status_code=500,
        )

    monkeypatch.setattr(
        ai_chat_service,
        "generate_ai_recommendation",
        fake_generate_ai_recommendation,
    )

    token = await register_and_login(test_client, "ai_parse_owner")
    await create_family_with_dishes(test_client, token)

    response = await test_client.post(
        "/ai-chat/messages",
        data={"content": "推荐一道菜"},
        headers=headers(token),
    )

    assert response.status_code == 500
    assert response.json()["message"] == "AI 返回格式解析失败，请稍后再试"
