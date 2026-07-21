import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.constants import ErrorCode
from app.core.exceptions import AppException


logger = logging.getLogger(__name__)


def build_error_response(
    *,
    status_code: int,
    code: int,
    message: str,
    data: Any = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message, "data": data},
    )


def map_http_status_to_error_code(status_code: int) -> int:
    if status_code == status.HTTP_401_UNAUTHORIZED:
        return ErrorCode.UNAUTHORIZED
    if status_code == status.HTTP_403_FORBIDDEN:
        return ErrorCode.FORBIDDEN
    if status_code == status.HTTP_404_NOT_FOUND:
        return ErrorCode.NOT_FOUND
    if 400 <= status_code < 500:
        return ErrorCode.BAD_REQUEST
    return ErrorCode.INTERNAL_ERROR


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
        return build_error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            data=None,
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return build_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code=ErrorCode.BAD_REQUEST,
            message="请求参数校验失败",
            data=exc.errors(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail
        message = detail if isinstance(detail, str) else "请求处理失败"
        data = detail if not isinstance(detail, str) else None
        return build_error_response(
            status_code=exc.status_code,
            code=map_http_status_to_error_code(exc.status_code),
            message=message,
            data=data,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled exception on %s",
            request.url.path,
            extra={"request_id": getattr(request.state, "request_id", "-")},
        )
        return build_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=ErrorCode.INTERNAL_ERROR,
            message="系统内部错误",
            data=None,
        )
