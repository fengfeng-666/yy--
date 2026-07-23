from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ErrorCode
from app.core.exceptions import AppException
from app.models.chat import ChatMessage
from app.repositories.chat import (
    advance_chat_read_state,
    count_unread_chat_messages,
    create_chat_message,
    create_chat_read_state,
    get_chat_message,
    get_chat_read_state,
    list_chat_messages,
)
from app.schemas.chat import ChatMessagePage, ChatMessageProfile, CreateChatMessageRequest


async def list_messages_for_family(
    session: AsyncSession,
    *,
    family_id: int,
    limit: int,
    before_id: int | None,
    after_id: int | None,
) -> ChatMessagePage:
    if before_id is not None and after_id is not None:
        raise AppException(message="before_id 和 after_id 不能同时使用")

    messages, has_more = await list_chat_messages(
        session,
        family_id=family_id,
        limit=limit,
        before_id=before_id,
        after_id=after_id,
    )
    return ChatMessagePage(
        items=[ChatMessageProfile.model_validate(message) for message in messages],
        has_more=has_more,
    )


async def send_message_to_family(
    session: AsyncSession,
    *,
    family_id: int,
    sender_id: int,
    payload: CreateChatMessageRequest,
) -> ChatMessage:
    message = await create_chat_message(
        session,
        family_id=family_id,
        sender_id=sender_id,
        content=payload.content,
    )
    message_id = message.id
    await session.commit()
    persisted = await get_chat_message(session, family_id=family_id, message_id=message_id)
    if persisted is None:
        raise AppException(
            code=ErrorCode.INTERNAL_ERROR,
            message="消息发送失败，请稍后重试",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return persisted


async def get_unread_count_for_user(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
) -> int:
    state = await get_chat_read_state(session, family_id=family_id, user_id=user_id)
    return await count_unread_chat_messages(
        session,
        family_id=family_id,
        user_id=user_id,
        last_read_message_id=state.last_read_message_id if state else None,
    )


async def mark_message_read_for_user(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
    message_id: int,
) -> int:
    message = await get_chat_message(session, family_id=family_id, message_id=message_id)
    if message is None:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message="消息不存在",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    state = await get_chat_read_state(session, family_id=family_id, user_id=user_id)
    try:
        if state is None:
            await create_chat_read_state(
                session,
                family_id=family_id,
                user_id=user_id,
                last_read_message_id=message_id,
            )
        else:
            await advance_chat_read_state(
                session,
                family_id=family_id,
                user_id=user_id,
                last_read_message_id=message_id,
            )
        await session.commit()
    except IntegrityError:
        # 两个页面首次同时标记已读时，保留数据库中更大的游标。
        await session.rollback()
        await advance_chat_read_state(
            session,
            family_id=family_id,
            user_id=user_id,
            last_read_message_id=message_id,
        )
        await session.commit()

    return await get_unread_count_for_user(
        session,
        family_id=family_id,
        user_id=user_id,
    )
