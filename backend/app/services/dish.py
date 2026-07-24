from fastapi import UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ErrorCode
from app.core.exceptions import AppException
from app.models.dish import Dish
from app.repositories.dish import (
    create_dish,
    delete_dish,
    get_dish_by_id,
    list_dishes,
)
from app.schemas.dish import DishCreateRequest, DishUpdateRequest
from app.services.upload import read_and_validate_image, save_image_bytes


async def list_dishes_for_family(session: AsyncSession, *, family_id: int) -> list[Dish]:
    return list(await list_dishes(session, family_id=family_id))


async def create_dish_for_family(
    session: AsyncSession,
    *,
    family_id: int,
    payload: DishCreateRequest,
) -> Dish:
    dish = await create_dish(
        session,
        family_id=family_id,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        image_url=payload.image_url,
        is_available=payload.is_available,
    )
    await session.commit()
    return await require_dish(session, family_id=family_id, dish_id=dish.id)


async def update_dish_for_family(
    session: AsyncSession,
    *,
    family_id: int,
    dish_id: int,
    payload: DishUpdateRequest,
) -> Dish:
    dish = await require_dish(session, family_id=family_id, dish_id=dish_id)
    dish.name = payload.name
    dish.description = payload.description
    dish.price = payload.price
    dish.image_url = payload.image_url
    dish.is_available = payload.is_available
    await session.commit()
    return await require_dish(session, family_id=family_id, dish_id=dish_id)


async def delete_dish_for_family(
    session: AsyncSession,
    *,
    family_id: int,
    dish_id: int,
) -> None:
    dish = await require_dish(session, family_id=family_id, dish_id=dish_id)
    await delete_dish(session, dish)
    await session.commit()


async def require_dish(session: AsyncSession, *, family_id: int, dish_id: int) -> Dish:
    dish = await get_dish_by_id(session, family_id=family_id, dish_id=dish_id)
    if dish is None:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message="菜品不存在",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return dish


async def save_dish_image(upload_file: UploadFile, *, family_id: int) -> str:
    content, suffix = await read_and_validate_image(upload_file)
    return save_image_bytes(
        content,
        family_id=family_id,
        category_segments=("dishes",),
        suffix=suffix,
    )
