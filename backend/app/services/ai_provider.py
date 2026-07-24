import json
import re
from collections.abc import Awaitable, Callable
from inspect import isawaitable
from typing import Any

import httpx
from fastapi import status

from app.core.config import get_settings
from app.core.constants import ErrorCode
from app.core.exceptions import AppException
from app.schemas.ai_chat import ParsedAiRecommendation

SummaryDeltaHandler = Callable[[str], Awaitable[None] | None]


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


def extract_streaming_summary(content: str) -> str:
    """Extract the decodable prefix of the summary JSON string from partial output."""
    match = re.search(r'"summary"\s*:\s*"', content)
    if match is None:
        return ""

    index = match.end()
    raw_chars: list[str] = []
    while index < len(content):
        char = content[index]
        if char == '"':
            break
        if char != "\\":
            raw_chars.append(char)
            index += 1
            continue

        if index + 1 >= len(content):
            break
        escape = content[index + 1]
        if escape == "u":
            if index + 6 > len(content):
                break
            raw_chars.append(content[index : index + 6])
            index += 6
            continue
        raw_chars.append(content[index : index + 2])
        index += 2

    try:
        return json.loads(f'"{"".join(raw_chars)}"')
    except json.JSONDecodeError:
        return ""


def _content_delta_text(delta: object) -> str:
    if isinstance(delta, str):
        return delta
    if not isinstance(delta, list):
        return ""
    return "".join(
        str(item.get("text", ""))
        for item in delta
        if isinstance(item, dict) and item.get("type") == "text"
    )


async def _emit_summary_delta(handler: SummaryDeltaHandler, delta: str) -> None:
    result = handler(delta)
    if isawaitable(result):
        await result


async def _stream_completion_content(
    client: httpx.AsyncClient,
    *,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    on_summary_delta: SummaryDeltaHandler,
) -> str:
    accumulated = ""
    emitted_summary = ""
    async with client.stream(
        "POST", url, headers=headers, json={**payload, "stream": True}
    ) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
            if not line.startswith("data:"):
                continue
            event_data = line[5:].strip()
            if not event_data or event_data == "[DONE]":
                continue
            try:
                event = json.loads(event_data)
                delta = _content_delta_text(event["choices"][0]["delta"].get("content"))
            except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                continue
            if not delta:
                continue
            accumulated += delta
            summary = extract_streaming_summary(accumulated)
            if summary.startswith(emitted_summary) and len(summary) > len(emitted_summary):
                await _emit_summary_delta(on_summary_delta, summary[len(emitted_summary) :])
                emitted_summary = summary
    return accumulated


async def generate_ai_recommendation(
    *,
    system_prompt: str,
    history_messages: list[dict[str, Any]],
    user_content: str,
    image_data_url: str | None = None,
    on_summary_delta: SummaryDeltaHandler | None = None,
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

    url = f"{settings.ai_base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.ai_api_key}"}
    try:
        timeout = httpx.Timeout(
            settings.ai_timeout_seconds,
            connect=min(settings.ai_timeout_seconds, 10),
        )
        async with httpx.AsyncClient(timeout=timeout) as client:
            if on_summary_delta is not None:
                content_text = (await _stream_completion_content(
                    client,
                    url=url,
                    headers=headers,
                    payload=payload,
                    on_summary_delta=on_summary_delta,
                )).strip()
            else:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                response_json = response.json()
                content = response_json["choices"][0]["message"]["content"]
                if isinstance(content, list):
                    text_segments = [
                        item.get("text", "")
                        for item in content
                        if isinstance(item, dict) and item.get("type") == "text"
                    ]
                    content_text = "\n".join(
                        segment for segment in text_segments if segment
                    ).strip()
                else:
                    content_text = str(content).strip()
    except httpx.HTTPError as exc:
        raise AppException(
            code=ErrorCode.INTERNAL_ERROR,
            message="AI 服务暂时不可用，请稍后再试",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc

    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise AppException(
            code=ErrorCode.INTERNAL_ERROR,
            message="AI 服务暂时不可用，请稍后再试",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc

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
