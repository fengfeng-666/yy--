from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class NotificationEventType:
    NEW_ORDER = "new_order"
    ORDER_ACCEPTED = "order_accepted"
    ALL = {NEW_ORDER, ORDER_ACCEPTED}


class NotificationStatus:
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class WechatSubscription(TimestampMixin, Base):
    __tablename__ = "wechat_subscriptions"
    __table_args__ = (
        UniqueConstraint("user_id", "event_type", name="uq_wechat_subscriptions_user_event"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    available_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user = relationship("User")


class WechatNotification(TimestampMixin, Base):
    __tablename__ = "wechat_notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    meal_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("meal_orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    template_id: Mapped[str] = mapped_column(String(128), nullable=False)
    page: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=NotificationStatus.PENDING, index=True
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    recipient = relationship("User")
    order = relationship("MealOrder")
