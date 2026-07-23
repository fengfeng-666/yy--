import json
import re
from typing import Any

import httpx
from fastapi import status

from app.core.config import get_settings
from app.core.constants import ErrorCode
from app.core.exceptions import AppException
from app.schemas.ai_chat import ParsedAiRecommendation


def extract_json_object(content: str) -> dict[str, Any]:
    stripped = content.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", stripped)
    if not match:
        raise AppException(
            code=ErrorCode.INTERNAL_ERROR,
            message="AI 返回格式解析失败，请稍后再试",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise AppException(
            code=ErrorCode.INTERNAL_ERROR,
            message="AI 返回格式解析失败，请稍后再试",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc


async def generate_ai_recommendation(
    *,
    system_prompt: str,
    history_messages: list[dict[str, Any]],
    user_content: str,
    image_data_url: str | None = None,
) -> ParsedAiRecommendation:
    settings = get_settings()
    if not settings.ai_enabled:
        raise AppException(message="AI 功能尚未开启")

    user_message_content: list[dict[str, Any]] = [{"type": "text", "text": user_content}]
    if image_data_url is not None:
        user_message_content.append(
            {
                "type": "image_url",
                "image_url": {"url": image_data_url},
            }
        )

    payload = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            *history_messages,
            {"role": "user", "content": user_message_content},
        ],
        "temperature": 0.4,
    }

    try:
        async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
            response = await client.post(
                f"{settings.ai_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.ai_api_key}"},
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise AppException(
            code=ErrorCode.INTERNAL_ERROR,
            message="AI 服务暂时不可用，请稍后再试",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc

    response_json = response.json()
    try:
        content = response_json["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AppException(
            code=ErrorCode.INTERNAL_ERROR,
            message="AI 服务暂时不可用，请稍后再试",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc

    if isinstance(content, list):
        text_segments = [
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        content_text = "\n".join(segment for segment in text_segments if segment).strip()
    else:
        content_text = str(content).strip()

    payload_json = extract_json_object(content_text)
    try:
        return ParsedAiRecommendation.model_validate(
            {
                "summary": payload_json.get("summary") or "已为你整理推荐结果。",
                "recognized_ingredients": payload_json.get("recognized_ingredients") or [],
                "recommendations": payload_json.get("recommendations") or [],
                "raw_model_output": content_text,
            }
        )
    except Exception as exc:
        raise AppException(
            code=ErrorCode.INTERNAL_ERROR,
            message="AI 返回格式解析失败，请稍后再试",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc
