import asyncio
import time
from functools import lru_cache
from typing import Any

import httpx
from fastapi import status

from app.core.config import get_settings
from app.core.exceptions import AppException


class WechatApiError(RuntimeError):
    pass


class WechatClient:
    def __init__(self, *, app_id: str, app_secret: str, api_base_url: str) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.api_base_url = api_base_url.rstrip("/")
        self._access_token = ""
        self._access_token_expires_at = 0.0
        self._token_lock = asyncio.Lock()

    def _require_credentials(self) -> None:
        if not self.app_id or not self.app_secret:
            raise AppException(
                message="微信小程序登录尚未配置",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    async def code_to_session(self, code: str) -> dict[str, Any]:
        self._require_credentials()
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.api_base_url}/sns/jscode2session",
                params={
                    "appid": self.app_id,
                    "secret": self.app_secret,
                    "js_code": code,
                    "grant_type": "authorization_code",
                },
            )
        response.raise_for_status()
        payload = response.json()
        if payload.get("errcode"):
            raise AppException(
                message="微信登录凭证无效或已过期",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        if not payload.get("openid"):
            raise WechatApiError("微信登录响应缺少 openid")
        return payload

    async def get_access_token(self) -> str:
        self._require_credentials()
        if self._access_token and time.monotonic() < self._access_token_expires_at:
            return self._access_token

        async with self._token_lock:
            if self._access_token and time.monotonic() < self._access_token_expires_at:
                return self._access_token
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.api_base_url}/cgi-bin/token",
                    params={
                        "grant_type": "client_credential",
                        "appid": self.app_id,
                        "secret": self.app_secret,
                    },
                )
            response.raise_for_status()
            payload = response.json()
            if payload.get("errcode") or not payload.get("access_token"):
                raise WechatApiError(payload.get("errmsg", "获取微信 access_token 失败"))
            self._access_token = payload["access_token"]
            expires_in = max(int(payload.get("expires_in", 7200)) - 300, 60)
            self._access_token_expires_at = time.monotonic() + expires_in
            return self._access_token

    async def send_subscribe_message(
        self,
        *,
        openid: str,
        template_id: str,
        page: str,
        data: dict[str, Any],
    ) -> None:
        token = await self.get_access_token()
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self.api_base_url}/cgi-bin/message/subscribe/send",
                params={"access_token": token},
                json={
                    "touser": openid,
                    "template_id": template_id,
                    "page": page,
                    "lang": "zh_CN",
                    "data": data,
                },
            )
        response.raise_for_status()
        payload = response.json()
        if payload.get("errcode"):
            raise WechatApiError(payload.get("errmsg", "发送微信订阅消息失败"))


@lru_cache
def get_wechat_client() -> WechatClient:
    settings = get_settings()
    return WechatClient(
        app_id=settings.wechat_app_id,
        app_secret=settings.wechat_app_secret,
        api_base_url=settings.wechat_api_base_url,
    )
