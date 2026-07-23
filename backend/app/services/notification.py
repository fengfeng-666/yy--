import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.models.notification import (
    NotificationEventType,
    NotificationStatus,
    WechatNotification,
    WechatSubscription,
)
from app.models.order import MealOrder
from app.models.user import User
from app.schemas.notification import NotificationEventType as NotificationEventTypeSchema
from app.schemas.notification import SubscriptionProfile
from app.services.wechat import get_wechat_client

logger = logging.getLogger(__name__)


async def grant_subscriptions(
    session: AsyncSession,
    *,
    user_id: int,
    event_types: list[NotificationEventTypeSchema],
) -> list[SubscriptionProfile]:
    profiles: list[SubscriptionProfile] = []
    for event_type in dict.fromkeys(event_types):
        result = await session.execute(
            select(WechatSubscription)
            .where(
                WechatSubscription.user_id == user_id,
                WechatSubscription.event_type == event_type,
            )
            .with_for_update()
        )
        subscription = result.scalar_one_or_none()
        if subscription is None:
            subscription = WechatSubscription(
                user_id=user_id,
                event_type=event_type,
                available_count=1,
            )
            session.add(subscription)
        else:
            subscription.available_count += 1
        profiles.append(
            SubscriptionProfile(
                event_type=event_type,
                available_count=subscription.available_count,
            )
        )
    await session.commit()
    return profiles


async def enqueue_order_notification(
    session: AsyncSession,
    *,
    order: MealOrder,
    event_type: str,
) -> int | None:
    settings = get_settings()
    template_ids = {
        NotificationEventType.NEW_ORDER: settings.wechat_template_new_order,
        NotificationEventType.ORDER_ACCEPTED: settings.wechat_template_order_accepted,
    }
    template_id = template_ids.get(event_type, "")
    if not template_id:
        return None

    recipient: User
    actor: User
    if event_type == NotificationEventType.NEW_ORDER:
        recipient = order.cook
        actor = order.requester
    elif event_type == NotificationEventType.ORDER_ACCEPTED:
        recipient = order.requester
        actor = order.cook
    else:
        raise ValueError(f"Unsupported notification event type: {event_type}")

    if not recipient.wechat_openid:
        return None

    result = await session.execute(
        select(WechatSubscription)
        .where(
            WechatSubscription.user_id == recipient.id,
            WechatSubscription.event_type == event_type,
            WechatSubscription.available_count > 0,
        )
        .with_for_update()
    )
    subscription = result.scalar_one_or_none()
    if subscription is None:
        return None

    dishes = "、".join(item.dish.name for item in order.items)
    planned_at = order.planned_date.strftime("%Y-%m-%d")
    if order.planned_time:
        planned_at += f" {order.planned_time.strftime('%H:%M')}"
    payload = {
        "thing1": {"value": dishes[:20]},
        "thing2": {"value": actor.nickname[:20]},
        "time3": {"value": planned_at},
    }
    notification = WechatNotification(
        recipient_id=recipient.id,
        meal_order_id=order.id,
        event_type=event_type,
        template_id=template_id,
        page="pages/orders/index",
        payload=payload,
        status=NotificationStatus.PENDING,
    )
    subscription.available_count -= 1
    session.add(notification)
    await session.commit()
    await session.refresh(notification)
    return notification.id


async def dispatch_notification(notification_id: int) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(WechatNotification)
            .options(selectinload(WechatNotification.recipient))
            .where(WechatNotification.id == notification_id)
        )
        notification = result.scalar_one_or_none()
        if notification is None or notification.status != NotificationStatus.PENDING:
            return

        notification.attempt_count += 1
        try:
            await get_wechat_client().send_subscribe_message(
                openid=notification.recipient.wechat_openid,
                template_id=notification.template_id,
                page=notification.page,
                data=notification.payload,
            )
        except Exception as exc:
            notification.status = NotificationStatus.FAILED
            notification.error_message = str(exc)[:500]
            logger.exception("Failed to send WeChat notification %s", notification_id)
        else:
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.now(UTC)
            notification.error_message = None
        await session.commit()
