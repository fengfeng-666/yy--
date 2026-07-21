from fastapi import status

from app.core.constants import ErrorCode


class AppException(Exception):
    def __init__(
        self,
        *,
        code: int = ErrorCode.BAD_REQUEST,
        message: str = "请求参数错误",
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)
