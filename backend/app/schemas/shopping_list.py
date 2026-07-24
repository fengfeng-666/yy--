from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ShoppingListItemInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    quantity: float | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=20)
    note: str | None = Field(default=None, max_length=500)
    source_dish_name: str | None = Field(default=None, max_length=100)
    sort_order: int = Field(default=0, ge=0, le=999)

    @field_validator("name", "unit", "note", "source_dish_name", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value


class CreateShoppingListRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    items: list[ShoppingListItemInput] = Field(min_length=1, max_length=100)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class ShoppingListItemProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shopping_list_id: int
    ingredient_id: int | None
    name: str
    quantity: float | None
    unit: str | None
    note: str | None
    source_dish_name: str | None
    is_purchased: bool
    sort_order: int


class ShoppingListProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    family_id: int
    name: str
    status: str
    source_type: str
    source_reference: str | None
    created_at: datetime
    updated_at: datetime
    items: list[ShoppingListItemProfile] = Field(default_factory=list)
