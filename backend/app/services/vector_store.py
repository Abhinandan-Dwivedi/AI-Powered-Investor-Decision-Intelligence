"""
Qdrant vector store service.

Unlike the reference project (which computed embeddings but then
queried Azure Search with `search_text=`, silently falling back to
keyword search), every query here goes through `query_points` with a
real dense vector — this is actual vector search.
"""
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.core.config import settings

_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    return _client


def init_vector_store() -> None:
    """Create the Qdrant collection on startup if it doesn't already exist."""
    client = get_qdrant_client()
    existing = {c.name for c in client.get_collections().collections}

    if settings.qdrant_collection not in existing:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(
                size=settings.embedding_dimensions,
                distance=Distance.COSINE,
            ),
        )
        print(f"[qdrant] Created collection '{settings.qdrant_collection}'.")
    else:
        print(f"[qdrant] Collection '{settings.qdrant_collection}' already exists.")


def upsert_chunks(points: list[PointStruct]) -> None:
    """Upsert embedded chunks. Point IDs are deterministic (see ingestion),
    so re-ingesting the same chunk overwrites rather than duplicates."""
    client = get_qdrant_client()
    client.upsert(collection_name=settings.qdrant_collection, points=points)


def search(
    query_vector: list[float],
    company: str | None = None,
    fiscal_year: int | None = None,
    top_k: int | None = None,
):
    """Real vector similarity search, optionally filtered by metadata."""
    client = get_qdrant_client()

    conditions = []
    if company:
        conditions.append(FieldCondition(key="company", match=MatchValue(value=company)))
    if fiscal_year:
        conditions.append(FieldCondition(key="fiscal_year", match=MatchValue(value=fiscal_year)))

    query_filter = Filter(must=conditions) if conditions else None

    return client.query_points(
        collection_name=settings.qdrant_collection,
        query=query_vector,
        query_filter=query_filter,
        limit=top_k or settings.retrieval_top_k,
        with_payload=True,
    ).points


def delete_by_content_hash(content_hash: str) -> None:
    """Remove all chunks belonging to a previously-ingested document version."""
    client = get_qdrant_client()
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=Filter(
            must=[FieldCondition(key="content_hash", match=MatchValue(value=content_hash))]
        ),
    )
