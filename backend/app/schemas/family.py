from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.auth import UserProfile


class CreateFamilyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("家庭名称不能为空")
        return normalized

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class JoinFamilyRequest(BaseModel):
    invite_code: str = Field(min_length=4, max_length=20)

    @field_validator("invite_code")
    @classmethod
    def normalize_invite_code(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("邀请码不能为空")
        return normalized


class FamilyMemberProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    family_id: int
    user_id: int
    role: str
    joined_at: datetime
    user: UserProfile


class FamilyProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    cover_url: str | None
    invite_code: str
    owner_id: int
    max_members: int
    created_at: datetime
    updated_at: datetime
    members: list[FamilyMemberProfile] = Field(default_factory=list)


class FamilyAccessResponse(BaseModel):
    family: FamilyProfile
    needs_onboarding: bool = False
