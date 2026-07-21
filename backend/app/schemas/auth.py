from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    nickname: str | None = Field(default=None, max_length=32)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("用户名不能为空")
        if not all(char.isalnum() or char in {"_", "-"} for char in normalized):
            raise ValueError("用户名仅支持字母、数字、下划线和短横线")
        return normalized

    @field_validator("nickname")
    @classmethod
    def normalize_nickname(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("用户名不能为空")
        return normalized


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str
    is_active: bool
    created_at: datetime


class AuthTokens(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_at: datetime


class AuthResponse(BaseModel):
    user: UserProfile
    tokens: AuthTokens
