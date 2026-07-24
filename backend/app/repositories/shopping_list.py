from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.shopping_list import ShoppingList, ShoppingListItem


async def get_shopping_list_by_id(
    session: AsyncSession,
    *,
    family_id: int,
    shopping_list_id: int,
) -> ShoppingList | None:
    result = await session.execute(
        select(ShoppingList)
        .execution_options(populate_existing=True)
        .options(selectinload(ShoppingList.items))
        .where(ShoppingList.family_id == family_id, ShoppingList.id == shopping_list_id)
    )
    return result.scalar_one_or_none()


async def list_shopping_lists(
    session: AsyncSession,
    *,
    family_id: int,
) -> Sequence[ShoppingList]:
    statement: Select[tuple[ShoppingList]] = (
        select(ShoppingList)
        .execution_options(populate_existing=True)
        .options(selectinload(ShoppingList.items))
        .where(ShoppingList.family_id == family_id)
        .order_by(ShoppingList.updated_at.desc(), ShoppingList.id.desc())
    )
    result = await session.execute(statement)
    return result.scalars().all()


async def create_shopping_list(
    session: AsyncSession,
    *,
    family_id: int,
    name: str,
    source_type: str,
    source_reference: str | None,
) -> ShoppingList:
    shopping_list = ShoppingList(
        family_id=family_id,
        name=name,
        source_type=source_type,
        source_reference=source_reference,
    )
    session.add(shopping_list)
    await session.flush()
    return shopping_list


async def add_shopping_list_item(
    session: AsyncSession,
    *,
    shopping_list_id: int,
    name: str,
    quantity: float | None,
    unit: str | None,
    note: str | None,
    source_dish_name: str | None,
    ingredient_id: int | None,
    sort_order: int,
) -> ShoppingListItem:
    item = ShoppingListItem(
        shopping_list_id=shopping_list_id,
        name=name,
        quantity=quantity,
        unit=unit,
        note=note,
        source_dish_name=source_dish_name,
        ingredient_id=ingredient_id,
        sort_order=sort_order,
    )
    session.add(item)
    await session.flush()
    return item
