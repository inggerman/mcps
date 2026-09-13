"""Embedding client — LM Studio (OpenAI-compatible) embeddings."""

from __future__ import annotations

import httpx

from mcp_engineering_knowledge.config import settings
from mcp_shared.errors import McpError


def embed_text(text: str) -> list[float]:
    """Generate embeddings for a single text via LM Studio."""
    return _embed_batch([text])[0]


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts via LM Studio."""
    return _embed_batch(texts)


def _embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    try:
        with httpx.Client(timeout=settings.default_timeout) as client:
            resp = client.post(
                f"{settings.embedding_base_url}/embeddings",
                json={
                    "model": settings.embedding_model,
                    "input": texts,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data["data"]]
    except httpx.HTTPStatusError as exc:
        raise McpError(
            f"Embedding API error: {exc.response.status_code} - {exc.response.text[:200]}"
        ) from exc
    except httpx.RequestError as exc:
        raise McpError(f"Network error generating embeddings: {exc}") from exc
    except (KeyError, IndexError) as exc:
        raise McpError(f"Invalid embedding response: {exc}") from exc
