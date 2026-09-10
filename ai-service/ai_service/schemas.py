from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=20000)


class RecommendationRequest(BaseModel):
    request_id: str = Field(min_length=1, max_length=128)
    content: str = Field(min_length=1, max_length=2000)
    dishes: list[dict[str, Any]] = Field(default_factory=list, max_length=2000)
    preferences: list[dict[str, Any]] = Field(default_factory=list, max_length=2000)
    dining_history: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    history: list[HistoryMessage] = Field(default_factory=list, max_length=12)
    image_data_url: str | None = Field(default=None, max_length=14000000)

    @field_validator("image_data_url")
    @classmethod
    def local_image_only(cls, value: str | None) -> str | None:
        if value is not None:
            import base64
            if not value.startswith(("data:image/jpeg;base64,", "data:image/png;base64,", "data:image/webp;base64,")):
                raise ValueError("Only inline JPEG, PNG or WebP images are supported")
            if not base64.b64decode(value.split(",", 1)[1], validate=True):
                raise ValueError("Empty image")
        return value


class Recommendation(BaseModel):
    dish_name: str = Field(min_length=1, max_length=100)
    rating: int = Field(ge=1, le=5)
    required_ingredients: list[str] = Field(default_factory=list)
    matched_ingredients: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    reason: str = ""

    @field_validator("required_ingredients")
    @classmethod
    def brief(cls, value: list[str]) -> list[str]:
        return value[:6]

    @field_validator("steps")
    @classmethod
    def no_steps(cls, value: list[str]) -> list[str]:
        return []


class RecommendationResult(BaseModel):
    summary: str = Field(min_length=1)
    recognized_ingredients: list[str] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list, max_length=20)
