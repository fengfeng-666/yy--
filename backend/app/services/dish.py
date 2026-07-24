from fastapi import UploadFile, status
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ErrorCode
from app.core.exceptions import AppException
from app.models.dish import Dish
from app.models.ingredient import DishIngredient, DishPreference, DishStep
from app.repositories.dish import (
    create_dish,
    create_ingredient,
    delete_dish,
    get_dish_by_id,
    get_ingredient_by_name,
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
        cooking_minutes=payload.cooking_minutes,
        difficulty=payload.difficulty,
        spicy_level=payload.spicy_level,
        need_prepare_ahead=payload.need_prepare_ahead,
        suitable_for_weekday=payload.suitable_for_weekday,
        is_available=payload.is_available,
    )
    await sync_dish_knowledge(
        session,
        family_id=family_id,
        dish=dish,
        payload=payload,
        clear_existing=False,
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
    dish.cooking_minutes = payload.cooking_minutes
    dish.difficulty = payload.difficulty
    dish.spicy_level = payload.spicy_level
    dish.need_prepare_ahead = payload.need_prepare_ahead
    dish.suitable_for_weekday = payload.suitable_for_weekday
    dish.is_available = payload.is_available
    await sync_dish_knowledge(
        session,
        family_id=family_id,
        dish=dish,
        payload=payload,
        clear_existing=True,
    )
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


async def sync_dish_knowledge(
    session: AsyncSession,
    *,
    family_id: int,
    dish: Dish,
    payload: DishCreateRequest | DishUpdateRequest,
    clear_existing: bool,
) -> None:
    if clear_existing:
        await session.execute(delete(DishIngredient).where(DishIngredient.dish_id == dish.id))
        await session.execute(delete(DishStep).where(DishStep.dish_id == dish.id))
        await session.execute(delete(DishPreference).where(DishPreference.dish_id == dish.id))
        await session.flush()

    for item in payload.ingredients:
        ingredient = await get_ingredient_by_name(
            session,
            family_id=family_id,
            name=item.ingredient_name,
        )
        if ingredient is None:
            ingredient = await create_ingredient(
                session,
                family_id=family_id,
                name=item.ingredient_name,
                category=item.category,
                default_unit=item.unit,
            )
        else:
            if item.category and not ingredient.category:
                ingredient.category = item.category
            if item.unit and not ingredient.default_unit:
                ingredient.default_unit = item.unit

        session.add(
            DishIngredient(
                dish_id=dish.id,
                ingredient_id=ingredient.id,
                quantity=item.quantity,
                unit=item.unit,
                is_optional=item.is_optional,
                note=item.note,
                sort_order=item.sort_order,
            )
        )

    for step in sorted(payload.steps, key=lambda value: (value.step_no, value.content)):
        session.add(
            DishStep(
                dish_id=dish.id,
                step_no=step.step_no,
                content=step.content,
                duration_minutes=step.duration_minutes,
            )
        )

    seen_user_ids: set[int] = set()
    for preference in payload.preferences:
        if preference.user_id in seen_user_ids:
            raise AppException(message="同一个成员的菜品偏好不能重复")
        seen_user_ids.add(preference.user_id)
        session.add(
            DishPreference(
                dish_id=dish.id,
                user_id=preference.user_id,
                preference_note=preference.preference_note,
            )
        )

    await session.flush()
