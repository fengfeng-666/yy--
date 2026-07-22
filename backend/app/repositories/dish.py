from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dish import Dish, DishCategory


async def get_dish_category_by_id(
    session: AsyncSession,
    *,
    family_id: int,
    category_id: int,
) -> DishCategory | None:
    result = await session.execute(
        select(DishCategory).where(
            DishCategory.family_id == family_id,
            DishCategory.id == category_id,
        )
    )
    return result.scalar_one_or_none()


async def get_dish_category_by_name(
    session: AsyncSession,
    *,
    family_id: int,
    name: str,
    exclude_category_id: int | None = None,
) -> DishCategory | None:
    statement: Select[tuple[DishCategory]] = select(DishCategory).where(
        DishCategory.family_id == family_id,
        DishCategory.name == name,
    )
    if exclude_category_id is not None:
        statement = statement.where(DishCategory.id != exclude_category_id)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def list_dish_categories(session: AsyncSession, *, family_id: int) -> Sequence[DishCategory]:
    result = await session.execute(
        select(DishCategory)
        .where(DishCategory.family_id == family_id)
        .order_by(DishCategory.sort_order.asc(), DishCategory.id.asc())
    )
    return result.scalars().all()


async def create_dish_category(
    session: AsyncSession,
    *,
    family_id: int,
    name: str,
    sort_order: int,
) -> DishCategory:
    category = DishCategory(
        family_id=family_id,
        name=name,
        sort_order=sort_order,
    )
    session.add(category)
    await session.flush()
    return category


async def count_dishes_by_category(
    session: AsyncSession,
    *,
    family_id: int,
    category_id: int,
) -> int:
    result = await session.execute(
        select(func.count(Dish.id)).where(
            Dish.family_id == family_id,
            Dish.category_id == category_id,
        )
    )
    return int(result.scalar_one())


async def delete_dish_category(session: AsyncSession, category: DishCategory) -> None:
    await session.delete(category)
    await session.flush()


async def get_dish_by_id(session: AsyncSession, *, family_id: int, dish_id: int) -> Dish | None:
    result = await session.execute(
        select(Dish)
        .options(selectinload(Dish.category))
        .where(Dish.family_id == family_id, Dish.id == dish_id)
    )
    return result.scalar_one_or_none()


async def list_dishes(
    session: AsyncSession,
    *,
    family_id: int,
    category_id: int | None = None,
) -> Sequence[Dish]:
    statement: Select[tuple[Dish]] = (
        select(Dish)
        .options(selectinload(Dish.category))
        .where(Dish.family_id == family_id)
        .order_by(Dish.updated_at.desc(), Dish.id.desc())
    )
    if category_id is not None:
        statement = statement.where(Dish.category_id == category_id)

    result = await session.execute(statement)
    return result.scalars().all()


async def create_dish(
    session: AsyncSession,
    *,
    family_id: int,
    category_id: int,
    name: str,
    description: str | None,
    price: float,
    image_url: str | None,
    is_available: bool,
) -> Dish:
    dish = Dish(
        family_id=family_id,
        category_id=category_id,
        name=name,
        description=description,
        price=price,
        image_url=image_url,
        is_available=is_available,
    )
    session.add(dish)
    await session.flush()
    return dish


async def delete_dish(session: AsyncSession, dish: Dish) -> None:
    await session.delete(dish)
    await session.flush()
