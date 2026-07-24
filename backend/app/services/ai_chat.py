import asyncio
import base64
import json
import logging
from collections.abc import AsyncIterator, Sequence
from contextlib import suppress
from datetime import datetime

from fastapi import UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.constants import ErrorCode
from app.core.exceptions import AppException
from app.models.ai_chat import AiChatMessage, AiChatMessageKind, AiChatRole
from app.models.dish import Dish
from app.repositories.ai_chat import (
    create_ai_chat_conversation,
    create_ai_chat_message,
    create_fridge_image_analysis,
    delete_ai_chat_conversation,
    get_ai_chat_conversation,
    get_ai_chat_message,
    get_ai_chat_message_by_id,
    list_ai_chat_conversations,
    list_ai_chat_messages,
    list_recent_ai_chat_messages,
    update_ai_chat_conversation,
    update_ai_chat_message_metadata,
)
from app.schemas.ai_chat import (
    AiChatConversationListItem,
    AiChatConversationPage,
    AiChatMessagePage,
    AiChatMessageProfile,
    AiChatMetadata,
    AiChatTurnResponse,
    AiRecommendationItem,
    ConfirmAiActionResponse,
    CreateAiChatMessageRequest,
)
from app.services.agent_runtime import execute_agent_turn
from app.services.ai_provider import SummaryDeltaHandler
from app.services.dish import list_dishes_for_family
from app.services.shopping_list import create_ai_agent_shopping_list
from app.services.upload import read_and_validate_image, save_image_bytes

DEFAULT_CONVERSATION_TITLE = "新对话"
logger = logging.getLogger(__name__)


def build_system_prompt(dishes: Sequence[Dish]) -> str:
    candidate_dishes = [
        {
            "dish_id": dish.id,
            "name": dish.name,
            "description": dish.description or "",
            "price": dish.price,
            "cooking_minutes": dish.cooking_minutes,
            "difficulty": dish.difficulty,
            "spicy_level": dish.spicy_level,
            "ingredients": [link.ingredient.name for link in dish.ingredients if link.ingredient],
            "is_available": dish.is_available,
        }
        for dish in dishes
        if dish.is_available
    ]
    return (
        "你是 YY私厨 的做饭助手。"
        "请优先从给定的家庭菜品库里推荐适合做的菜。"
        "如果菜品描述信息不足，可以根据常见做法推断所需食材和做法，但推荐菜名优先命中已有菜品。"
        "只有在用户明确上传了冰箱图片时，才可以提及冰箱图片、识别食材或看图分析。"
        "如果用户没有上传图片，不要主动提到冰箱、冰箱照片、食材识别、看不到图片、后续可上传图片等内容。"
        "如果用户上传了冰箱图片，请先识别冰箱中可能存在的食材，再结合用户问题给出推荐。"
        "你可以参考菜品里的结构化食材、步骤和家庭偏好。"
        "输出必须是 JSON 对象，不要输出 markdown。"
        'JSON 结构固定为 '
        '{"summary": string, "recognized_ingredients": string[], "recommendations": '
        '[{"dish_name": string, "rating": 1-5, "required_ingredients": string[], '
        '"matched_ingredients": string[], "steps": string[], "reason": string}]}.'
        "如果没有上传图片，recognized_ingredients 必须返回空数组。"
        "如果图片看不清，请在 summary 与 reason 中说明识别不确定。"
        f"家庭菜品库如下：{json.dumps(candidate_dishes, ensure_ascii=False)}"
    )


def build_history_messages(messages: Sequence[AiChatMessage]) -> list[dict[str, object]]:
    history: list[dict[str, object]] = []
    for message in messages:
        history.append(
            {
                "role": message.role,
                "content": [{"type": "text", "text": message.content}],
            }
        )
    return history


def build_image_data_url(content: bytes, suffix: str) -> str:
    encoded = base64.b64encode(content).decode("ascii")
    mime_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }[suffix]
    return f"data:{mime_type};base64,{encoded}"


def format_assistant_content(summary: str, recommendations: Sequence[AiRecommendationItem]) -> str:
    lines = [summary.strip() or "已为你整理推荐结果。"]
    for index, recommendation in enumerate(recommendations, start=1):
        rating = "★" * recommendation.rating + "☆" * (5 - recommendation.rating)
        lines.append(f"{index}. {recommendation.dish_name} {rating}")
        if recommendation.reason:
            lines.append(f"推荐理由：{recommendation.reason}")
        if recommendation.required_ingredients:
            lines.append(f"所需食材：{'、'.join(recommendation.required_ingredients)}")
        if recommendation.steps:
            lines.append(f"做法：{'；'.join(recommendation.steps)}")
    return "\n".join(lines)


def resolve_assistant_message_kind(metadata: AiChatMetadata) -> str:
    if metadata.action_draft is not None:
        return AiChatMessageKind.DRAFT_ACTION
    if metadata.tool_calls or metadata.retrieval_sources:
        return AiChatMessageKind.TOOL_RESULT
    return AiChatMessageKind.RECOMMENDATION


def build_conversation_title(content: str) -> str:
    normalized = " ".join(content.strip().split())
    if not normalized:
        return DEFAULT_CONVERSATION_TITLE
    return normalized[:30]


def build_conversation_preview(content: str) -> str | None:
    normalized = " ".join(content.strip().split())
    return normalized[:60] if normalized else None


def serialize_conversation(
    *,
    conversation_id: int,
    family_id: int,
    user_id: int,
    title: str,
    created_at: datetime,
    updated_at: datetime,
    last_message_preview: str | None,
    last_message_at: datetime | None,
) -> AiChatConversationListItem:
    return AiChatConversationListItem(
        id=conversation_id,
        family_id=family_id,
        user_id=user_id,
        title=title,
        created_at=created_at,
        updated_at=updated_at,
        last_message_preview=build_conversation_preview(last_message_preview or ""),
        last_message_at=last_message_at,
    )


async def list_ai_conversations_for_user(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
) -> AiChatConversationPage:
    rows = await list_ai_chat_conversations(session, family_id=family_id, user_id=user_id)
    items = [
        serialize_conversation(
            conversation_id=conversation.id,
            family_id=conversation.family_id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            last_message_preview=last_message_preview,
            last_message_at=last_message_at,
        )
        for conversation, last_message_preview, last_message_at in rows
    ]
    return AiChatConversationPage(items=items)


async def list_ai_messages_for_user(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
    conversation_id: int,
    limit: int,
    before_id: int | None,
) -> AiChatMessagePage:
    conversation = await get_ai_chat_conversation(
        session,
        family_id=family_id,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    if conversation is None:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message="AI 对话不存在或已被删除",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    messages, has_more = await list_ai_chat_messages(
        session,
        family_id=family_id,
        user_id=user_id,
        conversation_id=conversation_id,
        limit=limit,
        before_id=before_id,
    )
    return AiChatMessagePage(
        items=[AiChatMessageProfile.model_validate(message) for message in messages],
        has_more=has_more,
    )


async def delete_ai_conversation_for_user(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
    conversation_id: int,
) -> None:
    conversation = await get_ai_chat_conversation(
        session,
        family_id=family_id,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    if conversation is None:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message="AI 对话不存在或已被删除",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    await delete_ai_chat_conversation(session, conversation)
    await session.commit()


async def create_ai_turn(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
    payload: CreateAiChatMessageRequest,
    image: UploadFile | None = None,
    on_summary_delta: SummaryDeltaHandler | None = None,
) -> AiChatTurnResponse:
    settings = get_settings()
    dishes = await list_dishes_for_family(session, family_id=family_id)
    available_dishes = [dish for dish in dishes if dish.is_available]
    if not available_dishes:
        raise AppException(
            code=ErrorCode.BAD_REQUEST,
            message="当前家庭还没有可推荐的菜品，请先添加菜品",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    image_url: str | None = None
    image_data_url: str | None = None
    recognized_ingredients: list[str] = []
    raw_model_output: str | None = None
    user_message_kind = AiChatMessageKind.TEXT

    if image is not None:
        content, suffix = await read_and_validate_image(image)
        image_url = save_image_bytes(
            content,
            family_id=family_id,
            category_segments=("ai", "fridge"),
            suffix=suffix,
        )
        image_data_url = build_image_data_url(content, suffix)
        user_message_kind = AiChatMessageKind.FRIDGE_IMAGE

    conversation_title = build_conversation_title(payload.content)
    if payload.conversation_id is None:
        conversation = await create_ai_chat_conversation(
            session,
            family_id=family_id,
            user_id=user_id,
            title=conversation_title,
        )
    else:
        conversation = await get_ai_chat_conversation(
            session,
            family_id=family_id,
            user_id=user_id,
            conversation_id=payload.conversation_id,
        )
        if conversation is None:
            raise AppException(
                code=ErrorCode.NOT_FOUND,
                message="AI 对话不存在或已被删除",
                status_code=status.HTTP_404_NOT_FOUND,
            )

    recent_messages = await list_recent_ai_chat_messages(
        session,
        family_id=family_id,
        user_id=user_id,
        conversation_id=conversation.id,
        limit=settings.ai_max_history_messages,
    )
    agent_result = await execute_agent_turn(
        session,
        family_id=family_id,
        user_content=payload.content,
        image_data_url=image_data_url,
        recent_messages=recent_messages,
        dishes=available_dishes,
        on_summary_delta=on_summary_delta,
    )
    recognized_ingredients = agent_result.recognized_ingredients
    raw_model_output = agent_result.raw_model_output

    user_metadata: dict[str, object] | None = None
    if image_url is not None:
        user_metadata = {
            "fridge_image": {
                "image_url": image_url,
                "recognized_ingredients": recognized_ingredients,
            }
        }

    user_message = await create_ai_chat_message(
        session,
        family_id=family_id,
        user_id=user_id,
        conversation_id=conversation.id,
        role=AiChatRole.USER,
        content=payload.content,
        message_kind=user_message_kind,
        metadata_json=user_metadata,
    )

    recommendations = agent_result.recommendations
    assistant_content = format_assistant_content(agent_result.summary, recommendations)
    assistant_metadata = AiChatMetadata(
        summary=agent_result.summary,
        recognized_ingredients=recognized_ingredients,
        recommendations=recommendations,
        fridge_image=(
            {
                "image_url": image_url,
                "recognized_ingredients": recognized_ingredients,
            }
            if image_url is not None
            else None
        ),
        retrieval_sources=agent_result.retrieval_sources,
        tool_calls=agent_result.tool_calls,
        action_draft=agent_result.action_draft,
        confirmation_required=agent_result.action_draft is not None,
        confidence=agent_result.confidence,
        raw_model_output=raw_model_output,
    )
    assistant_message = await create_ai_chat_message(
        session,
        family_id=family_id,
        user_id=user_id,
        conversation_id=conversation.id,
        role=AiChatRole.ASSISTANT,
        content=assistant_content,
        message_kind=resolve_assistant_message_kind(assistant_metadata),
        metadata_json=assistant_metadata.model_dump(),
    )

    if image_url is not None and raw_model_output is not None:
        await create_fridge_image_analysis(
            session,
            family_id=family_id,
            user_id=user_id,
            image_url=image_url,
            recognized_ingredients=recognized_ingredients,
            raw_model_output=raw_model_output,
        )

    await update_ai_chat_conversation(session, conversation)
    user_message_id = user_message.id
    assistant_message_id = assistant_message.id
    conversation_id = conversation.id
    await session.commit()

    persisted_user = await get_ai_chat_message(
        session,
        family_id=family_id,
        user_id=user_id,
        conversation_id=conversation_id,
        message_id=user_message_id,
    )
    persisted_assistant = await get_ai_chat_message(
        session,
        family_id=family_id,
        user_id=user_id,
        conversation_id=conversation_id,
        message_id=assistant_message_id,
    )
    persisted_conversation = await get_ai_chat_conversation(
        session,
        family_id=family_id,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    if persisted_user is None or persisted_assistant is None or persisted_conversation is None:
        raise AppException(
            code=ErrorCode.INTERNAL_ERROR,
            message="AI 对话保存失败，请稍后重试",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return AiChatTurnResponse(
        conversation=serialize_conversation(
            conversation_id=persisted_conversation.id,
            family_id=persisted_conversation.family_id,
            user_id=persisted_conversation.user_id,
            title=persisted_conversation.title,
            created_at=persisted_conversation.created_at,
            updated_at=persisted_conversation.updated_at,
            last_message_preview=persisted_assistant.content,
            last_message_at=persisted_assistant.created_at,
        ),
        user_message=AiChatMessageProfile.model_validate(persisted_user),
        assistant_message=AiChatMessageProfile.model_validate(persisted_assistant),
    )


def encode_sse_event(event: str, data: object) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {payload}\n\n"


async def stream_ai_turn(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
    payload: CreateAiChatMessageRequest,
    image: UploadFile | None = None,
) -> AsyncIterator[str]:
    """Run an AI turn and expose summary deltas plus the persisted final turn as SSE."""
    deltas: asyncio.Queue[str] = asyncio.Queue()

    async def enqueue_delta(delta: str) -> None:
        if delta:
            await deltas.put(delta)

    task = asyncio.create_task(
        create_ai_turn(
            session,
            family_id=family_id,
            user_id=user_id,
            payload=payload,
            image=image,
            on_summary_delta=enqueue_delta,
        )
    )
    yield encode_sse_event("ready", {"status": "processing"})

    try:
        while not task.done() or not deltas.empty():
            if not deltas.empty():
                yield encode_sse_event("delta", {"content": deltas.get_nowait()})
                continue

            delta_task = asyncio.create_task(deltas.get())
            done, _ = await asyncio.wait(
                {task, delta_task},
                timeout=15,
                return_when=asyncio.FIRST_COMPLETED,
            )
            if delta_task in done:
                delta = delta_task.result()
                yield encode_sse_event("delta", {"content": delta})
            else:
                delta_task.cancel()
                with suppress(asyncio.CancelledError):
                    await delta_task
            if not done:
                yield ": keep-alive\n\n"

        turn = await task
        yield encode_sse_event("complete", turn.model_dump(mode="json", by_alias=True))
    except asyncio.CancelledError:
        task.cancel()
        raise
    except AppException as exc:
        yield encode_sse_event(
            "error",
            {"code": exc.code, "message": exc.message, "status_code": exc.status_code},
        )
    except Exception:
        logger.exception("Unexpected error while streaming AI chat response")
        yield encode_sse_event(
            "error",
            {
                "code": ErrorCode.INTERNAL_ERROR,
                "message": "AI 服务暂时不可用，请稍后再试",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            },
        )
    finally:
        if not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError, Exception):
                await task


async def confirm_ai_action_for_user(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
    message_id: int,
) -> ConfirmAiActionResponse:
    message = await require_ai_action_message(
        session,
        family_id=family_id,
        user_id=user_id,
        message_id=message_id,
    )
    metadata = AiChatMetadata.model_validate(message.metadata_json or {})
    draft = metadata.action_draft
    if draft is None or draft.action_type != "shopping_list":
        raise AppException(
            code=ErrorCode.BAD_REQUEST,
            message="当前消息没有可确认的购物清单草案",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if draft.status == "confirmed":
        return ConfirmAiActionResponse(message=AiChatMessageProfile.model_validate(message))

    shopping_list = await create_ai_agent_shopping_list(
        session,
        family_id=family_id,
        action_draft=draft,
        source_reference=f"ai_chat_message:{message.id}",
    )
    draft.status = "confirmed"
    draft.shopping_list_id = shopping_list.id
    metadata.action_draft = draft
    metadata.confirmation_required = False
    await update_ai_chat_message_metadata(
        session,
        message,
        metadata_json=metadata.model_dump(),
        message_kind=AiChatMessageKind.DRAFT_ACTION,
    )
    await session.commit()
    return ConfirmAiActionResponse(message=AiChatMessageProfile.model_validate(message))


async def cancel_ai_action_for_user(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
    message_id: int,
) -> ConfirmAiActionResponse:
    message = await require_ai_action_message(
        session,
        family_id=family_id,
        user_id=user_id,
        message_id=message_id,
    )
    metadata = AiChatMetadata.model_validate(message.metadata_json or {})
    draft = metadata.action_draft
    if draft is None:
        raise AppException(
            code=ErrorCode.BAD_REQUEST,
            message="当前消息没有可取消的动作草案",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    draft.status = "cancelled"
    metadata.action_draft = draft
    metadata.confirmation_required = False
    await update_ai_chat_message_metadata(
        session,
        message,
        metadata_json=metadata.model_dump(),
        message_kind=AiChatMessageKind.DRAFT_ACTION,
    )
    await session.commit()
    return ConfirmAiActionResponse(message=AiChatMessageProfile.model_validate(message))


async def require_ai_action_message(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
    message_id: int,
) -> AiChatMessage:
    message = await get_ai_chat_message_by_id(
        session,
        family_id=family_id,
        user_id=user_id,
        message_id=message_id,
    )
    if message is None:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message="AI 动作不存在或已失效",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return message
