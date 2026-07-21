from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ErrorCode
from app.core.exceptions import AppException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user import create_user, get_user_by_username
from app.schemas.auth import AuthResponse, AuthTokens, LoginRequest, RegisterRequest, UserProfile


async def register_user(session: AsyncSession, payload: RegisterRequest) -> AuthResponse:
    existing_user = await get_user_by_username(session, payload.username)
    if existing_user is not None:
        raise AppException(
            code=ErrorCode.USERNAME_ALREADY_EXISTS,
            message="用户名已存在",
            status_code=status.HTTP_409_CONFLICT,
        )

    user = await create_user(
        session,
        username=payload.username,
        nickname=payload.nickname or payload.username,
        password_hash=hash_password(payload.password),
    )
    token, expires_at = create_access_token(user.id)
    return build_auth_response(user, token, expires_at)


async def login_user(session: AsyncSession, payload: LoginRequest) -> AuthResponse:
    user = await get_user_by_username(session, payload.username)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise AppException(
            code=ErrorCode.INVALID_CREDENTIALS,
            message="用户名或密码错误",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        raise AppException(
            code=ErrorCode.FORBIDDEN,
            message="账号已停用",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    token, expires_at = create_access_token(user.id)
    return build_auth_response(user, token, expires_at)


def build_auth_response(user: User, access_token: str, expires_at) -> AuthResponse:
    return AuthResponse(
        user=UserProfile.model_validate(user),
        tokens=AuthTokens(access_token=access_token, expires_at=expires_at),
    )
