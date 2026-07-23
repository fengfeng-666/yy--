from collections.abc import Sequence

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import ChatMessage, ChatReadState


async def list_chat_messages(
    session: AsyncSession,
    *,
    family_id: int,
    limit: int,
    before_id: int | None = None,
    after_id: int | None = None,
) -> tuple[Sequence[ChatMessage], bool]:
    statement = (
        select(ChatMessage)
        .options(selectinload(ChatMessage.sender))
        .where(ChatMessage.family_id == family_id)
    )

    if before_id is not None:
        statement = statement.where(ChatMessage.id < before_id)
    elif after_id is not None:
        statement = statement.where(ChatMessage.id > after_id)

    descending = after_id is None
    order = ChatMessage.id.desc() if descending else ChatMessage.id.asc()
    result = await session.execute(statement.order_by(order).limit(limit + 1))
    messages = list(result.scalars().all())
    has_more = len(messages) > limit
    messages = messages[:limit]
    if descending:
        messages.reverse()
    return messages, has_more


async def get_chat_message(
    session: AsyncSession,
    *,
    family_id: int,
    message_id: int,
) -> ChatMessage | None:
    result = await session.execute(
        select(ChatMessage)
        .options(selectinload(ChatMessage.sender))
        .where(ChatMessage.family_id == family_id, ChatMessage.id == message_id)
    )
    return result.scalar_one_or_none()


async def create_chat_message(
    session: AsyncSession,
    *,
    family_id: int,
    sender_id: int,
    content: str,
) -> ChatMessage:
    message = ChatMessage(family_id=family_id, sender_id=sender_id, content=content)
    session.add(message)
    await session.flush()
    return message


async def get_chat_read_state(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
) -> ChatReadState | None:
    result = await session.execute(
        select(ChatReadState).where(
            ChatReadState.family_id == family_id,
            ChatReadState.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def create_chat_read_state(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
    last_read_message_id: int,
) -> ChatReadState:
    state = ChatReadState(
        family_id=family_id,
        user_id=user_id,
        last_read_message_id=last_read_message_id,
    )
    session.add(state)
    await session.flush()
    return state


async def advance_chat_read_state(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
    last_read_message_id: int,
) -> None:
    await session.execute(
        update(ChatReadState)
        .where(
            ChatReadState.family_id == family_id,
            ChatReadState.user_id == user_id,
            or_(
                ChatReadState.last_read_message_id.is_(None),
                ChatReadState.last_read_message_id < last_read_message_id,
            ),
        )
        .values(last_read_message_id=last_read_message_id)
    )


async def count_unread_chat_messages(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
    last_read_message_id: int | None,
) -> int:
    statement = select(func.count(ChatMessage.id)).where(
        ChatMessage.family_id == family_id,
        ChatMessage.sender_id != user_id,
    )
    if last_read_message_id is not None:
        statement = statement.where(ChatMessage.id > last_read_message_id)
    result = await session.execute(statement)
    return int(result.scalar_one())
