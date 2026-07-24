from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DishIngredientInput(BaseModel):
    ingredient_name: str = Field(min_length=1, max_length=100)
    quantity: float | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=20)
    is_optional: bool = False
    note: str | None = Field(default=None, max_length=255)
    category: str | None = Field(default=None, max_length=50)
    sort_order: int = Field(default=0, ge=0, le=999)

    @field_validator("ingredient_name", mode="before")
    @classmethod
    def normalize_ingredient_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("unit", "note", "category", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value


class DishStepInput(BaseModel):
    step_no: int = Field(ge=1, le=99)
    content: str = Field(min_length=1, max_length=2000)
    duration_minutes: int | None = Field(default=None, ge=0, le=1440)

    @field_validator("content", mode="before")
    @classmethod
    def normalize_content(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class DishPreferenceInput(BaseModel):
    user_id: int = Field(gt=0)
    preference_note: str = Field(min_length=1, max_length=2000)

    @field_validator("preference_note", mode="before")
    @classmethod
    def normalize_preference_note(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class DishCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: float = Field(ge=0, le=99999)
    image_url: str | None = Field(default=None, max_length=500)
    cooking_minutes: int | None = Field(default=None, ge=0, le=1440)
    difficulty: int | None = Field(default=None, ge=1, le=5)
    spicy_level: int | None = Field(default=None, ge=0, le=5)
    need_prepare_ahead: bool = False
    suitable_for_weekday: bool = False
    is_available: bool = True
    ingredients: list[DishIngredientInput] = Field(default_factory=list, max_length=50)
    steps: list[DishStepInput] = Field(default_factory=list, max_length=50)
    preferences: list[DishPreferenceInput] = Field(default_factory=list, max_length=10)

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
