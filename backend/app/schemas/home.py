from pydantic import BaseModel, Field

from app.schemas.order import MealOrderProfile


class HomeSummaryProfile(BaseModel):
    pending_orders_count: int = 0
    pending_to_me_count: int = 0
    review_pending_count: int = 0
    monthly_accepted_orders_count: int = 0
    monthly_top_dish_name: str | None = None
    monthly_top_dish_count: int = 0
    today_order: MealOrderProfile | None = None
    recent_history: list[MealOrderProfile] = Field(default_factory=list)
