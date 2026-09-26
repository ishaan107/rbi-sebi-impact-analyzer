"""
Module 1 (support): Local Relevance Filter
Reduces a large document to its most relevant paragraphs using a
self-hosted embedding model (bge-small via sentence-transformers) --
ZERO API calls, so it never hits provider rate limits. This is the
preferred path for large documents like the KYC Master Direction.

Approach: split the OLD document into paragraphs, embed each locally,
embed the NEW document as a reference query, and keep only the top-N
most semantically relevant paragraphs from OLD. This keeps the parts
of OLD most likely to relate to what changed in NEW, while dropping
unrelated boilerplate -- entirely offline, no quota risk.
"""
from sentence_transformers import SentenceTransformer, util
from src.config import EMBEDDING_MODEL

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _split_paragraphs(text: str, min_words: int = 15) -> list[str]:
    """Split on double newlines, drop very short fragments (likely headers/noise)."""
    raw_paragraphs = [p.strip() for p in text.split("\n\n")]
    return [p for p in raw_paragraphs if len(p.split()) >= min_words]


def reduce_to_relevant_paragraphs(
    old_text: str, new_text: str, target_word_count: int = 6000
) -> str:
    """
    Returns a reduced version of old_text containing only the paragraphs
    most semantically relevant to new_text, up to approximately
    target_word_count words. Entirely local -- no API calls.
    """
    model = _get_model()
    paragraphs = _split_paragraphs(old_text)

    if not paragraphs:
        return old_text[: target_word_count * 6]  # rough char fallback

    # Encode all old paragraphs + the new document (as a single reference)
    paragraph_embeddings = model.encode(paragraphs, convert_to_tensor=True)
    new_embedding = model.encode(new_text[:5000], convert_to_tensor=True)  # cap input size

    scores = util.cos_sim(new_embedding, paragraph_embeddings)[0]
    ranked_indices = scores.argsort(descending=True).tolist()

    selected = []
    word_count = 0
    for idx in ranked_indices:
        para = paragraphs[idx]
        selected.append((idx, para))
        word_count += len(para.split())
        if word_count >= target_word_count:
            break

    # Re-sort selected paragraphs back into original document order
    # so the Diff Agent sees them in a coherent sequence
    selected.sort(key=lambda x: x[0])
    return "\n\n".join(p for _, p in selected)


if __name__ == "__main__":
    import sys
    from src.ingestion.document_store import load_document, save_document

    if len(sys.argv) < 2:
        print("Usage: python -m src.ingestion.local_reducer <doc_id_pair_topic>")
        print("Example: python -m src.ingestion.local_reducer kyc")
        sys.exit(1)

    topic = sys.argv[1]
    old_doc = load_document(f"{topic}_old")
    new_doc = load_document(f"{topic}_new")

    print(f"Reducing {topic}_old ({len(old_doc['raw_text'])} chars) using local embeddings...")
    reduced = reduce_to_relevant_paragraphs(old_doc["raw_text"], new_doc["raw_text"])
    print(f"Reduced to {len(reduced)} chars, zero API calls used.")

    old_doc["condensed_text"] = reduced
    save_document(old_doc)
    print(f"Saved. {topic}_old.json now has condensed_text.")
