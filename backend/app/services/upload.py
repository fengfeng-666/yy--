from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import BASE_DIR, get_settings
from app.core.exceptions import AppException

ALLOWED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
CONTENT_TYPE_SUFFIX_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


async def read_and_validate_image(upload_file: UploadFile) -> tuple[bytes, str]:
    suffix = resolve_image_suffix(upload_file)
    content = await upload_file.read()
    if not content:
        raise AppException(message="上传图片不能为空")

    settings = get_settings()
    max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_size_bytes:
        raise AppException(message=f"图片不能超过 {settings.max_upload_size_mb}MB")

    return content, suffix


def save_image_bytes(
    content: bytes,
    *,
    family_id: int,
    category_segments: tuple[str, ...],
    suffix: str,
) -> str:
    settings = get_settings()
    relative_dir = Path("families") / str(family_id)
    for segment in category_segments:
        relative_dir /= segment

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
