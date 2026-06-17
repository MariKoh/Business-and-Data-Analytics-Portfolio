"""Lightweight, dependency-free markdown chunker.

Splits on markdown headers first (so each chunk keeps its section title for
citations), then size-bounds long sections with overlap. Kept simple and
deterministic so the index is reproducible — and so it's easy to read while
following the course.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)


_HEADER_RE = re.compile(r"^(#{1,3})\s+(.*)$")


def _split_by_headers(markdown: str) -> list[tuple[str, str]]:
    """Return (section_title, section_body) pairs."""
    sections: list[tuple[str, str]] = []
    title = ""
    buf: list[str] = []
    for line in markdown.splitlines():
        m = _HEADER_RE.match(line)
        if m:
            if buf:
                sections.append((title, "\n".join(buf).strip()))
                buf = []
            title = m.group(2).strip()
        else:
            buf.append(line)
    if buf:
        sections.append((title, "\n".join(buf).strip()))
    return [(t, b) for t, b in sections if b]


def _size_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    out, start = [], 0
    while start < len(text):
        end = start + chunk_size
        out.append(text[start:end])
        start = end - overlap
    return out


def chunk_markdown(markdown: str, source: str, chunk_size: int, overlap: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    for title, body in _split_by_headers(markdown):
        for i, piece in enumerate(_size_split(body, chunk_size, overlap)):
            chunks.append(
                Chunk(text=piece, metadata={"source": source, "section": title, "part": i})
            )
    return chunks
