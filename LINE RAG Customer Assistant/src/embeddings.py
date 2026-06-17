"""Embedding model wrapper (free, local, multilingual).

Uses sentence-transformers with an e5 model, which has strong Thai support.
e5 models expect task prefixes — "query:" for searches and "passage:" for stored
documents — so we expose two methods to apply them correctly. Getting these
prefixes right materially improves Thai retrieval quality.
"""
from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from .config import get_settings


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    s = get_settings()
    return SentenceTransformer(s.embedding_model)


def embed_passages(texts: list[str]) -> list[list[float]]:
    """Embed documents for storage."""
    prefixed = [f"passage: {t}" for t in texts]
    vecs = _model().encode(prefixed, normalize_embeddings=True)
    return [v.tolist() for v in vecs]


def embed_query(text: str) -> list[float]:
    """Embed a single user query for search."""
    vec = _model().encode(f"query: {text}", normalize_embeddings=True)
    return vec.tolist()
