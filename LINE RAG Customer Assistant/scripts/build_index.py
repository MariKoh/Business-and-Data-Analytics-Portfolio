"""Convenience entry point to (re)build the vector index from the knowledge base."""
import sys

sys.path.insert(0, ".")

from src.ingest import build_index  # noqa: E402

if __name__ == "__main__":
    build_index()
