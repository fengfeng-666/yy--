"""Request-scoped retrieval. Documents are supplied by the authorized Java service."""
import json
import re

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from .schemas import RecommendationRequest


def tokens(text: str) -> set[str]:
    words = set(re.findall(r"[a-z0-9]+", text.lower()))
    for run in re.findall(r"[\u4e00-\u9fff]+", text):
        words.update(run[i:i + 2] for i in range(max(1, len(run) - 1)))
    return words


class FamilyRetriever(BaseRetriever):
    documents: list[Document]
    top_k: int = 4

    def _get_relevant_documents(self, query: str, *, run_manager) -> list[Document]:
        query_tokens = tokens(query)
        ranked = sorted(self.documents, key=lambda d: len(tokens(d.page_content) & query_tokens), reverse=True)
        # Preserve each source category even when the question has no lexical overlap.
        selected = []
        for category in ("family_dish", "family_preference", "dining_history"):
            selected.extend([d for d in ranked if d.metadata["source_type"] == category][:self.top_k])
        return selected


def retrieve(request: RecommendationRequest) -> list[Document]:
    documents = []
    for category, rows in (("family_dish", request.dishes), ("family_preference", request.preferences), ("dining_history", request.dining_history)):
        for index, row in enumerate(rows):
            if category == "family_dish" and row.get("is_available") is False:
                continue
            documents.append(Document(
                page_content=json.dumps(row, ensure_ascii=False)[:1800],
                metadata={"source_type": category, "source_id": str(row.get("id", index)), "title": str(row.get("name", category))},
            ))
    return FamilyRetriever(documents=documents).invoke(request.content)
