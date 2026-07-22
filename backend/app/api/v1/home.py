from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, get_current_family, get_current_user
from app.models.family import Family
from app.models.user import User
from app.schemas.common import ApiResponse, success_response
from app.schemas.home import HomeSummaryProfile
from app.services.home import get_home_summary


router = APIRouter(prefix="/home", tags=["home"])


@router.get("/summary", response_model=ApiResponse[HomeSummaryProfile], summary="首页聚合信息")
async def get_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    current_family: Annotated[Family, Depends(get_current_family)],
    session: DbSession,
) -> ApiResponse[HomeSummaryProfile]:
    summary = await get_home_summary(session, family_id=current_family.id, current_user=current_user)
    return success_response(data=summary)
