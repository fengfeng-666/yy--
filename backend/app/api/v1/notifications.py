from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse, success_response
from app.schemas.notification import GrantSubscriptionsRequest, SubscriptionProfile
from app.services.notification import grant_subscriptions

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post(
    "/subscriptions/grant",
    response_model=ApiResponse[list[SubscriptionProfile]],
    summary="记录微信订阅消息授权",
)
async def grant_notification_subscriptions(
    payload: GrantSubscriptionsRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: DbSession,
) -> ApiResponse[list[SubscriptionProfile]]:
    subscriptions = await grant_subscriptions(
        session,
        user_id=current_user.id,
        event_types=payload.event_types,
    )
    return success_response(data=subscriptions, message="消息提醒已开启")
