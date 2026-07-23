from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_wechat_openid(session: AsyncSession, openid: str) -> User | None:
    result = await session.execute(select(User).where(User.wechat_openid == openid))
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    *,
    username: str,
    nickname: str,
    password_hash: str,
    wechat_openid: str | None = None,
    wechat_unionid: str | None = None,
) -> User:
    user = User(
        username=username,
        nickname=nickname,
        password_hash=password_hash,
        wechat_openid=wechat_openid,
        wechat_unionid=wechat_unionid,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_user_nickname(
    session: AsyncSession,
    *,
    user: User,
    nickname: str,
) -> User:
    user.nickname = nickname
    await session.commit()
    await session.refresh(user)
    return user
