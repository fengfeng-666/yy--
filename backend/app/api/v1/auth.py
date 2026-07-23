from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, get_current_user
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UpdateProfileRequest,
    UserProfile,
    WechatLoginRequest,
)
from app.schemas.common import ApiResponse, success_response
from app.services.auth import login_user, login_wechat_user, register_user, update_profile
from app.services.wechat import WechatClient, get_wechat_client

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/wechat/login", response_model=ApiResponse[AuthResponse], summary="微信小程序登录")
async def wechat_login(
    payload: WechatLoginRequest,
    session: DbSession,
    client: Annotated[WechatClient, Depends(get_wechat_client)],
) -> ApiResponse[AuthResponse]:
    auth_data = await login_wechat_user(session, payload, client)
    return success_response(data=auth_data, message="登录成功")


@router.post("/register", response_model=ApiResponse[AuthResponse], summary="注册")
async def register(payload: RegisterRequest, session: DbSession) -> ApiResponse[AuthResponse]:
    auth_data = await register_user(session, payload)
    return success_response(data=auth_data, message="注册成功")


@router.post("/login", response_model=ApiResponse[AuthResponse], summary="登录")
async def login(payload: LoginRequest, session: DbSession) -> ApiResponse[AuthResponse]:
    auth_data = await login_user(session, payload)
    return success_response(data=auth_data, message="登录成功")


@router.get("/me", response_model=ApiResponse[UserProfile], summary="当前用户")
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[UserProfile]:
    return success_response(data=UserProfile.model_validate(current_user))


@router.patch("/me", response_model=ApiResponse[UserProfile], summary="修改个人资料")
async def patch_me(
    payload: UpdateProfileRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: DbSession,
) -> ApiResponse[UserProfile]:
    profile = await update_profile(session, current_user=current_user, payload=payload)
    return success_response(data=profile, message="个人资料已更新")
