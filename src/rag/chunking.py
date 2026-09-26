"""
Module 3 (support): Chunk internal policy documents for embedding.
"""
from src.config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Simple sliding-window chunker by word count.
    Swap for LangChain's RecursiveCharacterTextSplitter if you want
    smarter boundary handling (paragraph/sentence aware).
    """
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap
    return chunks


def chunk_policy_document(doc_text: str, doc_source: str) -> tuple[list[str], list[dict], list[str]]:
    """
    Prepares chunks + metadata + ids ready for vector_store.index_policy_chunks().
    """
    chunks = chunk_text(doc_text)
    metadatas = [{"source": doc_source, "chunk_index": i} for i in range(len(chunks))]
    ids = [f"{doc_source}_chunk_{i}" for i in range(len(chunks))]
    return chunks, metadatas, ids
