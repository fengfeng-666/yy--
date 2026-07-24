"""Import ORM models here so Alembic autogenerate can discover metadata."""

from app.models.ai_chat import AiChatConversation, AiChatMessage, FridgeImageAnalysis
from app.models.chat import ChatMessage, ChatReadState
from app.models.dish import Dish
from app.models.family import Family
from app.models.family_member import FamilyMember
from app.models.ingredient import DishIngredient, DishPreference, DishStep, Ingredient
from app.models.notification import WechatNotification, WechatSubscription
from app.models.order import MealOrder, MealOrderItem, MealReview, OrderStatusLog
from app.models.shopping_list import ShoppingList, ShoppingListItem
from app.models.user import User

__all__ = [
    "AiChatMessage",
    "AiChatConversation",
    "ChatMessage",
    "ChatReadState",
    "Dish",
    "DishIngredient",
    "DishPreference",
    "DishStep",
    "Family",
    "FamilyMember",
    "FridgeImageAnalysis",
    "Ingredient",
    "MealOrder",
    "MealOrderItem",
    "MealReview",
    "OrderStatusLog",
    "ShoppingList",
    "ShoppingListItem",
    "User",
    "WechatNotification",
    "WechatSubscription",
]
