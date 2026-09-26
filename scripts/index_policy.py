"""
One-off script: chunk your mock policy doc and index it into ChromaDB.
Run this once after you've written your real policy document, and again
any time you edit it.

Usage: python scripts/index_policy.py data/policy/your_policy.md
"""
import sys
from src.rag.chunking import chunk_policy_document
from src.rag.vector_store import index_policy_chunks


def main(policy_path: str):
    with open(policy_path, "r", encoding="utf-8") as f:
        text = f.read()

    doc_source = policy_path.split("/")[-1].replace(".md", "")
    chunks, metadatas, ids = chunk_policy_document(text, doc_source)
    index_policy_chunks(chunks, metadatas, ids)
    print(f"Indexed {len(chunks)} chunks from {policy_path} into ChromaDB.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/index_policy.py <path_to_policy.md>")
        sys.exit(1)
    main(sys.argv[1])
