"""
Module 3 (support): Vector store for internal policy documents.
Uses ChromaDB with a local sentence-transformers embedding model —
fully free, no external embedding API needed.
"""
import chromadb
from chromadb.utils import embedding_functions
from src.config import CHROMA_PERSIST_DIR, COLLECTION_NAME, EMBEDDING_MODEL

_embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL
)

_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)


def get_collection():
    return _client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=_embedding_fn,
    )


def index_policy_chunks(chunks: list[str], metadatas: list[dict], ids: list[str]):
    """
    Add policy document chunks to the vector store.
    metadatas should include e.g. {"section": "4.2", "source": "Internal Policy v2"}
    """
    collection = get_collection()
    collection.add(documents=chunks, metadatas=metadatas, ids=ids)


def query_policy(query_text: str, top_k: int = 4) -> list[dict]:
    """
    Retrieve top_k relevant policy chunks for a given query.
    Returns list of {"text": ..., "metadata": ..., "distance": ...}
    """
    collection = get_collection()
    results = collection.query(query_texts=[query_text], n_results=top_k)

    output = []
    for i in range(len(results["documents"][0])):
        output.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return output
