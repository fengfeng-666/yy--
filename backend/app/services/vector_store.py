from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class VectorDocument:
    document_id: str
    content: str
    metadata: dict[str, Any]
    embedding: list[float] | None = None


@dataclass(slots=True)
class VectorSearchResult:
    document_id: str
    content: str
    metadata: dict[str, Any]
    score: float | None = None


class VectorStore(ABC):
    @abstractmethod
    def upsert_documents(self, documents: list[VectorDocument], *, collection: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def query_similar_documents(
        self,
        *,
        collection: str,
        query_text: str,
        top_k: int,
    ) -> list[VectorSearchResult]:
        raise NotImplementedError

    @abstractmethod
    def delete_documents_by_source(self, *, collection: str, source_id: str) -> None:
        raise NotImplementedError


class InMemoryVectorStore(VectorStore):
    def __init__(self) -> None:
        self._collections: dict[str, dict[str, VectorDocument]] = {}

    def upsert_documents(self, documents: list[VectorDocument], *, collection: str) -> None:
        bucket = self._collections.setdefault(collection, {})
        for document in documents:
            bucket[document.document_id] = document

    def query_similar_documents(
        self,
        *,
        collection: str,
        query_text: str,
        top_k: int,
    ) -> list[VectorSearchResult]:
        tokens = {token for token in query_text.lower().split() if token}
        bucket = self._collections.get(collection, {})
        ranked: list[VectorSearchResult] = []
        for document in bucket.values():
            content_tokens = set(document.content.lower().split())
            score = float(len(tokens & content_tokens))
            if score <= 0:
                continue
            ranked.append(
                VectorSearchResult(
                    document_id=document.document_id,
                    content=document.content,
                    metadata=document.metadata,
                    score=score,
                )
            )
        ranked.sort(key=lambda item: item.score or 0, reverse=True)
        return ranked[:top_k]

    def delete_documents_by_source(self, *, collection: str, source_id: str) -> None:
        bucket = self._collections.get(collection, {})
        for document_id in list(bucket.keys()):
            if bucket[document_id].metadata.get("source_id") == source_id:
                del bucket[document_id]


class ChromaVectorStore(VectorStore):
    def __init__(self, persist_directory: str) -> None:
        self.persist_directory = persist_directory

    def _client(self):  # pragma: no cover - optional dependency boundary
        import chromadb

        return chromadb.PersistentClient(path=self.persist_directory)

    def upsert_documents(self, documents: list[VectorDocument], *, collection: str) -> None:
        if not documents:
            return
        client = self._client()
        coll = client.get_or_create_collection(collection)
        coll.upsert(
            ids=[doc.document_id for doc in documents],
            documents=[doc.content for doc in documents],
            metadatas=[doc.metadata for doc in documents],
            embeddings=[doc.embedding for doc in documents] if documents[0].embedding else None,
        )

    def query_similar_documents(
        self,
        *,
        collection: str,
        query_text: str,
        top_k: int,
    ) -> list[VectorSearchResult]:
        client = self._client()
        coll = client.get_or_create_collection(collection)
        result = coll.query(query_texts=[query_text], n_results=top_k)
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        ids = result.get("ids", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            VectorSearchResult(
                document_id=document_id,
                content=content,
                metadata=metadata or {},
                score=None if distance is None else max(0.0, 1.0 - float(distance)),
            )
            for document_id, content, metadata, distance in zip(ids, documents, metadatas, distances)
        ]

    def delete_documents_by_source(self, *, collection: str, source_id: str) -> None:
        client = self._client()
        coll = client.get_or_create_collection(collection)
        coll.delete(where={"source_id": source_id})
