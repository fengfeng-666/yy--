from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.auth import UserProfile


class CreateChatMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=1000)

    @field_validator("content", mode="before")
    @classmethod
    def normalize_content(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class MarkChatReadRequest(BaseModel):
    last_read_message_id: int = Field(gt=0)


class ChatMessageProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    family_id: int
    sender_id: int
    content: str
    created_at: datetime
    sender: UserProfile


class ChatMessagePage(BaseModel):
    items: list[ChatMessageProfile] = Field(default_factory=list)
    has_more: bool = False


class ChatUnreadCount(BaseModel):
    unread_count: int = 0
