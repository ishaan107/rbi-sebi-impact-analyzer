"""
Module 1: Document Store
Saves/loads parsed circulars and policy docs as structured JSON.

Schema (per circular):
{
    "doc_id": "RBI_KYC_2023_v1",
    "title": "Master Direction - KYC (2023)",
    "issuer": "RBI",              # "RBI" | "SEBI"
    "category": "KYC",
    "version": "old",             # "old" | "new"
    "date": "2023-01-10",
    "raw_text": "...",
    "source_url": "..."
}
"""
import json
import os
from src.config import DATA_PROCESSED_DIR


def save_document(doc: dict) -> str:
    """Save a parsed document to data/processed/{doc_id}.json"""
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    path = os.path.join(DATA_PROCESSED_DIR, f"{doc['doc_id']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    return path


def load_document(doc_id: str) -> dict:
    path = os.path.join(DATA_PROCESSED_DIR, f"{doc_id}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_pair(topic_prefix: str) -> tuple[dict, dict]:
    """
    Load an old/new circular pair given a shared topic prefix.
    Expects files named e.g. {topic_prefix}_old.json and {topic_prefix}_new.json
    """
    old_doc = load_document(f"{topic_prefix}_old")
    new_doc = load_document(f"{topic_prefix}_new")
    return old_doc, new_doc


def list_all_documents() -> list[str]:
    """Return all doc_ids currently in the processed store."""
    if not os.path.exists(DATA_PROCESSED_DIR):
        return []
    return [f.replace(".json", "") for f in os.listdir(DATA_PROCESSED_DIR) if f.endswith(".json")]
