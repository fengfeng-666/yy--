from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ErrorCode
from app.core.exceptions import AppException
from app.models.shopping_list import ShoppingList, ShoppingListSourceType
from app.schemas.ai_chat import AiActionDraft
from app.repositories.shopping_list import (
    add_shopping_list_item,
    create_shopping_list,
    get_shopping_list_by_id,
    list_shopping_lists,
)
from app.schemas.shopping_list import CreateShoppingListRequest


async def list_shopping_lists_for_family(
    session: AsyncSession,
    *,
    family_id: int,
) -> list[ShoppingList]:
    return list(await list_shopping_lists(session, family_id=family_id))


async def create_manual_shopping_list(
    session: AsyncSession,
    *,
    family_id: int,
    payload: CreateShoppingListRequest,
) -> ShoppingList:
    shopping_list = await create_shopping_list(
        session,
        family_id=family_id,
        name=payload.name,
        source_type=ShoppingListSourceType.MANUAL,
        source_reference=None,
    )
    for item in payload.items:
        await add_shopping_list_item(
            session,
            shopping_list_id=shopping_list.id,
            name=item.name,
            quantity=item.quantity,
            unit=item.unit,
            note=item.note,
            source_dish_name=item.source_dish_name,
            ingredient_id=None,
            sort_order=item.sort_order,
        )
    await session.commit()
    return await require_shopping_list(session, family_id=family_id, shopping_list_id=shopping_list.id)


async def create_ai_agent_shopping_list(
    session: AsyncSession,
    *,
    family_id: int,
    action_draft: AiActionDraft,
    source_reference: str,
) -> ShoppingList:
    shopping_list = await create_shopping_list(
        session,
        family_id=family_id,
        name=action_draft.title,
        source_type=ShoppingListSourceType.AI_AGENT,
        source_reference=source_reference,
    )
    for index, item in enumerate(action_draft.items):
        await add_shopping_list_item(
            session,
            shopping_list_id=shopping_list.id,
            name=item.name,
            quantity=item.quantity,
            unit=item.unit,
            note=item.note,
            source_dish_name=item.source_dish_name,
            ingredient_id=None,
            sort_order=index,
        )
    await session.flush()
    return shopping_list


async def require_shopping_list(
    session: AsyncSession,
    *,
    family_id: int,
    shopping_list_id: int,
) -> ShoppingList:
    shopping_list = await get_shopping_list_by_id(
        session,
        family_id=family_id,
        shopping_list_id=shopping_list_id,
    )
    if shopping_list is None:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message="购物清单不存在",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return shopping_list
