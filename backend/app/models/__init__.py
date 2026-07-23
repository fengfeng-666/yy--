"""Import ORM models here so Alembic autogenerate can discover metadata."""

from app.models.ai_chat import AiChatConversation, AiChatMessage, FridgeImageAnalysis
from app.models.chat import ChatMessage, ChatReadState
from app.models.dish import Dish
from app.models.family import Family
from app.models.family_member import FamilyMember
from app.models.notification import WechatNotification, WechatSubscription
from app.models.order import MealOrder, MealOrderItem, MealReview, OrderStatusLog
from app.models.user import User

__all__ = [
    "AiChatMessage",
    "AiChatConversation",
    "ChatMessage",
    "ChatReadState",
    "Dish",
    "Family",
    "FamilyMember",
    "FridgeImageAnalysis",
    "MealOrder",
    "MealOrderItem",
    "MealReview",
    "OrderStatusLog",
    "User",
    "WechatNotification",
    "WechatSubscription",
]
