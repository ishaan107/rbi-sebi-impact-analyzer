"""
Basic tests. Expand once real data is loaded.
Run with: pytest tests/
"""
import pytest
from src.rag.chunking import chunk_text


def test_chunk_text_basic():
    text = " ".join(["word"] * 1000)
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert len(chunks) > 1
    assert all(len(c.split()) <= 100 for c in chunks)


def test_chunk_text_empty():
    assert chunk_text("") == [""]


# TODO once real circular pairs are loaded:
# def test_diff_agent_detects_known_change():
#     ...
#     assert "video kyc" in [c["topic"].lower() for c in delta["changes"]]
