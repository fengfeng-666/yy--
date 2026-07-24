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
from app.schemas.agent import AgentResult
from app.schemas.ai_chat import ParsedAiRecommendation
from app.services import agent_runtime as agent_runtime_service
from app.services import ai_chat as ai_chat_service
from app.services.ai_chat import build_system_prompt
from app.services.ai_provider import extract_streaming_summary
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


def build_stub_result(
    summary: str = "适合做这几道菜",
) -> AgentResult:
    return AgentResult.model_validate(
        {
            "summary": summary,
            "recognized_ingredients": ["鸡蛋", "番茄", "葱"],
            "recommendations": [
                {
                    "dish_name": "番茄炒蛋",
                    "rating": 5,
                    "required_ingredients": ["番茄", "鸡蛋", "油", "盐"],
                    "matched_ingredients": ["番茄", "鸡蛋"],
                    "steps": [],
                    "reason": "现有食材匹配度高，做法简单。",
                },
                {
                    "dish_name": "葱花煎蛋",
                    "rating": 4,
                    "required_ingredients": ["鸡蛋", "葱", "盐", "油"],
                    "matched_ingredients": ["鸡蛋", "葱"],
                    "steps": [],
                    "reason": "冰箱里现有食材足够。",
                },
            ],
            "retrieval_sources": [],
            "tool_calls": [],
            "action_draft": None,
            "confidence": 0.92,
            "raw_model_output": '{"summary":"ok"}',
        }
    )


def test_build_system_prompt_avoids_unsolicited_fridge_copy() -> None:
    prompt = build_system_prompt([])

    assert "如果用户没有上传图片，不要主动提到冰箱" in prompt
    assert "recognized_ingredients 必须返回空数组" in prompt
    assert "required_ingredients 最多 6 项" in prompt
    assert "steps 必须返回空数组" in prompt
    assert "不生成购物清单" in prompt


def test_ai_recommendation_keeps_ingredients_brief_and_omits_steps() -> None:
    parsed = ParsedAiRecommendation.model_validate(
        {
            "summary": "推荐一道菜",
            "recognized_ingredients": [],
            "recommendations": [
                {
                    "dish_name": "番茄炒蛋",
                    "rating": 5,
                    "required_ingredients": ["1", "2", "3", "4", "5", "6", "7"],
                    "matched_ingredients": [],
                    "steps": ["切菜", "翻炒"],
                    "reason": "家常菜",
                }
            ],
            "raw_model_output": '{"summary":"推荐一道菜"}',
        }
    )

    assert parsed.recommendations[0].required_ingredients == ["1", "2", "3", "4", "5", "6"]
    assert parsed.recommendations[0].steps == []


def test_extract_streaming_summary_handles_partial_json_and_escapes() -> None:
    assert extract_streaming_summary('{"summary":"番茄\\n炒') == "番茄\n炒"
    assert extract_streaming_summary('{"summary":"推荐\\u756a\\u8304') == "推荐番茄"
    assert extract_streaming_summary('{"summary":"尚未完成\\') == "尚未完成"


@pytest.mark.asyncio
async def test_execute_agent_turn_uses_only_basic_dish_knowledge_and_preferences(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = {"relationships_locked": False}

    class GuardedCollection:
        def __init__(self, values: list[object]) -> None:
            self.values = values

        def __iter__(self):
            if state["relationships_locked"]:
                raise AssertionError("dish relationships were accessed after await")
            return iter(self.values)

    class IngredientRef:
        def __init__(self, name: str) -> None:
            self.name = name

    class IngredientLink:
        def __init__(self, name: str) -> None:
            self.ingredient = IngredientRef(name)

    class Step:
        def __init__(self, content: str) -> None:
            self.content = content

    class Preference:
        def __init__(self, note: str) -> None:
            self.preference_note = note

    class FakeDish:
        def __init__(self) -> None:
            self.id = 1
            self.name = "番茄炒蛋"
            self.description = "家常快手菜"
            self.cooking_minutes = 10
            self.difficulty = 1
            self.spicy_level = 0
            self.is_available = True
            self.ingredients = GuardedCollection([IngredientLink("食材哨兵")])
            self.steps = GuardedCollection([Step("步骤哨兵")])
            self.preferences = GuardedCollection([Preference("少油少盐")])

    async def fake_retrieve_recipe_sources(*_: object, **__: object):
        state["relationships_locked"] = True
        return []

    async def fake_build_family_preference_summary(*_: object, **__: object):
        return "家庭偏好：少油少盐", ["少油少盐"]

    async def fake_generate_ai_recommendation(*_: object, **kwargs: object):
        prompt = kwargs["system_prompt"]
        assert "番茄炒蛋" in prompt
        assert "少油少盐" in prompt
        assert "食材哨兵" not in prompt
        assert "步骤哨兵" not in prompt
        assert "steps 必须返回空数组" in prompt
        return ParsedAiRecommendation.model_validate(
            {
                "summary": "推荐番茄炒蛋",
                "recognized_ingredients": [],
                "recommendations": [
                    {
                        "dish_name": "番茄炒蛋",
                        "rating": 5,
                        "required_ingredients": ["番茄", "鸡蛋"],
                        "matched_ingredients": ["番茄", "鸡蛋"],
                        "steps": [],
                        "reason": "家庭常做，食材齐全。",
                    }
                ],
                "raw_model_output": '{"summary":"推荐番茄炒蛋"}',
            }
        )

    monkeypatch.setattr(
        agent_runtime_service,
        "retrieve_recipe_sources",
        fake_retrieve_recipe_sources,
    )
    monkeypatch.setattr(
        agent_runtime_service,
        "build_family_preference_summary",
        fake_build_family_preference_summary,
    )
    monkeypatch.setattr(
        agent_runtime_service,
        "generate_ai_recommendation",
        fake_generate_ai_recommendation,
    )

    result = await agent_runtime_service.execute_agent_turn(
        session=None,  # type: ignore[arg-type]
        family_id=1,
        user_content="帮我推荐一个菜品",
        image_data_url=None,
        recent_messages=[],
        dishes=[FakeDish()],
    )

    assert result.summary == "推荐番茄炒蛋"
    assert result.recommendations[0].dish_name == "番茄炒蛋"
    assert result.action_draft is None


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
    async def fake_execute_agent_turn(*_: object, **__: object) -> AgentResult:
        return build_stub_result()

    monkeypatch.setattr(
        ai_chat_service,
        "execute_agent_turn",
        fake_execute_agent_turn,
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
    async def fake_execute_agent_turn(*_: object, **__: object) -> AgentResult:
        return build_stub_result()

    monkeypatch.setattr(
        ai_chat_service,
        "execute_agent_turn",
        fake_execute_agent_turn,
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
    async def fake_execute_agent_turn(*_: object, **__: object) -> AgentResult:
        return build_stub_result()

    monkeypatch.setattr(
        ai_chat_service,
        "execute_agent_turn",
        fake_execute_agent_turn,
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
async def test_stream_ai_chat_message_emits_delta_and_persisted_turn(
    test_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_execute_agent_turn(*_: object, **kwargs: object) -> AgentResult:
        on_summary_delta = kwargs.get("on_summary_delta")
        assert callable(on_summary_delta)
        await on_summary_delta("适合做")
        await on_summary_delta("番茄炒蛋")
        return build_stub_result("适合做番茄炒蛋")

    monkeypatch.setattr(ai_chat_service, "execute_agent_turn", fake_execute_agent_turn)
    token = await register_and_login(test_client, "ai_stream_owner")
    await create_family_with_dishes(test_client, token)

    response = await test_client.post(
        "/ai-chat/messages/stream",
        data={"content": "推荐一道快手菜"},
        headers=headers(token),
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["x-accel-buffering"] == "no"
    assert 'event: delta\ndata: {"content":"适合做"}' in response.text
    assert 'event: delta\ndata: {"content":"番茄炒蛋"}' in response.text
    assert "event: complete" in response.text
    assert '"assistant_message"' in response.text


@pytest.mark.asyncio
async def test_send_ai_chat_message_with_fridge_image_success(
    test_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_execute_agent_turn(*_: object, **__: object) -> AgentResult:
        return build_stub_result("根据冰箱图片，推荐这几道菜。")

    monkeypatch.setattr(
        ai_chat_service,
        "execute_agent_turn",
        fake_execute_agent_turn,
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
    async def fake_execute_agent_turn(*_: object, **__: object) -> AgentResult:
        return build_stub_result()

    monkeypatch.setattr(
        ai_chat_service,
        "execute_agent_turn",
        fake_execute_agent_turn,
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

    member_conversations = await test_client.get(
        "/ai-chat/conversations", headers=headers(member_token)
    )
    assert member_conversations.status_code == 200
    assert member_conversations.json()["data"]["items"] == []


@pytest.mark.asyncio
async def test_ai_chat_returns_provider_error(
    test_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_execute_agent_turn(*_: object, **__: object) -> AgentResult:
        raise AppException(
            code=ErrorCode.INTERNAL_ERROR,
            message="AI 服务暂时不可用，请稍后再试",
            status_code=500,
        )

    monkeypatch.setattr(
        ai_chat_service,
        "execute_agent_turn",
        fake_execute_agent_turn,
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
    async def fake_execute_agent_turn(*_: object, **__: object) -> AgentResult:
        raise AppException(
            code=ErrorCode.INTERNAL_ERROR,
            message="AI 返回格式解析失败，请稍后再试",
            status_code=500,
        )

    monkeypatch.setattr(
        ai_chat_service,
        "execute_agent_turn",
        fake_execute_agent_turn,
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


@pytest.mark.asyncio
async def test_shopping_list_endpoints_are_not_available(test_client: AsyncClient) -> None:
    token = await register_and_login(test_client, "ai_action_owner")
    await create_family(test_client, token)

    confirmed = await test_client.post(
        "/ai-chat/actions/1/confirm",
        headers=headers(token),
    )
    assert confirmed.status_code == 404

    shopping_lists = await test_client.get("/shopping-lists", headers=headers(token))
    assert shopping_lists.status_code == 404
