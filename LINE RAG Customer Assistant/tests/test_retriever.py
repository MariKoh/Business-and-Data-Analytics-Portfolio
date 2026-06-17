"""Retrieval-layer tests.

Unit tests run WITHOUT external services. The integration test needs a populated
Pinecone index + embedding model and is marked so CI can skip it.
"""
import pytest

from src.chunking import chunk_markdown
from src.config import get_settings


def test_settings_load():
    s = get_settings()
    assert s.top_k > 0
    assert 0.0 <= s.score_threshold <= 1.0
    assert s.chunk_overlap < s.chunk_size
    assert s.embedding_dim > 0


def test_chunker_keeps_section_metadata():
    md = "# Title\n\n## Calm Down\nกลิ่นลาเวนเดอร์ ช่วยให้ผ่อนคลาย\n\n## Main Character\nกลิ่นส้ม สดชื่น"
    chunks = chunk_markdown(md, source="products.md", chunk_size=600, overlap=80)
    assert chunks, "expected at least one chunk"
    assert any(c.metadata["section"] == "Calm Down" for c in chunks)
    assert all(c.metadata["source"] == "products.md" for c in chunks)


@pytest.mark.integration
def test_retrieve_returns_relevant_chunk():
    """End-to-end retrieval check (needs a populated Pinecone index)."""
    from src.retriever import retrieve

    hits = retrieve("กลิ่นไหนช่วยให้นอนหลับ")
    assert hits, "Expected at least one retrieved chunk for a sleep-related query"
    joined = " ".join(h.text for h in hits)
    assert "Calm Down" in joined or "ลาเวนเดอร์" in joined
