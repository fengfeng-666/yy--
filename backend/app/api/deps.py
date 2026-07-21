from typing import Annotated

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ErrorCode
from app.core.exceptions import AppException
from app.core.security import decode_access_token
from app.db.session import get_db_session
from app.models.family import Family
from app.models.user import User
from app.repositories.user import get_user_by_id
from app.services.family import get_current_family_for_user


DbSession = Annotated[AsyncSession, Depends(get_db_session)]

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: DbSession,
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppException(
            code=ErrorCode.UNAUTHORIZED,
            message="请先登录",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise AppException(
            code=ErrorCode.UNAUTHORIZED,
            message="登录凭证无效",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    user = await get_user_by_id(session, int(user_id))
    if user is None or not user.is_active:
        raise AppException(
            code=ErrorCode.UNAUTHORIZED,
            message="登录状态无效，请重新登录",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return user


async def get_current_family(
    current_user: Annotated[User, Depends(get_current_user)],
    session: DbSession,
) -> Family:
    return await get_current_family_for_user(session, current_user.id)
