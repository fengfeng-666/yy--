from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Dish(TimestampMixin, Base):
    __tablename__ = "dishes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cooking_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    spicy_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    need_prepare_ahead: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    suitable_for_weekday: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    ingredients = relationship(
        "DishIngredient",
        back_populates="dish",
        cascade="all, delete-orphan",
        order_by="DishIngredient.sort_order",
    )
    steps = relationship(
        "DishStep",
        back_populates="dish",
        cascade="all, delete-orphan",
        order_by="DishStep.step_no",
    )
    preferences = relationship(
        "DishPreference",
        back_populates="dish",
        cascade="all, delete-orphan",
        order_by="DishPreference.id",
    )
