from typing import Annotated
from urllib.parse import urljoin

from fastapi import APIRouter, Depends, File, Request, UploadFile

from app.api.deps import DbSession, get_current_family
from app.models.family import Family
from app.schemas.common import ApiResponse, success_response
from app.schemas.dish import DishCreateRequest, DishProfile, DishUpdateRequest, ImageUploadResponse
from app.services.dish import (
    create_dish_for_family,
    delete_dish_for_family,
    list_dishes_for_family,
    require_dish,
    save_dish_image,
    update_dish_for_family,
)


router = APIRouter(tags=["dishes"])


@router.get("/dishes", response_model=ApiResponse[list[DishProfile]], summary="菜品列表")
async def get_dishes(
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
) -> ApiResponse[list[DishProfile]]:
    dishes = await list_dishes_for_family(session, family_id=current_family.id)
    return success_response(data=[DishProfile.model_validate(item) for item in dishes])


@router.post("/dishes", response_model=ApiResponse[DishProfile], summary="创建菜品")
async def create_dish(
    payload: DishCreateRequest,
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
) -> ApiResponse[DishProfile]:
    dish = await create_dish_for_family(session, family_id=current_family.id, payload=payload)
    return success_response(data=DishProfile.model_validate(dish), message="菜品创建成功")


@router.get("/dishes/{dish_id}", response_model=ApiResponse[DishProfile], summary="菜品详情")
async def get_dish(
    dish_id: int,
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
) -> ApiResponse[DishProfile]:
    dish = await require_dish(session, family_id=current_family.id, dish_id=dish_id)
    return success_response(data=DishProfile.model_validate(dish))


@router.patch("/dishes/{dish_id}", response_model=ApiResponse[DishProfile], summary="更新菜品")
async def update_dish(
    dish_id: int,
    payload: DishUpdateRequest,
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
) -> ApiResponse[DishProfile]:
    dish = await update_dish_for_family(
        session,
        family_id=current_family.id,
        dish_id=dish_id,
        payload=payload,
    )
    return success_response(data=DishProfile.model_validate(dish), message="菜品更新成功")


@router.delete("/dishes/{dish_id}", response_model=ApiResponse[None], summary="删除菜品")
async def delete_dish(
    dish_id: int,
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
) -> ApiResponse[None]:
    await delete_dish_for_family(session, family_id=current_family.id, dish_id=dish_id)
    return success_response(message="菜品删除成功")


@router.post("/uploads/images", response_model=ApiResponse[ImageUploadResponse], summary="上传图片")
async def upload_image(
    request: Request,
    file: Annotated[UploadFile, File(...)],
    current_family: Annotated[Family, Depends(get_current_family)],
) -> ApiResponse[ImageUploadResponse]:
    path = await save_dish_image(file, family_id=current_family.id)
    url = urljoin(str(request.base_url), path.lstrip("/"))
    return success_response(
        data=ImageUploadResponse(path=path, url=url),
        message="图片上传成功",
    )
