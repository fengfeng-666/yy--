from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, get_current_family
from app.models.family import Family
from app.schemas.common import ApiResponse, success_response
from app.schemas.shopping_list import CreateShoppingListRequest, ShoppingListProfile
from app.services.shopping_list import (
    create_manual_shopping_list,
    list_shopping_lists_for_family,
)

router = APIRouter(prefix="/shopping-lists", tags=["shopping-lists"])


@router.get("", response_model=ApiResponse[list[ShoppingListProfile]], summary="购物清单列表")
async def get_shopping_lists(
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
) -> ApiResponse[list[ShoppingListProfile]]:
    shopping_lists = await list_shopping_lists_for_family(session, family_id=current_family.id)
    return success_response(data=[ShoppingListProfile.model_validate(item) for item in shopping_lists])


@router.post("", response_model=ApiResponse[ShoppingListProfile], summary="创建购物清单")
async def create_shopping_list_item(
    payload: CreateShoppingListRequest,
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
) -> ApiResponse[ShoppingListProfile]:
    shopping_list = await create_manual_shopping_list(
        session,
        family_id=current_family.id,
        payload=payload,
    )
    return success_response(data=ShoppingListProfile.model_validate(shopping_list), message="购物清单创建成功")
