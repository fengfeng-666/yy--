"""Import ORM models here so Alembic autogenerate can discover metadata."""

from app.models.chat import ChatMessage, ChatReadState
from app.models.dish import Dish
from app.models.family import Family
from app.models.family_member import FamilyMember
from app.models.notification import WechatNotification, WechatSubscription
from app.models.order import MealOrder, MealOrderItem, MealReview, OrderStatusLog
from app.models.user import User

__all__ = [
    "ChatMessage",
    "ChatReadState",
    "Dish",
    "Family",
    "FamilyMember",
    "MealOrder",
    "MealOrderItem",
    "MealReview",
    "OrderStatusLog",
    "User",
    "WechatNotification",
    "WechatSubscription",
]
