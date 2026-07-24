from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_chat import AiChatConversation, AiChatMessage, FridgeImageAnalysis


def _conversation_scope(
    *,
    family_id: int,
    user_id: int,
) -> tuple[object, ...]:
    return (
        AiChatConversation.family_id == family_id,
        AiChatConversation.user_id == user_id,
    )


def _message_scope(
    *,
    family_id: int,
    user_id: int,
    conversation_id: int,
) -> tuple[object, ...]:
    return (
        AiChatMessage.family_id == family_id,
        AiChatMessage.user_id == user_id,
        AiChatMessage.conversation_id == conversation_id,
    )


async def list_ai_chat_conversations(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
) -> Sequence[tuple[AiChatConversation, str | None, object | None]]:
    last_message_preview = (
        select(AiChatMessage.content)
        .where(AiChatMessage.conversation_id == AiChatConversation.id)
        .order_by(AiChatMessage.id.desc())
        .limit(1)
        .scalar_subquery()
    )
    last_message_at = (
        select(func.max(AiChatMessage.created_at))
        .where(AiChatMessage.conversation_id == AiChatConversation.id)
        .scalar_subquery()
    )
    result = await session.execute(
        select(AiChatConversation, last_message_preview, last_message_at)
        .where(*_conversation_scope(family_id=family_id, user_id=user_id))
        .order_by(AiChatConversation.updated_at.desc(), AiChatConversation.id.desc())
    )
    return result.all()


async def get_ai_chat_conversation(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
    conversation_id: int,
) -> AiChatConversation | None:
    result = await session.execute(
        select(AiChatConversation).where(
            *_conversation_scope(family_id=family_id, user_id=user_id),
            AiChatConversation.id == conversation_id,
        )
    )
    return result.scalar_one_or_none()


async def create_ai_chat_conversation(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
    title: str,
) -> AiChatConversation:
    conversation = AiChatConversation(family_id=family_id, user_id=user_id, title=title)
    session.add(conversation)
    await session.flush()
    return conversation


async def update_ai_chat_conversation(
    session: AsyncSession,
    conversation: AiChatConversation,
    *,
    title: str | None = None,
) -> AiChatConversation:
    if title is not None:
        conversation.title = title
    conversation.updated_at = datetime.now(UTC)
    await session.flush()
    return conversation


async def delete_ai_chat_conversation(
    session: AsyncSession,
    conversation: AiChatConversation,
) -> None:
    await session.delete(conversation)
    await session.flush()


async def list_ai_chat_messages(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
    conversation_id: int,
    limit: int,
    before_id: int | None = None,
) -> tuple[Sequence[AiChatMessage], bool]:
    statement: Select[tuple[AiChatMessage]] = select(AiChatMessage).where(
        *_message_scope(family_id=family_id, user_id=user_id, conversation_id=conversation_id)
    )
    if before_id is not None:
        statement = statement.where(AiChatMessage.id < before_id)

    result = await session.execute(statement.order_by(AiChatMessage.id.desc()).limit(limit + 1))
    messages = list(result.scalars().all())
    has_more = len(messages) > limit
    messages = messages[:limit]
    messages.reverse()
    return messages, has_more


async def list_recent_ai_chat_messages(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
    conversation_id: int,
    limit: int,
) -> Sequence[AiChatMessage]:
    result = await session.execute(
        select(AiChatMessage)
        .where(*_message_scope(family_id=family_id, user_id=user_id, conversation_id=conversation_id))
        .order_by(AiChatMessage.id.desc())
        .limit(limit)
    )
    messages = list(result.scalars().all())
    messages.reverse()
    return messages


async def get_ai_chat_message(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
    conversation_id: int,
    message_id: int,
) -> AiChatMessage | None:
    result = await session.execute(
        select(AiChatMessage).where(
            *_message_scope(family_id=family_id, user_id=user_id, conversation_id=conversation_id),
            AiChatMessage.id == message_id,
        )
    )
    return result.scalar_one_or_none()


async def get_ai_chat_message_by_id(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
    message_id: int,
) -> AiChatMessage | None:
    result = await session.execute(
        select(AiChatMessage).where(
            AiChatMessage.family_id == family_id,
            AiChatMessage.user_id == user_id,
            AiChatMessage.id == message_id,
        )
    )
    return result.scalar_one_or_none()


async def create_ai_chat_message(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
    conversation_id: int,
    role: str,
    content: str,
    message_kind: str,
    metadata_json: dict[str, Any] | None = None,
) -> AiChatMessage:
    message = AiChatMessage(
        family_id=family_id,
        user_id=user_id,
        conversation_id=conversation_id,
        role=role,
        content=content,
        message_kind=message_kind,
        metadata_json=metadata_json,
    )
    session.add(message)
    await session.flush()
    return message


async def update_ai_chat_message_metadata(
    session: AsyncSession,
    message: AiChatMessage,
    *,
    metadata_json: dict[str, Any] | None,
    message_kind: str | None = None,
) -> AiChatMessage:
    message.metadata_json = metadata_json
    if message_kind is not None:
        message.message_kind = message_kind
    await session.flush()
    return message


async def create_fridge_image_analysis(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
    image_url: str,
    recognized_ingredients: list[str],
    raw_model_output: str,
) -> FridgeImageAnalysis:
    analysis = FridgeImageAnalysis(
        family_id=family_id,
        user_id=user_id,
        image_url=image_url,
        recognized_ingredients_json=recognized_ingredients,
        raw_model_output=raw_model_output,
    )
    session.add(analysis)
    await session.flush()
    return analysis
