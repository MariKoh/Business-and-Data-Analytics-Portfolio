"""Knowledge-base ingestion: load -> chunk -> embed -> upsert to Pinecone.

Offline half of the RAG pipeline (course EP.8). Run whenever the knowledge base
changes. Deterministic so the index is reproducible.

    python -m src.ingest        # or: make index
"""
from __future__ import annotations

from pathlib import Path

from loguru import logger

from .chunking import chunk_markdown
from .config import get_settings
from .embeddings import embed_passages
from .pinecone_store import ensure_index

KB_DIR = Path("data/knowledge_base")
BATCH = 64


def load_chunks() -> list:
    s = get_settings()
    chunks = []
    for md_path in sorted(KB_DIR.glob("*.md")):
        raw = md_path.read_text(encoding="utf-8")
        chunks.extend(chunk_markdown(raw, md_path.name, s.chunk_size, s.chunk_overlap))
    logger.info("Built {} chunks from {} files", len(chunks), len(list(KB_DIR.glob('*.md'))))
    return chunks


def build_index() -> None:
    s = get_settings()
    chunks = load_chunks()
    if not chunks:
        raise RuntimeError(f"No documents found in {KB_DIR}. Add knowledge-base markdown first.")

    index = ensure_index()

    # Optional: clear the namespace so re-ingest is idempotent
    try:
        index.delete(delete_all=True, namespace=s.pinecone_namespace)
    except Exception:  # namespace may not exist yet on first run
        pass

    for start in range(0, len(chunks), BATCH):
        batch = chunks[start : start + BATCH]
        vectors = embed_passages([c.text for c in batch])
        records = [
            {
                # Pinecone vector IDs must be ASCII — use filename + global index.
                # The (possibly Thai) section title is preserved in metadata.
                "id": f"{c.metadata['source']}-{start + i}",
                "values": vec,
                "metadata": {**c.metadata, "text": c.text},
            }
            for i, (c, vec) in enumerate(zip(batch, vectors))
        ]
        index.upsert(vectors=records, namespace=s.pinecone_namespace)
        logger.info("Upserted {}/{}", min(start + BATCH, len(chunks)), len(chunks))

    logger.success("Ingestion complete -> index {!r} namespace {!r}", s.pinecone_index, s.pinecone_namespace)


if __name__ == "__main__":
    build_index()
