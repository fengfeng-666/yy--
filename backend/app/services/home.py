from collections import Counter
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import MealOrder, MealOrderStatus
from app.models.user import User
from app.repositories.order import list_dining_history, list_meal_orders
from app.schemas.home import HomeSummaryProfile
from app.schemas.order import MealOrderProfile


async def get_home_summary(
    session: AsyncSession,
    *,
    family_id: int,
    current_user: User,
) -> HomeSummaryProfile:
    today = date.today()
    all_orders = list(
        await list_meal_orders(
            session,
            family_id=family_id,
            current_user_id=current_user.id,
        )
    )
    history_orders = list(await list_dining_history(session, family_id=family_id))

    pending_orders = [order for order in all_orders if order.status == MealOrderStatus.PENDING]
    pending_to_me_count = sum(1 for order in pending_orders if order.cook_id == current_user.id)
    review_pending_count = sum(
        1
        for order in history_orders
        if order.requester_id == current_user.id and order.review is None and order.planned_date <= today
    )

    monthly_history = [
        order
        for order in history_orders
        if order.planned_date.year == today.year and order.planned_date.month == today.month
    ]
    top_dish_name, top_dish_count = summarize_top_dish(monthly_history)

    today_order = select_today_order(all_orders, today)
    recent_history = [MealOrderProfile.model_validate(order) for order in history_orders[:3]]

    return HomeSummaryProfile(
        pending_orders_count=len(pending_orders),
        pending_to_me_count=pending_to_me_count,
        review_pending_count=review_pending_count,
        monthly_accepted_orders_count=len(monthly_history),
        monthly_top_dish_name=top_dish_name,
        monthly_top_dish_count=top_dish_count,
        today_order=MealOrderProfile.model_validate(today_order) if today_order is not None else None,
        recent_history=recent_history,
    )


def summarize_top_dish(orders: list[MealOrder]) -> tuple[str | None, int]:
    dish_counter: Counter[str] = Counter()
    for order in orders:
        for item in order.items:
            dish_counter[item.dish.name] += item.quantity
    if not dish_counter:
        return None, 0
    return dish_counter.most_common(1)[0]


def select_today_order(orders: list[MealOrder], today: date) -> MealOrder | None:
    today_orders = [order for order in orders if order.planned_date == today]
    if not today_orders:
        return None
    today_orders.sort(
        key=lambda order: (
            0 if order.status == MealOrderStatus.PENDING else 1,
            order.planned_time is None,
            order.planned_time,
            order.created_at,
        )
    )
    return today_orders[0]
