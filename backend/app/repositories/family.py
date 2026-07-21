from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.family import Family
from app.models.family_member import FamilyMember


async def get_family_by_id(session: AsyncSession, family_id: int) -> Family | None:
    result = await session.execute(
        select(Family)
        .options(selectinload(Family.members).selectinload(FamilyMember.user))
        .where(Family.id == family_id)
    )
    return result.scalar_one_or_none()


async def get_family_by_invite_code(session: AsyncSession, invite_code: str) -> Family | None:
    result = await session.execute(
        select(Family)
        .options(selectinload(Family.members).selectinload(FamilyMember.user))
        .where(Family.invite_code == invite_code)
    )
    return result.scalar_one_or_none()


async def get_family_member_by_user_id(session: AsyncSession, user_id: int) -> FamilyMember | None:
    result = await session.execute(select(FamilyMember).where(FamilyMember.user_id == user_id))
    return result.scalar_one_or_none()


async def count_family_members(session: AsyncSession, family_id: int) -> int:
    result = await session.execute(
        select(func.count(FamilyMember.id)).where(FamilyMember.family_id == family_id)
    )
    return int(result.scalar_one())


async def list_family_members(session: AsyncSession, family_id: int) -> Sequence[FamilyMember]:
    result = await session.execute(
        select(FamilyMember)
        .options(selectinload(FamilyMember.user))
        .where(FamilyMember.family_id == family_id)
        .order_by(FamilyMember.joined_at.asc())
    )
    return result.scalars().all()


async def create_family(
    session: AsyncSession,
    *,
    name: str,
    description: str | None,
    invite_code: str,
    owner_id: int,
    max_members: int = 2,
) -> Family:
    family = Family(
        name=name,
        description=description,
        invite_code=invite_code,
        owner_id=owner_id,
        max_members=max_members,
    )
    session.add(family)
    await session.flush()
    return family


async def add_family_member(
    session: AsyncSession,
    *,
    family_id: int,
    user_id: int,
    role: str,
) -> FamilyMember:
    member = FamilyMember(family_id=family_id, user_id=user_id, role=role)
    session.add(member)
    await session.flush()
    return member
