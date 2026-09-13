"""Qdrant store — vector database operations for engineering knowledge."""

from __future__ import annotations

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from mcp_engineering_knowledge.config import settings
from mcp_shared.errors import McpError


def _client() -> QdrantClient:
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
        timeout=settings.default_timeout,
    )


def ensure_collection() -> dict[str, Any]:
    """Create the collection if it doesn't exist."""
    try:
        client = _client()
        collections = client.get_collections().collections
        names = [c.name for c in collections]
        if settings.collection_name not in names:
            client.create_collection(
                collection_name=settings.collection_name,
                vectors_config=VectorParams(
                    size=settings.embedding_dim,
                    distance=Distance.COSINE,
                ),
            )
            return {"collection": settings.collection_name, "status": "created"}
        return {"collection": settings.collection_name, "status": "exists"}
    except Exception as exc:
        raise McpError(f"Qdrant error: {exc}") from exc


def upsert_chunks(
    points: list[dict[str, Any]],
) -> dict[str, Any]:
    """Upsert chunks with pre-computed embeddings.

    Each point: {id, vector, payload}
    """
    try:
        client = _client()
        qdrant_points = [
            PointStruct(
                id=p["id"],
                vector=p["vector"],
                payload=p["payload"],
            )
            for p in points
        ]
        client.upsert(collection_name=settings.collection_name, points=qdrant_points)
        return {"collection": settings.collection_name, "points_upserted": len(qdrant_points)}
    except Exception as exc:
        raise McpError(f"Qdrant error: {exc}") from exc


def search(
    query_vector: list[float],
    limit: int = 5,
    domain_filter: str | None = None,
    type_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Search for similar vectors with optional metadata filters."""
    try:
        client = _client()
        must_conditions: list[FieldCondition] = []
        if domain_filter:
            must_conditions.append(
                FieldCondition(key="domain", match=MatchValue(value=domain_filter))
            )
        if type_filter:
            must_conditions.append(
                FieldCondition(key="type", match=MatchValue(value=type_filter))
            )
        query_filter = Filter(must=must_conditions) if must_conditions else None
        results = client.search(
            collection_name=settings.collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter,
        )
        return [
            {"id": r.id, "score": r.score, "payload": r.payload}
            for r in results
        ]
    except Exception as exc:
        raise McpError(f"Qdrant error: {exc}") from exc


def get_all_payloads() -> list[dict[str, Any]]:
    """Get all payloads (metadata) from the collection for freshness tracking."""
    try:
        client = _client()
        results, _ = client.scroll(
            collection_name=settings.collection_name,
            limit=10000,
            with_payload=True,
            with_vectors=False,
        )
        return [
            {"id": p.id, "payload": p.payload}
            for p in results
        ]
    except Exception as exc:
        raise McpError(f"Qdrant error: {exc}") from exc


def delete_by_file_path(file_path: str) -> dict[str, Any]:
    """Delete all points for a given file_path."""
    try:
        client = _client()
        client.delete(
            collection_name=settings.collection_name,
            points_selector=Filter(
                must=[FieldCondition(key="file_path", match=MatchValue(value=file_path))]
            ),
        )
        return {"deleted_file": file_path, "status": "ok"}
    except Exception as exc:
        raise McpError(f"Qdrant error: {exc}") from exc


def count_points() -> int:
    """Count total points in the collection."""
    try:
        client = _client()
        result = client.count(
            collection_name=settings.collection_name,
            exact=True,
        )
        return result.count
    except Exception:
        return 0


def list_collections() -> list[dict[str, Any]]:
    """List all Qdrant collections."""
    try:
        client = _client()
        collections = client.get_collections().collections
        return [{"name": c.name} for c in collections]
    except Exception as exc:
        raise McpError(f"Qdrant error: {exc}") from exc
