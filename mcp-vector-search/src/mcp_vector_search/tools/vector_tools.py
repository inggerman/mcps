"""Tools de vector search: Qdrant collections, upsert, search, embeddings via LM Studio."""

from __future__ import annotations

from typing import Any

import httpx
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from mcp_vector_search.config import settings
from mcp_shared.errors import McpError, NotFoundError


def _qdrant() -> QdrantClient:
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
        timeout=settings.default_timeout,
    )


def _embed(text: str) -> list[float]:
    """Genera embeddings usando LM Studio (OpenAI-compatible API)."""
    try:
        with httpx.Client(timeout=settings.default_timeout) as client:
            resp = client.post(
                f"{settings.embedding_base_url}/embeddings",
                json={"model": settings.embedding_model, "input": text},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]
    except httpx.HTTPStatusError as exc:
        raise McpError(f"Embedding API error: {exc.response.status_code} - {exc.response.text[:200]}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red al generar embeddings: {exc}") from exc
    except (KeyError, IndexError) as exc:
        raise McpError(f"Respuesta de embeddings inválida: {exc}") from exc


def list_collections() -> list[dict[str, Any]]:
    """Lista las colecciones de Qdrant."""
    try:
        client = _qdrant()
        collections = client.get_collections().collections
        return [{"name": c.name} for c in collections]
    except Exception as exc:
        raise McpError(f"Qdrant error: {exc}") from exc


def create_collection(collection_name: str, vector_dim: int | None = None) -> dict[str, Any]:
    """Crea una colección en Qdrant."""
    if not settings.allow_write:
        raise McpError("Escritura no permitida. Establece VECTOR_SEARCH_ALLOW_WRITE=true para habilitar.")
    try:
        client = _qdrant()
        dim = vector_dim or settings.embedding_dim
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        return {"collection": collection_name, "vector_dim": dim, "status": "created"}
    except Exception as exc:
        raise McpError(f"Qdrant error: {exc}") from exc


def delete_collection(collection_name: str) -> dict[str, Any]:
    """Elimina una colección de Qdrant."""
    if not settings.allow_write:
        raise McpError("Escritura no permitida. Establece VECTOR_SEARCH_ALLOW_WRITE=true para habilitar.")
    try:
        client = _qdrant()
        client.delete_collection(collection_name=collection_name)
        return {"collection": collection_name, "status": "deleted"}
    except Exception as exc:
        raise McpError(f"Qdrant error: {exc}") from exc


def upsert_points(collection_name: str, points: list[dict[str, Any]]) -> dict[str, Any]:
    """Inserta puntos con embeddings generados automáticamente.

    Cada point debe tener: id (int), text (str), y opcionalmente metadata (dict).
    """
    if not settings.allow_write:
        raise McpError("Escritura no permitida. Establece VECTOR_SEARCH_ALLOW_WRITE=true para habilitar.")
    try:
        client = _qdrant()
        qdrant_points: list[PointStruct] = []
        for p in points:
            vector = _embed(p["text"])
            qdrant_points.append(PointStruct(
                id=p["id"],
                vector=vector,
                payload={"text": p["text"], **p.get("metadata", {})},
            ))
        client.upsert(collection_name=collection_name, points=qdrant_points)
        return {"collection": collection_name, "points_upserted": len(qdrant_points)}
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Qdrant error: {exc}") from exc


def search_similar(collection_name: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Busca los puntos más similares a un texto de consulta."""
    try:
        client = _qdrant()
        query_vector = _embed(query)
        results = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
        )
        return [
            {
                "id": r.id,
                "score": r.score,
                "payload": r.payload,
            }
            for r in results
        ]
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Qdrant error: {exc}") from exc
