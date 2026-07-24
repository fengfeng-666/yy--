from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreateAiChatMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    conversation_id: int | None = Field(default=None, gt=0)

    @field_validator("content", mode="before")
    @classmethod
    def normalize_content(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class AiChatConversationProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    family_id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime


class AiChatConversationListItem(AiChatConversationProfile):
    last_message_preview: str | None = None
    last_message_at: datetime | None = None


class AiChatConversationPage(BaseModel):
    items: list[AiChatConversationListItem] = Field(default_factory=list)


class AiRecommendationItem(BaseModel):
    dish_name: str = Field(min_length=1, max_length=100)
    rating: int = Field(ge=1, le=5)
    required_ingredients: list[str] = Field(default_factory=list)
    matched_ingredients: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    reason: str = Field(default="")

    @field_validator("required_ingredients", mode="before")
    @classmethod
    def keep_ingredients_brief(cls, value: object) -> object:
        if isinstance(value, list):
            return value[:6]
        return value

    @field_validator("steps", mode="before")
    @classmethod
    def omit_steps(cls, _value: object) -> list[str]:
        return []


class FridgeImageAnalysisProfile(BaseModel):
    image_url: str
    recognized_ingredients: list[str] = Field(default_factory=list)


class AiRetrievalSource(BaseModel):
    source_type: str
    title: str
    snippet: str
    source_id: str | None = None
    score: float | None = None


class AiToolCallTrace(BaseModel):
    tool_name: str
    status: str
    summary: str


class AiActionDraftItem(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    quantity: float | None = None
    unit: str | None = None
    note: str | None = None
    source_dish_name: str | None = None


class AiActionDraft(BaseModel):
    action_type: str
    title: str
    summary: str | None = None
    status: str = "pending"
    items: list[AiActionDraftItem] = Field(default_factory=list)
    shopping_list_id: int | None = None


class AiChatMetadata(BaseModel):
    summary: str | None = None
    recognized_ingredients: list[str] = Field(default_factory=list)
    recommendations: list[AiRecommendationItem] = Field(default_factory=list)
    fridge_image: FridgeImageAnalysisProfile | None = None
    retrieval_sources: list[AiRetrievalSource] = Field(default_factory=list)
    tool_calls: list[AiToolCallTrace] = Field(default_factory=list)
    action_draft: AiActionDraft | None = None
    confirmation_required: bool = False
    confidence: float | None = None
    raw_model_output: str | None = None


class AiChatMessageProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    family_id: int
    user_id: int
    conversation_id: int
    role: str
    content: str
    message_kind: str
    metadata_json: AiChatMetadata | None = Field(default=None, alias="metadata_json")
    created_at: datetime


class AiChatMessagePage(BaseModel):
    items: list[AiChatMessageProfile] = Field(default_factory=list)
    has_more: bool = False


class AiChatTurnResponse(BaseModel):
    conversation: AiChatConversationListItem
    user_message: AiChatMessageProfile
    assistant_message: AiChatMessageProfile


class ParsedAiRecommendation(BaseModel):
    summary: str
    recognized_ingredients: list[str] = Field(default_factory=list)
    recommendations: list[AiRecommendationItem] = Field(default_factory=list)
    raw_model_output: str


class ConfirmAiActionResponse(BaseModel):
    message: AiChatMessageProfile


class OpenAiCompatibleMessagePart(BaseModel):
    type: str
    text: str | None = None
    image_url: dict[str, Any] | None = None
