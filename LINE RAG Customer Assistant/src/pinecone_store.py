"""Pinecone client + index helpers (course EP.8).

Centralises index creation and connection so ingest and retrieval share one
code path. Uses cosine similarity, matching the normalised e5 embeddings.
"""
from __future__ import annotations

import time
from functools import lru_cache

from loguru import logger
from pinecone import Pinecone, ServerlessSpec

from .config import get_settings


@lru_cache(maxsize=1)
def get_client() -> Pinecone:
    return Pinecone(api_key=get_settings().pinecone_api_key)


def ensure_index():
    """Create the serverless index if it doesn't exist, then return a handle."""
    s = get_settings()
    pc = get_client()
    existing = [idx["name"] for idx in pc.list_indexes()]
    if s.pinecone_index not in existing:
        logger.info("Creating Pinecone index {!r} (dim={})", s.pinecone_index, s.embedding_dim)
        pc.create_index(
            name=s.pinecone_index,
            dimension=s.embedding_dim,
            metric="cosine",
            spec=ServerlessSpec(cloud=s.pinecone_cloud, region=s.pinecone_region),
        )
        # wait until ready
        while not pc.describe_index(s.pinecone_index).status["ready"]:
            time.sleep(1)
    return pc.Index(s.pinecone_index)


def get_index():
    return get_client().Index(get_settings().pinecone_index)
