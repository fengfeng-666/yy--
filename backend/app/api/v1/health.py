from fastapi import APIRouter

from app.core.config import get_settings
from app.db.session import ping_database
from app.schemas.common import ApiResponse, HealthCheckData, HealthCheckDatabase, success_response


router = APIRouter(tags=["health"])


@router.get("/health", response_model=ApiResponse[HealthCheckData], summary="健康检查")
async def health_check() -> ApiResponse[HealthCheckData]:
    settings = get_settings()
    database_ready = await ping_database()
    return success_response(
        data=HealthCheckData(
            app_name=settings.app_name,
            environment=settings.app_env,
            status="ok" if database_ready else "degraded",
            database=HealthCheckDatabase(
                status="up" if database_ready else "down",
                host=settings.db_host,
                name=settings.db_name,
            ),
        )
    )
