from pydantic import BaseModel, Field

from app.schemas.ai_chat import (
    AiActionDraft,
    AiRecommendationItem,
    AiRetrievalSource,
    AiToolCallTrace,
)


class AgentResult(BaseModel):
    summary: str
    recommendations: list[AiRecommendationItem] = Field(default_factory=list)
    recognized_ingredients: list[str] = Field(default_factory=list)
    retrieval_sources: list[AiRetrievalSource] = Field(default_factory=list)
    tool_calls: list[AiToolCallTrace] = Field(default_factory=list)
    action_draft: AiActionDraft | None = None
    confidence: float | None = None
    raw_model_output: str
