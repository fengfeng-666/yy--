from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Path, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.api.deps import DbSession, get_current_family, get_current_user
from app.models.family import Family
from app.models.user import User
from app.schemas.ai_chat import (
    AiChatConversationPage,
    AiChatMessagePage,
    AiChatTurnResponse,
    ConfirmAiActionResponse,
    CreateAiChatMessageRequest,
)
from app.schemas.common import ApiResponse, success_response
from app.services.ai_chat import (
    cancel_ai_action_for_user,
    confirm_ai_action_for_user,
    create_ai_turn,
    delete_ai_conversation_for_user,
    list_ai_conversations_for_user,
    list_ai_messages_for_user,
    stream_ai_turn,
)

router = APIRouter(prefix="/ai-chat", tags=["ai-chat"])


@router.get(
    "/conversations",
    response_model=ApiResponse[AiChatConversationPage],
    summary="AI 对话列表",
)
async def get_ai_chat_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
) -> ApiResponse[AiChatConversationPage]:
    page = await list_ai_conversations_for_user(
        session,
        family_id=current_family.id,
        user_id=current_user.id,
    )
    return success_response(data=page)


@router.get("/messages", response_model=ApiResponse[AiChatMessagePage], summary="AI 聊天历史")
async def get_ai_chat_messages(
    current_user: Annotated[User, Depends(get_current_user)],
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
    conversation_id: Annotated[int, Query(gt=0)],
    before_id: Annotated[int | None, Query(gt=0)] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 30,
) -> ApiResponse[AiChatMessagePage]:
    page = await list_ai_messages_for_user(
        session,
        family_id=current_family.id,
        user_id=current_user.id,
        conversation_id=conversation_id,
        limit=limit,
        before_id=before_id,
    )
    return success_response(data=page)


@router.delete(
    "/conversations/{conversation_id}",
    response_model=ApiResponse[None],
    summary="删除 AI 对话",
)
async def delete_ai_chat_conversation_item(
    current_user: Annotated[User, Depends(get_current_user)],
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
    conversation_id: Annotated[int, Path(gt=0)],
) -> ApiResponse[None]:
    await delete_ai_conversation_for_user(
        session,
        family_id=current_family.id,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    return success_response(message="AI 对话已删除")


@router.post(
    "/messages",
    response_model=ApiResponse[AiChatTurnResponse],
    summary="发送 AI 聊天消息",
)
async def create_ai_chat_message(
    current_user: Annotated[User, Depends(get_current_user)],
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
    content: Annotated[str, Form(...)],
    conversation_id: Annotated[int | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
) -> ApiResponse[AiChatTurnResponse]:
    payload = CreateAiChatMessageRequest(content=content, conversation_id=conversation_id)
    turn = await create_ai_turn(
        session,
        family_id=current_family.id,
        user_id=current_user.id,
        payload=payload,
        image=image,
    )
    return success_response(data=turn, message="AI 回复已生成")


@router.post(
    "/messages/stream",
    response_class=StreamingResponse,
    summary="流式发送 AI 聊天消息",
)
async def stream_ai_chat_message(
    current_user: Annotated[User, Depends(get_current_user)],
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
    content: Annotated[str, Form(...)],
    conversation_id: Annotated[int | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
) -> StreamingResponse:
    payload = CreateAiChatMessageRequest(content=content, conversation_id=conversation_id)
    return StreamingResponse(
        stream_ai_turn(
            session,
            family_id=current_family.id,
            user_id=current_user.id,
            payload=payload,
            image=image,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/actions/{message_id}/confirm",
    response_model=ApiResponse[ConfirmAiActionResponse],
    summary="确认 AI 动作",
)
async def confirm_ai_chat_action(
    current_user: Annotated[User, Depends(get_current_user)],
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
    message_id: Annotated[int, Path(gt=0)],
) -> ApiResponse[ConfirmAiActionResponse]:
    result = await confirm_ai_action_for_user(
        session,
        family_id=current_family.id,
        user_id=current_user.id,
        message_id=message_id,
    )
    return success_response(data=result, message="购物清单已生成")


@router.post(
    "/actions/{message_id}/cancel",
    response_model=ApiResponse[ConfirmAiActionResponse],
    summary="取消 AI 动作",
)
async def cancel_ai_chat_action(
    current_user: Annotated[User, Depends(get_current_user)],
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
    message_id: Annotated[int, Path(gt=0)],
) -> ApiResponse[ConfirmAiActionResponse]:
    result = await cancel_ai_action_for_user(
        session,
        family_id=current_family.id,
        user_id=current_user.id,
        message_id=message_id,
    )
    return success_response(data=result, message="AI 动作已取消")
