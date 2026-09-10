import asyncio
import hashlib
import hmac
import json
import logging

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from langchain_openai import ChatOpenAI
from pydantic_settings import BaseSettings

from .runtime import generate
from .schemas import RecommendationRequest


class Settings(BaseSettings):
    ai_service_token: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_api_key: str = ""
    ai_model: str = ""
    ai_timeout_seconds: int = 60
    ai_enabled: bool = False


settings = Settings()
app = FastAPI(title="YY Kitchen internal AI", docs_url=None, redoc_url=None)
logger = logging.getLogger(__name__)


def authorized(authorization: str = Header(default="")):
    if not settings.ai_service_token or not hmac.compare_digest(authorization, "Bearer " + settings.ai_service_token):
        raise HTTPException(401, "Invalid service credentials")


def model():
    if not settings.ai_enabled or not settings.ai_api_key or not settings.ai_model:
        raise HTTPException(503, "AI service is not configured")
    return ChatOpenAI(model=settings.ai_model, api_key=settings.ai_api_key, base_url=settings.ai_base_url,
                      timeout=settings.ai_timeout_seconds, max_retries=0, streaming=True)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/internal/v1/config", dependencies=[Depends(authorized)])
def config():
    fingerprint = hashlib.sha256(json.dumps([settings.ai_base_url, settings.ai_model, "prompt-v1"]).encode()).hexdigest()
    return {"fingerprint": fingerprint}


def event(name: str, data: object) -> str:
    return f"event: {name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post("/internal/v1/recommendations/stream", dependencies=[Depends(authorized)])
async def recommendations(payload: RecommendationRequest, llm=Depends(model)):
    async def stream():
        yield event("ready", {"status": "processing"})
        generator = generate(payload, llm)
        try:
            async with asyncio.timeout(settings.ai_timeout_seconds):
                async for name, data in generator:
                    yield event(name, data)
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            yield event("error", {"message": "AI 推理超时，请重试", "status_code": 504})
        except Exception:
            logger.exception("AI generation failed request_id=%s", payload.request_id)
            yield event("error", {"message": "AI 结果生成失败，请稍后重试", "status_code": 502})
        finally:
            await generator.aclose()
    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
