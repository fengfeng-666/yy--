from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import BASE_DIR, get_settings
from app.core.constants import ErrorCode
from app.core.exceptions import AppException
from app.models.dish import Dish, DishCategory
from app.repositories.dish import (
    count_dishes_by_category,
    create_dish,
    create_dish_category,
    delete_dish,
    delete_dish_category,
    get_dish_by_id,
    get_dish_category_by_id,
    get_dish_category_by_name,
    list_dish_categories,
    list_dishes,
)
from app.schemas.dish import (
    DishCategoryCreateRequest,
    DishCategoryUpdateRequest,
    DishCreateRequest,
    DishUpdateRequest,
)


ALLOWED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
CONTENT_TYPE_SUFFIX_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


async def list_categories_for_family(session: AsyncSession, *, family_id: int) -> list[DishCategory]:
    return list(await list_dish_categories(session, family_id=family_id))


async def create_category_for_family(
    session: AsyncSession,
    *,
    family_id: int,
    payload: DishCategoryCreateRequest,
) -> DishCategory:
    duplicated = await get_dish_category_by_name(session, family_id=family_id, name=payload.name)
    if duplicated is not None:
        raise AppException(
            code=ErrorCode.CONFLICT,
            message="分类名称已存在",
            status_code=status.HTTP_409_CONFLICT,
        )

    category = await create_dish_category(
        session,
        family_id=family_id,
        name=payload.name,
        sort_order=payload.sort_order,
    )
    await session.commit()
    return category


async def update_category_for_family(
    session: AsyncSession,
    *,
    family_id: int,
    category_id: int,
    payload: DishCategoryUpdateRequest,
) -> DishCategory:
    category = await require_category(session, family_id=family_id, category_id=category_id)
    duplicated = await get_dish_category_by_name(
        session,
        family_id=family_id,
        name=payload.name,
        exclude_category_id=category_id,
    )
    if duplicated is not None:
        raise AppException(
            code=ErrorCode.CONFLICT,
            message="分类名称已存在",
            status_code=status.HTTP_409_CONFLICT,
        )

    category.name = payload.name
    category.sort_order = payload.sort_order
    await session.commit()
    refreshed = await get_dish_category_by_id(session, family_id=family_id, category_id=category_id)
    if refreshed is None:
        raise AppException(
            code=ErrorCode.INTERNAL_ERROR,
            message="分类更新失败，请稍后重试",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return refreshed


async def delete_category_for_family(
    session: AsyncSession,
    *,
    family_id: int,
    category_id: int,
) -> None:
    category = await require_category(session, family_id=family_id, category_id=category_id)
    dish_count = await count_dishes_by_category(session, family_id=family_id, category_id=category_id)
    if dish_count > 0:
        raise AppException(
            code=ErrorCode.CONFLICT,
            message="分类下还有菜品，不能删除",
            status_code=status.HTTP_409_CONFLICT,
        )

    await delete_dish_category(session, category)
    await session.commit()


async def list_dishes_for_family(
    session: AsyncSession,
    *,
    family_id: int,
    category_id: int | None = None,
) -> list[Dish]:
    if category_id is not None:
        await require_category(session, family_id=family_id, category_id=category_id)
    return list(await list_dishes(session, family_id=family_id, category_id=category_id))


async def create_dish_for_family(
    session: AsyncSession,
    *,
    family_id: int,
    payload: DishCreateRequest,
) -> Dish:
    await require_category(session, family_id=family_id, category_id=payload.category_id)
    dish = await create_dish(
        session,
        family_id=family_id,
        category_id=payload.category_id,
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
    await require_category(session, family_id=family_id, category_id=payload.category_id)

    dish.category_id = payload.category_id
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


async def require_category(
    session: AsyncSession,
    *,
    family_id: int,
    category_id: int,
) -> DishCategory:
    category = await get_dish_category_by_id(session, family_id=family_id, category_id=category_id)
    if category is None:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message="菜品分类不存在",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return category


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
    suffix = resolve_image_suffix(upload_file)
    content = await upload_file.read()
    if not content:
        raise AppException(message="上传图片不能为空")

    settings = get_settings()
    max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_size_bytes:
        raise AppException(message=f"图片不能超过 {settings.max_upload_size_mb}MB")

    relative_dir = Path("families") / str(family_id) / "dishes"
    upload_dir = Path(BASE_DIR / settings.upload_dir / relative_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4().hex}{suffix}"
    file_path = upload_dir / filename
    file_path.write_bytes(content)
    return f"/uploads/{relative_dir.as_posix()}/{filename}"


def resolve_image_suffix(upload_file: UploadFile) -> str:
    filename = upload_file.filename or ""
    suffix = Path(filename).suffix.lower()
    if suffix in ALLOWED_IMAGE_SUFFIXES:
        return suffix

    content_type = upload_file.content_type or ""
    mapped_suffix = CONTENT_TYPE_SUFFIX_MAP.get(content_type)
    if mapped_suffix is not None:
        return mapped_suffix

    raise AppException(message="仅支持 JPG、PNG、WEBP 图片上传")
