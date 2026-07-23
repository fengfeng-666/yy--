from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.family_member import FamilyMember


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    nickname: Mapped[str] = mapped_column(String(32), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    wechat_openid: Mapped[str | None] = mapped_column(
        String(128), unique=True, index=True, nullable=True
    )
    wechat_unionid: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    family_memberships: Mapped[list["FamilyMember"]] = relationship(back_populates="user")
