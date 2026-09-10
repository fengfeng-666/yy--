import asyncio
import json

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessageChunk
from pydantic import ValidationError

from ai_service.main import app, model, settings
from ai_service.retrieval import retrieve
from ai_service.runtime import generate, summary_prefix
from ai_service.schemas import RecommendationRequest


class ModelStub:
    def __init__(self, raw=None, failure=False):
        self.raw = raw or json.dumps({"summary": "推荐番茄炒蛋", "recognized_ingredients": ["鸡蛋"], "recommendations": [{"dish_name": "番茄炒蛋", "rating": 5, "reason": "符合口味"}]}, ensure_ascii=False)
        self.failure = failure
        self.messages = []
        self.closed = False

    async def astream(self, messages):
        self.messages = messages
        try:
            for i in range(0, len(self.raw), 3):
                yield AIMessageChunk(content=self.raw[i:i+3])
                await asyncio.sleep(0)
            if self.failure:
                raise RuntimeError("upstream error")
        finally:
            self.closed = True


def payload(**kwargs):
    return RecommendationRequest(request_id="test", content="番茄鸡蛋做什么", **kwargs)


def test_retrieves_all_categories_and_excludes_unavailable():
    docs = retrieve(payload(dishes=[{"id": 1, "name": "番茄炒蛋", "is_available": True}, {"id": 2, "name": "不可用", "is_available": False}], preferences=[{"preference_note": "不吃辣"}], dining_history=[{"id": 3, "name": "昨天吃面"}]))
    assert {d.metadata["source_type"] for d in docs} == {"family_dish", "family_preference", "dining_history"}
    assert all("不可用" not in d.page_content for d in docs)


async def test_streaming_and_no_image_hallucination():
    stub = ModelStub()
    events = [event async for event in generate(payload(), stub)]
    assert "".join(d["content"] for e, d in events if e == "delta") == "推荐番茄炒蛋"
    assert events[-1][0] == "complete"
    assert events[-1][1]["recognized_ingredients"] == []
    assert stub.closed


async def test_image_sent_to_model():
    stub = ModelStub()
    events = [event async for event in generate(payload(image_data_url="data:image/png;base64,aGVsbG8="), stub)]
    assert stub.messages[-1].content[1]["type"] == "image_url"
    assert events[-1][1]["recognized_ingredients"] == ["鸡蛋"]


async def test_invalid_result_never_completes():
    with pytest.raises(ValidationError):
        async for event in generate(payload(), ModelStub('{"summary":"ok","recommendations":[{"dish_name":"x","rating":9}]}')):
            assert event[0] != "complete"


async def test_cancellation_closes_model_stream():
    stub = ModelStub()
    stream = generate(payload(), stub)
    await anext(stream)
    await stream.aclose()
    assert stub.closed


def test_summary_escape_boundaries():
    assert summary_prefix('{"summary":"hello\\nworld\\u4f') == "hello\nworld"
    assert summary_prefix('{"summary":"hello\\nworld\\u4f60"') == "hello\nworld你"


def test_internal_authorization_and_error_event(monkeypatch):
    monkeypatch.setattr(settings, "ai_service_token", "test-token")
    app.dependency_overrides[model] = lambda: ModelStub(failure=True)
    try:
        with TestClient(app) as client:
            assert client.post("/internal/v1/recommendations/stream", json=payload().model_dump()).status_code == 401
            response = client.post("/internal/v1/recommendations/stream", headers={"Authorization": "Bearer test-token"}, json=payload().model_dump())
            assert response.status_code == 200
            assert "event: error" in response.text
            assert "event: complete" not in response.text
    finally:
        app.dependency_overrides.clear()


def test_remote_images_rejected():
    with pytest.raises(ValidationError):
        payload(image_data_url="http://localhost/private")
