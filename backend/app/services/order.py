from datetime import UTC, date, datetime

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ErrorCode
from app.core.exceptions import AppException
from app.models.order import MealOrder, MealOrderStatus
from app.models.user import User
from app.repositories.dish import get_dish_by_id
from app.repositories.family import get_family_member_by_user_id
from app.repositories.order import (
    OrderRole,
    add_meal_review,
    add_meal_order_item,
    add_order_status_log,
    create_meal_order,
    get_meal_order_by_id,
    list_dining_history,
    list_meal_orders,
)
from app.schemas.order import CreateMealOrderRequest, CreateMealReviewRequest


async def create_order_for_family(
    session: AsyncSession,
    *,
    family_id: int,
    current_user: User,
    payload: CreateMealOrderRequest,
) -> MealOrder:
    await ensure_valid_cook(session, family_id=family_id, requester_id=current_user.id, cook_id=payload.cook_id)
    await validate_order_items(session, family_id=family_id, payload=payload)

    order = await create_meal_order(
        session,
        family_id=family_id,
        requester_id=current_user.id,
        cook_id=payload.cook_id,
        planned_date=payload.planned_date,
        planned_time=payload.planned_time,
        note=payload.note,
        status=MealOrderStatus.PENDING,
    )
    for index, item in enumerate(payload.items):
        await add_meal_order_item(
            session,
            meal_order_id=order.id,
            dish_id=item.dish_id,
            quantity=item.quantity,
            note=item.note,
            sort_order=item.sort_order if item.sort_order else index,
        )
    await add_order_status_log(
        session,
        meal_order_id=order.id,
        from_status=None,
        to_status=MealOrderStatus.PENDING,
        operator_id=current_user.id,
        note="发起点菜",
    )
    await session.commit()
    return await require_meal_order(session, family_id=family_id, order_id=order.id)


async def list_orders_for_family(
    session: AsyncSession,
    *,
    family_id: int,
    current_user_id: int,
    role: OrderRole | None,
    status_value: str | None,
) -> list[MealOrder]:
    if status_value is not None:
        ensure_valid_status(status_value)
    return list(
        await list_meal_orders(
            session,
            family_id=family_id,
            current_user_id=current_user_id,
            role=role,
            status=status_value,
        )
    )


async def list_dining_history_for_family(
    session: AsyncSession,
    *,
    family_id: int,
) -> list[MealOrder]:
    return list(await list_dining_history(session, family_id=family_id))


async def accept_order_for_family(
    session: AsyncSession,
    *,
    family_id: int,
    order_id: int,
    current_user: User,
) -> MealOrder:
    order = await require_meal_order(session, family_id=family_id, order_id=order_id)
    if order.cook_id != current_user.id:
        raise AppException(
            code=ErrorCode.FORBIDDEN,
            message="只有被指定的厨师可以接受点菜",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    if order.status != MealOrderStatus.PENDING:
        raise AppException(
            code=ErrorCode.INVALID_STATUS,
            message="当前点菜状态不允许接受",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    order.status = MealOrderStatus.ACCEPTED
    order.accepted_at = datetime.now(UTC)
    await add_order_status_log(
        session,
        meal_order_id=order.id,
        from_status=MealOrderStatus.PENDING,
        to_status=MealOrderStatus.ACCEPTED,
        operator_id=current_user.id,
        note="接受点菜",
    )
    await session.commit()
    return await require_meal_order(session, family_id=family_id, order_id=order_id)


async def review_order_for_family(
    session: AsyncSession,
    *,
    family_id: int,
    order_id: int,
    current_user: User,
    payload: CreateMealReviewRequest,
) -> MealOrder:
    order = await require_meal_order(session, family_id=family_id, order_id=order_id)
    if order.requester_id != current_user.id:
        raise AppException(
            code=ErrorCode.FORBIDDEN,
            message="只有发起点菜的人可以评价",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    if order.status != MealOrderStatus.ACCEPTED:
        raise AppException(
            code=ErrorCode.INVALID_STATUS,
            message="只有已接受的点菜可以评价",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if order.planned_date > date.today():
        raise AppException(message="用餐日期未到，暂时不能评价")
    if order.review is not None:
        raise AppException(
            code=ErrorCode.DUPLICATE_REVIEW,
            message="这次用餐已经评价过了",
            status_code=status.HTTP_409_CONFLICT,
        )

    await add_meal_review(
        session,
        meal_order_id=order.id,
        reviewer_id=current_user.id,
        rating=payload.rating,
        content=payload.content,
    )
    await session.commit()
    return await require_meal_order(session, family_id=family_id, order_id=order_id)


async def require_meal_order(session: AsyncSession, *, family_id: int, order_id: int) -> MealOrder:
    order = await get_meal_order_by_id(session, family_id=family_id, order_id=order_id)
    if order is None:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message="点菜订单不存在",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return order


async def ensure_valid_cook(
    session: AsyncSession,
    *,
    family_id: int,
    requester_id: int,
    cook_id: int,
) -> None:
    if cook_id == requester_id:
        raise AppException(message="不能给自己发起点菜")

    membership = await get_family_member_by_user_id(session, cook_id)
    if membership is None or membership.family_id != family_id:
        raise AppException(
            code=ErrorCode.FORBIDDEN,
            message="指定厨师不属于当前家庭",
            status_code=status.HTTP_403_FORBIDDEN,
        )


async def validate_order_items(
    session: AsyncSession,
    *,
    family_id: int,
    payload: CreateMealOrderRequest,
) -> None:
    seen_dish_ids: set[int] = set()
    for item in payload.items:
        if item.dish_id in seen_dish_ids:
            raise AppException(message="同一个菜品不能重复添加")
        seen_dish_ids.add(item.dish_id)

        dish = await get_dish_by_id(session, family_id=family_id, dish_id=item.dish_id)
        if dish is None:
            raise AppException(
                code=ErrorCode.NOT_FOUND,
                message="菜品不存在",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if not dish.is_available:
            raise AppException(message=f"菜品「{dish.name}」当前不可点")


def ensure_valid_status(status_value: str) -> None:
    allowed_statuses = {MealOrderStatus.PENDING, MealOrderStatus.ACCEPTED}
    if status_value not in allowed_statuses:
        raise AppException(
            code=ErrorCode.INVALID_STATUS,
            message="无效的点菜状态",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
