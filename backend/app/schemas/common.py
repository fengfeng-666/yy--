from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

from app.core.constants import DEFAULT_SUCCESS_MESSAGE, SUCCESS_CODE


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(populate_by_name=True)

    code: int = SUCCESS_CODE
    message: str = DEFAULT_SUCCESS_MESSAGE
    data: T | None = None


def success_response(data: T | None = None, message: str = DEFAULT_SUCCESS_MESSAGE) -> ApiResponse[T]:
    return ApiResponse(data=data, message=message)


class HealthCheckDatabase(BaseModel):
    status: str
    host: str
    name: str


class HealthCheckData(BaseModel):
    app_name: str
    environment: str
    status: str
    database: HealthCheckDatabase
