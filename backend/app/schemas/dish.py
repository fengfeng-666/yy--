from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DishCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: float = Field(ge=0, le=99999)
    image_url: str | None = Field(default=None, max_length=500)
    is_available: bool = True

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("菜品名称不能为空")
        return normalized

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("image_url")
    @classmethod
    def normalize_image_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class DishUpdateRequest(DishCreateRequest):
    pass


class DishProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    family_id: int
    name: str
    description: str | None
    price: float
    image_url: str | None
    is_available: bool
    created_at: datetime
    updated_at: datetime


class ImageUploadResponse(BaseModel):
    path: str
    url: str
