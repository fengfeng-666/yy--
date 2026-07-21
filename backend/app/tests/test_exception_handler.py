from fastapi import FastAPI, HTTPException, Query
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.constants import ErrorCode
from app.core.exceptions import AppException
from app.middleware.exception_handler import register_exception_handlers


def create_test_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/app-exception")
    async def raise_app_exception() -> None:
        raise AppException(
            code=ErrorCode.CONFLICT,
            message="业务冲突",
            status_code=409,
        )

    @app.get("/http-exception")
    async def raise_http_exception() -> None:
        raise HTTPException(status_code=404, detail="资源不存在")

    @app.get("/validation")
    async def validation_endpoint(limit: int = Query(..., ge=1)) -> dict[str, int]:
        return {"limit": limit}

    return app


@pytest.mark.asyncio
async def test_app_exception_returns_unified_response() -> None:
    app = create_test_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/app-exception")

    assert response.status_code == 409
    assert response.json() == {
        "code": ErrorCode.CONFLICT,
        "message": "业务冲突",
        "data": None,
    }


@pytest.mark.asyncio
async def test_http_exception_returns_unified_response() -> None:
    app = create_test_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/http-exception")

    assert response.status_code == 404
    assert response.json() == {
        "code": ErrorCode.NOT_FOUND,
        "message": "资源不存在",
        "data": None,
    }


@pytest.mark.asyncio
async def test_request_validation_returns_unified_response() -> None:
    app = create_test_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/validation", params={"limit": 0})

    body = response.json()
    assert response.status_code == 422
    assert body["code"] == ErrorCode.BAD_REQUEST
    assert body["message"] == "请求参数校验失败"
    assert isinstance(body["data"], list)
    assert body["data"][0]["loc"] == ["query", "limit"]
