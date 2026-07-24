from app.services.embeddings import build_naive_embedding
from app.services.vector_store import VectorDocument, VectorStore


def index_recipe_documents(
    *,
    vector_store: VectorStore,
    collection: str,
    documents: list[tuple[str, str, dict[str, object]]],
) -> None:
    vector_store.upsert_documents(
        [
            VectorDocument(
                document_id=document_id,
                content=content,
                metadata=metadata,
                embedding=build_naive_embedding(content),
            )
            for document_id, content, metadata in documents
        ],
        collection=collection,
    )
