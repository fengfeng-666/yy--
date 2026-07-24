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


class IngredientProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    family_id: int
    name: str
    category: str | None
    default_unit: str | None


class DishIngredientProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dish_id: int
    ingredient_id: int
    quantity: float | None
    unit: str | None
    is_optional: bool
    note: str | None
    sort_order: int
    ingredient: IngredientProfile


class DishStepProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dish_id: int
    step_no: int
    content: str
    duration_minutes: int | None


class DishPreferenceProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dish_id: int
    user_id: int
    preference_note: str
    created_at: datetime
    updated_at: datetime


class DishProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    family_id: int
    name: str
    description: str | None
    price: float
    image_url: str | None
    cooking_minutes: int | None
    difficulty: int | None
    spicy_level: int | None
    need_prepare_ahead: bool
    suitable_for_weekday: bool
    is_available: bool
    ingredients: list[DishIngredientProfile] = Field(default_factory=list)
    steps: list[DishStepProfile] = Field(default_factory=list)
    preferences: list[DishPreferenceProfile] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ImageUploadResponse(BaseModel):
    path: str
    url: str
