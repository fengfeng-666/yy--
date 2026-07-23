import base64
import json
from collections.abc import Sequence
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
    list_ai_chat_conversations,
    list_ai_chat_messages,
    list_recent_ai_chat_messages,
    update_ai_chat_conversation,
)
from app.schemas.ai_chat import (
    AiChatConversationListItem,
    AiChatConversationPage,
    AiChatMessagePage,
    AiChatMessageProfile,
    AiChatTurnResponse,
    AiRecommendationItem,
    CreateAiChatMessageRequest,
)
from app.services.ai_provider import generate_ai_recommendation
from app.services.dish import list_dishes_for_family
from app.services.upload import read_and_validate_image, save_image_bytes

DEFAULT_CONVERSATION_TITLE = "新对话"


def build_system_prompt(dishes: Sequence[Dish]) -> str:
    candidate_dishes = [
        {
            "dish_id": dish.id,
            "name": dish.name,
            "description": dish.description or "",
            "price": dish.price,
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
    parsed = await generate_ai_recommendation(
        system_prompt=build_system_prompt(available_dishes),
        history_messages=build_history_messages(recent_messages),
        user_content=payload.content,
        image_data_url=image_data_url,
    )
    recognized_ingredients = parsed.recognized_ingredients
    raw_model_output = parsed.raw_model_output

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

    recommendations = parsed.recommendations
    assistant_content = format_assistant_content(parsed.summary, recommendations)
    assistant_message = await create_ai_chat_message(
        session,
        family_id=family_id,
        user_id=user_id,
        conversation_id=conversation.id,
        role=AiChatRole.ASSISTANT,
        content=assistant_content,
        message_kind=AiChatMessageKind.RECOMMENDATION,
        metadata_json={
            "summary": parsed.summary,
            "recognized_ingredients": recognized_ingredients,
            "recommendations": [item.model_dump() for item in recommendations],
            "fridge_image": (
                {
                    "image_url": image_url,
                    "recognized_ingredients": recognized_ingredients,
                }
                if image_url is not None
                else None
            ),
            "raw_model_output": raw_model_output,
        },
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
