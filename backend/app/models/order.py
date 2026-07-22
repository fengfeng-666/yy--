from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class MealOrderStatus:
    PENDING = "pending"
    ACCEPTED = "accepted"


class MealOrder(TimestampMixin, Base):
    __tablename__ = "meal_orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id", ondelete="CASCADE"), nullable=False)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    cook_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default=MealOrderStatus.PENDING)
    planned_date: Mapped[Date] = mapped_column(Date, nullable=False)
    planned_time: Mapped[Time | None] = mapped_column(Time, nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    accepted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    requester = relationship("User", foreign_keys=[requester_id])
    cook = relationship("User", foreign_keys=[cook_id])
    items: Mapped[list["MealOrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
    status_logs: Mapped[list["OrderStatusLog"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
    review: Mapped["MealReview | None"] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        uselist=False,
    )


class MealOrderItem(Base):
    __tablename__ = "meal_order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meal_order_id: Mapped[int] = mapped_column(
        ForeignKey("meal_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    order: Mapped[MealOrder] = relationship(back_populates="items")
    dish = relationship("Dish")


class OrderStatusLog(Base):
    __tablename__ = "order_status_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meal_order_id: Mapped[int] = mapped_column(
        ForeignKey("meal_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    operator_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    order: Mapped[MealOrder] = relationship(back_populates="status_logs")
    operator = relationship("User")


class MealReview(TimestampMixin, Base):
    __tablename__ = "meal_reviews"
    __table_args__ = (UniqueConstraint("meal_order_id", name="uq_meal_reviews_order"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meal_order_id: Mapped[int] = mapped_column(
        ForeignKey("meal_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str | None] = mapped_column(String(500), nullable=True)

    order: Mapped[MealOrder] = relationship(back_populates="review")
    reviewer = relationship("User")
