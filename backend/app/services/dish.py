from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import BASE_DIR, get_settings
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


ALLOWED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
CONTENT_TYPE_SUFFIX_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


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
