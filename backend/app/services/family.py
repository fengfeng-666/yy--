import secrets
import string

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ErrorCode
from app.core.exceptions import AppException
from app.models.family import Family
from app.models.family_member import FamilyMember, FamilyMemberRole
from app.models.user import User
from app.repositories.family import (
    add_family_member,
    count_family_members,
    create_family,
    get_family_by_id,
    get_family_by_invite_code,
    get_family_member_by_user_id,
    list_family_members,
)
from app.schemas.family import CreateFamilyRequest, FamilyAccessResponse, FamilyProfile, JoinFamilyRequest


INVITE_CODE_CHARS = string.ascii_uppercase + string.digits


async def ensure_user_has_no_family(session: AsyncSession, user_id: int) -> None:
    membership = await get_family_member_by_user_id(session, user_id)
    if membership is not None:
        raise AppException(
            code=ErrorCode.USER_ALREADY_IN_FAMILY,
            message="你已加入家庭，不能重复操作",
            status_code=status.HTTP_409_CONFLICT,
        )


async def generate_unique_invite_code(session: AsyncSession, length: int = 6) -> str:
    for _ in range(10):
        invite_code = "".join(secrets.choice(INVITE_CODE_CHARS) for _ in range(length))
        family = await get_family_by_invite_code(session, invite_code)
        if family is None:
            return invite_code
    raise AppException(
        code=ErrorCode.INTERNAL_ERROR,
        message="邀请码生成失败，请稍后重试",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def create_family_for_user(
    session: AsyncSession,
    *,
    current_user: User,
    payload: CreateFamilyRequest,
) -> FamilyAccessResponse:
    await ensure_user_has_no_family(session, current_user.id)
    invite_code = await generate_unique_invite_code(session)

    family = await create_family(
        session,
        name=payload.name,
        description=payload.description,
        invite_code=invite_code,
        owner_id=current_user.id,
    )
    await add_family_member(
        session,
        family_id=family.id,
        user_id=current_user.id,
        role=FamilyMemberRole.OWNER,
    )
    await session.commit()

    current_family = await get_family_by_id(session, family.id)
    if current_family is None:
        raise AppException(
            code=ErrorCode.INTERNAL_ERROR,
            message="家庭创建失败，请稍后重试",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return build_family_access_response(current_family)


async def join_family_for_user(
    session: AsyncSession,
    *,
    current_user: User,
    payload: JoinFamilyRequest,
) -> FamilyAccessResponse:
    await ensure_user_has_no_family(session, current_user.id)

    family = await get_family_by_invite_code(session, payload.invite_code)
    if family is None:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message="邀请码不存在，请检查后重试",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    current_members = await count_family_members(session, family.id)
    if current_members >= family.max_members:
        raise AppException(
            code=ErrorCode.FAMILY_FULL,
            message="当前家庭人数已满",
            status_code=status.HTTP_409_CONFLICT,
        )

    await add_family_member(
        session,
        family_id=family.id,
        user_id=current_user.id,
        role=FamilyMemberRole.MEMBER,
    )
    await session.commit()

    current_family = await get_family_by_id(session, family.id)
    if current_family is None:
        raise AppException(
            code=ErrorCode.INTERNAL_ERROR,
            message="加入家庭失败，请稍后重试",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return build_family_access_response(current_family)


async def get_current_family_for_user(session: AsyncSession, user_id: int) -> Family:
    membership = await get_family_member_by_user_id(session, user_id)
    if membership is None:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message="当前还未加入家庭",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    family = await get_family_by_id(session, membership.family_id)
    if family is None:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message="当前家庭不存在",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return family


async def get_current_family_members(session: AsyncSession, family_id: int) -> list[FamilyMember]:
    return list(await list_family_members(session, family_id))


def build_family_access_response(family: Family) -> FamilyAccessResponse:
    return FamilyAccessResponse(
        family=FamilyProfile.model_validate(family),
        needs_onboarding=False,
    )
