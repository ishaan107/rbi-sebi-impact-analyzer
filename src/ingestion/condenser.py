"""
Module 1 (support): Document Condenser
Large regulatory documents (some 200K+ characters) exceed free-tier LLM
token-per-minute limits when sent raw to the Diff Agent. This module
chunks a long document and produces a condensed, clause-level summary
BEFORE diffing -- preserving substantive content (obligations, thresholds,
eligibility criteria, processes) while dropping boilerplate/repetition.

This is a deliberate context-engineering decision: rather than truncating
(which risks silently dropping real changes), we summarize the full
document in sections so no part is ignored, then diff the condensed
versions. Document this tradeoff explicitly in your report.
"""
import time
from src.llm_client import generate
from src.rag.chunking import chunk_text

# Conservative pause between chunk calls to stay under free-tier
# tokens-per-minute limits (e.g. Groq free tier: 12000 TPM).
SECONDS_BETWEEN_CHUNKS = 8

CONDENSE_SYSTEM_PROMPT = """You are condensing a section of an RBI regulatory
circular for downstream comparison against another version of the same
document. Extract and preserve ALL substantive content: obligations,
eligibility criteria, thresholds, timelines, definitions, exceptions, and
procedural requirements. Drop only boilerplate (repeated headers, legal
preamble, formatting artifacts, table-of-contents entries). Do not
summarize away specific numbers, dates, or conditions -- these matter most
for detecting changes."""

CONDENSE_PROMPT_TEMPLATE = """Condense the following excerpt from a regulatory
document into a dense, information-preserving summary (aim for ~30% of
original length). Keep specific figures, conditions, and requirements intact.

Excerpt:
{chunk}

Return only the condensed text, no preamble."""


def condense_document(full_text: str, chunk_word_size: int = 1500) -> str:
    """
    Splits a long document into word-count chunks, condenses each chunk
    via LLM, and rejoins. Chunk size is chosen conservatively to stay
    well under free-tier token-per-minute limits per call.
    """
    chunks = chunk_text(full_text, chunk_size=chunk_word_size, overlap=0)
    condensed_parts = []

    for i, chunk in enumerate(chunks):
        prompt = CONDENSE_PROMPT_TEMPLATE.format(chunk=chunk)
        condensed = generate(prompt, system=CONDENSE_SYSTEM_PROMPT)
        condensed_parts.append(condensed.strip())
        print(f"  Condensed chunk {i+1}/{len(chunks)}")
        if i < len(chunks) - 1:
            time.sleep(SECONDS_BETWEEN_CHUNKS)

    return "\n\n".join(condensed_parts)


if __name__ == "__main__":
    import sys
    from src.ingestion.document_store import load_document, save_document

    if len(sys.argv) < 2:
        print("Usage: python -m src.ingestion.condenser <doc_id>")
        sys.exit(1)

    doc_id = sys.argv[1]
    doc = load_document(doc_id)
    print(f"Condensing {doc_id} ({len(doc['raw_text'])} chars)...")

    condensed_text = condense_document(doc["raw_text"])
    doc["condensed_text"] = condensed_text

    save_document(doc)
    print(f"Done. Condensed to {len(condensed_text)} chars. Saved back to {doc_id}.json")
