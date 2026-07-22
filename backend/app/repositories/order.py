from collections.abc import Sequence
from typing import Literal

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import MealOrder, MealOrderItem, MealReview, OrderStatusLog


OrderRole = Literal["my_requested", "to_me"]


async def get_meal_order_by_id(
    session: AsyncSession,
    *,
    family_id: int,
    order_id: int,
) -> MealOrder | None:
    result = await session.execute(
        select(MealOrder)
        .execution_options(populate_existing=True)
        .options(
            selectinload(MealOrder.requester),
            selectinload(MealOrder.cook),
            selectinload(MealOrder.items).selectinload(MealOrderItem.dish),
            selectinload(MealOrder.status_logs).selectinload(OrderStatusLog.operator),
            selectinload(MealOrder.review).selectinload(MealReview.reviewer),
        )
        .where(MealOrder.family_id == family_id, MealOrder.id == order_id)
    )
    return result.scalar_one_or_none()


async def list_meal_orders(
    session: AsyncSession,
    *,
    family_id: int,
    current_user_id: int,
    role: OrderRole | None = None,
    status: str | None = None,
) -> Sequence[MealOrder]:
    statement: Select[tuple[MealOrder]] = (
        select(MealOrder)
        .execution_options(populate_existing=True)
        .options(
            selectinload(MealOrder.requester),
            selectinload(MealOrder.cook),
            selectinload(MealOrder.items).selectinload(MealOrderItem.dish),
            selectinload(MealOrder.status_logs).selectinload(OrderStatusLog.operator),
            selectinload(MealOrder.review).selectinload(MealReview.reviewer),
        )
        .where(MealOrder.family_id == family_id)
        .order_by(MealOrder.created_at.desc(), MealOrder.id.desc())
    )
    if role == "my_requested":
        statement = statement.where(MealOrder.requester_id == current_user_id)
    elif role == "to_me":
        statement = statement.where(MealOrder.cook_id == current_user_id)

    if status is not None:
        statement = statement.where(MealOrder.status == status)

    result = await session.execute(statement)
    return result.scalars().all()


async def create_meal_order(
    session: AsyncSession,
    *,
    family_id: int,
    requester_id: int,
    cook_id: int,
    planned_date,
    planned_time,
    note: str | None,
    status: str,
) -> MealOrder:
    order = MealOrder(
        family_id=family_id,
        requester_id=requester_id,
        cook_id=cook_id,
        planned_date=planned_date,
        planned_time=planned_time,
        note=note,
        status=status,
    )
    session.add(order)
    await session.flush()
    return order


async def add_meal_order_item(
    session: AsyncSession,
    *,
    meal_order_id: int,
    dish_id: int,
    quantity: int,
    note: str | None,
    sort_order: int,
) -> MealOrderItem:
    item = MealOrderItem(
        meal_order_id=meal_order_id,
        dish_id=dish_id,
        quantity=quantity,
        note=note,
        sort_order=sort_order,
    )
    session.add(item)
    await session.flush()
    return item


async def add_order_status_log(
    session: AsyncSession,
    *,
    meal_order_id: int,
    from_status: str | None,
    to_status: str,
    operator_id: int,
    note: str | None = None,
) -> OrderStatusLog:
    log = OrderStatusLog(
        meal_order_id=meal_order_id,
        from_status=from_status,
        to_status=to_status,
        operator_id=operator_id,
        note=note,
    )
    session.add(log)
    await session.flush()
    return log


async def add_meal_review(
    session: AsyncSession,
    *,
    meal_order_id: int,
    reviewer_id: int,
    rating: int,
    content: str | None,
) -> MealReview:
    review = MealReview(
        meal_order_id=meal_order_id,
        reviewer_id=reviewer_id,
        rating=rating,
        content=content,
    )
    session.add(review)
    await session.flush()
    return review


async def list_dining_history(
    session: AsyncSession,
    *,
    family_id: int,
) -> Sequence[MealOrder]:
    result = await session.execute(
        select(MealOrder)
        .execution_options(populate_existing=True)
        .options(
            selectinload(MealOrder.requester),
            selectinload(MealOrder.cook),
            selectinload(MealOrder.items).selectinload(MealOrderItem.dish),
            selectinload(MealOrder.status_logs).selectinload(OrderStatusLog.operator),
            selectinload(MealOrder.review).selectinload(MealReview.reviewer),
        )
        .where(MealOrder.family_id == family_id, MealOrder.status == "accepted")
        .order_by(MealOrder.planned_date.desc(), MealOrder.accepted_at.desc(), MealOrder.id.desc())
    )
    return result.scalars().all()
