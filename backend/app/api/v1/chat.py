from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession, get_current_family, get_current_user
from app.models.family import Family
from app.models.user import User
from app.schemas.chat import (
    ChatMessagePage,
    ChatMessageProfile,
    ChatUnreadCount,
    CreateChatMessageRequest,
    MarkChatReadRequest,
)
from app.schemas.common import ApiResponse, success_response
from app.services.chat import (
    get_unread_count_for_user,
    list_messages_for_family,
    mark_message_read_for_user,
    send_message_to_family,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/messages", response_model=ApiResponse[ChatMessagePage], summary="家庭消息列表")
async def get_chat_messages(
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
    before_id: Annotated[int | None, Query(gt=0)] = None,
    after_id: Annotated[int | None, Query(gt=0)] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 30,
) -> ApiResponse[ChatMessagePage]:
    page = await list_messages_for_family(
        session,
        family_id=current_family.id,
        limit=limit,
        before_id=before_id,
        after_id=after_id,
    )
    return success_response(data=page)


@router.post("/messages", response_model=ApiResponse[ChatMessageProfile], summary="发送家庭消息")
async def create_chat_message(
    payload: CreateChatMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
) -> ApiResponse[ChatMessageProfile]:
    message = await send_message_to_family(
        session,
        family_id=current_family.id,
        sender_id=current_user.id,
        payload=payload,
    )
    return success_response(
        data=ChatMessageProfile.model_validate(message),
        message="消息已发送",
    )


@router.get(
    "/unread-count",
    response_model=ApiResponse[ChatUnreadCount],
    summary="未读家庭消息数",
)
async def get_chat_unread_count(
    current_user: Annotated[User, Depends(get_current_user)],
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
) -> ApiResponse[ChatUnreadCount]:
    unread_count = await get_unread_count_for_user(
        session,
        family_id=current_family.id,
        user_id=current_user.id,
    )
    return success_response(data=ChatUnreadCount(unread_count=unread_count))


@router.post("/read", response_model=ApiResponse[ChatUnreadCount], summary="标记家庭消息已读")
async def mark_chat_read(
    payload: MarkChatReadRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
) -> ApiResponse[ChatUnreadCount]:
    unread_count = await mark_message_read_for_user(
        session,
        family_id=current_family.id,
        user_id=current_user.id,
        message_id=payload.last_read_message_id,
    )
    return success_response(data=ChatUnreadCount(unread_count=unread_count))
