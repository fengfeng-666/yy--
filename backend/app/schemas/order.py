from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.auth import UserProfile


class CreateMealOrderItemRequest(BaseModel):
    dish_id: int = Field(gt=0)
    quantity: int = Field(default=1, ge=1, le=20)
    note: str | None = Field(default=None, max_length=255)
    sort_order: int = Field(default=0, ge=0, le=999)

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class CreateMealOrderRequest(BaseModel):
    cook_id: int = Field(gt=0)
    planned_date: date
    planned_time: time | None = None
    note: str | None = Field(default=None, max_length=500)
    items: list[CreateMealOrderItemRequest] = Field(min_length=1, max_length=20)

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class DishBriefProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    image_url: str | None


class MealOrderItemProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    meal_order_id: int
    dish_id: int
    quantity: int
    note: str | None
    sort_order: int
    dish: DishBriefProfile


class OrderStatusLogProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    meal_order_id: int
    from_status: str | None
    to_status: str
    operator_id: int
    note: str | None
    created_at: datetime
    operator: UserProfile


class MealOrderProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    family_id: int
    requester_id: int
    cook_id: int
    status: str
    planned_date: date
    planned_time: time | None
    note: str | None
    accepted_at: datetime | None
    created_at: datetime
    updated_at: datetime
    requester: UserProfile
    cook: UserProfile
    items: list[MealOrderItemProfile] = Field(default_factory=list)
    status_logs: list[OrderStatusLogProfile] = Field(default_factory=list)
