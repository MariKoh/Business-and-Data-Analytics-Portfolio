"""Retrieval layer: embed the query, search Pinecone, filter by score.

Separated from generation so it can be tested in isolation and the vector store
swapped without touching the chain.
"""
from __future__ import annotations

from dataclasses import dataclass

from .config import get_settings
from .embeddings import embed_query
from .pinecone_store import get_index


@dataclass
class Hit:
    text: str
    metadata: dict
    score: float


def retrieve(query: str) -> list[Hit]:
    """Return scored hits above the similarity threshold."""
    s = get_settings()
    vec = embed_query(query)
    res = get_index().query(
        vector=vec,
        top_k=s.top_k,
        namespace=s.pinecone_namespace,
        include_metadata=True,
    )
    hits = []
    for m in res.get("matches", []):
        md = m.get("metadata", {}) or {}
        score = m.get("score", 0.0)
        if score >= s.score_threshold:
            hits.append(Hit(text=md.get("text", ""), metadata=md, score=score))
    return hits


def format_context(hits: list[Hit]) -> str:
    """Render retrieved chunks into a citation-friendly context block."""
    blocks = []
    for i, h in enumerate(hits, start=1):
        src = h.metadata.get("source", "kb")
        section = h.metadata.get("section", "")
        header = f"[{i}] {src}" + (f" — {section}" if section else "")
        blocks.append(f"{header}\n{h.text.strip()}")
    return "\n\n".join(blocks)
