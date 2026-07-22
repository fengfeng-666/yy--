from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession, get_current_family, get_current_user
from app.models.family import Family
from app.models.user import User
from app.repositories.order import OrderRole
from app.schemas.common import ApiResponse, success_response
from app.schemas.order import CreateMealOrderRequest, CreateMealReviewRequest, MealOrderProfile
from app.services.order import (
    accept_order_for_family,
    create_order_for_family,
    list_dining_history_for_family,
    list_orders_for_family,
    review_order_for_family,
    require_meal_order,
)


router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=ApiResponse[list[MealOrderProfile]], summary="点菜列表")
async def get_orders(
    current_user: Annotated[User, Depends(get_current_user)],
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
    role: Annotated[OrderRole | None, Query()] = None,
    status_value: Annotated[str | None, Query(alias="status")] = None,
) -> ApiResponse[list[MealOrderProfile]]:
    orders = await list_orders_for_family(
        session,
        family_id=current_family.id,
        current_user_id=current_user.id,
        role=role,
        status_value=status_value,
    )
    return success_response(data=[MealOrderProfile.model_validate(item) for item in orders])


@router.post("", response_model=ApiResponse[MealOrderProfile], summary="创建点菜")
async def create_order(
    payload: CreateMealOrderRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
) -> ApiResponse[MealOrderProfile]:
    order = await create_order_for_family(
        session,
        family_id=current_family.id,
        current_user=current_user,
        payload=payload,
    )
    return success_response(data=MealOrderProfile.model_validate(order), message="点菜创建成功")


@router.get("/history", response_model=ApiResponse[list[MealOrderProfile]], summary="用餐历史")
async def get_dining_history(
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
) -> ApiResponse[list[MealOrderProfile]]:
    orders = await list_dining_history_for_family(session, family_id=current_family.id)
    return success_response(data=[MealOrderProfile.model_validate(item) for item in orders])


@router.get("/{order_id}", response_model=ApiResponse[MealOrderProfile], summary="点菜详情")
async def get_order_detail(
    order_id: int,
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
) -> ApiResponse[MealOrderProfile]:
    order = await require_meal_order(session, family_id=current_family.id, order_id=order_id)
    return success_response(data=MealOrderProfile.model_validate(order))


@router.post("/{order_id}/accept", response_model=ApiResponse[MealOrderProfile], summary="接受点菜")
async def accept_order(
    order_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
) -> ApiResponse[MealOrderProfile]:
    order = await accept_order_for_family(
        session,
        family_id=current_family.id,
        order_id=order_id,
        current_user=current_user,
    )
    return success_response(data=MealOrderProfile.model_validate(order), message="点菜已接受")


@router.post("/{order_id}/review", response_model=ApiResponse[MealOrderProfile], summary="评价用餐")
async def review_order(
    order_id: int,
    payload: CreateMealReviewRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
) -> ApiResponse[MealOrderProfile]:
    order = await review_order_for_family(
        session,
        family_id=current_family.id,
        order_id=order_id,
        current_user=current_user,
        payload=payload,
    )
    return success_response(data=MealOrderProfile.model_validate(order), message="评价已提交")
