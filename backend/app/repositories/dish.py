from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import Dish


async def get_dish_by_id(session: AsyncSession, *, family_id: int, dish_id: int) -> Dish | None:
    result = await session.execute(
        select(Dish).where(Dish.family_id == family_id, Dish.id == dish_id)
    )
    return result.scalar_one_or_none()


async def list_dishes(session: AsyncSession, *, family_id: int) -> Sequence[Dish]:
    statement: Select[tuple[Dish]] = (
        select(Dish)
        .where(Dish.family_id == family_id)
        .order_by(Dish.updated_at.desc(), Dish.id.desc())
    )

    result = await session.execute(statement)
    return result.scalars().all()


async def create_dish(
    session: AsyncSession,
    *,
    family_id: int,
    name: str,
    description: str | None,
    price: float,
    image_url: str | None,
    is_available: bool,
) -> Dish:
    dish = Dish(
        family_id=family_id,
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
