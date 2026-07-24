from app.core.config import get_settings


def build_naive_embedding(text: str) -> list[float]:
    normalized = text.strip().lower()
    if not normalized:
        return [0.0] * 8
    buckets = [0.0] * 8
    for index, char in enumerate(normalized.encode("utf-8")):
        buckets[index % 8] += float(char)
    length = max(len(normalized), 1)
    return [value / length for value in buckets]


def get_embedding_model_name() -> str:
    return get_settings().ai_embedding_model
