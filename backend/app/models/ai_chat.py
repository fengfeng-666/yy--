from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class AiChatRole:
    USER = "user"
    ASSISTANT = "assistant"


class AiChatMessageKind:
    TEXT = "text"
    FRIDGE_IMAGE = "fridge_image"
    RECOMMENDATION = "recommendation"


class AiChatConversation(TimestampMixin, Base):
    __tablename__ = "ai_chat_conversations"
    __table_args__ = (
        Index("ix_ai_chat_conversations_family_user_updated_at", "family_id", "user_id", "updated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    family_id: Mapped[int] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False, default="新对话")

    family = relationship("Family")
    user = relationship("User")


class AiChatMessage(Base):
    __tablename__ = "ai_chat_messages"
    __table_args__ = (
        Index(
            "ix_ai_chat_messages_family_user_conversation_id",
            "family_id",
            "user_id",
            "conversation_id",
            "id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    family_id: Mapped[int] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("ai_chat_conversations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_kind: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=AiChatMessageKind.TEXT,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    family = relationship("Family")
    user = relationship("User")
    conversation = relationship("AiChatConversation")


class FridgeImageAnalysis(Base):
    __tablename__ = "fridge_image_analyses"
    __table_args__ = (
        Index(
            "ix_fridge_image_analyses_family_user_id",
            "family_id",
            "user_id",
            "id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    family_id: Mapped[int] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    recognized_ingredients_json: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    raw_model_output: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    family = relationship("Family")
    user = relationship("User")
