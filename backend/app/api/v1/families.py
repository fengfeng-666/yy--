from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, get_current_family, get_current_user
from app.models.family import Family
from app.models.user import User
from app.schemas.common import ApiResponse, success_response
from app.schemas.family import (
    CreateFamilyRequest,
    FamilyAccessResponse,
    FamilyMemberProfile,
    FamilyProfile,
    JoinFamilyRequest,
)
from app.services.family import (
    build_family_access_response,
    create_family_for_user,
    get_current_family_members,
    join_family_for_user,
)


router = APIRouter(prefix="/families", tags=["families"])


@router.post("", response_model=ApiResponse[FamilyAccessResponse], summary="创建家庭")
async def create_family(
    payload: CreateFamilyRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: DbSession,
) -> ApiResponse[FamilyAccessResponse]:
    family_data = await create_family_for_user(session, current_user=current_user, payload=payload)
    return success_response(data=family_data, message="家庭创建成功")


@router.post("/join", response_model=ApiResponse[FamilyAccessResponse], summary="加入家庭")
async def join_family(
    payload: JoinFamilyRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: DbSession,
) -> ApiResponse[FamilyAccessResponse]:
    family_data = await join_family_for_user(session, current_user=current_user, payload=payload)
    return success_response(data=family_data, message="加入家庭成功")


@router.get("/current", response_model=ApiResponse[FamilyProfile], summary="当前家庭")
async def get_family(
    current_family: Annotated[Family, Depends(get_current_family)],
) -> ApiResponse[FamilyProfile]:
    return success_response(data=FamilyProfile.model_validate(current_family))


@router.get("/current/members", response_model=ApiResponse[list[FamilyMemberProfile]], summary="当前家庭成员")
async def get_family_members(
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
) -> ApiResponse[list[FamilyMemberProfile]]:
    members = await get_current_family_members(session, current_family.id)
    return success_response(data=[FamilyMemberProfile.model_validate(member) for member in members])
